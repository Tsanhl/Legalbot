---
title: Software and AI as Medical Devices
topic: biolaw
authority: notes
written: 2026-11-18
---
# Software and AI as Medical Devices

## Overview
A recurring question is: **when is software - including AI - a medical device?** The answer decides whether the MDR's demanding regime (and, through art 6(1) AI Act, the high-risk AI rules) applies. The test turns on the manufacturer's **intended purpose**, as confirmed by the CJEU in *SNITEM* (C-329/16). Critics point to two difficulties: manufacturers can avoid regulation by disclaiming a medical purpose, and adaptive machine-learning systems do not fit a model built for static products.

## The law

### 1. Definition and intention
- MDR art 2(1) expressly includes "software" intended by the manufacturer for a listed medical purpose (diagnosis, prevention, monitoring, prediction, prognosis, treatment, etc.) (see [medical-devices-regulation.md](medical-devices-regulation.md)). Art 2(12) defines intended purpose by reference to the manufacturer's labelling, instructions, promotional or sales materials and statements, and clinical evaluation (as discussed by Ludvigsen, Nagaraja and Daly).
- Recital 19 MDR: software specifically intended for medical purposes is a medical device; software for general purposes, even used in healthcare, or for lifestyle/well-being, is not (as summarised in the SNITEM commentary and the materials).

### 2. *SNITEM and Philips France v Premier Ministre*, Case C-329/16, ECLI:EU:C:2017:947 (CJEU, 7 December 2017)
- **Facts**: Philips's "Intellispace Critical Care and Anesthesia" (ICCA) software, used in resuscitation and anaesthesia, cross-referenced patient data with the drug a doctor intended to prescribe to flag contraindications, drug interactions and excessive doses. It bore a CE mark under the MDD. A French decree (No 2014-1359) required further national certification of prescription software. SNITEM and Philips challenged it; the Conseil d'Etat referred the question whether ICCA was a medical device under art 1(2)(a) of Directive 93/42.
- **Held**: software of which at least one function uses patient-specific data to detect contraindications, drug interactions and excessive doses is, for that function, a medical device - **even if it does not act directly in or on the human body** (para 39).
- **Two cumulative conditions**: (1) the manufacturer must intend it for a specifically medical purpose listed in the definition (following *Brain Products*, C-219/11: use in a medical context is not enough); (2) on the "action" - no need to act on or in the body; the legislature focused on purpose, not effect (Directive 2007/47/EC, recital 6).
- Software that only archives, collects and transmits data (e.g. patient record storage) is not a medical device. The Court drew on MEDDEV 2.1/6 (software that creates or modifies information by calculation, quantification or comparison to give patient-specific information). Once CE-marked, the device must circulate freely; no extra national certification.
- **Significance** (Minssen, Mimler and Mak, (2020) 28 Med L Rev 615): intended purpose is the key factor; the MEDDEV guidelines were effectively elevated into case law; a paradigm shift for digital health, AI and Big Data. the materials cites SNITEM on the "for human use" element.

### 3. Classification of software - MDR Annex VIII Rule 11
Diagnostic/therapeutic decision software: class IIa; IIb if decisions may cause serious deterioration or surgery; III if they may cause death or irreversible deterioration. Physiological monitoring software: IIa; IIb for vital parameters with risk of immediate danger. Other software: class I. Niemiec: most AI devices will be IIa or IIb and so need notified-body assessment; many devices move up from the lowest MDD class. Classification depends on intended use, not the technology (consistent with the International Medical Device Regulators Forum approach).

### 4. Ludvigsen, Nagaraja and Daly, "When Is Software a Medical Device? Understanding and Determining the 'Intention' and Requirements for Software as a Medical Device in European Union Law" (2022) 13 European Journal of Risk Regulation

- **Problem**: if intention is limited to public statements (art 2(12)), any manufacturer can avoid the MDR simply by saying the software is not a medical device - undermining art 1(1) and endangering patients. Software is also "deceptive": hidden layers, data collection and cyber risks.
- **Direct intention** - sources: (1) marketing materials; (2) internal documentation that regulators can access (e.g. via art 10); (3) informal sources (statements, tags in search systems).
- **Indirect intention** - what the software actually does: (1) data-gathering practices (e.g. biometric data, health records); (2) data analysis producing results resembling art 2(1) purposes; (3) specifications designed to function as, substitute for or replace existing devices.
- If either type of intention points to a medical device, the affirming intention prevails (but the software must still actually serve an art 2(1) purpose).
- **Requirements**: (1) intended for a medical purpose (direct or indirect); (2) not generic software unmodified for standalone/module use; (3) not an accessory (then the accessory rules apply); (4) used for or on human beings (from C-329/16). They criticise MEDDEV 2.1/6's storage/archiving distinction as lacking a basis in the Regulation but agree that pure storage does not fulfil any purpose. Regulators may survey the software market under their art 93 powers - though whether they have the expertise is open.

### 5. Interplay with the AI Act
AI software qualifying as a medical device requiring notified-body assessment is high-risk under art 6(1) AI Act; the AI Act requirements are integrated into the MDR conformity assessment (van Kolfschooten and van Oirschot). the materials flags recitals 46 and 50 and Annex I and asks which regime has priority: the AI alone, AI as a component, the whole system, or specialised rules - an open question. Art 6(1) obligations apply from 2 August 2027 (art 113). See [ai-and-the-eu-ai-act.md](ai-and-the-eu-ai-act.md).

## Key authorities
- *SNITEM* C-329/16 (2017) - prescription-support software is a medical device; no need to act on the body.
- *Brain Products* C-219/11 (2012) - purpose must be specifically medical; medical context alone insufficient.
- MDR arts 2(1), 2(2), 2(12), 10, 93; recital 19; Annex VIII Rule 11; Annex I s 17.
- AI Act art 6(1), Annex I, recitals 46, 50, art 113.
- Guidance: MEDDEV 2.1/6 (stand-alone software, under the MDD); MDCG 2019-11 (cited by Ludvigsen et al); MEDDEV 2.7/1 rev 4 (clinical evaluation).

## Debate and critique
- **Circumvention via intention**: the "wellness" framing problem (see also the direct-to-consumer neural implant scenario in [mental-privacy-and-neural-data.md](mental-privacy-and-neural-data.md)). Ludvigsen et al's indirect intention broadens coverage but raises legal certainty concerns: manufacturers may not know in advance that capabilities, rather than claims, will be judged.
- **Gerke, Babic, Evgeniou and Cohen, "The need for a system view to regulate AI/ML-based software as medical device" (2020) npj Digital Medicine 3:53**: current FDA-authorised AI devices (e.g. IDx-DR for diabetic retinopathy, 2018) use "locked" algorithms; updates trigger new review, so makers avoid updating, wasting AI's ability to learn ("the update problem"). More fundamentally, regulators review **products**, but AI/ML outcomes depend on the whole **system** - healthcare teams inputting data, physicians reacting to recommendations, insurers' reimbursement - so regulators should move towards a system view, even though this strains limits such as the FDA not regulating the practice of medicine. (A US-focused paper, but relevant to EU product-based regulation.)
- **Evidence quality** (Niemiec): retrospective, single-dataset validation inflates claims; the MDR's clinical evaluation and post-market rules may help.
- **What makes AI in or as a device different?** (reflection) Adaptiveness (art 3(1) AI Act "may exhibit adaptiveness"), opacity, data dependence, unpredictability (ML and LLM AI more than symbolic AI) and new cyber attack types (data/model poisoning - see [cybersecurity-of-medical-devices.md](cybersecurity-of-medical-devices.md)).
- **Accessories**: when should software that supports a device meet device-level requirements? Ludvigsen et al note accessories are defined by abilities, not just claims.

## Applying it to a problem question
1. What does the software do? Store/transmit only (not a device) or create patient-specific information by calculation/comparison (likely a device)?
2. Intended purpose: labelling, marketing, instructions (direct); data gathered, analysis, design as substitute for a device (indirect - argue using Ludvigsen et al).
3. Is it generic, an accessory, or for human beings?
4. Classify under Rule 11 by the consequences of decisions it informs.
5. Consequences: conformity route, GSPRs (Annex I s 17), AI Act high-risk duties if notified body needed.
6. If adaptive ML: how will updates be handled? Post-market surveillance; system-level risks (clinician reliance, workflow).
Example: a text-based AI diagnosis support tool marketed as "general information only" but trained on clinical records and producing differential diagnoses - argue indirect intention; Rule 11 class IIa or higher; high-risk under the AI Act.

## Links
- [medical-devices-regulation.md](medical-devices-regulation.md)
- [ai-and-the-eu-ai-act.md](ai-and-the-eu-ai-act.md)
- [cybersecurity-of-medical-devices.md](cybersecurity-of-medical-devices.md)
- [health-data-and-medical-implants.md](health-data-and-medical-implants.md)
