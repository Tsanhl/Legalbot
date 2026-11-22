---
title: Web Scraping, Training Data and the Status of AI Models (EDPB Opinion, Great Scrape, Getty, Everalbum)
topic: ai-data-protection
authority: notes
written: 2026-11-18
---
# Web Scraping, Training Data and the Status of AI Models

## Overview
Modern AI models, especially generative models and facial recognition, are trained on vast datasets harvested from the web by automated "scraping". Scraped data often contains personal data, collected without the knowledge of the people concerned. The issues are: whether scraping can have a lawful basis; whether the trained model itself contains personal data (so that the GDPR keeps applying to it); and what follows for later users of a model if it was trained unlawfully. The December 2024 EDPB opinion (requested by the Irish authority under art 64(2) GDPR) is the central EU document; Solove and Hartzog's *The Great Scrape* supplies the critical theory; *Clearview*, *Getty v Stability AI* and *Everalbum* are the enforcement and litigation examples.

## The law

### 1. The four EDPB questions
The Irish supervisory authority asked: (1) when and how can an AI model be considered anonymous? (2) and (3) how can controllers show legitimate interests is an appropriate basis in the development and deployment phases? (4) what are the consequences of unlawful processing in development for later processing or operation of the model? The opinion is a set of general considerations for supervisory authorities (SAs), to be applied case by case; it is not a binding adjudication of any particular model.

### 2. Is a model anonymous? (paras 36-43 and the summary)
- Personal data is any information relating to an identified or identifiable person (art 4(1)); information may relate to a person even when encoded so that the link is not obvious. AI models store parameters representing statistical relationships rather than records, but personal data may still be extractable or inferable (for example via membership inference or regurgitation).
- The EDPB's conclusion: AI models trained on personal data **cannot in all cases be considered anonymous**; claims of anonymity are to be assessed case by case by SAs.
- For anonymity, using "all the means reasonably likely to be used" (Recital 26 GDPR), both (i) the likelihood of direct, including probabilistic, extraction of personal data about training-data subjects and (ii) the likelihood of obtaining such data, intentionally or not, from queries must be **insignificant** for any data subject.
- Relevant factors: characteristics of the training data, the model and the training procedure; the context of release; additional information available to a person; cost and time needed to identify; available technology and its development. Consider both the controller and other persons, including unintended third parties.
- By default SAs should expect to need a thorough evaluation of identification risk. The opinion lists non-prescriptive methods a controller may use to demonstrate anonymity, including limiting or preventing collection of personal data for training, reducing identifiability, preventing extraction, and showing state-of-the-art resistance to attacks.

### 3. Legitimate interests for development and deployment
The three-step test (legitimate interest, necessity, balancing) and mitigating measures are set out in the lawful bases note. Points specific to scraping:
- Reasonable expectations are central; relevant context includes whether data was public, what privacy settings the source site offered, and whether people know their data is online at all.
- The art 14(5)(b) exception to the duty to inform is strictly limited.
- **Specific scraping mitigations** the EDPB lists (para 104-106): excluding content likely to expose people to abuse, prejudice or physical harm; not collecting certain categories of data or from certain sources (for example particularly sensitive sites); excluding sites or sections that clearly object to scraping for AI training (for example by respecting robots.txt or ai.txt files); other limits on collection such as time periods; and measures facilitating individuals' rights and transparency, such as a controller-managed opt-out list. The opinion records that scraping raises additional issues (for example ethics and other laws) that it does not cover.
- Unlawful uses cannot ground a legitimate interest: the opinion's examples include processing that breaches AI Act art 5, DSA rules on targeted advertising to minors, or copyright rules (Directive 2019/790).

### 4. Consequences of unlawful development: three scenarios (paras 109 onwards)
SAs retain discretionary corrective powers, to be exercised in a way that is appropriate, necessary and proportionate. The EDPB addresses only lawfulness under arts 5(1)(a) and 6.
1. **Personal data retained in the model, processed later by the same controller.** Whether development and deployment are separate purposes (separate processing activities) and how far a missing legal basis for development taints deployment is case-specific.
2. **Personal data retained, deployed by a different controller.** The deployer's accountability obligations require an appropriate assessment that the model was not developed by unlawfully processing personal data: consider the source of the data and whether an infringement was found by an SA or court. The depth of assessment scales with the risk of the deployment.
3. **Unlawful development, then genuine anonymisation, then deployment.** If it can be shown that the later operation of the model involves no personal data processing, the GDPR does not apply to it and the earlier unlawfulness should not affect later operation. Personal data collected during deployment is still subject to the GDPR and its lawfulness is assessed separately.

### 5. *Clearview AI* (CNIL, 2022)
A commercial scraper built a searchable database of over 20 billion facial images and biometric templates. The CNIL found no valid lawful basis (legitimate interests failed because the processing was highly intrusive and individuals could not reasonably expect their publicly posted images to be used this way), breaches of access and erasure rights, and imposed a EUR 20m fine, a deletion injunction and a periodic penalty. The AI Act's prohibition on creating or expanding facial recognition databases through untargeted scraping (art 5(1)(e)) addresses the same activity.

### 6. *Getty Images v Stability AI* [2025] EWHC 38 (Ch)
This is the High Court (Chancery Division, Joanna Smith J, 14 January 2025), a case-management judgment in ongoing proceedings. Getty alleges Stability AI scraped millions of images from Getty's websites without consent to train Stable Diffusion and that outputs infringe copyright and trade marks (claims: copyright, database right, trade mark infringement and passing off). The three copyright claims were: the training and development claim (downloads on UK servers or computers), secondary infringement by importing the pre-trained model as an "article", and the output claim (text prompts, image prompts, and combined). Stability admitted that at least some Getty images were used in training. The judgment decided only that the Sixth Claimant (Thomas M Barwick Inc) could not act as a representative of a class (CPR r 19.8(2) and r 19.3); it did not decide infringement. Use it to illustrate that scraped training data raises IP as well as data protection claims, and that English litigation is at an early stage; do not cite it as authority on the merits.

### 7. *FTC v Everalbum* (2021)
The FTC's consent order required deletion of photos and videos of users who had deactivated, face embeddings of users who had not given express affirmative consent, and models or algorithms developed with biometric information collected through the Ever app. It illustrates a remedy that follows the data into the model (sometimes called "algorithmic disgorgement"; that label is not used in the order itself).

## Key authorities
- EDPB Opinion on certain data protection aspects related to the processing of personal data in the context of AI models (Dec 2024), including paras 36-43 (anonymity), 60-76 (legitimate interests), 99-106 (mitigating measures, scraping) and 109 ff. (unlawful development).
- GDPR arts 4(1), 5(1)(a), 5(2), 6, 14(5)(b), 21; Recital 26.
- Solove and Hartzog, *The Great Scrape: The Clash Between Scraping and Privacy*.
- CNIL, *Clearview AI*, SAN-2022-019.
- *Getty Images (US) Inc v Stability AI Ltd* [2025] EWHC 38 (Ch) (representative claim application only).
- FTC, *In the Matter of Everalbum, Inc.*, Docket C-4743 (2021).
- AI Act art 5(1)(e).

## Debate and critique
- **Scraping versus every core principle.** Solove and Hartzog argue scraping violates nearly all key privacy principles: fairness, individual rights and control, transparency, consent, purpose specification and secondary-use limits, data minimisation, onward transfer rules and data security. Their central point is that data being publicly available does not exempt it; privacy law regularly protects public data and "publicly available information" is an incoherent concept.
- **Tension but no easy fix.** They argue reconciliation is not simply applying existing privacy law: consent regimes risk end-runs around meaningful control, while strict regimes could make scraping practically impossible, which is also undesirable. They propose treating scraping as a form of surveillance and a data-security problem, and asking whether it serves the **public interest**.
- **Regulator behaviour.** They describe the Italian authority's ChatGPT ban and rapid reinstatement as a weak enforcement signal, and the Dutch authority's view that scraping almost always breaches the GDPR as a sign of a coming showdown. Treat these as the authors' characterisation.
- **EDPB flexibility.** The EDPB opinion recognises benefits of AI and frames the GDPR as enabling "responsible innovation", but its case-by-case approach and its acceptance of the anonymised-model route (scenario 3) may be criticised as a loophole: a developer could process unlawfully, then claim anonymity. The EDPB's answer is that anonymity must be demonstrated to a high standard.
- **Anonymity and probabilistic extraction.** Whether a large language model can ever meet the "insignificant likelihood" standard is contested technically; the opinion treats this as a matter of evidence from the controller.
- **Cross-regime gaps.** *Getty* and *Everalbum* show that copyright and consumer-protection regimes also bite on training data, yet they remedy different harms from privacy law.

## Applying it to a problem question
1. Identify the data collected and how (scraping from which sources; any terms or opt-out signals ignored?). Is any of it special-category or biometric?
2. Lawful basis for the collection and training stage: consent is impracticable; apply the legitimate-interests three-step test and the scraping-specific mitigations; discuss reasonable expectations and the right to object.
3. Transparency: was art 14 information given, or is art 14(5)(b) properly engaged?
4. Is the trained model anonymous? Ask about extraction, regurgitation and membership inference, the "means reasonably likely" test, and what evidence the developer can produce.
5. If a third party deploys the model, apply the EDPB scenario 2 accountability assessment. If the developer claims anonymisation after unlawful training, apply scenario 3.
6. Check for AI Act issues (art 5(1)(e) if a facial recognition database; GPAI training-content summary) and for IP and consumer-protection exposure (the *Getty* and *Everalbum* types).
7. Remedies: SA corrective powers, deletion of data or models, fines.

## Links
- ai-and-privacy-overview
- gdpr-framework-for-ai
- gdpr-lawful-bases-and-consent
- data-subject-rights-and-erasure
- eu-ai-act
- international-transfers-schrems-ii
