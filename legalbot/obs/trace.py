"""Debug logging + issue filing + review queue (the knowledge-update loop).

debug/logs/YYYY-MM-DD.jsonl     one trace per turn: rewrite, intent, BM25 tokens/scores,
                                 vector distances, fusion, rerank, validation, latency
debug/issues/<date>-<FM>-<slug>/ issue.md + trace.json  (one folder per reported issue)
review_queue/pending.jsonl       unanswered / low-confidence / thumbs-down turns
"""
from __future__ import annotations

import datetime as dt
import json
import re
import uuid
from pathlib import Path

from .. import config

FAILURE_MODES = {
    "FM1": "Keyword miss (BM25 missed synonym / rewording)",
    "FM2": "Semantic false positive (vector found related-but-wrong chunk)",
    "FM3": "Wrong retrieval unit (section/chunk too big, too small, missing parent context)",
    "FM4": "Knowledge gap (KB has no answer but system answered anyway)",
    "FM5": "Generation: unfaithful to context / hallucinated authority",
    "FM6": "Style: wrong structure for essay / problem question",
    "FM7": "Conversation: follow-up rewrite lost context",
    "OTHER": "Other",
}


def new_trace_id() -> str:
    return dt.datetime.now().strftime("%Y%m%d-%H%M%S-") + uuid.uuid4().hex[:6]


def write_trace(trace: dict) -> None:
    d = config.path("debug") / "logs"
    d.mkdir(parents=True, exist_ok=True)
    with open(d / f"{dt.date.today().isoformat()}.jsonl", "a") as f:
        f.write(json.dumps(trace, default=str) + "\n")


def find_trace(trace_id: str) -> dict | None:
    d = config.path("debug") / "logs"
    day = trace_id[:8]
    files = sorted(d.glob(f"{day[:4]}-{day[4:6]}-{day[6:8]}.jsonl")) or sorted(d.glob("*.jsonl"), reverse=True)
    for fp in files:
        for line in fp.read_text().splitlines():
            if trace_id in line[:200]:
                t = json.loads(line)
                if t.get("trace_id") == trace_id:
                    return t
    return None


def recent_traces(limit: int = 50) -> list[dict]:
    d = config.path("debug") / "logs"
    out = []
    for fp in sorted(d.glob("*.jsonl"), reverse=True):
        for line in reversed(fp.read_text().splitlines()):
            t = json.loads(line)
            out.append({k: t.get(k) for k in ("trace_id", "ts", "question", "intent", "topics", "confidence",
                                                "fallback", "validation_verdict", "provider", "session_id", "user_id")})
            if len(out) >= limit:
                return out
    return out


def file_issue(trace_id: str, failure_mode: str, note: str, expected_source: str = "") -> Path:
    trace = find_trace(trace_id) or {"trace_id": trace_id, "missing": True}
    slug = re.sub(r"[^a-z0-9]+", "-", (trace.get("question") or "issue").lower())[:40].strip("-")
    folder = config.path("debug") / "issues" / f"{dt.date.today().isoformat()}-{failure_mode}-{slug}"
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "trace.json").write_text(json.dumps(trace, indent=2, default=str))
    ret = trace.get("retrieval_debug", {})
    (folder / "issue.md").write_text(f"""# {failure_mode}: {FAILURE_MODES.get(failure_mode, '')}

- **Date:** {dt.date.today().isoformat()}
- **Trace:** `{trace_id}`
- **Status:** open
- **Question:** {trace.get('question', '')}
- **Rewritten query:** {trace.get('rewritten_query', '')}
- **Intent / topics:** {trace.get('intent', '')} / {trace.get('topics', '')}
- **Confidence:** {trace.get('confidence', '')}
- **Expected source:** {expected_source or '(fill in)'}

## What went wrong
{note or '(describe)'}

## Retrieval evidence
- BM25 query tokens: `{ret.get('bm25', {}).get('query_tokens')}`
- Missing tokens (not in any section): `{ret.get('bm25', {}).get('missing_tokens')}`
- Top fused: {json.dumps([f.get('id') for f in ret.get('fused', [])[:5]])}

## Diagnosis (follow debug/playbook.md: retrieval -> prompt context -> LLM wording)
-

## Fix applied
-

## Regression
- [ ] added to eval/evalset.yaml
- [ ] re-indexed and re-run eval
""")
    return folder


def enqueue_review(trace: dict, reason: str) -> None:
    q = config.path("review_queue")
    q.mkdir(parents=True, exist_ok=True)
    with open(q / "pending.jsonl", "a") as f:
        f.write(json.dumps({"trace_id": trace["trace_id"], "ts": trace["ts"], "reason": reason,
                            "question": trace["question"], "rewritten_query": trace.get("rewritten_query"),
                            "topics": trace.get("topics"), "confidence": trace.get("confidence")}) + "\n")
