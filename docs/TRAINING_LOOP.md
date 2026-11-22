# The automated training loop

One command tests the bot, marks it against first-class (70+) standard, learns from every mistake and measures
whether it is improving. Nothing is committed: you review, then commit what you want to keep.
Where each lesson ends up, and how to trace it back: [`kb/LESSONS.md`](../kb/LESSONS.md).

## Who does what

| Role | Model | Notes |
|---|---|---|
| Writes the test questions | Sonnet | realistic problem questions, essays and everyday questions |
| Answers (the bot) | Sonnet by default (`--bot-model opus` to test Opus) | uses the knowledge base exactly as the website does |
| Website questions | whatever model you chose on the site | marked and learned from like test questions |
| Marks, checks accuracy, learns | Opus | marks against `eval/marking_guide.md`, sees the retrieved statute and judgment text |

## The cycle: `python -m legalbot.train --cycle 100 --per-area 3 --cross 2`

```
ROUND (about 20 questions; repeats until 100 are marked)
 0. Questions people asked on the website since the last round are marked by Opus and learned from (steps 3-5)
 1. Pick 6 areas: the 3 weakest in recent runs + the 3 tested least recently
 2. Write new questions; the bot answers them
 3. Opus marks each answer: score 1-5, estimated %, every legal error, what kept it below 70+
 4. LOG every error and every comment          -> eval/error_bank.jsonl
 5. LEARN
    - legal error the note taught               -> note corrected in place
    - legal error the note did not cause        -> note's "## Common errors to avoid"
    - the marker was wrong (statute shows it)   -> logged only
    - "how to do better" advice                 -> kb/style/*.md or kb/topics/<area>/style.md "Learned from testing"
    - question sent to the wrong area           -> routing words in kb/topics/<area>/manifest.yaml
    - case or Act missing                       -> downloaded from an official site, or a checked case note
 6. CHECK: re-ask up to 5 changed questions; undo any change that made an answer worse
 7. Tidy: merge duplicate rules, max 12 per learned section

CHECKPOINT (every 100 marked questions)
 8. REVIEW all errors, comments and retrieval problems since the last checkpoint
    - the same kind of mistake in 3+ answers across 2+ areas -> new item in the Accuracy checklist
      (kb/style/common.md, kb/style/general.md; max 20 each)
    - report: average mark, errors by area, retrieval gaps, notes to strengthen -> eval/reviews/<date>-after-<n>.md
 9. TEST ON NEW QUESTIONS: 20 fresh questions, 2 for each of the ~6 areas with the most errors (same law, new
    facts) and 1 for 8 other areas. Report: mark before vs now per area -> <checkpoint run>/checkpoint.md
10. Learn from the checkpoint's own errors (as in step 5)
```

If the Claude usage limit is reached, the loop stops cleanly, keeps everything marked so far, and the same command
carries on from `eval/progress.json` after the reset.

## Other commands

| Command | What it does |
|---|---|
| `python -m legalbot.train --areas tort-law --per-area 3` | one round on chosen areas |
| `python -m legalbot.train --replay <run folder> [--only q05,q13] --no-fix` | re-ask earlier questions to compare (no changes) |
| `python -m legalbot.train --replay eval/benchmark --no-fix` | the fixed 24-question benchmark (one per area), like for like |
| `python -m legalbot.train --learn-from <run folder> [--no-rules]` | learn from an earlier run's marks without re-asking |
| `python -m legalbot.train --from-site` | mark the questions asked on the website and learn from them now |
| `python -m legalbot.fix_gaps` | download missing law from official sites, or write a checked case note |
| `python -m legalbot.index build` | re-index after editing notes by hand |
| `python -m legalbot.evaluate` | retrieval check (no Claude tokens) |
| `.venv/bin/python -m pytest -q tests` | code tests (no Claude tokens) |

Useful options: `--max-rechecks 5` (0 = re-check all), `--checkpoint 100`, `--checkpoint-questions 20`,
`--round-areas 6`, `--bot-model opus`, `--focus <runs> --focus-n 7` (weakest areas only).

## What to read after a run

1. `improvement/training_runs/<run>/summary.md`: scores, estimated marks, legal errors, what changed, what was undone,
   and "Needs you" (things only you can do, e.g. law the gap fixer could not download).
2. `changes.md` in the same folder: every rule added and every note corrected (was / now).
3. At a checkpoint: `eval/reviews/<date>-after-<n>.md` and `checkpoint.md`.

To undo a change, copy the file back from the run's `backup/` (or `backup_learn/`) folder.

## Safeguards

- Rules may not contradict the fixed system rules (`[background]` tags, the gaps list, no citing from memory).
- A rule may only name a case the notes already contain.
- Notes are corrected only where the exact wrong text is found; every changed file is backed up first.
- Downloaded judgments are checked against the National Archives case name (a wrong citation once fetched the wrong case).
- Routing words removed by hand are listed in `kb/alias_blocklist.yaml` and never added back.
- Privacy: notes, rules and downloads are scanned for course, university and personal identifiers; anything matching
  is never added to the public index.

## Cost guide (Claude usage)

| Step | Calls |
|---|---|
| one round of ~20 questions | ~20 answers + ~20 marks + ~10 learning calls + up to 5 re-checks (x2) |
| 100-question cycle with checkpoint | roughly 2-3 five-hour usage windows |
| `--learn-from` on a 30-question run | ~35 Opus calls |
| retrieval check, tests, re-index | none |
