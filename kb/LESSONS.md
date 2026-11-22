# Where the bot's lessons live

Every mistake the marker finds is logged once, then written to exactly one place, depending on what kind of mistake
it is. Every lesson line ends with a tag `[date · ref <run>/<question>#<error>]` that points back to the log entry,
so any rule or warning can be traced to the question and the marker's comment that produced it.

## 1. Rule book: applies to every answer, every area, any model

| File | Section | What goes there |
|---|---|---|
| `kb/style/common.md` | `## Accuracy checklist (recurring errors found in testing)` | General patterns seen in 3+ answers across 2+ areas (attribution, majority v dissent, section numbers, thresholds, current law, facts, figures). Essays and problem questions. |
| `kb/style/general.md` | `## Accuracy checklist (recurring errors found in testing)` | The same for everyday plain-English answers. |
| `kb/style/essay.md`, `problem_question.md`, `general.md`, `cross_area.md` | `## Learned from testing` | How to structure and argue an answer of that type (from the marker's "what kept this below 70+" advice). |

Added by: the checkpoint review every 100 questions (checklists, ref `eval/reviews/…`) and by each round
(learned rules, ref `<run>/<questions>`).

## 2. Area instructions: applies to one area of law

| File | Section | What goes there |
|---|---|---|
| `kb/topics/<area>/style.md` | `## Learned from testing` (essays, problem questions) and `## Everyday questions (learned from testing)` | How to answer in this area: which issues to cover, which authorities lead, area-specific method. |

| `kb/topics/<area>/manifest.yaml` | `aliases:` | Routing words: when a question was sent to the wrong area, words users say for this area. |
| `kb/alias_blocklist.yaml` | per area | Routing words removed by hand as too broad; the loop never adds them back. |

Added by: each round, when the marker's advice is about one area only (rules) or a question was misrouted (aliases).

## 3. Specific law: the notes the bot retrieves

| File | What happens |
|---|---|
| `kb/topics/<area>/notes/<topic>.md` | **Corrected in place** when the note itself stated the law wrongly (the answer repeated the note's error). |
| `kb/topics/<area>/notes/<topic>.md` → `## Common errors to avoid` | A one-line warning with the correct position when the note was right but the answer still got that point wrong. Max 15 per note. Retrieved together with the law, so any model sees it. |

Added by: each round and `--learn-from`, after Opus checks the error against the statute and judgment text.

## 4. Log: everything, including what was not changed

| File | Contents |
|---|---|
| `eval/error_bank.jsonl` (local only) | One `"kind": "error"` line per legal error (question, what the answer said, the correct position, verdict, action taken, file changed, `ref`) and one `"kind": "feedback"` line per answer (mark, the marker's comment, its advice). Verdicts: `fix` (note corrected), `trap` (common error added), `marker_wrong` (the statute shows the answer was right; nothing changed), `none` (one-off slip), `unreviewed`. |
| `improvement/training_runs/<run>/` | The questions, every grade (`grades.jsonl`), what changed (`changes.md`, `learned.md`), and backups of every file before it changed (`backup/`, `backup_learn/`). |
| `eval/reviews/<date>-after-<n>.md` | Checkpoint reviews: recurring patterns, errors by area, retrieval gaps (wrong passages, wrong area, missing law), notes to strengthen. |
| `eval/progress.json`, `eval/checkpoints/` | Questions marked so far, and each checkpoint's new questions and marks. |

## Tracing a lesson back

`[2026-11-24 · ref 2026-11-22-1301/q05#2]` means: training run `2026-11-22-1301`, question `q05`, the marker's error
number 2. Find it with:

    grep '"ref": "2026-11-22-1301/q05#2"' eval/error_bank.jsonl

and the full answer's grade in `improvement/training_runs/2026-11-22-1301/grades.jsonl`.

## Not lessons

- `eval/marking_guide.md` is the **marker's** standard (what a 70+ answer looks like). It is not shown to the bot.
- `kb/topics/<area>/raw/` holds statutes and judgments. Never edited by the loop.
