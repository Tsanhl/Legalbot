---
title: Cybersecurity of AI Medical Devices
topic: biolaw
authority: notes
written: 2026-11-18
sources:
  - raw/lecture/regulation-eu-2024-1689-of-the-european-parliament-and-of-the-council--bba630.md
  - raw/lecture/regulation-eu-2017-745-of-the-european-parliament-and-of-the-council-o-3b0b6e.md
  - raw/legislation/nis2-directive-20d29e.md
  - raw/secondary/s-l4-e-the-role-of-cybersecurity-in-medical-devices-regulation-future--68c26a.md
  - raw/secondary/e-new-cybersecurity-requirements-for-medical-devices-in-the-eu-the-for-a5ef8a.md
  - raw/secondary/s-l3-eu-and-us-regulation-regulatory-approaches-towards-ai-based-medic-641201.md
  - raw/lecture/s-l4-e-on-medical-device-cybersecurity-compliance-in-eu-738f1b.md
  - raw/lecture/s-l4-e-security-and-privacy-issues-in-implantable-medical-devices-a-co-d07abc.md
  - raw/lecture/l2-reading-towards-new-human-rights-in-the-age-of-neuroscience-and-neu-3c0b05.md
---
# Cybersecurity of AI Medical Devices

## Overview
the materials of Topic 2 moves from safety (non-adversarial failures) to **security** (failures caused by an adversary). Connected medical devices - pacemakers, insulin pumps, surgical robots, AI diagnostic tools, hospital IT - can be attacked, harming patients directly. EU law addresses this through several overlapping instruments: the **MDR** (Annex I), the **AI Act** (art 15), the **Cyber Resilience Act (CRA)** for other products with digital elements, and the **NIS2 Directive (EU) 2022/2555** for critical entities such as hospitals. The materials' view: cybersecurity regulation is "finally going somewhere", but overlaps, standards-dependence and enforcement remain problems.

## The law

### 1. Security concepts (the materials)
- **Security = freedom from adversarial failures**; with digital devices everywhere, security means cybersecurity.
- Simpler than safety: the system moves from a first state to a second state, and what matters is that an adversary caused it. Safety modelling (hazards) can describe the system, but "errors" do not exist with adversaries - "adversarial failures" are used instead. Unreliability = insecurity.
- Key ideas: attack surface; threat modelling; testing; defences; supply chain security; physical cybersecurity. One must understand the device, its environment, users, use of public infrastructure, and adversaries.
- Implant-specific: Camara, Peris-Lopez and Tapiador's survey of implantable medical devices (pacemakers, defibrillators, neurostimulators, insulin pumps) shows constraints of energy, storage and computing power, and the tension between **normal mode** (strong access control and encryption, patient controls who connects) and **emergency mode** (the device must respond to medical staff even if authentication fails). Security must be balanced against patient safety and battery life.
- Brain-computer interfaces: "malicious brain-hacking" (Ienca and Haselager) at the measurement, decoding and feedback stages could hijack a user's control - linking cybersecurity to mental integrity ([neurorights.md](neurorights.md)).

### 2. AI Act - art 15 (accuracy, robustness and cybersecurity)
- Art 15(1): high-risk AI systems must achieve appropriate accuracy, robustness and cybersecurity, consistently throughout their lifecycle.
- Art 15(3): accuracy levels and metrics must be declared in instructions for use.
- Art 15(4): resilience to errors, faults and inconsistencies; technical redundancy (backup, fail-safe); continuously learning systems must address biased feedback loops.
- **Art 15(5)**: resilience against unauthorised third parties exploiting vulnerabilities; technical solutions must where appropriate prevent, detect, respond to, resolve and control **data poisoning, model poisoning, adversarial examples/model evasion, confidentiality attacks and model flaws**.
- Lecture assessment: authorities, notified bodies and general-purpose AI providers must consider security; but it is not as positive as it could be - **low-risk AI is not covered and can be a gateway into other systems**; better than the original proposal.

### 3. MDR - Annex I
- No standalone cybersecurity chapter, but functionality and intended use require security: the MDR's purpose is defeated without it (the materials - a "teleological" argument).
- **Annex I s 17.2**: software must be developed in line with the state of the art, including risk management "including information security", verification and validation. **s 17.4**: manufacturers must set minimum requirements for hardware, IT networks and IT security measures, "including protection against unauthorised access".
- Guidance: **MDCG 2019-16** on cybersecurity for medical devices, including aligning safety and security risk management (the cybersecurity compliance paper identifies four core concepts for compliance).

### 4. Cyber Resilience Act (CRA)
- Covers products with digital elements generally (non-medical devices; wide coverage, cumulative with NIS2) - for this course, it gives baseline cybersecurity requirements for AI not covered by the MDR (e.g. smartwatches).
- Art 1: rules for making such products available; essential requirements for design, development and production; essential requirements for vulnerability handling during expected use; market surveillance and enforcement.
- **Art 13(2)**: manufacturers must assess cybersecurity risks and account for them in planning, design, development, production, delivery and maintenance, to minimise risks, prevent incidents and minimise impacts, including on users' health and safety.
- Structure like other product laws (notified bodies, authorities), strong focus on testing; "generally quite strong", but "weak for a regulation" (the materials).

### 5. NIS2 Directive (EU) 2022/2555
- Successor to NIS1; critical infrastructure cybersecurity. Annex I lists **Health**: healthcare providers (Directive 2011/24/EU art 3(g)), EU reference laboratories, medicinal R&D, pharmaceutical manufacturing, and makers of devices critical in a public health emergency; Annex II covers manufacture of medical devices and IVDs.
- Lecture: applies to AI used in hospitals (always critical infrastructure), even when used in treatment outside hospitals; extra certification, easier if already compliant with other law. As a directive it must be implemented by Member States.
- **Art 20**: management bodies must approve and oversee risk-management measures, can be held liable, and must receive training.
- **Art 21(1)**: appropriate and proportionate technical, operational and organisational measures considering the state of the art, standards and cost. **Art 21(2)**: an all-hazards approach including at least: risk analysis and security policies; incident handling; business continuity (backups, disaster recovery); **supply chain security**; secure acquisition, development and maintenance including vulnerability handling; effectiveness assessment; cyber hygiene and training; cryptography/encryption; HR security, access control, asset management; multi-factor authentication and secure communications.
- **Art 23**: notify the CSIRT/competent authority without undue delay of significant incidents (severe operational disruption or financial loss, or considerable damage to others); notification alone does not increase liability.
- **Supervision (Ch VII)**: art 33(2) powers over important entities include on-site inspections, targeted security audits, security scans, information requests, access to data and evidence of implementation. **Art 34** sets administrative fines for breaches of arts 21 or 23: maxima of at least EUR 10m or 2% of worldwide turnover for essential entities, and at least EUR 7m or 1.4% for important entities.
- **Penalties**: Member States set effective, proportionate and dissuasive penalties and notify the Commission by 17 January 2025. The the materials slide labels this "Article 39", but in the Directive text in the raw folder the penalties provision is **art 36** (art 39 is the committee procedure).
- Lecture: "very strong" on paper; actual action depends on jurisdiction; like NIS1, extremely complex and yet to be tested.

## Key authorities
- AI Act art 15 (esp 15(5)).
- MDR Annex I s 17.2, 17.4; MDCG 2019-16.
- CRA arts 1, 13(2).
- NIS2 Directive arts 20, 21, 23, 32-34, 39; Annexes I-II.
- GDPR (security of processing, relevant to device data - see [health-data-and-medical-implants.md](health-data-and-medical-implants.md)).

## Debate and critique
- **Ludvigsen, "The Role of Cybersecurity in Medical Devices Regulation: Future Considerations and Solutions" (2023)** compares the EU, US and UK (distinguishing Great Britain and Northern Ireland). He models cybersecurity across three areas: the device itself, the surrounding institutional system (manufacturers, healthcare providers) and the data. He criticises reliance on **standards** - often privately produced products, not always best practice, and changeable - so they should not be the primary basis of regulation. He warns that state-mandated backdoors (e.g. the UK Online Safety Bill, the EU Child Sexual Abuse Regulation) undermine security: "any backdoor for the state is a backdoor for any adversary". He recommends four principles for primary legislation:
  1. **Technology specificity** - medical device law is technology-specific but vague on cybersecurity; strict rules would avoid "legacy device" problems (e.g. devices still on Windows XP) and focus on real threats like phishing;
  2. **Circumvention protection** (drawing on the "Bad Man's Law" idea that how law is written and how people act under it differ);
  3. **Genuine privacy**;
  4. **Security by design**.
- **New cybersecurity requirements** reading: forthcoming European Health Data Space, Data Act and AI Act add requirements for connected devices; risks include unauthorised access, data breaches and manipulation of functions, harming patients and trust.
- **Transatlantic perspective** reading: cybersecurity of AI medical devices sits at the intersection of three regulatory fields (medical devices, AI, cybersecurity) that are usually treated separately; attacks on healthcare infrastructure increased after COVID-19.
- **Overlaps** (reflection question): one AI pacemaker could fall under the MDR, the AI Act, NIS2 (if used by a hospital or made by a critical manufacturer) and the GDPR. Which certification first? Does compliance with one ease another (the materials says NIS2 is easier if other law is already met)?
- **Hospital digital security v physical patient security** (reflection): NIS2 protects network and information systems and their physical environment (all-hazards), unlike older security thinking focused on physical access.
- **Is the MDR adequate for present needs?** It relies on general Annex I wording and guidance; the materials and Ludvigsen argue for more explicit, technology-specific security duties.

## Applying it to a problem question
Seminar exercise: identify security failures in an AI device (surgical robot, text/image diagnosis tool, AI pacemaker) and how to make it more resilient.
1. **Threat model**: attack surface (wireless link, cloud, hospital network, training data); adversaries (criminals, ransomware, insiders, states); supply chain.
2. **AI-specific attacks**: data poisoning, model poisoning, adversarial examples, model inversion/confidentiality attacks (art 15(5)).
3. **Applicable law**: MDR Annex I s 17 (all software devices); AI Act art 15 if high-risk; CRA if non-medical connected product; NIS2 if hospital or covered manufacturer; GDPR for data.
4. **Design responses**: security by design; access control and encryption balanced with emergency access (implants); redundancy and fail-safes (art 15(4)); patching and vulnerability handling (CRA, NIS2 art 21(2)(e)); legacy device replacement.
5. **Organisational duties**: risk management, incident reporting (NIS2 art 23; MDR art 87 for serious incidents), management liability (art 20), training.
6. **Enforcement**: market surveillance, supervisory audits (art 33), fines.
Trap: confusing safety (accidents, non-adversarial) with security (adversarial) - examiners expect the distinction.

## Links
- [medical-devices-regulation.md](medical-devices-regulation.md)
- [ai-and-the-eu-ai-act.md](ai-and-the-eu-ai-act.md)
- [software-and-ai-as-medical-devices.md](software-and-ai-as-medical-devices.md)
- [health-data-and-medical-implants.md](health-data-and-medical-implants.md)
- [neurorights.md](neurorights.md)
