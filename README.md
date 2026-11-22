# Legalbot

A law Q&A assistant for UK and EU law. It answers from its own knowledge base of study notes, legislation and case law;
writes essays, problem-question answers and plain-English everyday answers in a consistent academic style; and shows
the exact passage behind every citation.

## What it does

- **Answers from sources first.** Each answer cites the passages it used as `[S1]`, `[S2]`…; click a citation to see
  the sentence it relies on.
- **Never a dead end.** If the knowledge base is thin, it adds clearly labelled general knowledge (`[background]`) or
  official web sources (`[W1]`, legislation.gov.uk, National Archives, EUR-Lex…) when the model supports web search.
- **Accuracy guard.** Every case and Act named is checked against the sources; anything that cannot be traced is marked ⚠︎.
- **Three answer styles.** Essays (thesis, argument, counter-argument), problem questions (issue by issue, every element,
  remedies), and everyday questions ("Yes, based on…, so you can…", with what to do next). Word limits are respected.
- **Per-user history.** Chats are saved under an anonymous browser ID, so each person can come back to their own.

## Quick start

```bash
git clone https://github.com/Tsanhl/Legalbot.git && cd Legalbot
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python -m legalbot.index fetch     # ready-made index + the two small search models
.venv/bin/python -m legalbot.run             # then open http://127.0.0.1:8800
```

In the ☰ menu choose a model:

| Model | What you need |
|---|---|
| `anthropic` | a Claude API key (☰ → Model settings, or the `ANTHROPIC_API_KEY` environment variable) |
| `claude_cli` | Claude Code installed and signed in (`claude`, then `/login`); start the app from your own terminal |
| `codex_cli` | the Codex CLI installed and signed in |
| `mock` | nothing; shows the retrieved passages without writing an answer (for testing) |

The ready-made index contains **study notes, UK and EU legislation, and judgments from official open sources**. It
contains no textbooks, journal articles or teaching materials.

## Add your own materials

1. Put your files (PDF, Word, PowerPoint, HTML, XML) in one folder and set `paths.law_root` in `config.yaml`.
2. Copy `kb/topic_map.example.yaml` to `kb/topic_map.yaml` and list, for each area of law, the sub-folders that belong to it.
3. Optional: put any names or ID numbers that must never appear in the knowledge base in `~/.config/legalbot/pii.yaml`
   (`pii: [{pattern: "...", replace: "[student]"}]`). They are scrubbed from every extracted file.
4. Import and index:
   ```bash
   .venv/bin/python -m legalbot.ingest.run      # extract into kb/topics/<area>/raw/ (only new or changed files)
   .venv/bin/python -m legalbot.index build     # rebuild search (only new text is embedded)
   ```

Marked work placed in `feedback_folders` is used only to shape answer style (`kb/style/`), never as evidence.

## How it works

```
browser ── WebSocket ──► chat service ──gRPC──► query processor → retrieval → LLM
                         (history, logs)        (intent, area,    (keyword + meaning search, rerank,
                                                 legal issue)      notes + cases/sections they cite)
```

- Knowledge base: `kb/topics/<area>/` holds one area of law per folder, with `notes/` and `raw/<type>/`.
- Answer instructions: `kb/style/` (essay, problem question, general, common rules) and `kb/topics/<area>/style.md`.
- Design notes: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) · debugging: [debug/playbook.md](debug/playbook.md).

## Improving it

Feedback (👍 / 👎 with a comment) and gaps the system detects are filed by date under `improvement/` (see
[improvement/README.md](improvement/README.md)); changes are recorded in [improvement/CHANGELOG.md](improvement/CHANGELOG.md).

```bash
.venv/bin/python -m legalbot.loop report                  # weekly summary of gaps and feedback
.venv/bin/python -m legalbot.train --areas tort-law --per-area 3   # automated test-and-improve round
.venv/bin/python -m legalbot.index search "query"         # inspect retrieval without the LLM
.venv/bin/python -m legalbot.evaluate                     # retrieval and fallback metrics on eval/evalset.yaml
.venv/bin/python -m pytest -q tests                       # unit tests
```

## Hosting for several users

`LEGALBOT_PUBLIC=1 .venv/bin/python -m legalbot.run --host 0.0.0.0` runs a shared site: each visitor uses their own
API key (kept in their browser, never stored on the server), sees only their own chats, and is rate-limited
(`LEGALBOT_RATE_PER_HOUR`). A `Dockerfile` is included; the full search stack needs about 2 GB of RAM.

## Disclaimer

For study and general information only; not legal advice.
