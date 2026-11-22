# Legal bot: architecture

## Request path (online)

```
Client (browser)
   │  WebSocket /ws   (ask / stop / ping  ←→  session, status, meta, sources, token…, done)
   ▼
Chat Service  (FastAPI, legalbot/chat/)
   ├─ Conversation Store (SQLite: sessions, messages, feedback; 10-turn sliding window)
   │  gRPC (proto/legalbot.proto)
   ├─► Query Processor   intent (essay | problem_question | general | out_of_scope),
   │                     topic routing (manifest aliases → metadata filter),
   │                     conversation-aware rewrite, input injection scan
   ├─► Retrieval         Markdown KB: heading sections + BM25 (+ synonyms)
   │                     Vector RAG:  chunks + bge-small embeddings + FAISS
   │                     → RRF fusion at section level → bge cross-encoder rerank → top-K + confidence
   ├─  Fallback gate     confidence < min_confidence (strict mode) → "can't confirm" + review queue
   ├─  Prompt            system rules + style guide (by intent / topic) + <document> isolated context
   └─► LLM (server-stream)   anthropic API | claude_cli (your Claude Code login) | codex_cli | mock
          tokens ──gRPC stream──► Chat Service ──WebSocket──► Client
   └─  Output validation  [S#] labels exist, cases / Acts / Articles appear in context → pass/warn/fail badge
   └─  Trace              debug/logs/<date>.jsonl (every stage, scores, timings)
```

## Offline paths

| Path | Command | Writes |
|---|---|---|
| Index build (write-then-swap) | `python -m legalbot.index build` | `data/indexes/` and `last_indexed` in each manifest |
| Freshness check | `python -m legalbot.index status` | – (lists new/changed originals per topic) |
| Retrieval eval | `python -m legalbot.evaluate` | `eval/runs/<ts>.json` (Recall@K, MRR, fallback accuracy) |
| Update loop | `python -m legalbot.loop list / cluster / promote / out-of-scope` | `improvement/`, `eval/evalset.yaml` |
| Issue filing | UI ⚑ report / 👎 | `debug/issues/<date>-<FM>-<slug>/` |

## Data layout

```
kb/
  topics/<slug>/manifest.yaml     name, aliases, law_folders, last_updated, last_indexed, sources ledger
  topics/<slug>/raw/{legislation,case_law,journals,lectures}/*.md   ← (1) original raw, extracted
  topics/<slug>/notes/*.md        ← (2) our rephrased knowledge (entry point; cites raw ids)
  topics/<slug>/style.md          area-specific answer rules (optional)
  style/{common,essay,problem_question,general}.md   ← (3) answer styling rules
  feedback/                       extracted assessment feedback (shapes prompts; NOT retrieved as evidence)
  synonyms.yaml                   BM25 alias groups (FM1 fix)
eval/evalset.yaml                 core / paraphrase / negative cases
debug/{logs,issues,playbook.md}   retrieval debug logging + one folder per issue
improvement/                      user_feedback/ + knowledge_gaps/ + daily_review/ (by date); pending.jsonl
```

## Hallucination layers
1. **Prompt restriction**: grounding rules, `[S#]` citation labels, "[authority not in knowledge base]" placeholder, strict / extended modes.
2. **Retrieval quality**: hybrid BM25 + vector, RRF, cross-encoder rerank, topic filter, parent-section expansion.
3. **Output validation**: label check + authority-in-context check → badge + review queue on fail.
4. **Fallback**: confidence gate before the LLM is called; out-of-scope reply.

## Safety
- **Query intent isolation**: input injection patterns flagged in the trace; the user's question is placed after the documents, labelled as the question.
- **Untrusted content isolation**: retrieved text is wrapped in `<document>` tags, tag-breaking text is stripped, and documents are declared evidence-only.
- **Tool policy**: no tools for any provider (`claude -p --tools ""`, `codex exec --sandbox read-only`), run from an empty `data/llm_sandbox/` cwd; localhost-only gRPC and HTTP; API keys are kept in memory or in a `data/secrets.json` (0600) and never logged.

## Gaps added to your design (and where each one stands)

| # | Gap | Status |
|---|---|---|
| 1 | **Fusion step** between the two tracks (they need merging, not just running side by side): RRF + reranker | built |
| 2 | **Topic routing → metadata filter**, with auto-relax when the routed topic returns nothing | built |
| 3 | **Raw vs notes authority**: notes are the entry point, raw is the evidence, so a mistake in a summary can't be passed off as a cited authority | layout built; enforced during step 2 |
| 4 | **Drafts** of marked work must **not** become KB evidence. Only feedback, and final versions if chosen | decide in step 2 |
| 5 | **PII**: student IDs and names can appear in filenames and feedback, so they are scrubbed on extraction | step 2 |
| 6 | **Point-in-time law**: legislation version date and "law as at" in each raw file's front matter; flag superseded material | step 2 |
| 7 | **Freshness ledger**: per-topic `last_updated` / `last_indexed` plus a sha256 per original, so `status` shows what changed | built |
| 8 | **Confidence calibration**: thresholds must be tuned on the real eval set (bge-reranker-base scores are poorly calibrated) | config knobs built; tune in step 4 |
| 9 | **Long answers** (3,000+ word essays): streaming plus a 900 s CLI timeout now; plan → write → self-check later | partial |
| 10 | **OSCOLA output** (footnotes vs inline) and word-count control | style files; step 3 |
| 11 | **Scanned PDFs** need OCR, and pptx speaker notes should be included | step 2 |
| 12 | **Hot re-index** without a restart (a Reload RPC) | todo |
| 13 | **MCP server** exposing `search_law_kb` so Claude Code / Codex can use the KB directly inside their own chat | optional next |
| 14 | **Backups / git** for `kb/`, which is your curated asset | recommended |
