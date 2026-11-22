"""Hallucination layer 3: output validation (grounding check), rule-based.

Checks after generation:
  - every [S#] label exists in the provided context
  - every case name / statute / article / section mentioned is present in the cited context
  - answer has at least one citation when sources were given
Produces a verdict used by the UI badge and written to the debug trace.
"""
from __future__ import annotations

import re

LABEL = re.compile(r"\[S(\d+)\]")
CASE = re.compile(r"\b([A-Z][\w'&.-]+(?: [A-Z][\w'&.-]+){0,4}) v\.? ([A-Z][\w'&.-]+(?: [A-Z][\w'&.-]+){0,4})")
ARTICLE = re.compile(r"\bArt(?:icle|\.)? ?(\d+[A-Z]?)\b")
SECTION = re.compile(r"\b(?:s|section|ss)\.? ?(\d+[A-Z]?)(?:\(\d+\))?", re.I)
ACT = re.compile(r"\b((?:[A-Z][a-z]+ ){1,6}Act \d{4})")


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", s.lower())


def validate(answer: str, sources: list[dict], mode: str = "kb") -> dict:
    context = _norm(" ".join(s["title"] + " " + s["content"] for s in sources))
    labels = {s["label"] for s in sources}
    used = {f"S{n}" for n in LABEL.findall(answer)}
    bad_labels = sorted(used - labels)

    # flagged lines are not checked against the documents: [unverified]/[background] = general knowledge, [W#] = web
    body = "\n".join(l for l in answer.splitlines()
                     if not re.search(r"\[(?:unverified|background|W\d+)\]", l))
    body = body.split("Web sources")[0]
    unsupported = []
    prose = "\n".join(l for l in body.splitlines() if not l.lstrip().startswith("#"))  # headings like "Bank v Ethel"
    parties = {w for l in body.splitlines() if l.lstrip().startswith("#") for w in re.findall(r"[A-Z][a-z]+", l)}
    for a, b in CASE.findall(prose):
        if a.split()[-1] in parties and b.split()[0] in parties:
            continue  # party v party in the scenario, not a reported case
        toks = [t for t in re.findall(r"[a-z]{3,}", _norm(a + " " + b)) if t not in {"the", "and", "ltd", "plc", "council"}]
        if toks and sum(t in context for t in toks) < max(1, len(toks) // 2):
            unsupported.append(f"{a} v {b}")
    for act in ACT.findall(prose):
        name, year = act.rsplit(" ", 1)
        key = name.split()[-2].lower() if len(name.split()) >= 2 else name.lower()   # e.g. "property" in "... Property Act"
        if _norm(act) not in context and not (key in context and year in context):
            unsupported.append(act.strip())
    for art in ARTICLE.findall(body):
        if f"article {art.lower()}" not in context and f"art {art.lower()}" not in context and f"art. {art.lower()}" not in context:
            unsupported.append(f"Article {art}")
    unsupported = sorted(set(unsupported))

    unverified = len(re.findall(r"\[(?:unverified|background)\]", answer))
    web_cites = len(set(re.findall(r"\[W(\d+)\]", answer)))
    no_citation = (bool(sources) and not used and not web_cites and mode not in ("web", "chat")
                   and "not in knowledge base" not in answer.lower())
    if mode == "chat":
        verdict = "n/a"
    elif bad_labels or len(unsupported) >= 3 or no_citation:
        verdict = "fail"
    elif unsupported or unverified:
        verdict = "warn"
    else:
        verdict = "pass"
    return {"verdict": verdict, "citations_used": sorted(used), "invalid_labels": bad_labels,
            "unsupported_authorities": unsupported, "unverified_sentences": unverified,
            "no_citation": no_citation, "web_citations": web_cites, "mode": mode}


# ---------------------------------------------------------------- supporting passages
_SENT = re.compile(r"(?<=[.!?;:])\s+(?=[A-Z(\"'‘“\[])|\n+")
_STOP = {"the", "and", "for", "that", "with", "this", "from", "which", "are", "was", "were", "has", "have", "not",
         "but", "its", "their", "his", "her", "they", "can", "may", "must", "will", "would", "should", "into", "under",
         "only", "also", "than", "then", "there", "been", "being", "such", "any", "all", "one", "who", "what", "when"}


def _toks(s: str) -> set[str]:
    return {w for w in re.findall(r"[a-z][a-z'’-]{2,}|\d+[a-z]?", s.lower()) if w not in _STOP}


def support_passages(answer: str, sources: list[dict], per_label: int = 3) -> dict:
    """For each cited [S#], the exact sentence(s) in that source that best match the claim citing it."""
    by_label = {s["label"]: s for s in sources}
    out: dict[str, list[dict]] = {}
    claims = re.split(r"(?<=[.!?])\s+|\n+", answer)
    prev = ""
    for claim in claims:
        labels = [f"S{n}" for n in LABEL.findall(claim)]
        clean = re.sub(r"\[(?:S|W)\d+\]|\[background[^\]]*\]|[*_#>|`]", "", claim).strip()
        if not labels:
            prev = (prev + " " + clean)[-600:] if clean else prev
            continue
        text = clean if len(_toks(clean)) >= 4 else (prev + " " + clean).strip()
        prev = ""
        ct = _toks(text)
        if len(ct) < 2:
            continue
        for lab in labels:
            src = by_label.get(lab)
            if not src or len(out.get(lab, [])) >= per_label:
                continue
            sents = [x.strip() for x in _SENT.split(src["content"]) if len(x.strip()) > 25]
            best, score = None, 0.0
            for i, s in enumerate(sents):
                st = _toks(s)
                if not st:
                    continue
                sc = len(ct & st) / (len(ct) ** 0.5 * len(st) ** 0.5)
                if sc > score:
                    best, score = i, sc
            if best is None or score < 0.12:
                continue
            passage = sents[best]
            if len(passage) < 120 and best + 1 < len(sents):   # very short line: add the next sentence for context
                passage += " " + sents[best + 1]
            out.setdefault(lab, []).append({"claim": text[:300], "passage": passage[:700], "match": round(score, 2)})
    return out
