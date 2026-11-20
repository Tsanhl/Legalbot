---
title: GDPR Lawful Bases, Consent and Legitimate Interests in AI
topic: ai-data-protection
authority: notes
written: 2026-11-18
sources:
  - raw/secondary/gdpr-bd84e6.md
  - raw/secondary/planet49-cjeu-c-673-17-2019-f60bbc.md
  - raw/secondary/edpb-opinion-on-ai-models-december-2024-addcaf.md
  - raw/secondary/clearview-ai-cnil-2022-ffd6d7.md
  - raw/secondary/the-great-scrape-the-clash-between-scraping-and-privacy-f3e2b4.md
---
# GDPR Lawful Bases, Consent and Legitimate Interests in AI

## Overview
Every processing operation involving personal data under the GDPR needs a lawful basis from art 6(1). AI is awkward for this requirement because it spans many stages (collecting training data, training, deployment, further use) and because data is often gathered at huge scale from people the developer has no relationship with. In practice the debate narrows to two bases: consent (art 6(1)(a), art 7) and legitimate interests (art 6(1)(f)). Planet49 shows how demanding the CJEU is about consent; the EDPB's December 2024 opinion and the CNIL's Clearview decision show how legitimate interests is tested for AI models. This is EU law (GDPR, with the ePrivacy Directive 2002/58 in Planet49).

## The law

### 1. The six bases (art 6(1) GDPR)
Processing is lawful only if at least one applies:
- (a) the data subject has consented "for one or more specific purposes";
- (b) necessary for a contract with the data subject (or pre-contractual steps at their request);
- (c) necessary to comply with a legal obligation;
- (d) necessary to protect vital interests;
- (e) necessary for a task in the public interest or in the exercise of official authority;
- (f) necessary for the legitimate interests of the controller or a third party, unless overridden by the interests or fundamental rights and freedoms of the data subject, "in particular where the data subject is a child". Point (f) does not apply to public authorities performing their tasks.

The EDPB opinion repeats that the GDPR sets no hierarchy among the bases; it is for the controller to identify the appropriate one for each processing activity (para 60). Different stages of AI development and deployment may be separate processing activities needing their own basis (para 63).

### 2. Further processing for a new purpose (art 6(4))
Where a new purpose is not based on consent or a qualifying legal provision, the controller must test compatibility with the original purpose, looking at: the link between purposes; the context of collection (especially the relationship between controller and data subject); the nature of the data (special categories or criminal data); possible consequences for data subjects; and safeguards such as encryption or pseudonymisation. This matters for models trained on data originally collected for something else.

### 3. Conditions for valid consent (arts 4(11), 7, 8)
- The controller must be able to demonstrate consent (art 7(1)).
- If given in a written declaration covering other matters, the request must be clearly distinguishable, intelligible and in plain language (art 7(2)).
- Consent can be withdrawn at any time; withdrawal does not make earlier processing unlawful; it must be as easy to withdraw as to give (art 7(3)); the person must be told of this before consenting.
- When assessing whether consent is freely given, "utmost account" is taken of whether performance of a contract or provision of a service is made conditional on consent to processing not necessary for that contract (art 7(4)).
- For information society services offered directly to a child, processing on consent is lawful where the child is at least 16; below that, parental authorisation is needed. Member States may lower the age but not below 13 (art 8).

### 4. Planet49: active, informed, specific consent
*Planet49* (CJEU, Grand Chamber, C-673/17, 2019): a German consumer federation challenged an online lottery operator whose registration page contained a pre-ticked checkbox consenting to cookies that tracked users' browsing for advertising by sponsors and partners. The Bundesgerichtshof referred questions under Directive 2002/58 (art 2(f), art 5(3)), read with Directive 95/46 art 2(h) and GDPR arts 4(11) and 6(1)(a). The Court held:
1. Consent is not validly constituted where storage of, or access to, information on a user's terminal equipment is permitted by a pre-checked checkbox which the user must deselect to refuse. The Court reasoned that an "indication" of wishes requires active behaviour, and that it is practically impossible to establish objectively that a user who simply did not untick a box had actually consented and had been informed. It added that the GDPR makes active consent explicit, so the result holds *a fortiori* under the GDPR.
2. The answer does not differ depending on whether the information stored or accessed is personal data.
3. The "clear and comprehensive information" the service provider must give includes the duration of the cookies' operation and whether third parties may have access to them (the Court linked this to GDPR art 13(1)(e) and art 13(2)(a) on recipients and storage period).

### 5. Legitimate interests: the three-step test
The EDPB opinion (paras 66-76), drawing on EDPB Guidelines 1/2024 and CJEU case law it cites (including *Meta v Bundeskartellamt*, C-252/21), requires controllers to assess and document, ideally at the outset and with the DPO involved:
1. **Legitimate interest.** The interest must be (a) lawful, (b) clearly and precisely articulated, and (c) real and present, not speculative. Examples the EDPB gives for AI: developing a conversational agent to assist users; developing a system to detect fraudulent content or behaviour; improving threat detection in an information system. An interest contrary to law (for example a prohibited AI practice under AI Act art 5, or processing infringing copyright rules) cannot qualify.
2. **Necessity.** Does the processing allow the interest to be pursued, and is there no less intrusive way? If the aim can be achieved with a model that does not process personal data, processing personal data is not necessary. Volume of data matters, in light of data minimisation. Technical safeguards (such as pseudonymisation) can help meet this step. The analysis differs for first-party data (existing relationship) and third-party data.
3. **Balancing.** The controller's interest is weighed against data subjects' interests, rights and freedoms. In development these include self-determination and control over data; in deployment, financial, personal and socio-economic interests. The EDPB flags risks to Charter rights (private life, data protection, and others), the nature of the data, the context and consequences of the processing, and above all **reasonable expectations**: whether the data was public, the relationship, the source website and its privacy settings, the potential later uses of the model, and whether people even know their data is online.
4. **Mitigating measures** may tip the balance. They must go beyond what the GDPR already requires. Development-phase examples include pseudonymisation, masking or substituting personal data in training sets, leaving a reasonable gap between collection and training so people can exercise rights, an unconditional opt-out, allowing erasure even where art 17 grounds are not met, and transparency measures beyond arts 13-14. Specific web-scraping measures are discussed in the note on scraping.
- Whenever legitimate interests is relied on, the art 21 right to object applies and must be capable of being exercised.

### 6. Special categories
Art 9 prohibits processing of special categories (and the Great Scrape authors note that inferences from ordinary data can themselves be sensitive, so that "nearly all personal data could be sensitive data"). Legitimate interests cannot by itself justify special-category processing; an art 9(2) condition is also needed. Art 9(2)(e) (data manifestly made public by the data subject) is only an exception to the art 9 prohibition and is not a general licence for public data.

## Key authorities
- *Planet49* (CJEU, C-673/17, 2019): pre-ticked box is not valid consent; information must include cookie duration and third-party access; same rule whether or not data is personal.
- GDPR art 6(1), 6(4), art 7, art 8, art 9, art 21.
- EDPB Opinion on AI models (December 2024): no hierarchy of bases; three-step legitimate interests test applied to AI development and deployment; reasonable expectations; mitigating measures.
- CNIL, *Clearview AI* (Restricted Committee deliberation SAN-2022-019, 17 Oct 2022): scraped images and biometric templates; no consent, and legitimate interests failed on the balancing step (people posting photos do not expect them to feed facial recognition sold to third parties, and the processing is highly intrusive); no lawful basis, breach of art 6; fine of EUR 20 million.
- *Meta v Bundeskartellamt* (C-252/21), cited in the EDPB opinion for the three cumulative conditions of art 6(1)(f).

## Debate and critique
- **"Publicly available" is not a lawful basis.** The CNIL in *Clearview* stressed that public availability is no general authorisation to reuse personal data, quoting the Article 29 Working Party that data made public still needs appropriate safeguards. Solove and Hartzog (*The Great Scrape*) agree: the GDPR has no general exception for publicly available data and they call "publicly available information" an incoherent concept.
- **Consent is impracticable at scale.** Solove and Hartzog note that consent from every person whose data is scraped is practically impossible, so legitimate interests is the base that "most seemingly fits", but it is unreliable: purposes for general-purpose AI can be too unspecified; the balancing outcome is uncertain; and it cannot cover sensitive data. They also describe the Italian DPA's 2023 ban and reinstatement of ChatGPT (reinstated subject to removal mechanisms and age verification, with OpenAI to rely on consent or legitimate interests), and the Dutch authority's guide saying scraping will almost always breach the GDPR. These are the authors' accounts, and are useful as commentary rather than as primary law.
- **Flexibility versus certainty.** The EDPB opinion is deliberately non-prescriptive and case-by-case; critics (as the Great Scrape does) see this as leaving developers with little certainty and leaving individuals with the burden of objecting. Supporters say it fits the diversity of AI models.
- **Consent fatigue and design.** Planet49 forces genuine choice, but the wider literature in the files questions how meaningful consent is when AI uses are opaque (see the overview note on individual control).

## Applying it to a problem question
1. Identify each processing stage (collection, training, fine-tuning, deployment, further use) and the controller at each. Treat them separately.
2. Is the data personal and is any of it special-category or biometric? If yes, art 9 as well as art 6.
3. Which basis is claimed? If consent: was it active (no pre-ticked boxes), specific, informed (purpose, recipients, duration), demonstrable, easy to withdraw, and not bundled (art 7(4))? Is a child involved (art 8)?
4. If legitimate interests: run the three steps in order; state the interest precisely; ask whether less intrusive means (synthetic or anonymised data, less data) exist; weigh reasonable expectations and risks; list mitigating measures that go beyond mere compliance; confirm the right to object can be exercised.
5. Check art 6(4) if data was reused for a new purpose.
6. Traps: relying on "it was public"; treating a privacy-policy notice as consent; forgetting that consent can be withdrawn and that art 17 may then follow; assuming one basis covers every stage.
7. Remedies and consequences: consider art 17 erasure, the art 83 fine ceiling (see the framework note), and the EDPB's scenarios on what unlawful development means for later deployment (see the scraping note).

## Links
- gdpr-framework-for-ai
- ai-and-privacy-overview
- automated-decision-making-and-right-to-explanation
- data-subject-rights-and-erasure
- web-scraping-and-ai-training-data
- eu-ai-act
