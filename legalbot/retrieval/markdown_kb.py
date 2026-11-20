"""Track A: Markdown KB — heading sections + BM25.

Debuggable by design: every hit carries the matched query tokens and per-token score,
so an FM1 (keyword miss) can be diagnosed by reading the trace.
"""
from __future__ import annotations

import json
import math
import re
from collections import Counter
from pathlib import Path

import yaml

from ..kb import Section

STOP = set(
    """a an and are as at be been but by can could did do does for from had has have how i if in into is it
    its me my not of on or our so than that the their them then there these they this to was we were what when
    where which who why will with would you your about under above any all also may must should shall""".split()
)
TOKEN = re.compile(r"[a-z0-9]+")


def stem(t: str) -> str:
    for suf in ("ies", "ing", "ed", "es", "s"):
        if len(t) > len(suf) + 2 and t.endswith(suf) and not t.endswith("ss"):
            return t[: -len(suf)] + ("y" if suf == "ies" else "")
    return t


def tokenize(text: str) -> list[str]:
    return [stem(t) for t in TOKEN.findall(text.lower()) if t not in STOP and (len(t) > 1 or t.isdigit())]


def load_synonyms(path: Path) -> list[list[str]]:
    if not path.exists():
        return []
    data = yaml.safe_load(path.read_text()) or {}
    return [[g.lower() for g in group] for group in data.get("groups", [])]


class BM25Index:
    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1, self.b = k1, b
        self.sections: list[Section] = []
        self.doc_tokens: list[Counter] = []
        self.df: Counter = Counter()
        self.avgdl = 0.0
        self.synonyms: list[list[str]] = []

    # ---- build / persist ----
    def build(self, sections: list[Section], synonyms: list[list[str]]):
        self.sections = sections
        self.synonyms = synonyms
        self._topic_idx: dict[str, set] = {}
        for i, sec in enumerate(sections):
            self._topic_idx.setdefault(sec.topic, set()).add(i)
        # heading text is weighted x2: headings are human-curated structure
        self.doc_tokens = [Counter(tokenize(s.title) * 2 + tokenize(s.content)) for s in sections]
        self.df = Counter(t for c in self.doc_tokens for t in c)
        self.doc_len = [sum(c.values()) for c in self.doc_tokens]
        self.avgdl = sum(self.doc_len) / max(len(sections), 1)
        # inverted index: token -> [(doc_idx, tf)] so a query only touches matching sections
        self.postings: dict[str, list[tuple[int, int]]] = {}
        for i, c in enumerate(self.doc_tokens):
            for t, f in c.items():
                self.postings.setdefault(t, []).append((i, f))
        self.doc_tokens = []  # postings hold everything needed; free memory
        return self

    def save(self, path: Path):
        path.write_text(json.dumps({
            "doc_tokens": [dict(c) for c in self.doc_tokens],
            "synonyms": self.synonyms,
        }))

    # ---- query ----
    def expand(self, q_tokens: list[str], raw_query: str) -> tuple[list[str], list[str]]:
        """Synonym/alias expansion (FM1 fix). Returns (tokens, expansions_used)."""
        used, extra = [], []
        lq = raw_query.lower()
        for group in self.synonyms:
            if any(term in lq for term in group):
                for term in group:
                    if term not in lq:
                        used.append(term)
                        extra += tokenize(term)
        return q_tokens + [t for t in extra if t not in q_tokens], used

    def search(self, query: str, top_k: int, topics: list[str] | None = None) -> tuple[list[dict], dict]:
        q_tokens = tokenize(query)
        q_tokens, expansions = self.expand(q_tokens, query)
        n = len(self.sections)
        allowed = None
        if topics:
            allowed = {i for i, sec in enumerate(self.sections) if sec.topic in topics} if not hasattr(self, "_topic_idx") \
                else set().union(*(self._topic_idx.get(t, set()) for t in topics))
        scores: dict[int, float] = {}
        matched: dict[int, dict] = {}
        for t in set(q_tokens):
            plist = self.postings.get(t)
            if not plist:
                continue
            idf = math.log(1 + (n - self.df[t] + 0.5) / (self.df[t] + 0.5))
            for i, f in plist:
                if allowed is not None and i not in allowed:
                    continue
                dl = self.doc_len[i]
                sc = idf * f * (self.k1 + 1) / (f + self.k1 * (1 - self.b + self.b * dl / self.avgdl))
                scores[i] = scores.get(i, 0.0) + sc
                matched.setdefault(i, {})[t] = round(sc, 3)
        scored = [(sc, i, matched[i]) for i, sc in scores.items()]
        scored.sort(key=lambda x: -x[0])
        hits = [
            {"idx": i, "id": self.sections[i].id, "score": round(s, 4), "matched_tokens": m,
             "heading": self.sections[i].title}
            for s, i, m in scored[:top_k]
        ]
        debug = {"query_tokens": q_tokens, "synonym_expansions": expansions,
                 "missing_tokens": [t for t in q_tokens if t not in self.df]}
        return hits, debug
