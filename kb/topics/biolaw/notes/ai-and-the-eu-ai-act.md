---
title: AI in Healthcare and the EU AI Act
topic: biolaw
authority: notes
written: 2026-11-18
---
# AI in Healthcare and the EU AI Act

## Overview
The analysis of cybersecurity and safety for AI in healthcare focuses on EU law rather than UK law, because UK medical device law does not cover a wide enough market and, because of Northern Ireland, UK law does not fully apply to medical devices. Commentary defines AI technically and legally and introduces the **AI Act, Regulation (EU) 2024/1689**. The Act is product-safety legislation with a fundamental-rights purpose; AI used in or as a medical device that must undergo third-party conformity assessment is high-risk. Understanding how the AI Act overlaps with the Medical Device Regulation (MDR) is the bridge to the rest of the topic.

## The law

### 1. Three types of AI used
- **Symbolic AI**: rule-based decision-making (from video games to automated tax/legal processing; some cyber-physical systems). No learning or generative elements; detailed but time-consuming to code; considered **safer**.
- **Machine-learning (ML) AI**: from slightly tweaked symbolic systems to neural networks (robots, antivirus/firewalls, cars). Can be autonomous or supervised; dataset- and learning-based; can be unpredictable; black-box and transparency problems.
- **LLM AI**: ML at scale; originally for language, repurposed to predict next steps; enormous datasets ("foundation models"); AI as a service; resource-demanding; adoption lags (small language models may help); more unpredictable and unsafe; relies on vast human labour to fix.
Commentary uses both the Act's distinctions and these technical categories because the Act alone does not capture the technical concepts.

### 2. Background and structure
- Built on the GDPR and the EU's product regulation (New Legislative Framework).
- Structure: recitals; definitions; prohibited practices; high-risk AI (classification and obligations); transparency obligations; general-purpose AI; innovation measures; governance (European AI Board, national competent authorities, single points of contact); high-risk AI database; post-market monitoring and market surveillance; codes of conduct; delegation; penalties.
- **Purpose - art 1(1)**: improve the functioning of the internal market and promote the uptake of "human-centric and trustworthy" AI, while ensuring a high level of protection of health, safety and Charter fundamental rights (including democracy, rule of law, environment) against harmful effects of AI, and supporting innovation.
- **Art 1(2)**: harmonised rules on placing on the market, putting into service and use; prohibitions; requirements for high-risk AI and obligations of operators; transparency rules; rules for general-purpose AI models; market monitoring, surveillance, governance and enforcement; innovation support especially for SMEs.

### 3. Definition - art 3(1)
"AI system" means a machine-based system designed to operate with varying levels of autonomy, that **may** exhibit adaptiveness after deployment, and that, for explicit or implicit objectives, **infers** from its input how to generate outputs (predictions, content, recommendations or decisions) that can influence physical or virtual environments. Commentary treats the elements as cumulative and asks of each: machine-based? autonomy? adaptiveness (only "may")? objectives? inference? generation? output? influence on environments? Question whether purely symbolic systems "infer".

### 4. Prohibited practices - art 5
Include: subliminal/manipulative/deceptive techniques materially distorting behaviour and causing significant harm (art 5(1)(a)); exploiting vulnerabilities due to age, disability or socio-economic situation (b); social scoring leading to unjustified detrimental treatment (c); predicting criminal offending based solely on profiling or personality traits (d); untargeted scraping of facial images to build recognition databases (e); emotion inference in the workplace and education, **except for medical or safety reasons** (f); plus biometric categorisation and real-time remote biometric identification for law enforcement, subject to detailed exceptions. Commentary asks: are these future-proof? circumventable? Fines up to EUR 35m or 7% of worldwide turnover (art 99(3)).

### 5. High-risk classification - art 6
- **Art 6(1)**: an AI system is high-risk where (a) it is a safety component of a product, or is itself a product, covered by Union harmonisation legislation in **Annex I**, and (b) that product must undergo **third-party conformity assessment** under that legislation. The MDR (Regulation (EU) 2017/745) and IVDR (2017/746) are listed in Annex I.
- **Art 6(2)**: Annex III use-cases are also high-risk (in health: emergency call evaluation and dispatch, emergency triage, access to essential services, life and health insurance risk assessment and pricing - van Kolfschooten and van Oirschot).
- **Art 6(3)**: an Annex III system is not high-risk if it poses no significant risk of harm (e.g. narrow procedural task, improving a completed human activity).
- Commentary: "AI used in or as medical devices will always be considered high-risk." Van Kolfschooten and van Oirschot refine this: in practice the art 6(1) route captures medical devices of **class IIa or higher** (which need notified-body assessment); **class I** devices and wellbeing apps outside the MDR are generally low-risk with only transparency duties (and the art 4 AI literacy duty).
- Timing (art 113): applies from 2 August 2026; Chapters I-II (including prohibitions) from 2 February 2025; **art 6(1) and corresponding obligations from 2 August 2027**.

### 6. Obligations for high-risk AI (Chapter III, Sections 2-3)
Art 8 compliance; art 9 risk management system; art 10 data and data governance; art 11 technical documentation; art 12 record-keeping; art 13 transparency to deployers; art 14 human oversight; **art 15 accuracy, robustness and cybersecurity** (see [cybersecurity-of-medical-devices.md](cybersecurity-of-medical-devices.md)); art 16 provider obligations; art 17 quality management; art 26 deployer obligations; art 27 fundamental rights impact assessment. Obligations are positively (sometimes negatively) defined, written widely and mirror other product legislation. General-purpose AI models have separate duties (arts 53-55, including systemic-risk models).

### 7. Enforcement and liability
- Enforcement = scope + special rules + authority powers (Chapter VII Sections 2-3; national competent authorities, notifying/notified bodies, post-market monitoring). Art 99: penalties "effective, proportionate and dissuasive"; up to EUR 15m/3% for breaches of operator obligations (arts 16, 22-24, 26, 50).
- Liability: obligations create liability for providers, users and third parties (breach of obligations, standards, authority orders). Commentary does not cover the AI Liability Directive. In the UK, liability would rest on tort and the implementation of the old Product Liability Directive.
- Individual rights are thin: art 85 right to complain to a market surveillance authority; art 86 right to explanation, which does not apply to AI medical devices and only for high-risk decisions with significant adverse effects (van Kolfschooten and van Oirschot).

### 8. Legal overlap (recitals 46, 50; Annex I)
Which comes first: the AI by itself, AI as part of a system, the whole system, or specialised (sectoral) AI rules? Commentary calls this an open question - arguments run in several directions. For AI medical devices, the AI Act requirements are integrated into the MDR conformity assessment, creating an extra layer of regulation (van Kolfschooten and van Oirschot). See [software-and-ai-as-medical-devices.md](software-and-ai-as-medical-devices.md).

## Key authorities
- Regulation (EU) 2024/1689 (AI Act): arts 1, 3(1), 5, 6(1)-(3), 8-17, 26-27, 50, 85-86, 99, 113; Annex I; Annex III.
- Regulation (EU) 2017/745 (MDR) as Annex I legislation.

## Debate and critique
- **Is product legislation enough?** (reflection question). **Almada and Petit, "The EU AI Act: A Medley of Product Safety and Fundamental Rights?"** (RSC Working Paper 2023/59): the Act combines two repertoires - product safety and fundamental rights - and may fail if it ignores their structural differences. They identify three classic law-and-technology problems: the **pacing problem**, a **mismatch between means and ends**, and **institutional path dependence** (reliance on harmonised standards and product-safety institutions to protect rights), and propose adjustments.
- **Van Kolfschooten and van Oirschot, "The EU AI Act (2024): Implications for healthcare"**: horizontal, not sector-specific; welcome data governance rules for AI medical devices; but (1) little oversight of low-risk health AI, risking unproven or harmful tools and loss of trust; (2) the art 27 FRIA only lists impacts, without a duty to assess acceptability, applies only on first use, and may not bind private healthcare providers (recital 96) - creating disparities across Member States; (3) few individual patient rights (no right to object to AI diagnosis; narrow art 86); (4) national security exemption (e.g. biothreat screening); (5) scientific research exemption may cover clinical trials. They recommend guidelines defining key concepts, extending the FRIA to all healthcare uses, and multi-stakeholder standards.
- **Hospitals as providers**: hospitals that build their own AI (e.g. COVID triage tools trained on own patient data) become providers with full obligations.
- **Security exceptions**: the UN Advisory Committee (A/HRC/57/61) criticises national security and law enforcement exceptions in the AI Act as offering insufficient protection against misuse of neurotechnology.
- **Regulators v GDPR experience**: will AI regulators perform better than data protection authorities? (reflection question).
- **Does the type of AI matter?** Symbolic AI is predictable and easier to certify; ML and LLM systems are adaptive, opaque and harder to fit within fixed conformity assessment - this drives the "system view" critique (see [software-and-ai-as-medical-devices.md](software-and-ai-as-medical-devices.md)).

## Applying it to a problem question
Example devices: AI surgical robot; text-based diagnosis support; image-based diagnosis support; AI-supported pacemaker.
1. **Is it an "AI system" under art 3(1)?** Walk through each element.
2. **Is it prohibited (art 5)?** E.g. emotion inference at work (allowed for medical/safety reasons).
3. **Is it high-risk?** Is it (or a safety component of) a medical device under the MDR ([medical-devices-regulation.md](medical-devices-regulation.md))? What MDR class - does it need notified-body assessment (art 6(1)(b))? Or an Annex III health use?
4. **Who is the operator?** Provider (developer, or a hospital building its own tool) or deployer (clinician/hospital using it)?
5. **Which obligations?** Arts 9-15 for providers; art 26 and possibly art 27 for deployers; art 15 cybersecurity.
6. **Enforcement and remedies**: market surveillance, fines, complaint (art 85), explanation (art 86, limited), tort/product liability.
7. **Timing**: art 6(1) obligations apply from 2 August 2027.
Traps: assuming every health app is high-risk; forgetting AI Act duties sit on top of MDR duties; assuming the AI Act gives patients strong individual rights.

## Links
- [medical-devices-regulation.md](medical-devices-regulation.md)
- [software-and-ai-as-medical-devices.md](software-and-ai-as-medical-devices.md)
- [cybersecurity-of-medical-devices.md](cybersecurity-of-medical-devices.md)
- [health-data-and-medical-implants.md](health-data-and-medical-implants.md)
- [mental-privacy-and-neural-data.md](mental-privacy-and-neural-data.md)
