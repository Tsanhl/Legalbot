---
title: International Data Transfers and Schrems II (Case C-311/18, Advocate General's Opinion)
topic: ai-data-protection
authority: notes
written: 2026-11-18
sources:
  - raw/secondary/schrems-ii-cjeu-2020-819817.md
  - raw/secondary/schrems-ii-cjeu-2020-opinion-3a62ff.md
  - raw/secondary/gdpr-bd84e6.md
  - raw/secondary/clearview-ai-cnil-2022-ffd6d7.md
---
# International Data Transfers and Schrems II (Case C-311/18, Advocate General's Opinion)

## Overview
AI development is global: data is collected in one jurisdiction, processed by cloud and model providers in another, and results are returned elsewhere. Chapter V of the GDPR restricts transfers of personal data outside the EU so that the EU level of protection is not undermined. *Data Protection Commissioner v Facebook Ireland and Schrems* (Case C-311/18, "Schrems II") concerned transfers by Facebook Ireland to its US parent under standard contractual clauses (SCCs) and, indirectly, the EU-US Privacy Shield adequacy decision. **Important limitation on the sources:** both Schrems II files in the knowledge base are the Opinion of Advocate General Saugmandsgaard Øe delivered on 19 December 2019 (ECLI:EU:C:2019:1145), not the Court's own judgment. Everything below about *Schrems II* is the AG's reasoning; the Court is not bound by it, and its eventual ruling is not in the files, so do not present the AG's views as the Court's holding.

## The law

### 1. Three routes for transfers (AG Opinion paras 1-2; GDPR Chapter V)
1. **Adequacy decision** (GDPR art 45): the Commission finds that the third country ensures an "adequate" level of protection; this means "essentially equivalent" to that in the EU under the GDPR read in the light of the Charter (the AG cites *Schrems* (the first case) for this standard, para 112).
2. **Appropriate safeguards** (art 46), for example Commission-approved standard data protection clauses (art 46(2)(c)): the exporter and importer contract for protection. Art 46(1) conditions this on enforceable data subject rights and effective legal remedies being available.
3. **Derogations** (art 49), for example data subject consent, where neither of the above is available.

Art 44 states the general principle: transfers must not undermine the level of protection the GDPR guarantees.

### 2. The dispute
Mr Schrems complained to the Irish DPC about transfers of his data by Facebook Ireland to Facebook Inc. in the US. The DPC considered the outcome depended on the validity of Decision 2010/87/EU (SCCs for transfers to processors in third countries, as amended by Implementing Decision 2016/2297). The High Court of Ireland referred questions to the CJEU, including concerns about US intelligence access to transferred data (section 702 FISA, Executive Order 12333, PPD 28) and about the Commission's Privacy Shield decision (Implementing Decision 2016/1250).

### 3. The AG's analysis
- **Scope.** The AG held that EU law applies to a transfer for commercial purposes to a third country even if the importing company's data may later be processed by that country's authorities for national security purposes. The transfer itself is "processing" carried out in a Member State; the purpose of later processing by foreign authorities is irrelevant to whether EU law governs the transfer (paras 100-106). The exclusion of public-security activities (GDPR art 2(2); Art 4(2) TEU) does not cover the commercial export.
- **Level of protection for SCC transfers.** The AG agreed with the DPC, Mr Schrems and Ireland that the "appropriate safeguards" in art 46 must give a level of protection essentially equivalent to that guaranteed by the GDPR read in light of the Charter (para 115). Charter requirements do not vary with the legal basis of transfer, but the *way* continuity is secured does. An adequacy decision certifies the third country's own law; SCCs supply safeguards where the third country's law is inadequate (paras 117-120).
- **Validity of the SCC Decision.** The AG concluded that nothing affected the validity of Decision 2010/87 (para 5, para 343). Reasoning, in summary: the SCCs are a general mechanism that does not depend on the law of any particular third country; the burden falls on the exporter and importer, and on supervisory authorities, to ensure protection in the specific case.
  - *Controllers' obligations:* the clauses require the importer to inform the exporter if it cannot comply (for example because of conflicting foreign law); in that event the exporter must suspend the transfer or terminate the contract. The AG read the exporter's right under Clause 5(a) and related clauses as a duty, not a mere option (para 132). A footnote to Clause 5 treats compliance with mandatory foreign requirements as consistent with the clauses only if they do not go beyond what is necessary in a democratic society for the listed interests (such as public security); beyond that, compliance is a breach.
  - *Supervisory authorities' obligations:* under GDPR art 58(2)(f) and (j) (limit or ban processing, suspend data flows to third countries), authorities must, after diligent examination, act to remedy a breach, if necessary by suspending the transfer (paras 140-149). Powers cannot be limited by a Commission implementing decision, and recital 11 of Decision 2010/87 ("exceptional cases") was obsolete (para 142-143).
  - *Objections answered:* case-by-case enforcement may give fragmented outcomes, but that is inherent in the decentralised design, mitigated by the cooperation and consistency mechanism and EDPB resolution of disagreements (para 155). The lack of remedies in the third country does not itself invalidate the SCC decision (para 157-158), which cannot depend on the level of protection in every destination.
- **Privacy Shield.** The AG advised the Court *not* to examine the validity of the Privacy Shield decision as it was unnecessary to resolve the dispute, but in the alternative expressed doubts (paras 6, 308 and following): that section 702 FISA surveillance is accompanied by sufficiently clear and precise limits, that PPD 28 creates rights for individuals, that the proportionality safeguards are adequate, and that individuals have effective judicial redress, including whether the Ombudsperson mechanism could compensate for gaps (paras 328-333 and following). He framed the task as comparing US rules and practices with EU standards under the "essential equivalence" test.

## Key authorities
- *Data Protection Commissioner v Facebook Ireland Ltd and Schrems* (C-311/18), Opinion of AG Saugmandsgaard Øe, 19 December 2019 (the files). The Court's judgment is not in the knowledge base.
- *Schrems* (the first case) on essential equivalence, as cited by the AG.
- GDPR arts 44-46, 49, 58(2), 2(2); Directive 95/46 art 25/26 (predecessor); Decision 2010/87/EU (SCCs); Implementing Decision 2016/1250 (Privacy Shield); Charter arts 7, 8, 47.
- CNIL *Clearview AI*: relevant on territorial reach, the GDPR applying to a US controller under art 3(2)(b).

## Debate and critique
- **Case-by-case versus structural fixes.** The DPC argued the problems with US surveillance law are structural and cannot be solved by case-by-case enforcement; the AG replied that EU law does not require a general preventive solution for all transfers to a country, and that the decentralised model is a legislative choice. The practical effect is that exporters bear the burden of assessing foreign law.
- **Balance of pragmatism and fundamental rights.** The AG states his approach as balancing "a reasonable degree of pragmatism in order to allow interaction with other parts of the world" against the Charter's fundamental values (para 7).- **National security carve-outs.** The AG's scope analysis separates the commercial transfer (governed by EU law) from later foreign intelligence processing (outside the GDPR's territorial scope). This sidesteps but does not resolve the underlying incompatibility between EU rights and foreign surveillance.
- **Relevance to AI.** Cloud-based training, vendor APIs and cross-border model deployment all involve transfers. The same Chapter V analysis applies to personal data used to train or run models by processors outside the EU, and a deployer must consider the importer's local legal environment.

## Applying it to a problem question
1. Is personal data leaving the EU/EEA, even to a group company or cloud processor? (The transfer itself is processing.)
2. Which Chapter V route is used: adequacy decision (is one in force for the destination?), SCCs or other art 46 safeguards, or an art 49 derogation?
3. For SCCs: does the importer's national law (for example intelligence access) prevent it complying? If so, is the exporter prepared to suspend or terminate, and are there supplementary safeguards? On the AG's view the exporter must act, not merely may.
4. What can the supervisory authority do (art 58(2))? Expect an obligation to act on a well-founded complaint, including suspension.
5. Distinguish the AG's Opinion from the Court's judgment; state clearly which you are citing.
6. For an AI scenario, identify each recipient in the training or inference chain (data labelling, cloud, model API) and test each flow.

## Links
- gdpr-framework-for-ai
- gdpr-lawful-bases-and-consent
- data-subject-rights-and-erasure
- web-scraping-and-ai-training-data
- ai-and-privacy-overview
