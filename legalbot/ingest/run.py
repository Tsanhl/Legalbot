"""Ingest the Law folder into kb/  (originals are only read, never modified).

  python -m legalbot.ingest.run                 full run (incremental: unchanged files are skipped)
  python -m legalbot.ingest.run --dry-run       classify only, write the report
  python -m legalbot.ingest.run --topic pensions-law

Outputs
  kb/topics/<slug>/raw/<authority>/<name>-<hash>.md   evidence (indexed)
  kb/feedback/<slug>/…   kb/questions/<slug>/…   kb/guidance/…   (not indexed)
  kb/topics/<slug>/manifest.yaml                      topic metadata + source ledger
  data/ingest/report.json  +  kb/INGEST_REPORT.md     what went where, and why
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import time
from collections import Counter, defaultdict
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

import yaml

from .. import config
from .classify import classify
from .tidy import tidy_text
from .extract import extract
from .ledger import INGESTABLE, SKIP, sha256

KB = config.path("kb")
LAW = config.path("law_root")
REPORT_DIR = config.ROOT / "data" / "ingest"


def load_map() -> dict:
    tm = yaml.safe_load((KB / "topic_map.yaml").read_text())
    local = Path(os.environ.get("LEGALBOT_PII", Path.home() / ".config" / "legalbot" / "pii.yaml"))  # outside the project
    if local.exists():
        tm["pii"] = (tm.get("pii") or []) + ((yaml.safe_load(local.read_text()) or {}).get("pii") or [])
    return tm


def scrub(text: str, pii: list[dict]) -> str:
    for rule in pii:
        # tolerate "_", "-", "." or several spaces between words (Turnitin file names use underscores)
        pat = r"[\s_.-]+".join(re.escape(w) for w in rule["pattern"].split())
        text = re.sub(pat, rule["replace"], text, flags=re.I)
    return text


def slug(text: str, n: int = 70) -> str:
    s = re.sub(r"[^\w\s-]", " ", text.lower())
    return re.sub(r"[\s_-]+", "-", s).strip("-")[:n] or "file"


def nice_title(stem: str) -> str:
    t = re.sub(r"\.(docx?|pdf|pptx)$", "", stem, flags=re.I)
    t = re.sub(r"^(?:L\d+(?:-\d+)?|Tutorial \d+|T\d+)\s*\**\s*", "", t)
    t = re.sub(r"\s*(?:copy(?: \d+)?|\(\d\))\s*$", "", t)
    return re.sub(r"\s+", " ", t.replace(":", "/")).strip(" -_*.") or stem


def discover(tm: dict, only_topic: str | None):
    prefixes = sorted([(f.rstrip("/"), s) for s, t in tm["topics"].items() for f in t["folders"]]
                      + [(f.rstrip("/"), "_feedback") for f in tm.get("feedback_folders", [])],
                      key=lambda x: -len(x[0]))
    ignore = tm.get("ignore", [])
    ignore_patterns = tm.get("ignore_patterns", [])
    st = KB / "source_topics.yaml"   # one area of law per shared primary source (python -m legalbot.ingest.sort_sources)
    by_orig = {v["original"]: v["topic"] for v in (yaml.safe_load(st.read_text()) or {}).values()} if st.exists() else {}
    for p in sorted(LAW.rglob("*")):
        if not p.is_file() or SKIP.search(p.name):
            continue
        rel = p.relative_to(LAW).as_posix()
        if any(rel.startswith(i) for i in ignore) or any(re.search(pat, p.name, re.I) for pat in ignore_patterns):
            continue
        topic = next((s for f, s in prefixes if rel == f or rel.startswith(f + "/")), None)
        if topic == "general-law":
            topic = by_orig.get(rel, topic)
        if only_topic and topic not in (only_topic, "_feedback"):
            continue
        yield p, rel, topic


def module_topic(name: str, codes: dict) -> str | None:
    m = re.search(r"LAW\d{4}", name)
    return codes.get(m.group(0)) if m else None


def process(job: dict) -> dict:
    """Runs in a worker process."""
    src = Path(job["path"])
    rec = {k: job[k] for k in ("rel", "topic", "role", "authority", "reason", "sha256", "ext")}
    out = Path(job["out"]) if job.get("out") else None
    if out and out.exists() and not job.get("force"):
        return {**rec, "status": "unchanged", "out": str(out)}
    t0 = time.time()
    try:
        ex = extract(src)
    except Exception as e:
        return {**rec, "status": "error", "error": f"{type(e).__name__}: {e}"[:300]}
    pii = job["pii"]
    body, comments = scrub(ex.body, pii), [scrub(c, pii) for c in ex.comments]
    role = rec["role"]
    if role == "student_script":
        # Turnitin / GradeMark exports: script pages are images, the grade report page is text
        gm = re.search(r"(FINAL GRADE.*|GRADEMARK REPORT.*|GENERAL COMMENTS.*)", body, re.S)
        if gm:
            comments = comments + [re.sub(r"\s*\n\s*", " ", gm.group(1)).strip()]
        role = "feedback" if comments else "own_work"
        rec["role"] = role
        rec["reason"] = "marked script with annotations" if comments else "your script, no marker annotations"
        if role == "own_work":
            return {**rec, "status": "skipped"}
    chars = len(body)
    rec.update(chars=chars, pages=ex.meta.get("pages") or ex.meta.get("slides"), comments=len(comments),
               ocr_pages=ex.meta.get("ocr_pages", 0),
               seconds=round(time.time() - t0, 1))
    if ex.meta.get("needs_ocr"):
        rec["status"] = "needs_ocr"
        if role == "evidence":
            return rec
    if chars < 200 and not comments:
        return {**rec, "status": "empty"}

    title = scrub(ex.meta.get("title") or nice_title(src.stem), pii)
    fm = {"authority": rec["authority"] if role == "evidence" else role, "title": title,
          "original": scrub(rec["rel"], pii), "sha256": rec["sha256"], "topic": rec["topic"],
          "extracted_at": dt.date.today().isoformat()}
    for k in ("citation", "version_date", "date", "url", "restrict_extent"):
        if ex.meta.get(k):
            fm[k] = ex.meta[k]
    year = re.search(r"[\[(]((?:19|20)\d\d)[\])]", src.stem)
    if year:
        fm["year"] = int(year.group(1))
    if rec.get("status") == "needs_ocr":
        fm["needs_ocr"] = True
    if ex.meta.get("ocr_pages"):
        fm["ocr_pages"] = ex.meta["ocr_pages"]  # OCR text: check spelling of names/citations
    text = f"---\n{yaml.safe_dump(fm, sort_keys=False, allow_unicode=True)}---\n# {title}\n\n"
    if comments:
        label = "Marker comments" if role == "feedback" else "Reading annotations"
        text += f"## {label}\n\n" + "\n\n".join(f"- {c}" for c in comments) + "\n\n"
        if role == "feedback":
            text += "## Script / document text\n\n"
    text += _demote(body) if role == "feedback" and comments else body
    if role == "evidence":   # strip print boilerplate; re-section Act PDFs by section
        text = tidy_text(text, rec["authority"] == "legislation" and src.suffix.lower() == ".pdf")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text)
    rec.setdefault("status", "ok")
    return {**rec, "out": str(out)}


def _demote(body: str) -> str:
    return re.sub(r"^(#{2,5}) ", lambda m: "#" + m.group(1) + " ", body, flags=re.M)


def output_path(role: str, topic: str, authority: str, rel: str, sha: str, pii) -> Path | None:
    stem = slug(scrub(nice_title(Path(rel).stem), pii))
    name = f"{stem}-{sha[:6]}.md"
    if role == "evidence":
        return KB / "topics" / topic / "raw" / authority / name
    if role == "feedback":
        return KB / "feedback" / (topic or "general") / name
    if role == "question":
        return KB / "questions" / (topic or "general") / name
    if role == "guidance":
        return KB / "guidance" / name
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--topic")
    ap.add_argument("--force", action="store_true", help="re-extract even if output exists (after extractor changes)")
    ap.add_argument("--workers", type=int, default=max(2, (os.cpu_count() or 4) - 2))
    args = ap.parse_args()
    # Safety: never prune the knowledge base because the Law folder is missing, moved or unmounted
    n_orig = sum(1 for x in LAW.rglob("*") if x.is_file()) if LAW.exists() else 0
    if n_orig < 50:
        raise SystemExit(f"Law folder not found or nearly empty: {LAW} ({n_orig} files). Nothing was changed.\n"
                         "If you moved it, set paths.law_root in config.yaml to the new location and run again.")
    tm = load_map()
    pii, codes = tm.get("pii", []), tm.get("module_codes", {})

    jobs, records, seen = [], [], {}
    tf = KB / "source_types.yaml"
    type_fix = (yaml.safe_load(tf.read_text()) or {}) if tf.exists() else {}
    for p, rel, topic in discover(tm, args.topic):
        ext = p.suffix.lower()
        base = {"rel": rel, "topic": topic, "ext": ext, "sha256": "", "authority": ""}
        if ext not in INGESTABLE:
            records.append({**base, "role": "unsupported", "reason": f"{ext} not supported", "status": "skipped"})
            continue
        role, authority, reason = classify(rel, ext)
        if rel in type_fix:   # corrected by hand / by the re-filing pass (kb/source_types.yaml)
            role, authority, reason = "evidence", type_fix[rel], "type corrected in kb/source_types.yaml"
        if topic == "_feedback":
            topic = module_topic(p.name, codes) or "general"
            if role not in ("feedback", "student_script", "guidance", "question"):
                role, authority, reason = "student_script", "feedback", "file in feedback folder"
        elif role == "own_work" and ext == ".pdf" and not re.match(r"(part [ab] )?ai[-, ]", p.name, re.I) \
                and "previous" not in rel.lower():
            role, reason = "student_script", reason + "; checked for marker comments"
            topic = module_topic(p.name, codes) or topic
        elif role in ("feedback", "student_script"):
            topic = module_topic(p.name, codes) or topic
        sha = sha256(p)
        key = (topic, sha)
        rec = {**base, "topic": topic, "role": role, "authority": authority, "reason": reason, "sha256": sha}
        if topic is None:
            records.append({**rec, "role": "unmapped", "status": "skipped"})
            continue
        if key in seen:
            records.append({**rec, "status": "duplicate", "duplicate_of": seen[key]})
            continue
        seen[key] = rel
        if role in ("own_work", "admin"):
            records.append({**rec, "status": "skipped"})
            continue
        out = output_path("feedback" if role == "student_script" else role, topic, authority, rel, sha, pii)
        jobs.append({**rec, "path": str(p), "out": str(out) if out else "", "pii": pii, "force": args.force})

    print(f"{len(jobs)} files to extract, {len(records)} skipped/duplicate/unsupported")
    if not args.dry_run:
        t0 = time.time()
        with ProcessPoolExecutor(max_workers=args.workers) as ex:
            futs = [ex.submit(process, j) for j in jobs]
            for n, f in enumerate(as_completed(futs), 1):
                records.append(f.result())
                if n % 100 == 0 or n == len(futs):
                    print(f"  {n}/{len(futs)}  ({time.time() - t0:.0f}s)", flush=True)
    else:
        records += [{**{k: j[k] for k in ("rel", "topic", "role", "authority", "reason", "sha256", "ext")},
                     "status": "planned", "out": j["out"]} for j in jobs]

    if not args.dry_run:
        prune(records, [args.topic] if args.topic else list(tm["topics"]) + ["general"])
    write_manifests(tm, records, args.dry_run, args.topic)
    write_report(records, args.dry_run)


def prune(records: list[dict], topics: list[str]):
    """Delete generated .md files no longer produced (e.g. a file was reclassified). Only touches kb outputs."""
    keep = {Path(r["out"]).resolve() for r in records if r.get("out")}
    removed = 0
    for t in topics:
        for base in (KB / "topics" / t / "raw", KB / "feedback" / t, KB / "questions" / t):
            for md in base.rglob("*.md") if base.exists() else []:
                if md.resolve() not in keep and "original: 'downloaded:" not in md.read_text(errors="ignore")[:800]:
                    md.unlink()   # files fetched from official sources are kept (no original in the Law folder)
                    removed += 1
    if not topics or len(topics) > 1:
        for md in (KB / "guidance").glob("*.md") if (KB / "guidance").exists() else []:
            if md.resolve() not in keep:
                md.unlink()
                removed += 1
    if removed:
        print(f"pruned {removed} stale outputs")


def write_manifests(tm: dict, records: list[dict], dry: bool, only_topic: str | None = None):
    if dry:
        return
    by_topic = defaultdict(list)
    for r in records:
        if r.get("role") == "evidence" and r.get("status") in ("ok", "unchanged"):
            by_topic[r["topic"]].append(r)
    today = dt.date.today().isoformat()
    for slug_, t in tm["topics"].items():
        if only_topic and slug_ != only_topic:
            continue   # a single-module run must not blank the other modules' file lists
        d = KB / "topics" / slug_
        d.mkdir(parents=True, exist_ok=True)
        mf = d / "manifest.yaml"
        old = (yaml.safe_load(mf.read_text()) or {}) if mf.exists() else {}
        lf = d / "sources.local.yaml"   # your own files: kept on this machine only
        old_ledger = (yaml.safe_load(lf.read_text()) or []) if lf.exists() else (old.get("sources") or [])
        old_srcs = {s["original"]: s for s in old_ledger}
        sources = []
        for r in sorted(by_topic.get(slug_, []), key=lambda r: r["rel"]):
            prev = old_srcs.get(r["rel"], {})
            sources.append({"original": r["rel"], "sha256": r["sha256"], "authority": r["authority"],
                            "raw": str(Path(r["out"]).relative_to(KB / "topics" / slug_)),
                            "extracted_at": prev.get("extracted_at") if prev.get("sha256") == r["sha256"] else today})
        changed = {s["original"] for s in sources} != set(old_srcs) or any(
            old_srcs.get(s["original"], {}).get("sha256") != s["sha256"] for s in sources)
        data = {"slug": slug_, "name": t["name"], "aliases": t.get("aliases", []),
                "jurisdiction": t.get("jurisdiction", []),
                "always_search": t.get("always_search", False),
                "last_updated": today if changed or not old.get("last_updated") else old["last_updated"],
                "last_indexed": old.get("last_indexed"), "counts": dict(Counter(s["authority"] for s in sources))}
        mf.write_text(yaml.safe_dump(data, sort_keys=False, allow_unicode=True))
        lf.write_text(yaml.safe_dump(sources, sort_keys=False, allow_unicode=True))


def write_report(records: list[dict], dry: bool):
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    (REPORT_DIR / ("plan.json" if dry else "report.json")).write_text(scrub(json.dumps(records, indent=1), load_map().get("pii", [])))
    print(json.dumps(Counter(f"{r.get('role')}:{r.get('status')}" for r in records).most_common(), indent=0))


if __name__ == "__main__":
    main()
