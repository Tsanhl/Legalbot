---
title: The EU AI Act (Regulation (EU) 2024/1689)
topic: ai-data-protection
authority: notes
written: 2026-11-18
---
# The EU AI Act (Regulation (EU) 2024/1689)

## Overview
The AI Act, adopted on 13 June 2024 and published in the Official Journal on 12 July 2024, is described in the secondary material (ISACA, *Understanding the EU AI Act*) as the first comprehensive AI law in the world. It is a product-safety style regulation built on a risk-based classification: some practices are banned, "high-risk" systems face heavy obligations, some systems carry transparency duties, and general-purpose AI (GPAI) models have their own regime. It sits alongside the GDPR, not in place of it: wherever AI systems process personal data, both apply. For data-protection essays the key themes are the overlap with the GDPR, bias-testing data, transparency, and enforcement.

## The law

### 1. Scope and roles (arts 2-3)
- Applies to providers placing AI systems or GPAI models on the EU market (wherever established); deployers established or located in the EU; providers and deployers in third countries where the system's *output is used in the Union*; importers and distributors; product manufacturers; authorised representatives of non-EU providers (art 2(1)). The ISACA note adds affected persons located in the EU.
- Key roles: **provider** (develops, or has developed, a system or GPAI model placed on the market), **deployer** (uses a system in a professional capacity), importer, distributor, product manufacturer. One organisation can be a deployer for one use and a provider for another.
- A system is characterised (per ISACA's summary) as machine-based, operating with varying autonomy, inferring from inputs how to generate outputs such as predictions, content, recommendations or decisions. Risk is the combination of probability and severity of harm.
- Exclusions include military, defence and national-security systems (unless also used for other purposes) and AI used solely for scientific research and development.
- **AI literacy (art 4):** providers and deployers must take measures, to their best extent, to ensure sufficient AI literacy among staff and others operating AI on their behalf.

### 2. Prohibited practices (art 5)
Subject to narrow exceptions, banned practices include (summarised): subliminal or manipulative/deceptive techniques that materially distort behaviour and cause significant harm; exploiting vulnerabilities (for example age or disability); social scoring leading to detrimental or unjustified treatment; risk assessments predicting criminal offending based solely on profiling or personality traits; untargeted scraping of facial images from the internet or CCTV to build facial recognition databases; inferring emotions in the workplace or education; biometric categorisation inferring sensitive traits such as race, political opinions or sexual orientation; and "real-time" remote biometric identification in public spaces for law enforcement, with exceptions (targeted search for victims of abduction or trafficking; prevention of specific, substantial, imminent threats; identifying suspects of listed offences). Link this to *Clearview*: the facial-database scraping ban is the AI Act's direct response to that type of business model.

### 3. High-risk systems (art 6, Annex I and III)
- Art 6(1): a system is high-risk if it is a safety component of (or is itself) a product under the Annex I harmonisation legislation and that product needs third-party conformity assessment.
- Art 6(2): systems in the Annex III areas are high-risk. Annex III areas include biometrics (where permitted), critical infrastructure, education and vocational training, employment and workers' management, access to essential private and public services and benefits, and law enforcement (the ISACA note also lists immigration and border management and the judicial and democratic processes).
- Art 6(3): an Annex III system is *not* high-risk where it poses no significant risk of harm to health, safety or fundamental rights, including by not materially influencing the outcome of decisions, for example where it performs a narrow procedural task, improves the result of a prior human activity, detects decision patterns without replacing human assessment, or performs a purely preparatory task.

### 4. Obligations for high-risk providers (summarised from ISACA with article references it gives)
- **Risk management** system across the lifecycle, iterative, including risks to under-18s and vulnerable groups (art 9).
- **Data and data governance** (art 10): training, validation and testing data must be relevant, representative and as free of errors as possible; bias must be examined and mitigated. **Art 10(5)** lets providers exceptionally process special-category personal data where strictly necessary for bias detection and correction, if conditions are met (including that bias cannot be effectively addressed with other data such as synthetic or anonymised data, technical limits on reuse, state-of-the-art security such as pseudonymisation). This is an AI Act gateway that sits beside, and does not displace, the GDPR.
- **Accuracy, robustness and cybersecurity** (art 15), including resilience to data poisoning, model poisoning and adversarial attacks, and handling of feedback loops for systems that keep learning.
- **Quality management system** (art 17), technical documentation, record-keeping/logging, transparency to deployers, **human oversight** (art 14), conformity assessment, registration, post-market monitoring and serious-incident reporting.

### 5. Obligations for deployers
Use according to instructions; ensure oversight by people with competence, training and authority; ensure input data is relevant and representative where under their control; monitor and report incidents (to provider, importer/distributor and authorities); keep logs; inform workers when high-risk AI is used in the workplace; and, where applicable, carry out a GDPR data protection impact assessment. **Art 27 FRIA:** before deploying certain high-risk systems, public bodies, private entities providing public services, and deployers of certain Annex III 5(b) and (c) systems must assess impact on fundamental rights (describing processes, duration and frequency of use, affected groups, specific risks, human oversight measures and remediation arrangements).

### 6. Transparency (art 50)
People must be told they are interacting with an AI system (such as a chatbot); providers of systems generating synthetic content must mark outputs as artificially generated or manipulated in a machine-readable way, considering technical feasibility; deployers of emotion-recognition or biometric-categorisation systems must inform those exposed.

### 7. General-purpose AI models (arts 51-55)
- GPAI model providers must keep technical documentation (including training and testing), supply information to downstream system providers, and publish a sufficiently detailed summary of the content used for training (art 53, as ISACA reports).
- **Systemic risk (art 51):** a GPAI model has systemic risk if it has high-impact capabilities (by tools, indicators and benchmarks) or is so designated by the Commission; high impact is *presumed* where cumulative training compute exceeds 10^25 floating point operations (the Commission can amend thresholds by delegated act). Such providers must evaluate the model, run adversarial testing, assess and mitigate systemic risks, report serious incidents to the AI Office, and ensure cybersecurity.

### 8. Rights, supervision and penalties
- **Art 86:** right to explanation for affected persons of certain Annex III high-risk decisions (see the ADM note).
- **Art 99 fines:** up to EUR 35m or 7% of worldwide annual turnover (whichever higher) for breach of art 5 prohibitions; up to EUR 15m or 3% for most other operator obligations; ISACA adds up to EUR 7.5m or 1% for supplying incorrect, incomplete or misleading information; for SMEs the lower of the amounts applies. Anyone may complain to the market surveillance authority. The Commission (through the AI Office) supervises GPAI obligations (art 88).
- Each Member State must have at least one **regulatory sandbox** to support innovation (art 57).

### 9. Timeline (art 113)
Entered into force 1 August 2024 (twentieth day after publication). General application from 2 August 2026, but: Chapters I and II (including art 4 and the art 5 bans) from 2 February 2025; GPAI obligations, governance and penalties chapters from 2 August 2025; art 6(1) high-risk (Annex I products) from 2 August 2027. ISACA's timeline also notes 31 December 2030 for certain large-scale IT systems.

## Key authorities
- Regulation (EU) 2024/1689 (AI Act): arts 2, 4, 5, 6, 9, 10 (especially 10(5)), 14, 15, 17, 27, 50, 51, 53, 55, 57, 86, 88, 99, 113; Annexes I and III.
- GDPR (applies concurrently where personal data is processed).
- EDPB Opinion on AI models (Dec 2024): cites AI Act art 5 as a limit on what counts as a legitimate interest, and art 10(5) on bias-correction data (footnotes to paras 64 and 68).
- ISACA, *Understanding the EU AI Act: Requirements and Next Steps* (2024): practitioner summary used above.

## Debate and critique
- **Complement or overlap?** ISACA stresses that many AI Act requirements (risk management, data governance, record-keeping, accuracy, oversight, transparency) already exist in GDPR practice and that privacy teams should lead compliance, since the GDPR applies concurrently. A contrasting concern is duplicated or inconsistent obligations and multiple regulators.
- **Product-safety versus rights model.** The Act regulates systems and providers; individuals' rights are comparatively thin (notably art 86, complaints). The GDPR gives individual rights but, as the overview note explains, struggles with scale. Consider whether the two together close the accountability gap.
- **Innovation.** ISACA records the criticism that the Act may stifle innovation and notes sandboxes as the Act's answer. Contrast the more permissive US approaches in the discussion (see ai-and-privacy-overview).
- **Classification uncertainty.** The art 6(3) derogation and the "preparatory task" exceptions invite borderline arguments about whether a system is high-risk, echoing the "solely automated" loophole in GDPR art 22.
- **GPAI thresholds.** A compute-based presumption (10^25 FLOPs) is simple but crude; the Commission can amend it, and ISACA notes classification may need periodic reassessment.
- **Extraterritoriality.** Output-used-in-the-Union jurisdiction (art 2(1)(c)) resembles the GDPR's reach, so non-EU developers may be caught (compare *Clearview* applying GDPR art 3(2)(b)).

## Applying it to a problem question
1. Is it an "AI system" or a GPAI model? Who is the provider, deployer, importer or distributor? Is the EU connection (placing on market, establishment, or output used in the EU) satisfied?
2. Check art 5 first: any prohibited practice (manipulation, social scoring, facial-image scraping, emotion inference at work, and so on)?
3. If not prohibited, classify: Annex I product safety component, or Annex III area? Could the art 6(3) derogation apply?
4. List obligations for the party's role: provider (risk management, data governance, documentation, oversight, conformity, monitoring) or deployer (oversight, monitoring, logs, worker notice, DPIA, FRIA if applicable).
5. Add transparency duties (chatbots, synthetic content, emotion recognition).
6. For GPAI models: documentation, training-content summary; is systemic risk presumed (over 10^25 FLOPs)?
7. Overlay the GDPR: lawful basis, DPIA, art 22, data subject rights, art 10(5) for bias data (strictly necessary, safeguards).
8. Penalties: identify the tier (art 5 breach versus other obligations versus misleading information) and check dates of application.

## Links
- ai-and-privacy-overview
- gdpr-framework-for-ai
- gdpr-lawful-bases-and-consent
- automated-decision-making-and-right-to-explanation
- web-scraping-and-ai-training-data
- data-subject-rights-and-erasure
