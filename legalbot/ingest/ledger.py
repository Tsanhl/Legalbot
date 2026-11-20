"""Source ledger: which originals in the Law folder a topic has ingested, and what changed since.

manifest.yaml keeps `sources: [{original, sha256, raw, authority, extracted_at}]`.
`topic_status` compares that ledger with the files currently in the topic's Law folder(s),
so you can see "Competition Law — last updated 18 Nov, 3 new files, 1 changed".
"""
from __future__ import annotations

import hashlib
import re
from pathlib import Path

from .. import config

INGESTABLE = {".pdf", ".docx", ".pptx", ".xml", ".html", ".htm", ".md", ".txt"}
SKIP = re.compile(r"(^~\$|^\.|\.DS_Store$)")


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()[:16]


def topic_files(manifest: dict) -> list[Path]:
    root = config.path("law_root")
    folders = manifest.get("law_folders") or []
    if not folders:   # folder names live in your local kb/topic_map.yaml, not in the shared manifest
        tmp = config.path("kb") / "topic_map.yaml"
        if tmp.exists():
            t = (__import__("yaml").safe_load(tmp.read_text()) or {}).get("topics", {}).get(manifest.get("slug", ""), {})
            folders = t.get("folders") or []
    out = []
    for folder in folders:
        base = root / folder
        if base.is_file():
            out.append(base)
            continue
        for p in base.rglob("*"):
            if p.is_file() and p.suffix.lower() in INGESTABLE and not SKIP.search(p.name):
                out.append(p)
    return sorted(out)


def topic_status(manifest: dict) -> dict:
    root = config.path("law_root")
    lf = config.path("kb") / "topics" / str(manifest.get("slug", "")) / "sources.local.yaml"
    rows = (__import__("yaml").safe_load(lf.read_text()) or []) if lf.exists() else (manifest.get("sources") or [])
    ledger = {s["original"]: s for s in rows}
    current = {str(p.relative_to(root)): p for p in topic_files(manifest)}
    new = [r for r in current if r not in ledger]
    changed = [r for r in current if r in ledger and ledger[r].get("sha256") != sha256(current[r])]
    missing = [r for r in ledger if r not in current and not ledger[r].get("manual")]
    return {"tracked": len(ledger), "new": new, "changed": changed, "missing": missing}
