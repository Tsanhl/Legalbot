---
title: The GDPR Framework Applied to AI – Scope, Principles, Accountability, DPIAs and Design
topic: ai-data-protection
authority: notes
written: 2026-11-18
sources:
  - raw/secondary/gdpr-bd84e6.md
  - raw/secondary/the-european-union-general-data-protection-regulation-what-it-is-and-w-7d3974.md
  - raw/secondary/gdpr-3-areas-of-ambiguity-75df02.md
  - raw/secondary/gdpr-series-a-design-for-life-designing-the-future-of-privacy-327f4a.md
  - raw/secondary/artificial-intelligence-and-privacy-daniel-j-solove-435ba1.md
---
# The GDPR Framework Applied to AI – Scope, Principles, Accountability, DPIAs and Design

## Overview
The General Data Protection Regulation (Regulation (EU) 2016/679, adopted May 2016, applicable from 25 May 2018) is the baseline law for any AI system that processes personal data in the EU (and, as "UK GDPR", in the UK; see uk-data-protection-reform.md). It is technology-neutral: it does not mention "AI", but its scope, principles and duties apply to every stage of the AI lifecycle (collecting training data, training, deployment and outputs). This note sets out the architecture: scope and key definitions; the art 5 principles and their tension with AI; accountability; data protection by design and default (art 25); DPIAs (art 35); and fines. Lawful bases, automated decisions, inferences, erasure and transfers have their own notes.

## The law

### 1. Background and normative foundations (Hoofnagle, van der Sloot and Zuiderveen Borgesius (2019) 28 ICT Law 65)
- Europe treats privacy as a human right and, separately, **data protection** as a fundamental right: EU Charter art 7 (private and family life) and **art 8** (protection of personal data: fair processing for specified purposes on consent or another legitimate basis laid down by law; rights of access and rectification; control by an independent authority). The Charter became binding with the Lisbon Treaty (2009). ECHR art 8 also applies.
- In the 1970s the US developed the **Fair Information Practices** but applied them seriously only to government (Privacy Act 1974) and credit reporting (FCRA 1970). Europe deepened them and applied them horizontally to business and vertically to government. The US is **sectoral**, with the FTC as general consumer-protection enforcer.
- The **1995 Data Protection Directive** (95/46/EC) did not fully harmonise and suffered weak enforcement (some states courted big tech; the French fined Facebook just €150,000 in 2017). The GDPR (Commission proposal 2012, nearly 4,000 Parliament amendments) responds with harmonisation and strong enforcement.
- Dual goal (art 1): free flow of data and protection of people, but with emphasis on protection. The GDPR is in "great tension with big data". It encourages information governance, in-house data use and **humans in the loop**; it favours firms with direct customer relationships over third-party adtech; it uses "big sticks... but only a few carrots".
- The CJEU is the final interpreter (it has struck down data retention mandates and the Safe Harbor agreement, and recognised the right to be forgotten). The **EDPB** gives persuasive but non-binding guidance.

### 2. Scope
- **Material scope (art 2)**: processing of personal data wholly or partly by automated means (and manual filing systems). Exclusions: activities outside EU law; common foreign and security policy; purely personal or household activity; law-enforcement processing by competent authorities (covered by a separate directive).
- **Territorial scope (art 3)**: (1) processing in the context of an EU establishment, wherever it takes place; (2) non-EU controllers or processors offering goods or services to, or **monitoring the behaviour** of, people in the EU. This captures non-EU AI developers serving EU users.

### 3. Key definitions (art 4)
- **Personal data** (art 4(1)): "any information relating to an identified or identifiable natural person", directly or indirectly, including by identifiers such as name, ID number, location data, online identifier, or physical, physiological, genetic, mental, economic, cultural or social factors.
- **Identifiability** (recital 26): consider "all the means reasonably likely to be used, such as singling out", taking account of cost, time and available technology. **Pseudonymised** data remain personal data; the GDPR does not apply to **anonymous** information. (Central to whether trained AI models contain personal data: see edpb-opinion-ai-models.md.)
- **Processing** (art 4(2)): any operation (collection, structuring, storage, adaptation, retrieval, use, disclosure, combination, erasure...). Training and running a model involve processing.
- **Profiling** (art 4(4)): any automated processing using personal data "to evaluate certain personal aspects", in particular to "analyse or predict" performance at work, economic situation, health, preferences, interests, reliability, behaviour, location or movements.
- **Pseudonymisation** (art 4(5)); **controller** (art 4(7)): determines "purposes and means", alone or jointly; **processor** (art 4(8)): processes on the controller's behalf. In AI supply chains (developer, deployer, API user) the allocation of controller and processor roles is crucial.
- **Consent** (art 4(11)): "freely given, specific, informed and unambiguous", by statement or "clear affirmative action".
- **Biometric data** (art 4(14)), including facial images, and **health data** (art 4(15)) are special-category data under art 9.

### 4. Principles (art 5(1)) and AI
| Principle | Text (short) | AI pressure point |
|---|---|---|
| (a) Lawfulness, fairness, transparency | processed lawfully, fairly and transparently | opaque "black box" models; scraped data without notice |
| (b) Purpose limitation | specified, explicit, legitimate purposes; no incompatible further processing (research and statistics exception via art 89(1)) | repurposing user data for training; general-purpose models with no fixed purpose |
| (c) Data minimisation | adequate, relevant, limited to what is necessary | models need vast datasets; Wolff, Yoo and Lehr (via Solove): minimisation and purpose limitation are "nearly impossible" for general-purpose training data |
| (d) Accuracy | accurate, kept up to date | hallucinations; inaccurate inferences |
| (e) Storage limitation | no longer than necessary (research exception) | data memorised in model weights |
| (f) Integrity and confidentiality | appropriate security | model inversion, prompt injection, data poisoning |
- **Accountability (art 5(2))**: the controller "shall be responsible for, and be able to demonstrate compliance with" para 1.
- **Further processing compatibility test (art 6(4))**: where further processing is not based on consent or law, consider: (a) the link between the original and new purposes; (b) the context of collection and the relationship with data subjects; (c) the nature of the data (special categories, criminal data); (d) possible consequences; (e) safeguards such as encryption or pseudonymisation. This is the key test when a platform wants to train AI on existing user data.

### 5. Special categories (art 9)
- Processing that reveals racial or ethnic origin, political opinions, religious or philosophical beliefs, trade union membership, genetic data, biometric data for unique identification, health, sex life or sexual orientation is **prohibited** unless an art 9(2) exception applies: (a) **explicit consent**; (b) employment and social protection law; (c) vital interests; (d) not-for-profit bodies; (e) data "**manifestly made public by the data subject**"; (f) legal claims; (g) substantial public interest under law; (h) health and social care; (i) public health; (j) archiving, research and statistics.
- AI inference can generate special-category data from innocuous inputs (see inferences-and-profiling.md). The **Austrian Post** fine (€18m) concerned processing the statistical likelihood that individuals would vote for particular parties, i.e. political opinion (Tobin).

### 6. Data protection by design and by default (art 25)
- **Art 25(1)**: taking account of the state of the art, cost, the nature, scope, context and purposes of processing and the risks, the controller must, **both when determining the means and at the time of processing**, implement appropriate technical and organisational measures (e.g. pseudonymisation) designed to implement principles such as minimisation effectively and to integrate safeguards.
- **Art 25(2)**: **by default**, only data necessary for each purpose are processed (amount, extent, storage period, accessibility); data must not by default be made accessible to an indefinite number of people.
- Certification (art 42) can help demonstrate compliance.
- **Flannery (Deloitte, 2017)**: Privacy by Design was coined in the 1990s by Ann Cavoukian (Information and Privacy Commissioner of Ontario). PbD means building privacy into the design, operation and management of systems; Privacy by Default means the strictest settings apply automatically. Both are proactive, not reactive. The GDPR codified them in art 25 with little formal guidance, so organisations must work out how to embed them.
- For AI: minimisation at the dataset stage, pseudonymisation, filtering of special-category data, output filters, privacy-enhancing technologies, and documentation.

### 7. Data protection impact assessments (art 35)
- **Art 35(1)**: where processing, "in particular using new technologies", is **likely to result in a high risk** to rights and freedoms, the controller must assess its impact **before** processing.
- **Art 35(3)** – a DPIA is required in particular for: (a) **systematic and extensive evaluation of personal aspects based on automated processing, including profiling, on which decisions with legal or similarly significant effects are based**; (b) large-scale processing of special-category or criminal data; (c) large-scale systematic monitoring of publicly accessible areas.
- Supervisory authorities publish lists of processing requiring (art 35(4)) or not requiring (art 35(5)) a DPIA.
- **Content (art 35(7))**: (a) a systematic description of the processing and purposes (including legitimate interests); (b) necessity and proportionality; (c) risks to rights and freedoms; (d) measures to address the risks.
- Codes of conduct are taken into account (art 35(8)); seek data subjects' views where appropriate (art 35(9)); prior consultation with the authority if high risk remains (art 36).
- Solove: "rights and freedoms" extend beyond privacy to free speech, thought, movement, non-discrimination, liberty, conscience and religion. But self-assessment risks the "fox... in the henhouse", and the GDPR does not require DPIAs to be published.

### 8. Rights (arts 12–22, briefly)
- Transparency and information (arts 12–14, including "meaningful information about the logic involved" in automated decision-making), access (art 15), rectification (16), erasure (17), restriction (18), portability (20), objection (21), automated decisions (22). See automated-decision-making-and-right-to-explanation.md and right-to-erasure-google-spain.md.

### 9. Enforcement and fines (art 83)
- Fines must be "effective, proportionate and dissuasive". Infringements of the **basic principles** (arts 5, 6, 7, 9), **data subject rights** (arts 12–22) and **transfers** (arts 44–49) attract up to **€20 million or 4% of total worldwide annual turnover**, whichever is higher.
- **Tobin, "GDPR – 3 areas of ambiguity" (2019)**:
  1. **Fines**: art 83 factors are abstract. The Article 29 Working Party's 2017 guidelines and the EDPB (at that time) gave no calculation framework. Dutch guidance starts from the nature of the infringement (fines generally in the hundreds of thousands); German guidance uses a five-step, size- and turnover-based method that may give harsher fines. Examples: **CNIL v Google €50m** (lack of transparency; invalid consent for lack of information); **Berlin DPA v Deutsche Wohnen €14.5m** (archiving tenants' data; arts 5 and 25); **Austrian Post €18m** (art 9, inferred political opinions).
  2. **Cookies and consent**: *Planet49* (pre-ticked boxes are not consent; cookie information must include duration and third-party access); regulators disagree (Spain accepted continued browsing; the ICO says continuing to use a site is not valid consent). See lawful-basis-consent-legitimate-interests.md.
  3. **Territorial scope of the right to be forgotten**: *Google v CNIL* (C-507/17) (de-referencing need not be global but must be effective within the EU, discouraging access to non-EU versions; the court left open the possibility of global orders).

## Key authorities
- GDPR arts 1–6, 9, 25, 35, 36, 83; recital 26.
- EU Charter arts 7–8; ECHR art 8.
- Data Protection Directive 95/46/EC.
- Enforcement examples: CNIL v Google (€50m); Berlin DPA v Deutsche Wohnen (€14.5m); Austrian Post (€18m).
- *Planet49* (C-673/17); *Google v CNIL* (C-507/17).
- Commentary: Hoofnagle, van der Sloot and Zuiderveen Borgesius (2019); Tobin (2019); Flannery (2017); Solove (structural critique).

## Debate and critique
- **Is the GDPR fit for AI?** Hoofnagle et al: it constrains information-intensive business models but enables others; it is in tension with big data. Solove: it still over-relies on individual control and its duties may be "symbolic" (Waldman). Defenders point to accountability, art 25 and DPIAs as structural tools that can reach AI.
- **Purpose limitation and minimisation vs general-purpose AI**: can foundation models ever comply? Options include treating training as a distinct purpose with research or legitimate-interest justification, the compatibility test in art 6(4), and the EDPB's case-by-case approach (see edpb-opinion-ai-models.md).
- **Technology neutrality**: a strength (future-proof) and a weakness (vagueness; uncertainty prompting AI-specific law such as the AI Act).
- **Enforcement uncertainty**: fines methodology and divergent national approaches (Tobin) undermine predictability (see enforcement-and-regulatory-limits.md).
- **Design duties**: art 25 is potentially the most AI-relevant provision, but it is open-textured ("state of the art", "cost"), and enforcement on art 25 has been rare apart from cases such as Deutsche Wohnen.

## Applying it to a problem question
1. **Does the GDPR apply?** Is personal data involved (art 4(1); recital 26 identifiability; is the model or output anonymous)? Material scope exclusions (art 2)? Territorial reach (art 3(1) establishment; art 3(2) targeting or monitoring EU individuals)?
2. **Who is the controller or processor** at each stage (data collection, training, fine-tuning, deployment)? Joint controllership?
3. **Principles**: test each art 5 principle against the facts (purpose drift, excessive data, inaccuracy, retention in weights, security).
4. **Lawful basis** (art 6) and **special-category condition** (art 9). See the separate note.
5. **Further processing**: apply the art 6(4) factors if reusing data.
6. **DPIA**: is it required (art 35(3)(a)–(c); national lists)? Was it adequate (art 35(7))? Prior consultation (art 36)?
7. **Design and default** (art 25): what measures were or could have been taken?
8. **Rights and automated decisions**: arts 13–15, 21, 22.
9. **Enforcement**: likely fine band (art 83(5)); authority (one-stop shop and lead authority for cross-border processing; see enforcement note).

## Links
- ai-and-privacy-overview.md
- lawful-basis-consent-legitimate-interests.md
- automated-decision-making-and-right-to-explanation.md
- inferences-and-profiling.md
- edpb-opinion-ai-models.md
- right-to-erasure-google-spain.md
- international-transfers-schrems-ii.md
- enforcement-and-regulatory-limits.md
- uk-data-protection-reform.md
