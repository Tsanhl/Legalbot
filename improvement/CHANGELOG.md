# Improvement changelog

One entry per fix: what triggered it, what changed, where. Newest first. Answer-writing rules learned from a
review also go in that module's `kb/topics/<module>/style.md` → "Review log", which the prompt loads.

## 2026-11-19 — Case notes for judgments that could not be found
- **Added** cross-checked case notes (our own words, sources listed in front matter): *R v Donovan* (LawTeacher + course
  seminar), *R v Savage; DPP v Parmenter* (Lawprof + *Mowatt*, *Cunningham*), *R v Latimer* (Lord Mustill in A-G's Ref No 3
  of 1994 + course slides), *Re W* and *Re R* (Lowe and Juss (1993) 56 MLR 865, added to law-and-medicine journals).
- **Removed** an AI-generated *Savage* "summary" that invented facts (stone, shop window, Criminal Damage Act); it is on
  the ignore list so it can never be re-imported.

## 2026-11-19 — 16 older judgments added by hand
- Moved from the Desktop into `Law/…/Cases added 2026-11` (land, medicine, criminal); imported and indexed.
- **Bug fixed:** a re-import could undo type corrections (it re-derived "lecture" and pruned the re-filed copy).
  Corrections now live in `kb/source_types.yaml` and the import applies them. Import report crash fixed.
- AI-written *Savage; Parmenter* summary filed as secondary. Still to find: *Latimer*, *Donovan*, *Re R*, *Re W*.

## 2026-11-19 — Gaps from the Keck essay-plan tests
- **Trigger:** gap items `204002-…-57471e`, `204334-…-f9b890` (essay plan on abandoning *Keck*)
- **Finding:** only the *Keck* judgment itself was missing; *Torfaen*, *Caixa-Bank*, *Mickelsson*, *Scotch Whisky*,
  *Commission v Italy* (Trailers) were present.
- **Change:** added Joined Cases C-267/91 and C-268/91 *Keck and Mithouard* (EUR-Lex, paras 1–19 + ruling) to
  `kb/topics/eu-law/raw/case_law/`.

## 2026-11-19 — Review of law & medicine essay (fetal abnormality v PGT)
- **Trigger:** trace `20261119-204531-55a2cd` · gap item `improvement/knowledge_gaps/2026-11-19/204922-missing-authority-20261119-204531-55a2cd.md`
- **Finding:** the "missing" authorities (*Crowter*, *Jepson*, Robinson 2024, Sheldon & Wilkinson 2001, HFEA s 13(9)) were
  in the knowledge base; retrieval did not reach them. One wrong citation came from our own note.
- **Changes**
  - Retrieval follows **academics** named in notes ("Robinson (2024)", "Sheldon and Wilkinson (2001)") and more cases /
    statute sections for essays and problem questions (`legalbot/retrieval/engine.py`: `_follow_academics`, `_follow_authorities`).
  - Case names with brackets ("*R (Crowter) v …*") and abbreviations ("s.13(9) HFEA") are recognised; bold headings are no
    longer mistaken for cases; the judgment file is preferred over articles that discuss it.
  - **Re-filed** 16 sources stored under the wrong type (EU regulations, statute extracts, HFEA 1990) as legislation.
  - **HFEA 1990** current text fetched (legislation.gov.uk); old print excluded (`kb/topic_map.yaml` ignore list).
  - **Note corrected:** Robinson (2024) **87(1)** MLR 218 (`kb/topics/law-and-medicine/notes/abortion-fetal-abnormality.md`).
  - Word-limit target tightened (answers ran ~4–5% over): now aims at 88–97% of the limit.
- **Check:** the same essay title now retrieves *Crowter*, *Jepson*, Robinson, Sheldon & Wilkinson, McGuinness, Abortion Act ss 1, 5.

## 2026-11-19 — Knowledge base reorganised: one folder per area of law
- 416 shared Acts / judgments moved from `official-sources` to their area (`kb/source_topics.yaml`); 8 new areas.
- Statute sections followed by Act name + section number; notes always consulted (meaning + keyword search).

## 2026-11-19 — Always answer (no dead ends)
- Answer ladder: knowledge base → web (official sites, [W#]) / background ([background]); accuracy guard marks
  unverified authorities ⚠︎; supporting passage shown for every [S#].
