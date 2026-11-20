# Brief: writing rephrased topic notes

Goal: turn one topic's raw study material into **our own** structured study notes, which the Q&A bot
retrieves alongside the raw text. Notes are the "explained" layer: clear rules, leading authorities, debate.

## Where things are (project root: this repository's folder)
- Input: `kb/topics/<slug>/raw/<authority>/*.md` (authority = lecture, textbook, journal, case_law, legislation, secondary).
  Each file has YAML front matter (`title`, `original`) and Markdown headings.
- Shared statutes and cases for every topic: `kb/topics/official-sources/raw/`.
- Output: `kb/topics/<slug>/notes/*.md` ONLY. Write nothing anywhere else. Never edit `raw/` or the Law folder.

## How to work
1. Map the syllabus first. Files are big (a topic can be millions of characters), so do not read everything.
   Use `grep -n "^#" file` for headings, `wc -c`, and `grep -il` for terms. Start from the syllabus,
   lecture schedule, study materials / slides, revision lectures and tutorial sheets in `raw/lecture/`.
   Their structure is the syllabus spine. Some files in `raw/lecture/` are really articles or reports; treat
   them as supporting reading.
2. List the subtopics (typically 10–25 per module). One note file per subtopic, e.g. `psychiatric-harm.md`.
3. For each subtopic, read the relevant lecture sections in full, then check the key textbook / journal /
   case / statute passages to get the rules and authorities exactly right.
4. Write in your own words. Do not copy paragraphs. Short quotes (under ~25 words) are fine only for key
   statutory wording or a famous judicial dictum, in quotation marks.

## Accuracy rules (most important)
- Every rule, case name, citation, section number and academic name must come from the files you read.
  Never add one from memory. If a lecture mentions a case without detail, list it with only what the source says.
- When you are unsure, leave it out rather than guess.
- Note where the law is from (England & Wales, EU, etc.) and if a source says something was reformed or overruled.
- Do not include anything identifying any person (names, ID numbers).

## Note file format
```markdown
---
title: <Subtopic name>
topic: <slug>
authority: notes
written: 2026-11-18
sources:            # raw files you actually used, as paths relative to kb/topics/<slug>/ (or official-sources/...)
  - raw/lecture/xxx.md
  - raw/textbook/yyy.md
---
# <Subtopic name>

## Overview
2–4 sentences: what the issue is and why it matters.

## The law
The rules as numbered elements / tests, each with its authority (case or statute section).

## Key authorities
- *Case name* [citation if in source]: facts in one line; held / principle; why it matters.
- Statute s X: what it does.

## Debate and critique
Academic views (named author: argument), tensions, policy, reform proposals. This is the essay material.

## Applying it to a problem question
Step-by-step checklist of questions to ask on facts, typical traps, and which facts change the outcome.

## Links
Related subtopics in this module (by note filename).
```
Write each section in depth: this is the main revision resource. A typical note is 1,500–4,000 words.
Skip a heading only if the sources truly have nothing for it.

## When done
Reply with: the list of note files written (with one line each), subtopics you could not cover and why,
and anything in the raw folder that looked misfiled (wrong topic or wrong authority type).
