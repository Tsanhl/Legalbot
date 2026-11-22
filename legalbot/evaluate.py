"""Retrieval evaluation: Recall@K, MRR, fallback correctness, per category.

  python -m legalbot.evaluate                 run eval/evalset.yaml, write eval/runs/<ts>.json
  python -m legalbot.evaluate --compare A B   show metric deltas between two runs

Eval case:
  - id: art102-core-1
    category: core | paraphrase | negative
    topic: competition-law            (optional)
    query: What does Article 102 prohibit?
    expected_sources: [_demo/notes/article-102.md#prohibition]   (prefix match on section id)
    expected_behavior: answer | fallback
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
from collections import defaultdict

import yaml

from . import config
from .retrieval.engine import RetrievalEngine


def run(k: int) -> dict:
    f = config.path("eval") / "evalset.yaml"
    if not f.exists():
        f = config.path("eval") / "evalset.example.yaml"
    cases = yaml.safe_load(f.read_text()) or []
    eng = RetrievalEngine()
    eng.load()
    min_conf = eng.cfg["min_confidence"]
    rows, agg = [], defaultdict(lambda: defaultdict(float))
    for c in cases:
        r = eng.retrieve(c["query"], [c["topic"]] if c.get("topic") else None, k)
        ids = [s["id"] for s in r["sources"]]
        expected = c.get("expected_sources") or []
        rank = next((i + 1 for i, sid in enumerate(ids) if any(sid.startswith(e) for e in expected)), None)
        would_fallback = r["confidence"] < min_conf or not ids
        want_fb = c.get("expected_behavior") == "fallback"
        row = {"id": c["id"], "category": c.get("category", "core"), "query": c["query"], "rank": rank,
               "confidence": r["confidence"], "fallback": would_fallback, "behavior_ok": would_fallback == want_fb,
               "top": ids[:3], "missing_tokens": r["debug"]["bm25"]["missing_tokens"]}
        rows.append(row)
        for bucket in ("all", row["category"]):
            a = agg[bucket]
            a["n"] += 1
            a["behavior_ok"] += row["behavior_ok"]
            if not want_fb:
                a["n_answerable"] += 1
                a[f"recall@{k}"] += rank is not None
                a["mrr"] += 1 / rank if rank else 0
    metrics = {}
    for b, a in agg.items():
        na = a["n_answerable"] or 1
        metrics[b] = {"n": int(a["n"]), f"recall@{k}": round(a[f"recall@{k}"] / na, 3),
                      "mrr": round(a["mrr"] / na, 3), "behavior_acc": round(a["behavior_ok"] / a["n"], 3)}
    return {"ts": dt.datetime.now().isoformat(timespec="seconds"), "k": k,
            "config": {x: eng.cfg[x] for x in ("use_vector", "use_reranker", "min_confidence", "chunk_chars")},
            "metrics": metrics, "cases": rows}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("-k", type=int, default=5)
    ap.add_argument("--compare", nargs=2)
    args = ap.parse_args()
    runs = config.path("eval") / "runs"
    if args.compare:
        a, b = (json.loads((runs / f).read_text()) for f in args.compare)
        for bucket in b["metrics"]:
            ma, mb = a["metrics"].get(bucket, {}), b["metrics"][bucket]
            print(bucket, {m: f"{ma.get(m, 0)} -> {v}" for m, v in mb.items()})
        return
    res = run(args.k)
    runs.mkdir(parents=True, exist_ok=True)
    out = runs / f"{res['ts'].replace(':', '')}.json"
    out.write_text(json.dumps(res, indent=2))
    for bucket, m in res["metrics"].items():
        print(f"{bucket:<12} {m}")
    for r in res["cases"]:
        if not r["behavior_ok"] or (r["rank"] is None and r["category"] != "negative"):
            print(f"  FAIL {r['id']}: rank={r['rank']} conf={r['confidence']} top={r['top'][:2]} missing={r['missing_tokens']}")
    print(f"\nsaved {out.relative_to(config.ROOT)}")


if __name__ == "__main__":
    main()
