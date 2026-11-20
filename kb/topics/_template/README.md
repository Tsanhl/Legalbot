Topic folder layout

  raw/legislation/   extracted statutes / regulations / treaty articles   (authority: legislation)
  raw/case_law/      extracted judgments                                  (authority: case_law)
  raw/journals/      extracted journal articles                           (authority: journal)
  raw/lectures/      extracted slides / handouts / seminar sheets         (authority: lecture)
  notes/             OUR rephrased knowledge, one file per sub-topic      (authority: note)
  style.md           optional module-specific answer style (marker preferences)

Each .md file starts with front matter, e.g.

  ---
  authority: case_law
  title: United Brands v Commission
  citation: Case 27/76 United Brands v Commission [1978] ECR 207
  original: My Law Notes/Competition/united-brands.pdf
  date: 1978-02-14
  ---

Notes should cite raw ids they summarise:  `sources: [competition-law/raw/case_law/united-brands.md#dominance]`
Raw sections are the evidence authority; notes are the entry point.
