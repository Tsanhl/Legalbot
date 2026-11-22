"""Index CLI.

  python -m legalbot.index build            rebuild BM25 sections + FAISS chunks from kb/
  python -m legalbot.index status           per topic: last_updated, last_indexed, new/changed originals
  python -m legalbot.index search "query"   inspect retrieval without the LLM (debug)
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path

import yaml

from . import config
from .ingest.ledger import topic_status
from .kb import load_manifests
from .retrieval.engine import RetrievalEngine


PUBLIC_INDEX_URL = ("https://github.com/Tsanhl/Legalbot/releases/download/index-2026-11-19/"
                    "legalbot-public-index.tar.gz")


def fetch(url: str) -> None:
    """Download and unpack the shareable index (notes + legislation + official judgments)."""
    import shutil
    import tarfile
    import tempfile
    import urllib.request
    dest = config.path("indexes")
    if (dest / "sections.json").exists():
        print(f"{dest} already has an index; keeping it.")
        download_models()
        return
    with tempfile.TemporaryDirectory() as tmp:
        tgz = Path(tmp) / "index.tar.gz"
        print("downloading", url)
        with urllib.request.urlopen(url) as r, open(tgz, "wb") as out:
            shutil.copyfileobj(r, out)
        dest.mkdir(parents=True, exist_ok=True)
        with tarfile.open(tgz) as t:
            t.extractall(dest, filter="data")
    print("index ready in", dest)
    download_models()


def download_models() -> None:
    """Fetch the two small search models once (embedding + reranker) so the app can run offline afterwards."""
    import os
    os.environ["HF_HUB_OFFLINE"] = "0"
    cfg = config.load()["retrieval"]
    from sentence_transformers import CrossEncoder, SentenceTransformer
    SentenceTransformer(cfg["embedding_model"])
    if cfg.get("use_reranker"):
        CrossEncoder(cfg["reranker_model"])
    print("search models ready")


OFFICIAL_ORIGINS = ("Official Legislation/", "downloaded: https://www.legislation.gov.uk",
                    "downloaded: https://caselaw.nationalarchives.gov.uk", "downloaded: https://eur-lex.europa.eu")


# anything tying material to a particular institution, course or person never goes into the shareable index
def _identifiers():
    """Course and personal identifiers that must never reach the shareable index. Generic patterns live here;
    the names that would identify a particular university or person (institution, term names, module-code and
    student-ID formats) live in kb/identifiers.local.txt, one regex per line, which is never uploaded."""
    import re
    generic = [r"module (?:handbook|leader|convenor|code)", r"lecturer", r"taught by", r"tutorial \d", r"seminar \d",
               r"\[student(?:-id)?\]", r"turnitin", r"grademark", r"summative",
               r"formative (?:assessment|essay|work|feedback|task|exercise)"]
    local = config.path("kb") / "identifiers.local.txt"
    extra = [l.strip() for l in local.read_text().splitlines()
             if l.strip() and not l.lstrip().startswith("#")] if local.exists() else []
    return re.compile("|".join(generic + extra), re.I)


IDENTIFIERS = _identifiers()


NOT_LEGISLATION = __import__("re").compile(
    r"law-trove|handbook|deconstructing|statutory-implied-terms|completely-constituting|statutory-regulation-of", __import__("re").I)


def is_public(s) -> bool:
    """May this section be redistributed? Our own notes; legislation (Crown copyright under the Open Government
    Licence; EU law reusable); judgments only from official open sources. Textbooks, articles, lectures: never."""
    if IDENTIFIERS.search(s.content) or IDENTIFIERS.search(s.title) or IDENTIFIERS.search(s.id):
        return False
    if s.kind == "note":
        return True
    if s.authority == "legislation":
        # textbook chapters and articles sometimes get filed as legislation; never share those
        return not NOT_LEGISLATION.search(s.id)
    return s.authority == "case_law" and str(s.original_path or "").startswith(OFFICIAL_ORIGINS)


def scrub_public(dir_: Path) -> None:
    """Remove where each document came from on the owner's machine (original paths, front-matter sources)."""
    sj = dir_ / "sections.json"
    rows = json.loads(sj.read_text())
    for r in rows:
        r["original_path"] = ""
        meta = r.get("meta") or {}
        for k in ("original", "sources", "verified_against", "sha256", "extracted_at", "note"):
            meta.pop(k, None)
        r["meta"] = meta
    sj.write_text(json.dumps(rows, default=str))


def main():
    import logging
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build")
    b.add_argument("--public", action="store_true",
                   help="shareable index: our notes + legislation + official-source judgments only (no copyrighted books/articles)")
    sub.add_parser("status")
    f = sub.add_parser("fetch", help="download the ready-made public index from GitHub into data/indexes/")
    f.add_argument("--url", default=PUBLIC_INDEX_URL)
    s = sub.add_parser("search")
    s.add_argument("query")
    s.add_argument("--topic", default="")
    s.add_argument("-k", type=int, default=6)
    args = ap.parse_args()

    if args.cmd == "fetch":
        fetch(args.url)
        return
    if args.cmd == "build" and args.public:
        eng = RetrievalEngine()
        eng.idx_dir = config.ROOT / "data" / "indexes_public"
        stats = eng.build(only=is_public)
        scrub_public(eng.idx_dir)
        print(json.dumps(stats, indent=2))
        return
    if args.cmd == "build":
        stats = RetrievalEngine().build()
        today = dt.date.today().isoformat()
        for mf in (config.path("kb") / "topics").glob("*/manifest.yaml"):
            data = yaml.safe_load(mf.read_text()) or {}
            data["last_indexed"] = today
            mf.write_text(yaml.safe_dump(data, sort_keys=False, allow_unicode=True))
        print(json.dumps(stats, indent=2))
    elif args.cmd == "status":
        for slug, m in load_manifests(config.path("kb")).items():
            st = topic_status(m)
            print(f"\n{m.get('name', slug)}  [{slug}]")
            print(f"  last_updated: {m.get('last_updated')}   last_indexed: {m.get('last_indexed')}")
            print(f"  originals tracked: {st['tracked']}  new: {len(st['new'])}  changed: {len(st['changed'])}  missing: {len(st['missing'])}")
            for p in (st["new"] + st["changed"])[:15]:
                print(f"    * {p}")
    elif args.cmd == "search":
        eng = RetrievalEngine()
        eng.load()
        r = eng.retrieve(args.query, [args.topic] if args.topic else None, args.k)
        d = r["debug"]
        print(f"query tokens: {d['bm25']['query_tokens']}  expansions: {d['bm25']['synonym_expansions']}")
        print(f"missing tokens: {d['bm25']['missing_tokens']}  confidence: {r['confidence']}")
        for x in r["sources"]:
            print(f"  [{x['label']}] {x['kind']:<4} {x['authority']:<11} {x['id']}")


if __name__ == "__main__":
    main()
