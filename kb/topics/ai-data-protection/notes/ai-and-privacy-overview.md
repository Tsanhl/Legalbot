---
title: AI and Privacy – Mapping the Problems (Overview)
topic: ai-data-protection
authority: notes
written: 2026-11-18
---
# AI and Privacy – Mapping the Problems (Overview)

## Overview
This note gives the conceptual map of AI and data protection law. The best single framework is Daniel J. Solove, "Artificial Intelligence and Privacy" (US privacy law scholar). Solove argues that AI's privacy problems are mostly **old problems "remixed" and amplified**. AI exposes deep flaws in privacy law's foundations (especially the **individual-control model**), and privacy law "properly conceptualized and constituted" can do much to regulate AI, but it needs rebuilding rather than a patch. Use this note to frame a research question, then go to the specific notes (GDPR, automated decisions, inferences, scraping, AI Act, US law).

## The law (the framework)

### 1. What AI is, and "AI exceptionalism"
- Today's "AI" mostly means machine learning, neural networks and generative AI, not sentient robots. Many technologies are **rebranded** older ones, and misleading metaphors cause confusion. AI is "both old and new": a step in a long evolution and also a leap forward. The difference is more data, more computing power and better analytics.
- **Against "AI exceptionalism"**: do not treat AI as so special that we miss how its privacy problems are existing problems enhanced. AI is continuous with digital-age data collection and use. Echoing Easterbrook's "Law of the Horse" point, Solove says AI will affect nearly every area of law, though it has dimensions needing special consideration.
- Contrast: Eric Goldman warns privacy law is "devouring" other fields and that privacy experts should not make policy outside their "swimlanes".
- Solove takes no position on whether to enact new laws or amend old ones. What matters is an adequate vision of the whole landscape. A general AI law risks missing privacy problems; adding AI rules on top of flawed privacy law is like "adding a story to a building with an unstable and poorly designed foundation".

### 2. The architecture problem: individual control
- Privacy law is dominated by **"privacy self-management"**. In the US this is **notice-and-choice** (post a notice; silence equals consent; some opt-outs and a few opt-ins). Susser: businesses can do what they want if they tell users and users proceed. Hartzog and Richards: "notice" means fine print and "choice" means take-it-or-leave-it.
- The **GDPR** is stronger: it rejects opt-out consent (consent must be express/opt-in), gives many rights (access, rectification, erasure, portability, objection, challenging automated decisions), and imposes duties (DPIAs, data minimisation, records of processing, data protection by design and default). But Waldman says such duties are often carried out in a hollow, "symbolic" way, and the GDPR "still places far too much weight on the individual".
- Why control fails with AI: people do not read or understand notices; there are thousands of controllers; people lack the expertise to assess risk; and AI works on **collective datasets**. Solow-Niederman's "**inference economy**" and Viljoen's relational view of data show that understanding a decision requires everyone's data, which cannot be given to individuals. Individual rights such as FCRA correction do not reach systemic methodology.
- Solove's conclusion: "the individual control model is doomed". The law should **bring the collection and use of data under control** through structural measures, meaningful duties on organisations and accountability.
- **Harm/risk approach**: the EU AI Act's risk categories (unacceptable, high, minimal). Kaminski: risk regulation aims to reduce known, measurable harms rather than ban. The GDPR's DPIA requirement (high risk to rights and freedoms, e.g. systematic and extensive evaluation including profiling producing legal or similarly significant effects) is a partial harm approach, and US state laws copy it. Problems: risk frameworks fit unquantifiable, individual harms badly (Kaminski); who assesses (organisations assessing themselves is "the fox... in the henhouse"); whether assessments should be shared; general-purpose and generative AI make risk assessment nearly impossible (Helberger and Diakopoulos; Wolff, Yoo and Lehr, who add that purpose limitation and minimisation are nearly impossible for training data); timing (pre-deployment review approaches licensing).

### 3. Inputs: data collection
**Scraping**
- AI data is gathered mainly by **scraping** or by **repurposing user data**. Clearview AI scraped billions of photos for facial recognition without consent.
- Scraping ignores almost all privacy principles: transparency, notice, purpose specification and limitation, consent or opt-out, vetting of recipients, rights, retention, minimisation, accuracy and security.
- US law largely leaves scraping alone because the data seems "public". This reflects the "**secrecy paradigm**", a binary view that only concealed data is private. Privacy is really about boundaries and **practical obscurity**. US authorities recognise privacy in public data: *Carpenter v United States* (geolocation in public places is an "intimate window" into a person's life; a warrant is needed) and *DOJ v Reporters Committee* (a compiled dossier from public records differs from scattered courthouse files).
- Inconsistency: the GDPR has no general exemption for publicly available data. It does refer to public data in several places: art 14(2)(f) ("publicly accessible sources"), art 49(1)(g) (public registers) and art 9(2)(e) (special-category data "manifestly made public"). None of these supplies a lawful basis. Art 9(2)(e) only lifts the art 9 prohibition, so an art 6 basis is still needed. The CCPA exempts "publicly available information" broadly; Colorado and Connecticut define it narrowly. FCRA and HIPAA protect data regardless of public availability.
- Platforms' terms of service (e.g. LinkedIn) bar scraping, but privacy laws generally do not require sites to protect against it. Solove says they should, since failing to stop scraping is functionally like transferring data without consent. *hiQ v LinkedIn*: the court treated LinkedIn's blocking of scraping as anticompetitive; Solove says the court was wrong to let competition override privacy, though the concern that only incumbents can use data is real. Governments should attach conditions to public-records access (*Los Angeles Police Department v United Reporting*: conditional access is not a speech restriction).
**"Consensual" collection**
- Firms changed notices to cover AI training: Zoom (2023, "any purpose", reversed after backlash), Google, X.
- **Consent is a fiction**, whether opt-in or opt-out. Clicking "agree" barely increases reading (by about 1%). With generative AI the uses are unknown, so consent is "a blank check". Bietti: consent is a "free pass".
- Under the GDPR, scraping needs one of six art 6 bases. Express consent is impractical at web scale, so **legitimate interests** is the most plausible basis but is "restrictive" and uncertain. Strict enforcement could produce a "data famine", favour big firms with user bases, and skew models away from EU populations.

### 4. Outputs: data generation
- **Inference** through the "aggregation effect": innocuous data can reveal health, religion, politics or sex life (the *Target* pregnancy-prediction example). Inferences harm whether accurate (exposure) or inaccurate (misjudgment).
- Privacy laws regulate collection, not **generation**. Inference blurs collection and processing and lets firms evade collection limits and minimisation. Solove: the law should treat inferred data **on an equal footing** with collected data. Wachter and Mittelstadt: under the GDPR inferences get less protection, and they propose a "**right to reasonable inferences**" (ex ante justification for high-risk inferences). Solove calls that welcome but "far from enough". Hildebrandt: EU law does not grasp the new knowledge data processing creates.
- **End-runs** around confidentiality protections (privileges, the Genetic Information Nondiscrimination Act) and around de-identification (Tschider, on HIPAA and the CCPA).
- **Malevolent material**: hallucinated defamatory claims (ChatGPT falsely naming a professor as a harasser), deepfakes (mostly targeting women; Citron counts more than 9,500 sites hosting non-consensual intimate images), voice-clone scams. US s 230 of the Communications Decency Act immunises platforms, and courts have read it broadly, wiping out distributor liability (Citron, Franks). Creators of AI tools should bear responsibility.
- **Security**: prompt injection, data poisoning. Breach notification is "not a vaccine or a cure". The law fails to allocate responsibility to all who could prevent harm.
- **Simulation**: AI passing as human (Turing test; Pasquale calls such bots "counterfeiters"). The law should require disclosure of AI interactions and recognise the manipulative power of simulation even when disclosed.

### 5. Decision-making
- **Prediction** threatens agency (judging people for things they have not done), "fossilises the past", creates **self-fulfilling prophecies**, and raises fairness issues beyond accuracy.
- **Bias**: biased training data and new forms of discrimination (see algorithmic-discrimination-and-auditing.md).
- **Automation**: quantification and depersonalisation. GDPR **art 22** is limited to "solely" automated decisions, and the GDPR lacks guidance on how humans should be integrated. Technology should not be seen as a panacea for human flaws, nor humans as the cure for machine flaws; the aim is fair decisions.

### 6. Data analysis
- Surveillance, identification (e.g. facial recognition), interpretation and decoding. A line must be drawn on law-enforcement use. Privacy law has long dealt poorly with surveillance.

### 7. Oversight, participation and accountability
- **Transparency** is hard with "black box" AI (Pasquale). What should be transparent: code, logic, training data? Trade secrets block it, and individuals cannot understand it anyway. Transparency remains valuable, but the law should not over-rely on it. Kaminski: transparency has a clear place in algorithmic accountability.
- **Due process**: individuals need ways to challenge algorithmic decisions (Crawford and Schultz: a neutral party should review).
- **Stakeholder involvement**: AI development often excludes affected groups.
- **Accountability and remedies**: enforcement needs strengthening (see the FTC's algorithmic disgorgement in scraping-and-generative-ai-training-data.md).

## Key authorities
- GDPR (Regulation (EU) 2016/679) arts 5(1)(c), 6, 7, 9(2)(e), 13–15, 22, 25, 30, 35.
- EU AI Act (risk tiers).
- US: *Carpenter v United States*; *DOJ v Reporters Committee for Freedom of the Press*; *Los Angeles Police Department v United Reporting*; *hiQ v LinkedIn*; CCPA "publicly available information" exemption; FCRA; HIPAA; GINA; Communications Decency Act s 230.
- Scholars cited by Solove: Kaminski, Solow-Niederman, Viljoen, Hartzog and Richards, Waldman, Wachter and Mittelstadt, Hildebrandt, Citron, Pasquale, Bietti, Goldman.

## Debate and critique
- **Privacy law vs AI-specific law**: Solove (rebuild privacy law; avoid exceptionalism) vs Goldman (keep privacy in its lane) vs the EU's dual-track approach (GDPR plus AI Act). A research essay can test whether the AI Act fills the gaps Solove identifies (inference, scraping, collective harms) or merely adds "a story" to a weak foundation.
- **Individual control vs structural regulation**: is GDPR consent and rights-based protection fit for AI? Solove: no. A defender would point to GDPR duties (DPIA, by design, accountability), which already go beyond control.
- **Risk-based regulation**: attractive but has limits (who assesses; unquantifiable harms; general-purpose AI).
- **Public data**: the secrecy paradigm against contextual integrity and obscurity. The GDPR's lack of a public-data exemption is a key EU/US difference.
- **Data famine vs feeding frenzy**: strict enforcement may entrench incumbents and bias models.
- **Inferences**: should inferred data be personal data with full rights? (See inferences-and-profiling.md.)

## Applying it to a problem question
For a research essay, use Solove's map as a checklist for any AI system:
1. **Inputs**: how was the data obtained (scraped, repurposed, consented)? Which lawful basis (GDPR art 6)? Is it special-category data (art 9)? Is "public" data treated as fair game?
2. **Outputs**: does the system infer new data? Is it treated as personal data? Are there end-runs around protections? Does it produce harmful content?
3. **Decisions**: are there solely automated decisions with legal or similarly significant effects (art 22)? Is there bias? Is there meaningful human involvement?
4. **Oversight**: transparency (arts 13–15), contestability, DPIA (art 35), accountability and enforcement.
5. **Jurisdiction**: EU/UK GDPR and the AI Act vs the US patchwork (FTC Act s 5, state laws).

## Links
- gdpr-framework-for-ai.md
- lawful-basis-consent-legitimate-interests.md
- automated-decision-making-and-right-to-explanation.md
- inferences-and-profiling.md
- scraping-and-generative-ai-training-data.md
- eu-ai-act.md
- us-ai-privacy-regulation.md
- algorithmic-discrimination-and-auditing.md
