# Improvement inbox

Different kinds of improvement go in different folders, all filed **by date**.

| Folder | What lands here | Who creates it |
|---|---|---|
| `user_feedback/<date>/` | Your 👍 / 👎 on a specific answer **plus your comment**, with the question and the answer given | you, by clicking 👍 / 👎 in the chat |
| `knowledge_gaps/<date>/` | What the system spotted: the bot **couldn't answer** (low confidence), the answer **failed the grounding check**, or the answer **said a case/Act was missing** from the knowledge base | the chat, automatically |
| `daily_review/<date>.md` | **Start here.** That day's checklist of both, plus anything still open from earlier days | rewritten automatically whenever an item arrives |
| `weekly_report.md` | Totals and the most frequently missing authorities over the last 7 days | `python -m legalbot.loop report` |
| `pending.jsonl` | Machine queue for `python -m legalbot.loop list / cluster / promote` | automatic |

Every item file begins with `status: open`. When dealt with, change it to `status: fixed` (or `wontfix`).

Full logs of every question stay in `debug/logs/<date>.jsonl` (for debugging; local only, never uploaded).

## Daily routine
1. Open today's `daily_review/<date>.md`.
2. **Knowledge gaps**: add the missing law (Law folder, or download it into `kb/topics/<topic>/raw/case_law/` with
   `original: 'downloaded: <url>'`), or write a note. Then `python -m legalbot.ingest.run && python -m legalbot.index build`.
3. **Your feedback**: 👎 items say what was wrong (wrong law, structure, missing case …): fix the note, style guide
   (`kb/style/`, `kb/topics/<topic>/style.md`) or retrieval; or `python -m legalbot.loop promote <trace> --source <id>`
   to turn it into a test question.
4. Set `status: fixed`; run `python -m legalbot.evaluate` to check nothing got worse.
