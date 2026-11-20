# Knowledge base layout

**One folder = one area of law.** A question that needs several areas is answered by searching each relevant folder
and combining the results (the query processor picks up to 3 areas; statutes and cases named in your notes are
fetched from whichever folder holds them).

```
kb/
  topics/<area>/                 one area of law (land-law, criminal-law, employment-law, ...)
    manifest.yaml                name, search terms (aliases), last updated / indexed
    style.md                     corrections from your marked work in this module (essay / problem answers only)
    notes/                       our rephrased study notes (written by Claude; updated by Claude, not you)
    raw/legislation/             Acts and regulations
    raw/case_law/                judgments
    raw/journal/  raw/textbook/  raw/lecture/  raw/secondary/
  topics/general-law/            new primary sources not yet sorted (small; sort with the command below)
  style/                         answer instructions: essay.md, problem_question.md, general.md, common.md
  feedback/  questions/  guidance/   your marked work, past questions, OSCOLA/exam guidance (instructions, not evidence)
  source_topics.yaml             which area each shared Act / judgment belongs to (edit `topic` to move one)
  lay_concepts.yaml              everyday / problem-question facts -> the legal issue (improves search)
  synonyms.yaml                  search synonyms
  topic_map.yaml                 Law-folder subfolders -> areas, ignore list, privacy patterns
```

## Areas of law

Your modules: ai-data-protection, biolaw, business-law, commercial-law, competition-law, contract-law, criminal-law,
eu-law, international-commercial-mediation, land-law, law-and-medicine, pensions-law, private-international-law,
tort-law, trusts-law.

Primary-source areas (statutes and judgments outside your modules): civil-procedure, constitutional-law,
employment-law, family-law, financial-services-law, intellectual-property, tax-law, wills-succession.

## Keeping it tidy

- New file in the Law folder → `python -m legalbot.ingest.run` files it by its module folder.
- New Acts / judgments in "Official Legislation" → land in `general-law`, then
  `python -m legalbot.ingest.sort_sources` (propose) and `--apply` (move) give each one its area.
- Moved a file to the wrong area? Change its `topic` in `source_topics.yaml`, then run `sort_sources --apply`
  (or tell Claude).
- After any change: `python -m legalbot.index build` (only new text is embedded).
