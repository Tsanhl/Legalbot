"""Chat Service turn pipeline (strictly sequential, each step depends on the last):

  history (Conversation Store) -> Query Processor (gRPC) -> Retrieval (gRPC)
  -> fallback gate -> prompt -> LLM (gRPC server stream) -> WebSocket tokens -> validation -> store + trace
"""
from __future__ import annotations

import json
import re as _re
import time
from typing import Awaitable, Callable

import grpc

from .. import config
from ..guard.validation import validate
from ..llm.prompts import build_system, build_user
from ..obs.trace import enqueue_review, new_trace_id, write_trace
from ..obs import improve
from ..rpc import legalbot_pb2 as pb
from ..rpc import legalbot_pb2_grpc as rpc
from .conversation_store import ConversationStore

Send = Callable[[dict], Awaitable[None]]

OUT_OF_SCOPE = ("This assistant answers questions from your law knowledge base (cases, legislation, journals, "
                "lecture notes). Your message doesn't look like a legal question — could you rephrase it?")


class Orchestrator:
    def __init__(self, store: ConversationStore):
        self.cfg = config.load()
        self.store = store
        g = self.cfg["grpc"]
        self.channel = grpc.aio.insecure_channel(
            f"{g['host']}:{g['port']}",
            options=[("grpc.max_receive_message_length", 64 << 20), ("grpc.max_send_message_length", 64 << 20)])
        self.query = rpc.QueryProcessorStub(self.channel)
        self.retrieval = rpc.RetrievalStub(self.channel)
        self.llm = rpc.LLMStub(self.channel)

    async def handle(self, msg: dict, settings: dict, send: Send) -> None:
        t0 = time.time()
        trace_id = new_trace_id()
        text = (msg.get("message") or "").strip()
        opts = msg.get("options") or {}
        strict = bool(opts.get("strict", settings.get("strict", True)))
        provider = opts.get("provider") or settings.get("provider") or self.cfg["llm"]["default_provider"]
        model = opts.get("model") or settings.get("models", {}).get(provider, "")

        user_id = msg.get("user_id") or "local"
        sid = self.store.ensure_session(msg.get("session_id"), text, user_id)
        history = self.store.history(sid, self.cfg["conversation"]["window_turns"])
        user_mid = self.store.add_message(sid, "user", text)
        await send({"type": "session", "session_id": sid, "user_message_id": user_mid, "trace_id": trace_id})

        trace = {"trace_id": trace_id, "ts": time.time(), "session_id": sid, "user_id": user_id, "question": text,
                 "provider": provider, "strict": strict, "timings_ms": {}}

        # 1. Query Processor ------------------------------------------------
        await send({"type": "status", "stage": "understanding"})
        qp = await self.query.Process(pb.ProcessRequest(
            message=text, history=[pb.Turn(**h) for h in history],
            forced_intent=opts.get("intent", "") if opts.get("intent") != "auto" else "",
            forced_topic=opts.get("topic", "") or ""))
        trace.update(intent=qp.intent, intent_confidence=qp.intent_confidence, intent_reason=qp.intent_reason,
                     topics=list(qp.topics), rewritten_query=qp.rewritten_query, is_follow_up=qp.is_follow_up,
                     safety_flags=list(qp.safety_flags))
        trace["timings_ms"]["query"] = _ms(t0)
        await send({"type": "meta", "intent": qp.intent, "intent_reason": qp.intent_reason,
                    "topics": list(qp.topics), "rewritten_query": qp.rewritten_query,
                    "is_follow_up": qp.is_follow_up, "safety_flags": list(qp.safety_flags)})

        # 2. Retrieval (skipped for non-legal chat) ----------------------------
        if qp.intent == "out_of_scope":
            sources, rr_conf = [], 0.0
            trace.update(confidence=0.0, sources=[])
            return await self._generate(sid, trace, text, qp, history, sources, send, provider, model, settings,
                                        strict, mode="chat", rr_conf=0.0)
        await send({"type": "status", "stage": "retrieving"})
        t1 = time.time()
        top_k = self.cfg["retrieval"].get("top_k_by_intent", {}).get(qp.intent, 0)
        rr = await self.retrieval.Retrieve(pb.RetrieveRequest(
            query=qp.rewritten_query, topics=list(qp.topics), trace_id=trace_id, top_k=top_k))
        sources = [_src(s) for s in rr.sources]
        trace.update(confidence=round(rr.confidence, 3), retrieval_debug=json.loads(rr.debug_json or "{}"),
                     sources=[{k: s[k] for k in ("label", "id", "score", "retrieved_by", "authority")} for s in sources])
        trace["timings_ms"]["retrieval"] = _ms(t1)
        await send({"type": "sources", "confidence": round(rr.confidence, 3),
                    "sources": [{k: v for k, v in s.items() if k != "content"} | {"snippet": s["content"][:400]}
                                for s in sources]})

        # 3. Answer ladder (never a dead end) ---------------------------------
        #   kb      confidence >= min_confidence: answer from the knowledge base
        #   kb_low  below it, "Knowledge base only" on: answer from the closest material, clearly flagged
        #   hybrid  below it: knowledge base first + general knowledge tagged [background]
        #   web     very little in the KB: official web sources, cited [W#]
        rc = self.cfg["retrieval"]
        min_conf, web_below = rc["min_confidence"], rc.get("web_below", 0.30)
        web_ok = provider in ("claude_cli", "anthropic")
        if sources and rr.confidence >= min_conf:
            mode = "kb"
        elif strict:
            mode = "kb_low"
        elif sources and rr.confidence >= web_below:
            mode = "hybrid"
        else:
            mode = "web" if web_ok else "hybrid"
        if mode == "kb" and not strict and web_ok:
            mode = "kb_web"   # documents first; Claude may look up what they don't cover
        if mode not in ("kb", "kb_web"):
            enqueue_review(trace, f"answered_{mode}")
        return await self._generate(sid, trace, text, qp, history, sources, send, provider, model, settings,
                                    strict, mode=mode, rr_conf=rr.confidence)

    async def _generate(self, sid, trace, text, qp, history, sources, send, provider, model, settings,
                        strict, mode: str, rr_conf: float):
        trace["answer_mode"] = mode
        await send({"type": "mode", "mode": mode})
        # 4. Prompt + LLM stream -------------------------------------------
        topic = qp.topics[0] if qp.topics else (sources[0]["topic"] if sources else None)
        system = build_system(config.path("kb"), qp.intent if mode != "chat" else "general", topic, strict, mode)
        user, flagged_docs = build_user(text, qp.rewritten_query, history, sources, qp.intent)
        if _re.search(r"\b(?:essay |answer )?(?:plan|outline|skeleton)\b|\bstructure (?:for|of) (?:an|my|the) (?:essay|answer)\b",
                      text, _re.I) and not _re.search(r"\b(?:write|draft) (?:the|an|my) (?:full )?essay\b", text, _re.I):
            trace["answer_format"] = "plan"
            user += ("\n\nFORMAT: this is a PLAN, not an essay. Give the thesis in one or two sentences, then each section as a "
                     "heading that states its argument with 2–4 short bullets (the point, the key authorities [S#], the "
                     "counter-argument). No paragraphs of prose. 400–700 words in total; gaps list at most 3 bullets.")
        m = _re.search(r"(\d{1,2},?\d{3}|\d{3})\s*[- ]?words?\b", text, _re.I)
        if m and mode != "chat":
            limit = int(m.group(1).replace(",", ""))
            trace["word_limit"] = limit
            user += (f"\n\nWORD LIMIT (strict): the answer itself must be {int(limit * 0.88)}–{int(limit * 0.97)} words (never over {limit}). Plan the word "
                     f"budget per section before writing, and cut the least important points rather than exceed {limit}. "
                     "Citations and any final 'Gaps in the knowledge base' / 'Web sources' lists do not count; keep those "
                     "lists to at most 5 short bullets. Do not print a word count.")
        trace.update(prompt_chars=len(system) + len(user), flagged_documents=flagged_docs, style_topic=topic)
        await send({"type": "status", "stage": "generating", "provider": provider})
        t2 = time.time()
        parts: list[str] = []
        first_token_ms = None
        error = ""
        call = self.llm.Generate(pb.GenerateRequest(
            provider=provider, system_prompt=system, user_prompt=user, model=model, web=mode in ("web", "kb_web"),
            api_key=settings.get("api_keys", {}).get(provider, "")))
        try:
            async for tok in call:
                if tok.error:
                    error = tok.error
                    break
                if tok.text:
                    if first_token_ms is None:
                        first_token_ms = _ms(t2)
                    parts.append(tok.text)
                    await send({"type": "token", "text": tok.text})
                if tok.info:
                    trace["provider_info"] = tok.info
        finally:
            call.cancel()
        trace["timings_ms"].update(first_token=first_token_ms, generation=_ms(t2))
        answer = "".join(parts)
        if error:
            trace["error"] = error
            await send({"type": "error", "message": error})
            if not answer:
                return await self._finish(sid, trace, f"⚠️ Generation failed: {error}", sources, send, fallback="error")
        return await self._finish(sid, trace, answer, sources, send)

    async def _finish(self, sid, trace, answer, sources, send, fallback: str = ""):
        mode = trace.get("answer_mode", "kb")
        if mode in ("kb", "kb_web"):   # label by what the answer actually used
            mode = "web" if _re.search(r"\[W\d+\]", answer) else \
                "hybrid" if len(_re.findall(r"\[(?:background|unverified)[^\]]*\]", answer)) > 2 else "kb"
            trace["answer_mode"] = mode
        v = validate(answer, sources, mode) if (sources or mode == "web") and not fallback else {"verdict": "n/a"}
        original = answer
        # ---- Accuracy guard (automatic, every answer) -------------------------------
        # Any case / Act named that is not in the sources used is looked up in the WHOLE knowledge base.
        # Found there -> accepted. Not found anywhere -> marked ⚠︎ in the text and listed for checking.
        unverified, in_kb = [], []
        try:
            for name in (v.get("unsupported_authorities") or [])[:10]:
                r = await self.retrieval.Retrieve(pb.RetrieveRequest(query=name, top_k=3))
                hay = " ".join((x.title + " " + x.content).lower() for x in r.sources)
                toks = [t for t in _re.findall(r"[a-z]{4,}|\d{4}", name.lower()) if t not in {"with", "from"}]
                (in_kb if toks and sum(t in hay for t in toks) >= max(1, (len(toks) + 1) // 2) else unverified).append(name)
            if unverified:
                for name in unverified:
                    answer = answer.replace(name, f"{name} ⚠︎")
                answer += ("\n\n---\n**Accuracy check:** ⚠︎ marks authorities that were not found in your knowledge base "
                           "or in a cited web source. Verify them before relying on them: " + "; ".join(unverified) + ".")
            v.update(unsupported_authorities=unverified, verified_elsewhere_in_kb=in_kb)
            if v.get("verdict") in ("warn", "fail") and not v.get("invalid_labels") and not v.get("no_citation"):
                v["verdict"] = "warn" if (unverified or v.get("unverified_sentences")) else "pass"
        except Exception as e:
            trace["guard_error"] = str(e)
        # ---- Word limit ------------------------------------------------------------
        limit = trace.get("word_limit")
        if limit and not fallback:
            body = _re.split(r"\n(?:---\n)?\**(?:Gaps in the knowledge base|Web sources|Accuracy check)", answer)[0]
            words = len(_re.findall(r"\b[\w’'-]+\b", _re.sub(r"\[(?:S|W)\d+\]|\[background\]", "", body)))
            v.update(word_limit=limit, words=words)
        support = {}
        try:
            from ..guard.validation import support_passages
            support = support_passages(original, sources) if sources and not fallback else {}
        except Exception as e:
            trace["support_error"] = str(e)
        trace["support"] = support
        trace.update(answer=answer, validation=v, validation_verdict=v["verdict"], fallback=fallback,
                     total_ms=int((time.time() - trace["ts"]) * 1000))
        if v["verdict"] == "fail":
            enqueue_review(trace, "validation_fail")
        try:  # improvement inbox: ONE item per answer, only when there is something specific to add
            if not fallback:
                trace.setdefault("sources", [{"label": s["label"], "id": s["id"]} for s in sources])
                details = improve.missing_authorities(original) + [f"unverified: {x}" for x in unverified]
                urls = sorted(set(_re.findall(r"https?://[^\s)>\]]+", original)))[:10]
                details += [f"web source: {u}" for u in urls]
                details += [f"invalid label: {x}" for x in v.get("invalid_labels", [])]
                if details:
                    improve.record_gap(trace, "missing authority" if not urls else "answered from the web", details)
        except Exception as e:  # never break a reply because of logging
            trace["improve_error"] = str(e)
        mid = self.store.add_message(sid, "assistant", answer, {
            "trace_id": trace["trace_id"], "validation": v, "fallback": fallback,
            "confidence": trace.get("confidence"), "intent": trace.get("intent"), "support": support,
            "mode": mode,
            "sources": [{k: s[k] for k in ("label", "id", "title", "authority", "score", "original_path")} for s in sources]})
        write_trace(trace)
        await send({"type": "done", "message_id": mid, "trace_id": trace["trace_id"], "validation": v,
                    "mode": mode, "support": support,
                    "fallback": fallback, "answer": answer if (fallback or answer != original) else None,
                    "timings_ms": trace["timings_ms"], "total_ms": trace["total_ms"]})


def _src(s) -> dict:
    return {"id": s.id, "title": s.title, "topic": s.topic, "kind": s.kind, "authority": s.authority,
            "content": s.content, "original_path": s.original_path, "score": round(s.score, 4),
            "retrieved_by": s.retrieved_by, "label": s.label}


def _ms(t0: float) -> int:
    return int((time.time() - t0) * 1000)
