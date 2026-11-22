"""Knowledge-update loop:
   unanswered / low confidence / thumbs-down -> cluster -> expert review -> update KB -> re-index -> add to eval set

  python -m legalbot.loop list                 pending items
  python -m legalbot.loop cluster              group pending questions by topic + shared terms
  python -m legalbot.loop promote <trace_id> --source <expected id> [--category paraphrase]
                                               add a reviewed question to eval/evalset.yaml, mark it resolved
  python -m legalbot.loop out-of-scope <trace_id>   add as a negative eval case, mark resolved
  python -m legalbot.loop report [--days 7]    write improvement/weekly_report.md: fallbacks, weak answers, missing law
"""
from __future__ import annotations

import argparse
import json
from collections import defaultdict

import yaml

from . import config
from .retrieval.markdown_kb import tokenize

Q = lambda: config.path("review_queue") / "pending.jsonl"  # noqa: E731
DONE = lambda: config.path("review_queue") / "resolved.jsonl"  # noqa: E731


def pending() -> list[dict]:
    p = Q()
    return [json.loads(l) for l in p.read_text().splitlines() if l.strip()] if p.exists() else []


def cluster(items: list[dict]) -> list[dict]:
    groups: list[dict] = []
    for it in items:
        toks = set(tokenize(it.get("rewritten_query") or it["question"]))
        topic = ",".join(it.get("topics") or []) or "unrouted"
        best = None
        for g in groups:
            if g["topic"] == topic and len(toks & g["tokens"]) / max(len(toks | g["tokens"]), 1) >= 0.3:
                best = g
                break
        if best:
            best["items"].append(it)
            best["tokens"] |= toks
        else:
            groups.append({"topic": topic, "tokens": toks, "items": [it]})
    groups.sort(key=lambda g: -len(g["items"]))
    return groups


def resolve(trace_id: str, resolution: str):
    items = pending()
    keep = [i for i in items if i["trace_id"] != trace_id]
    done = [i for i in items if i["trace_id"] == trace_id]
    Q().write_text("".join(json.dumps(i) + "\n" for i in keep))
    with open(DONE(), "a") as f:
        for i in done:
            f.write(json.dumps({**i, "resolution": resolution}) + "\n")
    return done[0] if done else None


def add_eval(case: dict):
    p = config.path("eval") / "evalset.yaml"
    cases = (yaml.safe_load(p.read_text()) or []) if p.exists() else []
    cases.append(case)
    p.write_text(yaml.safe_dump(cases, sort_keys=False, allow_unicode=True))


GAP_CASE = __import__("re").compile(r"\*([A-Z][^*\n]{2,80}?)\*")


def report(days: int) -> str:
    """Summarise recent traces: what failed, and which authorities users needed but the KB lacks."""
    import re
    import time
    from collections import Counter
    cutoff = time.time() - days * 86400
    traces = []
    for f in sorted((config.path("debug") / "logs").glob("*.jsonl")):
        for line in f.read_text().splitlines():
            try:
                t = json.loads(line)
            except ValueError:
                continue
            if float(t.get("ts", 0)) >= cutoff:
                traces.append(t)
    n = len(traces)
    fb = [t for t in traces if t.get("fallback")]
    low = [t for t in traces if not t.get("fallback") and (t.get("confidence") or 1) < 0.6]
    bad = [t for t in traces if t.get("validation_verdict") in ("warn", "fail")]
    missing_auth, missing_tok = Counter(), Counter()
    for t in traces:
        ans = t.get("answer") or ""
        gap = ans.split("Gaps in the knowledge base")[-1] if "Gaps in the knowledge base" in ans else ""
        for m in GAP_CASE.findall(gap.replace("**", "")):
            m = m.strip()
            if not m.endswith(".") and len(m.split()) <= 8:
                missing_auth[m] += 1
        for m in re.findall(r"([^.\n]{0,80})\[authority not in knowledge base\]", ans):
            missing_auth[m.strip()[-80:]] += 1
        dbg = t.get("retrieval_debug") or {}
        for tok in (dbg.get("bm25") or {}).get("missing_tokens", []):
            missing_tok[tok] += 1
    by_topic = Counter(tp for t in traces for tp in (t.get("topics") or ["(unrouted)"]))
    L = [f"# Improvement report: last {days} days", "",
         f"{n} questions · {len(fb)} fallbacks (no answer) · {len(low)} low-confidence answers · "
         f"{len(bad)} grounding warn/fail · {len(pending())} items waiting in the review queue", "",
         "## What to do", "",
         "1. **Fallbacks / low confidence**: is the law missing (add a file to the Law folder or a note), or was the "
         "question badly routed? Then `python -m legalbot.loop promote <trace_id> --source <id>` or `out-of-scope <trace_id>`.",
         "2. **Missing authorities**: download or add the judgments/Acts listed below, then `python -m legalbot.ingest.run` "
         "and `python -m legalbot.index build`.",
         "3. **Grounding warn/fail**: open the trace in the chat's Logs tab; file an issue (⚑ report) if retrieval was wrong.", "",
         "## Questions by topic", ""] + [f"- {k}: {v}" for k, v in by_topic.most_common()] + [""]
    def rows(title, items, extra):
        L.extend([f"## {title} ({len(items)})", ""])
        L.extend(f"- `{t['trace_id']}` {extra(t)} — {(t.get('question') or '')[:140]}" for t in items[-40:])
        L.append("")
    rows("Fallbacks (the bot did not answer)", fb, lambda t: f"**{t.get('fallback')}**")
    rows("Low-confidence answers", low, lambda t: f"conf {t.get('confidence')}")
    rows("Grounding warn / fail", bad, lambda t: f"**{t.get('validation_verdict')}**")
    L.extend(["## Authorities the answers needed but the knowledge base lacks", ""]
             + ([f"- {k} ({v}×)" for k, v in missing_auth.most_common(40)] or ["- none recorded"]) + [""])
    L.extend(["## Search words not found anywhere in the knowledge base", ""]
             + ([f"- {k} ({v}×)" for k, v in missing_tok.most_common(30)] or ["- none"]) + [""])
    out = config.path("review_queue") / "weekly_report.md"
    out.write_text("\n".join(L) + "\n")
    return str(out)


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list")
    sub.add_parser("cluster")
    rp = sub.add_parser("report")
    rp.add_argument("--days", type=int, default=7)
    pr = sub.add_parser("promote")
    pr.add_argument("trace_id")
    pr.add_argument("--source", required=True)
    pr.add_argument("--category", default="paraphrase")
    oo = sub.add_parser("out-of-scope")
    oo.add_argument("trace_id")
    a = ap.parse_args()
    if a.cmd == "report":
        print("wrote", report(a.days))
        return

    if a.cmd == "list":
        for i in pending():
            print(f"{i['trace_id']}  [{i['reason']}] conf={i.get('confidence')}  {i['question'][:90]}")
    elif a.cmd == "cluster":
        for g in cluster(pending()):
            print(f"\n## {g['topic']}  ({len(g['items'])} questions)  terms: {sorted(g['tokens'])[:10]}")
            for i in g["items"]:
                print(f"   - {i['trace_id']}  {i['question'][:90]}")
    elif a.cmd in ("promote", "out-of-scope"):
        it = resolve(a.trace_id, a.cmd)
        if not it:
            raise SystemExit("trace not in pending queue")
        neg = a.cmd == "out-of-scope"
        add_eval({"id": f"loop-{a.trace_id}", "category": "negative" if neg else a.category,
                  "query": it["question"], "expected_sources": [] if neg else [a.source],
                  "expected_behavior": "fallback" if neg else "answer"})
        print("added to eval/evalset.yaml" + ("" if neg else " — now update the KB, re-index, and run the eval"))


if __name__ == "__main__":
    main()
