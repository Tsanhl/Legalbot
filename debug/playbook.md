# Retrieval debug playbook

**Order of investigation:** retrieval result → prompt context → LLM wording. Never tune the prompt
before you've confirmed the right section reached the top-K.

Every turn writes a full trace to `debug/logs/YYYY-MM-DD.jsonl` (also visible in the UI → Debug / Logs tabs).
Use the UI's **⚑ report** button (or 👎) on a bad answer: it saves `debug/issues/<date>-<FM>-<slug>/`
with `issue.md` (fill in diagnosis + fix) and `trace.json` (frozen evidence).

Inspect retrieval without the LLM:

```bash
.venv/bin/python -m legalbot.index search "your query" --topic competition-law
```

---

## FM1 — Keyword miss (Markdown KB / BM25)
**Symptom:** expected section is not in `bm25.hits`; `missing_tokens` contains the user's words.
**Check:** `query_tokens`, `synonym_expansions`, `missing_tokens` in the trace.
**Fix:** add a synonym group to `kb/synonyms.yaml`; add aliases to the topic `manifest.yaml`;
improve note headings (headings are weighted ×2); rely on vector track (hybrid).
**Verify:** expected source back in top-K → add the paraphrase to `eval/evalset.yaml`.

## FM2 — Semantic false positive (Vector RAG)
**Symptom:** top chunks are *about* the topic but can't answer the question (e.g. a different test, a different Act).
**Check:** `vector.hits` distances vs `fused[].rerank`; did the reranker demote it?
**Fix:** keep reranker on; tighten topic routing (manifest aliases); split notes so one heading = one question;
add metadata (authority / jurisdiction) and filter.
**Verify:** wrong chunk drops below the expected one; add as eval case.

## FM3 — Wrong retrieval unit
**Symptom:** answer is vague (section too big, many `part i/n` splits) or fragmentary (section too small, lost context).
**Check:** section length in `sources`, `chunk_index`, whether parent heading makes sense on its own.
**Fix:** re-head the raw markdown (judgments: Facts / Issues / Held / Ratio / Obiter); notes ≈ one legal point per heading;
tune `chunk_chars` / `chunk_overlap`; `MAX_SECTION_CHARS` in `legalbot/kb.py`.

## FM4 — Knowledge gap
**Symptom:** KB has no answer but the system still returned "closest" material and answered.
**Check:** `confidence` vs `min_confidence`; was the fallback triggered?
**Fix:** add material (raw + note) → re-index; or recalibrate `retrieval.calibration` / `min_confidence`
using the eval run (look at negative-case confidences vs answerable ones).
**Verify:** negative eval cases → `fallback`, answerable ones don't.

## FM5 — Unfaithful generation
**Symptom:** `validation.verdict` warn/fail; `unsupported_authorities` lists cases/Acts not in context.
**Check:** was the authority in the documents at all (retrieval) or did the model invent it (generation)?
**Fix:** retrieval first; then system rules in `legalbot/llm/prompts.py`; strict mode.

## FM6 — Wrong answer style
**Fix:** `kb/style/<type>.md` or `kb/topics/<slug>/style.md`; check intent classification in trace (`intent_reason`).

## FM7 — Follow-up lost context
**Check:** `is_follow_up`, `rewritten_query`.
**Fix:** `rewrite()` in `legalbot/query/processor.py` (entity carry-over); later: LLM rewrite.

---

## Knowledge update loop
```
unanswered / low-confidence / 👎  →  review_queue/pending.jsonl
  → python -m legalbot.loop cluster          (group by topic + shared terms)
  → expert review: add material | fix KB | mark out-of-scope
  → python -m legalbot.index build           (re-index)
  → python -m legalbot.loop promote <trace> --source <id>   (add to eval set)
  → python -m legalbot.evaluate              (Recall@K / MRR / fallback accuracy must not drop)
```
