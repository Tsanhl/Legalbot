"""Write kb/INGEST_REPORT.md from data/ingest/report.json, for your review.

  python -m legalbot.ingest.report
"""
from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path

import yaml

from .. import config

KB = config.path("kb")
AUTH_ORDER = ["legislation", "case_law", "journal", "textbook", "lecture", "secondary"]


def main():
    recs = json.loads((config.ROOT / "data" / "ingest" / "report.json").read_text())
    tm = yaml.safe_load((KB / "topic_map.yaml").read_text())
    by_topic = defaultdict(list)
    for r in recs:
        by_topic[r.get("topic") or "unmapped"].append(r)

    role_status = Counter((r.get("role"), r.get("status")) for r in recs)
    ev_ok = [r for r in recs if r.get("role") == "evidence" and r.get("status") in ("ok", "unchanged")]
    total_chars = sum(r.get("chars") or 0 for r in ev_ok)
    L = ["# Ingest report: please review", "",
         f"{len(recs)} files scanned in `{config.path('law_root')}`. Originals were only read.", "",
         "## Summary", "",
         "| What | Files | Where it went |", "|---|---:|---|",
         f"| Evidence (indexed) | {len(ev_ok)} | `kb/topics/<topic>/raw/<authority>/`, about {total_chars / 1e6:.0f}M characters |",
         f"| Marker feedback | {sum(v for (ro, s), v in role_status.items() if ro == 'feedback' and s in ('ok', 'unchanged'))} | `kb/feedback/<topic>/`, used for step 3 (style), not indexed |",
         f"| Assessment questions | {sum(v for (ro, s), v in role_status.items() if ro == 'question' and s in ('ok', 'unchanged'))} | `kb/questions/<topic>/`, used for the eval set and style, not indexed |",
         f"| Guidance (OSCOLA, tips, model answers) | {sum(v for (ro, s), v in role_status.items() if ro == 'guidance' and s in ('ok', 'unchanged'))} | `kb/guidance/`, not indexed |",
         f"| Your own work (drafts / answers) | {sum(v for (ro, _), v in role_status.items() if ro == 'own_work')} | **skipped**, so drafts never become cited evidence |",
         f"| Duplicates | {sum(1 for r in recs if r.get('status') == 'duplicate')} | skipped (same file twice in a topic) |",
         f"| Scanned PDFs (need OCR) | {sum(1 for r in recs if r.get('status') == 'needs_ocr')} | **not indexed yet** |",
         f"| Empty / errors | {sum(1 for r in recs if r.get('status') in ('empty', 'error'))} | not indexed |",
         f"| Admin / unsupported / unmapped | {sum(1 for r in recs if r.get('role') in ('admin', 'unsupported', 'unmapped'))} | skipped |",
         "", "## How to correct things", "",
         "- **Wrong topic:** edit `folders:` in `kb/topic_map.yaml`.",
         "- **Wrong classification** (e.g. a case marked as a journal, or a draft that slipped in): tell me the filename, "
         "or adjust the rules in `legalbot/ingest/classify.py`.",
         "- Then run `python -m legalbot.ingest.run` followed by `python -m legalbot.index build`. Unchanged files are skipped.", "",
         "## Per topic", "",
         "| Topic | Last updated | " + " | ".join(AUTH_ORDER) + " | skipped own work | needs OCR |",
         "|---|---|" + "---:|" * (len(AUTH_ORDER) + 2)]
    for slug in list(tm["topics"]) + ["general"]:
        rs = by_topic.get(slug, [])
        if not rs:
            continue
        c = Counter(r["authority"] for r in rs if r.get("role") == "evidence" and r.get("status") in ("ok", "unchanged"))
        mf = KB / "topics" / slug / "manifest.yaml"
        upd = (yaml.safe_load(mf.read_text()) or {}).get("last_updated", "") if mf.exists() else ""
        name = tm["topics"].get(slug, {}).get("name", slug)
        L.append(f"| {name} | {upd} | " + " | ".join(str(c.get(a, 0)) for a in AUTH_ORDER)
                 + f" | {sum(1 for r in rs if r.get('role') == 'own_work')} | {sum(1 for r in rs if r.get('status') == 'needs_ocr')} |")

    def section(title: str, pred, note: str = ""):
        rows = [r for r in recs if pred(r)]
        if not rows:
            return
        L.extend(["", f"## {title} ({len(rows)})", ""] + ([note, ""] if note else []))
        grouped = defaultdict(list)
        for r in rows:
            grouped[r.get("topic") or "unmapped"].append(r)
        for t, rs in sorted(grouped.items()):
            L.append(f"<details><summary><b>{t}</b> ({len(rs)})</summary>\n")
            for r in sorted(rs, key=lambda r: r["rel"]):
                extra = f" · {r.get('authority')}" if r.get("authority") and r.get("role") == "evidence" else ""
                L.append(f"- `{r['rel']}`{extra}: {r.get('reason') or r.get('error') or ''}")
            L.append("\n</details>")

    section("Check: skipped as your own work", lambda r: r.get("role") == "own_work",
            "These are excluded from evidence. If any is actually reading material, tell me which.")
    section("Check: marker feedback found", lambda r: r.get("role") == "feedback")
    section("Check: assessment questions", lambda r: r.get("role") == "question")
    section("Check: classed as 'secondary' (uncertain type)", lambda r: r.get("role") == "evidence" and r.get("authority") == "secondary")
    section("Scanned PDFs that need OCR", lambda r: r.get("status") == "needs_ocr")
    section("Empty or failed extractions", lambda r: r.get("status") in ("empty", "error"))
    section("Unsupported or unmapped", lambda r: r.get("role") in ("unsupported", "unmapped"))

    L.extend(["", "## Full evidence list", ""])
    for slug in tm["topics"]:
        rs = [r for r in by_topic.get(slug, []) if r.get("role") == "evidence" and r.get("status") in ("ok", "unchanged")]
        if not rs:
            continue
        L.append(f"<details><summary><b>{tm['topics'][slug]['name']}</b> ({len(rs)})</summary>\n")
        for a in AUTH_ORDER:
            ra = sorted((r for r in rs if r["authority"] == a), key=lambda r: r["rel"])
            if ra:
                L.append(f"\n**{a}** ({len(ra)})\n")
                L.extend(f"- {Path(r['rel']).name}" for r in ra)
        L.append("\n</details>")
    out = KB / "INGEST_REPORT.md"
    out.write_text("\n".join(L) + "\n")
    print(f"wrote {out.relative_to(config.ROOT)}")


if __name__ == "__main__":
    main()
