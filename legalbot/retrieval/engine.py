"""Retrieval engine: BM25 sections  +  FAISS chunks  ->  RRF fusion  ->  cross-encoder rerank.

    query ─┬─ Markdown KB (section BM25) ── top sections ─┐
           └─ Vector RAG (chunk FAISS) ─── top chunks ──→ parent section ─┤
                                                          RRF fuse ─→ rerank ─→ final top-K + confidence
"""
from __future__ import annotations

import dataclasses
import json
import logging
import math
import re
import time
from pathlib import Path

from .. import config
from ..kb import Section, load_manifests, load_sections
from .markdown_kb import BM25Index, load_synonyms, tokenize
from .vector_rag import VectorIndex, make_chunks

log = logging.getLogger(__name__)


class RetrievalEngine:
    def __init__(self):
        self.cfg = config.load()["retrieval"]
        self.kb_root = config.path("kb")
        self.idx_dir = config.path("indexes")
        self.sections: list[Section] = []
        self.bm25 = BM25Index()
        self.vector: VectorIndex | None = None
        self._reranker = None
        self.manifests: dict = {}
        self.built_at = None

    # ------------------------------------------------------------------ build
    def build(self, only=None) -> dict:
        """Full rebuild from kb/ (raw + notes). Write-then-swap so a failed build keeps the old index.
        `only`: optional filter on sections (used for the shareable public index)."""
        t0 = time.time()
        sections = load_sections(self.kb_root)
        if only:
            sections = [s for s in sections if only(s)]
        tmp = self.idx_dir.with_name(self.idx_dir.name + ".tmp")
        tmp.mkdir(parents=True, exist_ok=True)
        (tmp / "sections.json").write_text(json.dumps([dataclasses.asdict(s) for s in sections], default=str))
        stats = {"sections": len(sections), "chunks": 0, "vector": False}
        if self.cfg["use_vector"]:
            try:
                chunks = make_chunks(sections, self.cfg["chunk_chars"], self.cfg["chunk_overlap"])
                VectorIndex(self.cfg["embedding_model"]).build(chunks, config.ROOT / "data" / "embedding_cache.sqlite3").save(tmp)
                stats.update(chunks=len(chunks), vector=True)
            except Exception as e:  # vector track is optional; BM25 still works
                log.warning("vector index build failed: %s", e)
                stats["vector_error"] = str(e)
        (tmp / "build.json").write_text(json.dumps({**stats, "built_at": time.time()}))
        if self.idx_dir.exists():
            old = self.idx_dir.with_name(self.idx_dir.name + ".old")
            if old.exists():
                _rmtree(old)
            self.idx_dir.rename(old)
            tmp.rename(self.idx_dir)
            _rmtree(old)
        else:
            tmp.rename(self.idx_dir)
        stats["seconds"] = round(time.time() - t0, 1)
        self.load()
        return stats

    def load(self) -> bool:
        self.manifests = load_manifests(self.kb_root)
        sj = self.idx_dir / "sections.json"
        if not sj.exists():
            log.warning("no index yet — run: python -m legalbot.index build")
            self.sections = []
            self.bm25.build([], [])
            return False
        self.sections = [Section(**d) for d in json.loads(sj.read_text())]
        self.bm25.build(self.sections, load_synonyms(self.kb_root / "synonyms.yaml"))
        if self.cfg["use_vector"]:
            try:
                v = VectorIndex(self.cfg["embedding_model"])
                self.vector = v if v.load(self.idx_dir) else None
            except Exception as e:
                log.warning("vector index unavailable: %s", e)
                self.vector = None
        bj = self.idx_dir / "build.json"
        self.built_at = json.loads(bj.read_text()).get("built_at") if bj.exists() else None
        return True

    @property
    def reranker(self):
        if self._reranker is None and self.cfg["use_reranker"]:
            try:
                from sentence_transformers import CrossEncoder
                self._reranker = CrossEncoder(self.cfg["reranker_model"])
            except Exception as e:
                log.warning("reranker unavailable: %s", e)
                self.cfg["use_reranker"] = False
        return self._reranker

    # --------------------------------------------------------------- retrieve
    ACT_REF = re.compile(r"((?:[A-Z][a-z]+ |and |of |the |for |to )*[A-Z][a-z]+ Act \d{4})(?:,? ss?\.? ?(\d+[A-Z]?))?")
    ACT_ABBR = {"OAPA": "Offences Against the Person Act 1861", "MCA": "Mental Capacity Act 2005",
                "LRA": "Land Registration Act 2002", "LPA": "Law of Property Act 1925", "HTA": "Human Tissue Act 2004",
                "TOLATA": "Trusts of Land and Appointment of Trustees Act 1996", "CRA": "Consumer Rights Act 2015",
                "SGA": "Sale of Goods Act 1979", "FLRA": "Family Law Reform Act 1969", "TA": "Trustee Act 1925",
                "PA": "Pensions Act 1995", "CJA": "Criminal Justice Act 1988",
                "HFEA": "Human Fertilisation and Embryology Act 1990", "HFE Act": "Human Fertilisation and Embryology Act 1990"}
    ACT_ABBR_RE = re.compile(r"\b(ss?\.? ?\d+[A-Z]?(?:\(\d+\))?(?:(?:,| and| or|,? ?[-–]) ?\d+[A-Z]?(?:\(\d+\))?)*\s+(?:of (?:the )?)?)?"
                             r"(OAPA|MCA|LRA|LPA|HTA|TOLATA|CRA|SGA|FLRA|CJA|HFEA|HFE Act)(?: \d{4})?(?: \(as amended\))?(?:,? ss?\.? ?(\d+[A-Z]?))?\b")
    CASE_NAME = re.compile(r"\*([A-Z][A-Za-z'’.&() -]{3,90})\*")   # italic case names in notes, incl. short names

    def _follow_authorities(self, query: str, final: list, topics: list[str] | None, limit: int, c_stat: int = 3) -> list:
        """Two-hop retrieval: cases named in the retrieved notes are fetched as primary sources.

        An abstract essay title rarely names the leading cases; the topic note does. Cheap (BM25 only)."""
        if limit <= 0:
            return []
        have = {self.sections[i].file for i, _ in final}
        names = []
        note_topics = {self.sections[i].topic for i, _ in final if self.sections[i].kind == "note"}
        for i, _ in final:
            sec = self.sections[i]
            if sec.kind != "note":
                continue
            for m in self.CASE_NAME.finditer(sec.content.replace("**", "")):
                nm = m.group(1).strip()
                looks_like_case = (" v " in nm or nm.startswith(("Re ", "R (")) or
                                   (len(nm.split()) <= 3 and not nm.endswith((".", ":"))))
                if looks_like_case and nm not in names:
                    names.append(nm)
        # cases whose sentence shares words with the question come first
        q = set(tokenize(query))
        def near(nm: str) -> int:
            best = 0
            for i, _ in final:
                c = self.sections[i].content
                k = c.find(f"*{nm}*")
                if k >= 0:
                    best = max(best, len(q & set(tokenize(c[max(0, k - 200): k + 300]))))
            return -best
        names.sort(key=near)
        extra = []
        # statutes named in the notes ("Mental Capacity Act 2005, s 3") -> that section of the Act
        acts = []
        note_files = {self.sections[i].file for i, _ in final if self.sections[i].kind == "note"}
        texts = [query] + [sec.content for sec in self.sections if sec.file in note_files]
        for txt in texts:
            for m in self.ACT_REF.finditer(txt):
                name = re.sub(r"^(?:(?:of|the|and|for|to) )+", "", m.group(1).strip())
                acts.append((name, m.group(2) or ""))
                window = txt[m.end(): m.end() + 260]
                window = re.split(r"\b[A-Z][a-z]+ Act \d{4}", window)[0]   # stop at the next Act named
                acts.extend((name, n) for n in re.findall(r"\bss?\.? ?(\d+[A-Z]?)\b", window))
            for m in self.ACT_ABBR_RE.finditer(txt):   # "ss47, 20 and 18 OAPA 1861", "s 3 MCA", "MCA 2005, s 4"
                nums = re.findall(r"\d+[A-Z]?", m.group(1) or "") or ([m.group(3)] if m.group(3) else [])
                acts.extend((self.ACT_ABBR[m.group(2)], n) for n in nums)
        for txt in texts:   # "Sch 3 para 2 LRA 2002" / "Schedule 3 to the Land Registration Act 2002"
            for m in re.finditer(r"\bSch(?:edule)?\.? ?(\d+)\b[^.\n]{0,40}?\b(LRA|MCA|HTA|CRA|TOLATA)\b", txt):
                key = (self.ACT_ABBR[m.group(2)], f"Schedule {m.group(1)}")
                if key not in acts:
                    acts.append(key)
        for txt in texts:   # "Land Registration Act 2002 … Schedule 3"
            for m in re.finditer(r"((?:[A-Z][a-z]+ )+Act \d{4})[^\n]{0,160}?\bSchedule (\d+)\b", txt):
                acts.append((m.group(1).strip(), f"Schedule {m.group(2)}"))
        acts = [a for a in acts if a[1]]   # only specific provisions: a bare Act name is too vague to follow
        q = set(tokenize(query))
        from collections import Counter
        freq = Counter(acts)
        acts = sorted(set(acts), key=lambda a: (-len(q & set(tokenize(a[0]))), -freq[a]))
        used_idx = {i for i, _ in final}
        # rank candidate sections by how well the section's own heading matches the question
        if getattr(self, "_leg", None) is None:
            self._leg = [(i, sec.title.lower()) for i, sec in enumerate(self.sections) if sec.authority == "legislation"]

        def sec_rank(a):
            want = rf"> {re.escape(a[1].lower())}\b" if a[1].startswith("Schedule") else rf"> s ?{re.escape(a[1].lower())}\b"
            t = next((t for _, t in self._leg if t.startswith(a[0].lower()) and re.search(want, t)), "")
            return (0 if t else 1, -len(q & set(tokenize(t))))
        acts = sorted(dict.fromkeys(acts), key=sec_rank)
        if getattr(self, "_leg", None) is None:   # direct lookup table: legislation sections only
            self._leg = [(i, sec.title.lower()) for i, sec in enumerate(self.sections) if sec.authority == "legislation"]
        for act, sec in acts[:12]:
            act_l = act.lower()
            want = (rf"> {re.escape(sec.lower())}\b" if sec.startswith("Schedule")
                    else rf"> s(?:ection)? ?{re.escape(sec.lower())}\b")
            hits = [{"idx": i} for i, t in self._leg if t.startswith(act_l) and re.search(want, t)]
            act_t = set(tokenize(act))
            for h in hits:
                s2 = self.sections[h["idx"]]
                if s2.authority != "legislation" or h["idx"] in used_idx:
                    continue
                if not act_t <= set(tokenize(s2.title + " " + s2.file.replace("-", " "))):
                    continue
                if sec.startswith("Schedule"):
                    if not re.search(rf"\b{re.escape(sec)}\b", s2.title, re.I):
                        continue
                elif "schedule" in s2.title.lower() or not re.search(rf"> s(?:ection)? ?{re.escape(sec)}\b", s2.title, re.I):
                    continue   # a section of the Act itself, not a Schedule entry amending another Act
                extra.append((h["idx"], {"rrf": 0.0, "by": {"bm25"}, "followed_from": f"{act} s {sec}".strip()}))
                used_idx.add(h["idx"])
                break
            if len(extra) >= c_stat:
                break
        for nm in names[:12]:
            hits, _ = self.bm25.search(nm, 25, topics)
            key = [t for t in tokenize(nm) if len(t) > 3][:2]
            # the judgment itself (case name in its title / file name) before articles that discuss it
            hits.sort(key=lambda h: 0 if key and all(k in (self.sections[h["idx"]].title + " " + self.sections[h["idx"]].file).lower()
                                                    for k in key) else 1)
            for h in hits:
                sec = self.sections[h["idx"]]
                if sec.authority == "case_law" and sec.file not in have and sec.topic in note_topics:
                    extra.append((h["idx"], {"rrf": 0.0, "by": {"bm25"}, "followed_from": nm}))
                    have.add(sec.file)
                    break
            if len(extra) >= limit + c_stat:
                break
        return extra

    ACADEMIC = re.compile(r"\b([A-Z][a-z]{2,})(?: (?:and|&) ([A-Z][a-z]{2,}))?(?:,? (?:et al\.?))?"
                          r"(?:,? ['‘\"][^'’\"\n]{5,200}['’\"])? \(((?:19|20)\d\d)\)")

    def _follow_academics(self, query: str, final: list, limit: int) -> list:
        """Articles / chapters named in the retrieved notes ("Robinson (2024)") -> their best-matching section."""
        if limit <= 0:
            return []
        note_files = {self.sections[i].file for i, _ in final if self.sections[i].kind == "note"}
        topics_ = {self.sections[i].topic for i, _ in final if self.sections[i].kind == "note"}
        q = set(tokenize(query))
        scored: dict = {}
        for sec in self.sections:
            if sec.file in note_files:
                for m in self.ACADEMIC.finditer(sec.content):
                    r = (m.group(1).lower(), (m.group(2) or "").lower(), m.group(3))
                    ctx = sec.content[max(0, m.start() - 300): m.end() + 300]
                    scored[r] = max(scored.get(r, 0), len(q & set(tokenize(ctx))))   # closeness to the question
        refs = sorted(scored, key=lambda r: -scored[r])
        have = {self.sections[i].file for i, _ in final}
        out = []
        for a1, a2, year in refs[:15]:
            cands = [i for i, sec in enumerate(self.sections)
                     if sec.kind == "raw" and sec.topic in topics_ and sec.authority in ("journal", "textbook", "secondary")
                     and sec.file not in have and a1 in sec.file.lower() and year in sec.file and (not a2 or a2 in sec.file.lower())]
            if not cands:
                continue
            best = max(cands, key=lambda i: len(q & set(tokenize(self.sections[i].content[:3000]))))
            out.append((best, {"rrf": 0.0, "by": {"bm25"}, "followed_from": f"{a1} ({year})"}))
            have.add(self.sections[best].file)
            if len(out) >= limit:
                break
        return out

    def retrieve(self, query: str, topics: list[str] | None, top_k: int | None = None) -> dict:
        c = self.cfg
        top_k = top_k or c["final_top_k"]
        t0 = time.time()
        if topics:  # cross-topic primary sources (manifest always_search) join every routed search
            topics = list(dict.fromkeys(list(topics) + [s for s, m in self.manifests.items() if m.get("always_search")]))
        debug: dict = {"query": query, "topics_filter": topics or [], "timings_ms": {}}

        bm25_hits, bm25_dbg = self.bm25.search(query, c["bm25_top_k"], topics)
        debug["bm25"] = {**bm25_dbg, "hits": bm25_hits}
        debug["timings_ms"]["bm25"] = _ms(t0)

        vec_hits = []
        if self.vector:
            t1 = time.time()
            vec_hits = self.vector.search(query, c["vector_top_k"], topics)
            debug["timings_ms"]["vector"] = _ms(t1)
        debug["vector"] = {"enabled": bool(self.vector), "hits": vec_hits}

        # topic filter too strict? (router guessed wrong) -> retry unfiltered, record it
        if topics and not bm25_hits and not vec_hits:
            debug["topic_filter_relaxed"] = True
            return {**self.retrieve(query, None, top_k), "relaxed": True}

        # ---- RRF fusion at section level (chunk -> parent section) ----
        fused: dict[int, dict] = {}
        for rank, h in enumerate(bm25_hits):
            e = fused.setdefault(h["idx"], {"rrf": 0.0, "by": set(), "bm25_rank": None, "vec_rank": None})
            e["rrf"] += 1 / (c["rrf_k"] + rank + 1)
            e["by"].add("bm25")
            e["bm25_rank"] = rank + 1
        seen_sec = set()
        vrank = 0
        for h in vec_hits:
            si = h["section_idx"]
            if si in seen_sec:
                continue
            seen_sec.add(si)
            e = fused.setdefault(si, {"rrf": 0.0, "by": set(), "bm25_rank": None, "vec_rank": None})
            e["rrf"] += 1 / (c["rrf_k"] + vrank + 1)
            e["by"].add("vector")
            e["vec_rank"] = vrank + 1
            e["similarity"] = h["similarity"]
            vrank += 1
        cands = sorted(fused.items(), key=lambda kv: -kv[1]["rrf"])[: c["fused_top_k"]]

        # ---- Stage 2: cross-encoder rerank ("can it answer?", FM2 fix) ----
        rr = self.reranker if cands else None
        if rr is not None:
            t2 = time.time()
            pairs = [(query, f"{self.sections[i].title}\n{self.sections[i].content[:2000]}") for i, _ in cands]
            scores = rr.predict(pairs, show_progress_bar=False)
            for (i, e), s in zip(cands, scores):
                p_ = min(max(float(s), 1e-9), 1 - 1e-9)
                e["rerank"] = math.log(p_ / (1 - p_))  # back to logit: sigmoid output is badly calibrated
            # final order = rank fusion of first-stage order and rerank order (reranker alone overfits on short sections)
            by_rr = sorted(range(len(cands)), key=lambda j: -cands[j][1]["rerank"])
            for r, j in enumerate(by_rr):
                cands[j][1]["final"] = 1 / (c["rrf_k"] + j + 1) + 1.5 / (c["rrf_k"] + r + 1)
            cands.sort(key=lambda kv: -kv[1]["final"])
            debug["timings_ms"]["rerank"] = _ms(t2)

        # diversity: at most `max_per_doc` sections from one file, so one long article cannot crowd out
        # the cases and notes; and keep the best note (our rephrased knowledge) if one was a candidate
        cap, final, per_doc = c.get("max_per_doc", 2), [], {}
        cap_leg = c.get("max_per_statute", 4)   # an Act can legitimately supply several sections
        for i, e in cands:
            f = self.sections[i].file
            if per_doc.get(f, 0) < (cap_leg if self.sections[i].authority == "legislation" else cap):
                final.append((i, e)); per_doc[f] = per_doc.get(f, 0) + 1
            if len(final) >= top_k:
                break
        if final and not any(self.sections[i].kind == "note" for i, _ in final):
            note = next(((i, e) for i, e in cands if self.sections[i].kind == "note"), None)
            if note:
                final[-1] = note
        # always consult our own notes: they are the map to the leading cases and statutes
        have_notes = {self.sections[i].file for i, _ in final if self.sections[i].kind == "note"}
        want = c.get("min_notes", 3)
        if len(have_notes) < want:
            # rank note sections by meaning (vector) + keywords (BM25), fused; best section per note file
            score: dict[int, float] = {}
            nh, _ = self.bm25.search(query, 400, topics)
            for r_, h in enumerate([h for h in nh if self.sections[h["idx"]].kind == "note"][:40]):
                score[h["idx"]] = score.get(h["idx"], 0) + 1 / (c["rrf_k"] + r_ + 1)
            if self.vector:
                vh = self.vector.search(query, 60, topics, kind="note")
                for r_, h in enumerate(vh):
                    score[h["section_idx"]] = score.get(h["section_idx"], 0) + 1.3 / (c["rrf_k"] + r_ + 1)
            for i in sorted(score, key=lambda k: -score[k]):
                sec = self.sections[i]
                if sec.file in have_notes:
                    continue
                final.append((i, {"rrf": 0.0, "by": {"notes"}, "note_search": True}))
                have_notes.add(sec.file)
                if len(have_notes) >= want:
                    break
        main = [x for x in final if not x[1].get("note_search")] or list(final)  # confidence on ranked results only
        long_answer = top_k >= 12   # essays / problem questions get more primary sources and the academics behind the notes
        final = final + self._follow_authorities(query, final, topics, c.get("max_followed_cases", 3) + (3 if long_answer else 0), 5 if long_answer else 3)
        final = final + self._follow_academics(query, final, 3 if long_answer else 1)
        sources = []
        for n, (i, e) in enumerate(final, 1):
            s = self.sections[i]
            score = e.get("rerank", e["rrf"])  # logit when reranked, else RRF
            sources.append({
                "id": s.id, "title": s.title, "topic": s.topic, "kind": s.kind,
                "authority": s.authority, "content": s.content, "original_path": s.original_path,
                "score": round(float(score), 4), "label": f"S{n}",
                "retrieved_by": "both" if len(e["by"]) == 2 else next(iter(e["by"])),
            })
        confidence = self._confidence(query, main)
        debug["fused"] = [
            {"id": self.sections[i].id, "rrf": round(e["rrf"], 5), "by": sorted(e["by"]),
             "bm25_rank": e["bm25_rank"], "vec_rank": e["vec_rank"],
             "similarity": e.get("similarity"), "rerank": round(e["rerank"], 3) if "rerank" in e else None}
            for i, e in cands
        ]
        debug["confidence"] = confidence
        debug["timings_ms"]["total"] = _ms(t0)
        return {"sources": sources, "confidence": confidence, "debug": debug}

    def _confidence(self, query: str, final) -> float:
        """0..1 blend of three calibrated signals (tune ranges in config.yaml -> retrieval.calibration)."""
        if not final:
            return 0.0
        cal = self.cfg.get("calibration", {})
        lo, hi = cal.get("rerank_logit_range", [-10.0, 0.0])
        vlo, vhi = cal.get("vector_sim_range", [0.55, 0.85])
        clip = lambda x: max(0.0, min(1.0, x))  # noqa: E731
        idx, top = final[0]
        q = set(tokenize(query))
        sec = self.sections[idx]
        coverage = len(q & set(tokenize(sec.title + " " + sec.content))) / max(len(q), 1)
        vec = clip(((top.get("similarity") or max((e.get("similarity") or 0) for _, e in final)) - vlo) / (vhi - vlo))
        if "rerank" in top:
            rr = clip((max(e["rerank"] for _, e in final) - lo) / (hi - lo))
            return round(0.4 * rr + 0.4 * vec + 0.2 * coverage, 3)
        return round(0.6 * vec + 0.4 * coverage, 3) if self.vector else round(coverage * 0.8, 3)

    def stats(self) -> dict:
        by_topic: dict[str, dict] = {}
        for s in self.sections:
            t = by_topic.setdefault(s.topic, {"sections": 0, "raw": 0, "notes": 0})
            t["sections"] += 1
            t["raw" if s.kind == "raw" else "notes"] += 1
        return {"sections": len(self.sections), "vector": bool(self.vector),
                "reranker": self.cfg["use_reranker"], "built_at": self.built_at,
                "topics": {slug: {**by_topic.get(slug, {}), "name": m.get("name", slug),
                                  "last_updated": str(m.get("last_updated", "")),
                                  "last_indexed": str(m.get("last_indexed", ""))}
                           for slug, m in self.manifests.items()}}


def _ms(t0: float) -> int:
    return int((time.time() - t0) * 1000)


def _rmtree(p: Path):
    import shutil
    shutil.rmtree(p, ignore_errors=True)
