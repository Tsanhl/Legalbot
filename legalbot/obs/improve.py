"""Improvement inbox: one file per item, filed by date, so fixes can be reviewed regularly.

improvement/
  user_feedback/<date>/<time>-<up|down>-<trace>.md     👍 / 👎 + your comment on a specific answer
  knowledge_gaps/<date>/<time>-<reason>-<trace>.md      found by the system: no answer (low confidence),
                                                         grounding warn/fail, authorities the answer needed but the KB lacks
  daily_review/<date>.md                                 that day's checklist of both, rewritten as items arrive
  pending.jsonl                                          machine queue used by `python -m legalbot.loop`

Every item starts with `status: open`. Change it to `fixed` (or `wontfix`) when dealt with; the daily review
shows what is still open.
"""
from __future__ import annotations

import datetime as dt
import re
from pathlib import Path

from .. import config

GAP_SECTION = re.compile(r"(?:Gaps in the knowledge base|not in the (?:knowledge base|documents))", re.I)
ITALIC = re.compile(r"\*([A-Z][^*\n]{2,80}?)\*")
NOT_IN_KB = re.compile(r"([^.\n]{0,90})\[authority not in knowledge base\]")


def root() -> Path:
    return config.path("review_queue")


def _day(ts: float | None = None) -> str:
    return dt.datetime.fromtimestamp(ts or dt.datetime.now().timestamp()).date().isoformat()


def _write(kind: str, trace: dict, tag: str, body: list[str]) -> Path:
    day = _day(float(trace.get("ts") or 0) or None)
    d = root() / kind / day
    d.mkdir(parents=True, exist_ok=True)
    t = dt.datetime.now().strftime("%H%M%S")
    p = d / f"{t}-{tag}-{trace.get('trace_id', 'x')}.md"
    head = [f"status: open", f"trace: {trace.get('trace_id')}", f"topics: {', '.join(trace.get('topics') or []) or '-'}",
            f"intent: {trace.get('intent')}", f"confidence: {trace.get('confidence')}", "",
            "## Question", "", (trace.get("question") or "").strip(), ""]
    p.write_text("\n".join(head + body) + "\n")
    write_daily(day)
    return p


def missing_authorities(answer: str) -> list[str]:
    """Authorities the model said it needed but could not find in the sources."""
    found = []
    m = GAP_SECTION.search(answer or "")
    if m:
        tail = answer[m.start():].replace("**", "")
        for x in ITALIC.findall(tail):
            x = x.strip()
            if not x.endswith(".") and len(x.split()) <= 8 and x not in found:
                found.append(x)
    for x in NOT_IN_KB.findall(answer or ""):
        x = x.strip(" -*\t")[-90:]
        if x and x not in found:
            found.append(x)
    return found


def record_gap(trace: dict, reason: str, details: list[str] | None = None) -> Path:
    src = [f"- [{s.get('label')}] {s.get('id')}" for s in (trace.get("sources") or [])][:8]
    body = [f"## Reason: {reason}", ""] + [f"- {d}" for d in (details or [])] + \
           ["", "## Sources it had", ""] + (src or ["- none"]) + \
           ["", "## Fix", "", "Add the missing law (Law folder, or download into kb/topics/<topic>/raw/ with "
            "`original: 'downloaded: <url>'`), or write a note; then ingest + index build; then set status: fixed."]
    return _write("knowledge_gaps", trace, re.sub(r"\W+", "-", reason)[:30], body)


def record_feedback(trace: dict, rating: int, comment: str = "", category: str = "", by: str = "user") -> Path:
    ans = (trace.get("answer") or "").strip()
    body = [f"## Rating: {'👍 helpful' if rating > 0 else '👎 not helpful'}" + (f" ({category})" if category else ""), "",
            f"by: {by}", "", "## Your comment" if by == "user" else "## Tester comment", "", comment.strip() or "(none)", "",
            "## Answer given", "", ans[:6000] + ("\n\n[…truncated]" if len(ans) > 6000 else "")]
    return _write("user_feedback", trace, ("up" if rating > 0 else "down") + ("" if by == "user" else "-auto"), body)


def _items(kind: str, day: str) -> list[tuple[Path, str, str]]:
    d = root() / kind / day
    out = []
    for p in sorted(d.glob("*.md")) if d.exists() else []:
        lines = p.read_text(errors="ignore").splitlines()
        status = lines[0].split(":", 1)[1].strip() if lines and lines[0].startswith("status:") else "open"
        q = next((lines[i + 2] for i, l in enumerate(lines) if l == "## Question" and i + 2 < len(lines)), "")
        out.append((p, status, q))
    return out


def write_daily(day: str | None = None) -> Path:
    day = day or _day()
    fb, gaps = _items("user_feedback", day), _items("knowledge_gaps", day)
    older_open = []
    for kind in ("user_feedback", "knowledge_gaps"):
        for d in sorted((root() / kind).glob("*")) if (root() / kind).exists() else []:
            if d.name < day:
                older_open += [(kind, p, q) for p, s, q in _items(kind, d.name) if s == "open"]

    def line(p, s, q):
        rel = p.relative_to(root())
        return f"- [{'x' if s != 'open' else ' '}] [{p.stem.split('-')[1]}]({rel.as_posix()}) {q[:120]}"
    L = [f"# Daily review {day}", "",
         f"{len(fb)} user feedback · {len(gaps)} knowledge gaps today · {len(older_open)} still open from earlier days", "",
         "## Your feedback (👍 / 👎 with comments)", ""] + ([line(*x) for x in fb] or ["- none"]) + \
        ["", "## Knowledge gaps the system found", ""] + ([line(*x) for x in gaps] or ["- none"]) + \
        ["", "## Still open from earlier days", ""] + \
        ([f"- [ ] {k}: [{p.name}]({p.relative_to(root()).as_posix()}) {q[:100]}" for k, p, q in older_open[-40:]] or ["- none"]) + \
        ["", "Fix → set `status: fixed` in the item file → the box is ticked next time this page is rewritten.",
         "Rebuild after adding law: `python -m legalbot.ingest.run && python -m legalbot.index build`."]
    out = root() / "daily_review" / f"{day}.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(L) + "\n")
    return out
