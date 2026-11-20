---
title: Safety and the EU Medical Device Regulation
topic: biolaw
authority: notes
written: 2026-11-18
sources:
  - raw/lecture/regulation-eu-2017-745-of-the-european-parliament-and-of-the-council-o-3b0b6e.md
  - raw/lecture/council-directive-93-42-eec-of-14-june-1993-concerning-medical-devices-db939b.md
  - raw/lecture/will-the-eu-medical-device-regulation-help-to-improve-the-safety-and-p-010dbb.md
  - raw/lecture/opportunities-and-risks-of-uk-medical-device-reform-a62035.md
  - raw/lecture/when-is-software-a-medical-device-understanding-and-determining-the-in-0ee708.md
---
# Safety and the EU Medical Device Regulation (MDR)

## Overview
Lectures 2 and 3 of Topic 2 introduce **safety** as a technical and legal concept and then work through the **Medical Device Regulation, Regulation (EU) 2017/745**, which replaced the Medical Device Directive (Council Directive 93/42/EEC). The MDR is product legislation: it controls when a device may be placed on the market, imposes extensive obligations on manufacturers, sets up notified bodies to assess conformity, and gives national authorities strong powers. AI that is, or is part of, a medical device must comply with it (and, if high-risk, with the AI Act on top - see [ai-and-the-eu-ai-act.md](ai-and-the-eu-ai-act.md)).

## The law

### 1. Safety concepts (the materials, drawing on safety engineering, e.g. Leveson, *Safeware* (1995))
- **Safety** = "freedom from accidents or losses". Read literally, an absolute requirement.
- **Accident**: an undesired and unplanned (but not necessarily unexpected) event resulting in at least a specified level of loss. Accidents are **non-adversarial** failures (adversarial failures are security - see [cybersecurity-of-medical-devices.md](cybersecurity-of-medical-devices.md)).
- **Loss**: anything undesirable - physical, financial, reputational damage.
- **Failure**: nonperformance or inability of a system/component to perform its intended function for a specified time under specified conditions.
- **Error**: a design flaw or deviation from a desired or intended state.
- **Hazard**: a state or set of conditions that, together with environmental conditions, will lead inevitably to an accident.
- **Risk** = hazard level plus the likelihood of the hazard leading to an accident, considering exposure/duration.
- Why it matters: compare a scalpel, a surgical robot and AI scanning software - very different hazard profiles.

### 2. From MDD to MDR
- The MDD was a directive (needing national implementation); the MDR is a directly applicable regulation (the materials). Not to be confused with the UK's Medical Devices Regulations 2002 (SI 2002/618), which do not apply in Northern Ireland.
- Structure (similar to the AI Act): Ch I scope and definitions; Ch II making available, obligations, CE marking; Ch III identification and traceability of devices (with the Eudamed database); Ch IV notified bodies; Ch V classification and conformity assessment; Ch VI clinical evaluation and investigations; Ch VII post-market surveillance, vigilance, market surveillance; Ch VIII cooperation; Ch IX confidentiality, data protection; Ch X final provisions.

### 3. Scope and definitions
- **Art 1(1)**: rules on placing on the market, making available or putting into service medical devices for human use and their accessories in the Union; also clinical investigations.
- **Art 2(1) "medical device"**: any instrument, apparatus, appliance, **software**, implant, reagent, material or other article **intended by the manufacturer** to be used, alone or in combination, for human beings for specific medical purposes: diagnosis, prevention, monitoring, **prediction, prognosis**, treatment or alleviation of disease; diagnosis, monitoring, treatment, alleviation of or compensation for injury/disability; investigation, replacement or modification of anatomy or a physiological/pathological process; providing information by in vitro examination of specimens - and which does not achieve its principal intended action by pharmacological, immunological or metabolic means. Devices for control/support of conception and cleaning/disinfection/sterilisation products are deemed devices.
- **Art 2(2) "accessory"**: not itself a device but intended by its manufacturer to be used with a device to enable or directly assist its intended medical functionality. Recital 19 addresses software; "standard" v custom software raises certification problems (e.g. surgical robots).
- **Manufacturer**: a person who manufactures or fully refurbishes a device, or has it designed/manufactured, and markets it under its own name or trademark.
- **Adverse event**: any untoward medical occurrence, unintended disease or injury, or untoward clinical sign in subjects, users or others in a clinical investigation.
- **SNITEM**, Case C-329/16 (CJEU) - on whether software is a medical device (see [software-and-ai-as-medical-devices.md](software-and-ai-as-medical-devices.md)).

### 4. Intention (the materials)
- Arts 2(1), 5(1) and 5(2): a device may be placed on the market only if it complies when properly used for its **intended purpose**, and it must meet the Annex I general safety and performance requirements (GSPRs) applicable to that purpose; conformity includes clinical evaluation (art 5(3), art 61). Intention is assessed from public sources and applications.
- If the manufacturer does not intend the product to be a medical device, the first criterion is not met - a grey area. Ludvigsen suggests distinguishing **direct and indirect intention**, to prevent circumvention and capture *de facto* medical devices; general authority powers may help.
- Art 5(4)-(5): devices made and used within health institutions count as put into service; an in-house exemption applies (only Annex I GSPRs) if conditions are met (not transferred to another entity, appropriate QMS, justification that no equivalent device exists, etc.).

### 5. Manufacturer obligations - art 10
- Risk management system (art 10(2)).
- Quality management system (art 10(9)): keep series production in conformity; take account of design changes and changes in standards; establish, document, implement, maintain, update and continually improve a QMS proportionate to risk class.
- **Sole responsibility** (art 10(1), (12), (13), (14)). Art 10(14): if the manufacturer fails to cooperate or gives incomplete or incorrect information, the competent authority may prohibit or restrict availability, withdraw or recall the device until it cooperates.
- **Financial responsibility** (art 10(16)): persons may claim compensation for damage caused by a defective device under Union and national law; manufacturers must have sufficient financial coverage proportionate to risk class, device type and enterprise size for liability under the **Product Liability Directive 85/374/EEC**.
- Post-market surveillance system (art 83), integral to the QMS; serious incident and field safety corrective action reporting (art 87).

### 6. Annex I - general safety and performance requirements (hard requirements)
- **Ch I(1)**: devices must achieve the intended performance, be suitable for intended purpose, be safe and effective, and not compromise patients' or users' safety - any risks must be acceptable when weighed against benefits, compatible with a high level of protection, "taking into account the generally acknowledged state of the art".
- **Ch I(4)**: risk control must follow safety principles in an order of priority: (a) eliminate or reduce risks as far as possible through safe design and manufacture; (b) adequate protection measures, including alarms; (c) information for safety and training. Residual risk must be acceptable and users informed of it.
- **Ch I(5)**: reduce use-error risks (ergonomics, use environment) and consider users' knowledge, training and conditions (lay, professional, disabled users).
- **Section 17** (electronic programmable systems and software): repeatability, reliability and performance; single-fault conditions; software developed according to the state of the art considering development life cycle, risk management **including information security**, verification and validation (17.2); mobile platforms (17.3); minimum hardware, IT network and IT security requirements including protection against unauthorised access (17.4).

### 7. Classification and conformity assessment
- **Art 51**: classes I, IIa, IIb, III by intended purpose and inherent risk, per Annex VIII; disputes with notified bodies go to the competent authority.
- **Annex VIII Rule 11 (software)**: software providing information used for diagnostic or therapeutic decisions is class IIa, but class III if decisions may cause death or irreversible deterioration, and class IIb if they may cause serious deterioration or surgical intervention; software monitoring physiological processes is IIa (IIb for vital parameters where variations could cause immediate danger); all other software is class I.
- **Art 52**: conformity assessment procedures; class I generally self-assessed, higher classes need a notified body.

### 8. Notified bodies and authorities (the materials)
- Process: design and application; testing by notified bodies; notified body approval; authority approval; market infrastructure; continuous quality and risk management; end-of-life measures. Authorities have full power at any stage.
- **Notified bodies** (Ch IV): art 36 basic requirements; art 39 management; art 42 notification. Can be private or public - do they have too much freedom?
- **Authorities**: request documents and act on non-cooperation (art 10(14)); market surveillance (art 93); evaluation of devices suspected of unacceptable risk (art 94); procedure for devices presenting unacceptable risk (art 95); other non-compliance (art 97).

### 9. UK position
- UK law does not fully apply to medical devices because of Northern Ireland; teaching focuses on EU law (handout).
- Post-Brexit, the UKCA mark (UKNI in Northern Ireland) replaces CE marking in Great Britain; CE recognition was to continue until 30 June 2023 per the reading. Opportunities: independent framework, innovation and investment; risks: delays from a shortage of approved bodies, reduced competitiveness. Recommendations: cross-sector collaboration, patient and public partnership, international engagement ("Opportunities and Risks of UK Medical Device Reform").

## Key authorities
- Regulation (EU) 2017/745 (MDR): arts 1, 2(1), 2(2), 5, 10, 51, 52, 61, 83, 87, 93-97; Annex I (Ch I(1), (4), (5); s 17); Annex VIII Rule 11.
- Council Directive 93/42/EEC (MDD) - predecessor.
- Directive 85/374/EEC (Product Liability) - via art 10(16).
- *SNITEM*, C-329/16.

## Debate and critique
- **Niemiec, "Will the EU Medical Device Regulation help to improve the safety and performance of medical AI devices?"**: evidence on medical AI is weak - lack of external validation (same dataset for training and validation), few randomised or multi-site trials, mostly retrospective studies, heterogeneous metrics, unavailable datasets/code - so claimed performance may be overstated. The MDR helps: Rule 11 will move most AI devices to IIa/IIb, requiring notified body assessment; clinical evaluation is required for all classes with higher standards and more emphasis on post-market evidence (incorporating MEDDEV 2.7/1 rev 4; MDCG guidance on software); stronger post-market surveillance; requirements for notified-body expertise. But impact depends on enforcement by Member States.
- **Is product regulation the right model?** (reflection) Safety, defined absolutely, cannot be achieved; the MDR instead requires acceptable residual risk against the "state of the art", which moves quickly for AI. Are manufacturers' and distributors' responsibilities enough given the consequences of failure?
- **Intention as gatekeeper**: manufacturers may avoid the regime by not claiming a medical purpose (wellness framing) - Ludvigsen's direct/indirect intention proposal; compare the "enhancement not treatment" argument in the neurotech seminar scenario ([mental-privacy-and-neural-data.md](mental-privacy-and-neural-data.md)).
- **Accessories and standard software** - when should they meet device-level requirements?
- **Liability**: art 10(16) relies on the old Product Liability Directive, which fits software and adaptive AI poorly; UK liability rests on tort plus the old PLD implementation.
- **Authority capacity**: are powers enough for widespread AI? Notified body shortages (also a UK risk).

## Applying it to a problem question
1. **Is it a medical device?** Art 2(1): intended medical purpose (from labelling, instructions, promotional material); not principally pharmacological. Or an accessory (art 2(2))?
2. **Who is the manufacturer?** Including hospitals making in-house devices (art 5(5)).
3. **Class** under Annex VIII (Rule 11 for software) and therefore conformity route (self-assessment v notified body); this also triggers AI Act high-risk status.
4. **GSPRs**: what hazards exist? Has the manufacturer followed the Annex I(4) priority order? Is software built to state of the art including information security (s 17)?
5. **Post-market**: surveillance, incident reporting, corrective action.
6. **Enforcement**: authority powers (arts 10(14), 93-97) - withdrawal, recall.
7. **Remedies for patients**: compensation via product liability (art 10(16)), tort; manufacturer's insurance.
Seminar device examples: AI surgical robot (hazards from autonomy, use error), image-based diagnosis tool (Rule 11 class depends on consequences of wrong decisions), AI pacemaker (vital parameters; implant - see [health-data-and-medical-implants.md](health-data-and-medical-implants.md)).

## Links
- [ai-and-the-eu-ai-act.md](ai-and-the-eu-ai-act.md)
- [software-and-ai-as-medical-devices.md](software-and-ai-as-medical-devices.md)
- [cybersecurity-of-medical-devices.md](cybersecurity-of-medical-devices.md)
- [health-data-and-medical-implants.md](health-data-and-medical-implants.md)
