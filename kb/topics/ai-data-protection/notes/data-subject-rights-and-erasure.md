---
title: Data Subject Rights, Erasure and the Right to be Forgotten in AI Systems
topic: ai-data-protection
authority: notes
written: 2026-11-18
---
# Data Subject Rights, Erasure and the Right to be Forgotten in AI Systems

## Overview
The GDPR gives individuals rights of access, rectification, erasure, restriction, portability and objection (arts 12-22). They are the main tool by which a person can reach into an AI pipeline: to see what is held, to stop use, or to demand deletion. The difficulty is practical and conceptual: data may be copied across massive training sets, embedded as statistical parameters in a model, and held by companies the individual has never heard of. *Google Spain* created the "right to be forgotten" for search engines; the CNIL's *Clearview AI* decision shows erasure and access rights enforced against a scraping-based facial-recognition company; the EDPB opinion on AI models addresses how rights should work around models; the FTC's *Everalbum* order is a US example in which deletion extended to the models themselves.

## The law

### 1. Rights in outline (GDPR Chapter III)
- **Art 12:** the controller must facilitate the exercise of rights under arts 15-22 (the CNIL in *Clearview* quoted it).
- **Art 15 access:** confirmation of processing and access to the data, plus information on purposes, categories, recipients (particularly in third countries), storage period or criteria, the existence of rights to rectification, erasure, restriction or objection, the right to complain, and the existence of automated decision-making (art 15(1)(h)).
- **Art 17 erasure:** the controller must erase without undue delay where (a) data are no longer necessary for the purposes; (b) consent is withdrawn and there is no other ground; (c) the person objects under art 21(1) and there are no overriding legitimate grounds, or under art 21(2) (direct marketing); (d) data were unlawfully processed; (e) erasure is required by law; (f) data were collected in relation to information society services offered to a child (art 8(1)).
- **Art 17(2):** where the controller has made data public and must erase, it must take reasonable steps (having regard to technology and cost), including technical measures, to inform other controllers processing the data that the person has requested erasure of links, copies or replications.
- **Art 17(3) exceptions:** freedom of expression and information; legal obligation or public-interest task; public health; archiving, scientific or historical research or statistics where erasure would render impossible or seriously impair the objectives; establishment, exercise or defence of legal claims.
- **Art 21 objection:** a person may object, on grounds relating to their particular situation, to processing based on art 6(1)(e) or (f), including profiling; the controller must stop unless it shows compelling legitimate grounds overriding the person's interests or needs the data for legal claims. There is an absolute right to object to direct marketing (art 21(2)-(3)).
- Other rights in the GDPR text include rectification, restriction (art 18) and portability (art 20); art 22 on automated decisions is covered in a separate note.

### 2. *Google Spain* (CJEU, C-131/12, 2014)
Facts: Mr Costeja González complained to the Spanish authority (AEPD) that searching his name on Google returned links to 1998 pages of the newspaper *La Vanguardia* announcing a real-estate auction connected with attachment proceedings for social security debts, which had long been resolved. He asked for the newspaper to alter or remove the pages and for Google to remove or conceal the links. The AEPD rejected the complaint against the newspaper (publication was legally justified) but upheld it against Google.

The Grand Chamber ruled (under Directive 95/46, the GDPR's predecessor):
1. A search engine's activity of finding, automatically indexing, temporarily storing and making available information published by third parties is "processing of personal data" and the operator is a "controller" of it.
2. Processing is carried out "in the context of the activities of an establishment" in a Member State where the operator sets up a branch or subsidiary there to promote and sell advertising space, orientated toward that State's inhabitants.
3. To comply with the rights to rectification/erasure and objection (arts 12(b), 14(a)), the operator must remove from the list of results for a name search links to pages published by third parties, even where the name or information is not erased beforehand or simultaneously from those pages and even where their publication is itself lawful.
4. The assessment turns on whether the person has a right that the information should no longer be linked to their name by a results list, without needing to show prejudice. The person's Charter rights (arts 7 and 8) override, as a rule, both the operator's economic interest and the public's interest in access, *unless* there are particular reasons, such as the role played by the data subject in public life, making the interference justified by the preponderant interest of the public in access.

### 3. *Clearview AI* (CNIL Restricted Committee, SAN-2022-019, 17 October 2022)
- **Facts:** Clearview, a US company, collected over 20 billion facial images from public web pages and social networks (including from adults and minors with no filter), computed biometric templates, and sold a face-search tool, marketed to law enforcement. After complaints (including from Privacy International), the CNIL issued an order in November 2021 to comply with arts 6, 12, 15 and 17; the company did not respond.
- **Applicability:** the GDPR applied under art 3(2)(b) (monitoring of behaviour of people in the Union), since the processing was "related to" monitoring; the CNIL held that Clearview was the controller.
- **Findings:** no lawful basis under art 6 (no consent; legitimate interests failed because the processing was highly intrusive and people could not reasonably expect their photographs to feed a facial-recognition database sold to third parties); breach of the right of access (the complainant was effectively obstructed, for example by demands for a photograph and ID, and a four-month delay on one request); breach of art 17 because the processing had no lawful basis, so erasure was "legally binding" and the company failed to respond; failure to cooperate with the CNIL.
- **Sanction:** administrative fine of EUR 20 million; an injunction to stop collecting and processing data of individuals on French territory without a legal basis and to delete such data (after answering pending access requests), with a periodic penalty of EUR 100,000 per day after two months; publication of the decision.

### 4. EDPB opinion on AI models (December 2024)
- Where a model is not anonymous, data subjects keep their rights over the model's processing. The EDPB recommends, as *mitigating measures* in legitimate-interests balancing, a reasonable delay between data collection and training so rights can be used, an unconditional opt-out, allowing erasure even where art 17 grounds do not strictly apply, and a procedure for people to submit claims of **regurgitation or memorisation** so that controllers can reproduce the problem and assess "unlearning" techniques.
- Where legitimate interests is the basis, the art 21 right to object applies and it must be possible to exercise it.
- Reliance on the art 14(5)(b) exception to the duty to inform (where data was not obtained from the person) is strictly limited when data is scraped at scale.

### 5. US comparison: *FTC v Everalbum* (2021)
The FTC consent order against Everalbum (Ever app; later Paravision) required deletion within set periods of photos and videos of users who had deactivated accounts, of "Face Embeddings" derived from users who had not given express affirmative consent, and of any "Affected Work Product", defined as models or algorithms developed in whole or in part using biometric information collected from users of the Ever app. The files contain the order, not the complaint's reasoning, so it is evidence of the remedy (deletion reaching the trained models) and not of the legal theory.

## Key authorities
- GDPR arts 12, 15, 17, 18, 20, 21 (and 22).
- *Google Spain SL v AEPD and Costeja González* (CJEU, C-131/12, 2014).
- CNIL, *Clearview AI*, SAN-2022-019 (2022): EUR 20m fine, deletion injunction.
- EDPB Opinion on AI models (Dec 2024), paras 63 and 65 and the mitigating measures.
- FTC, *In the Matter of Everalbum, Inc.*, Docket C-4743 (2021): deletion of data and derived models.

## Debate and critique
- **Erasure and models.** Deleting a row from a database is simple; removing the influence of one person's data from trained parameters is not. The EDPB treats "unlearning" as something controllers should be willing to assess, not as a settled technique. The *Everalbum* order shows a regulator accepting the blunt remedy of deleting the model.
- **Anonymity as an escape.** If a model is anonymous, the GDPR (and so the rights) do not apply to it; the EDPB therefore insists anonymity be demonstrated, not assumed (see the scraping note).
- **Exercising rights against hidden controllers.** In *Clearview* most people did not know the database existed. The CNIL justified publicity of the decision on that ground: people cannot exercise rights they do not know they have. This echoes the overview note's "individual control" critique.
- **Balancing with expression and public interest.** *Google Spain* tied delisting to a case-by-case balance that depends on the person's public role and the age and relevance of the data; this approach is relevant when generative models repeat old or false information about a person.
- **Territorial effectiveness.** Clearview was not in the EU and did not appear; enforcement against foreign controllers depends on practical leverage (fines, injunctions, publicity). *Google Spain* reached a non-EU parent through the EU establishment.

## Applying it to a problem question
1. Who is the controller (the search engine, scraper, model developer, deployer)? Is the GDPR applicable (establishment, or art 3(2) targeting or monitoring)?
2. Which right is invoked (access, erasure, objection)? Was a response given without undue delay, and did the controller facilitate (art 12) or obstruct (excessive ID demands, forms)?
3. For erasure, run through art 17(1) grounds. Unlawful processing (d) is often the cleanest ground (compare *Clearview*). Then test the art 17(3) exceptions, especially expression and research.
4. Search or generative outputs about a named person: apply *Google Spain* balancing (role in public life, time elapsed, nature of information).
5. Is the data inside a model? Consider whether the model is anonymous; if not, discuss feasibility of unlearning, regurgitation claims, and the EDPB's recommended measures.
6. Where legitimate interests is the basis, check whether the art 21 objection was honoured.
7. Remedies: complaint to the authority, orders to delete, fines (art 83), and, in the US analogue, FTC deletion of models.

## Links
- gdpr-framework-for-ai
- gdpr-lawful-bases-and-consent
- automated-decision-making-and-right-to-explanation
- web-scraping-and-ai-training-data
- ai-and-privacy-overview
- international-transfers-schrems-ii

## Common errors to avoid

- Art 12(3) GDPR: the one-month deadline is not extendable 'only in complex cases'; it may be extended by two further months where necessary, considering the complexity and number of requests, and the data subject must be told, with reasons, within the first month. [2026-11-24 · ref 2026-11-22-1301/q01#2]
