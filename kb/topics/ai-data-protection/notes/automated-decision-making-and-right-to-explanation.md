---
title: Automated Decision-Making (Art 22 GDPR) and the "Right to Explanation"
topic: ai-data-protection
authority: notes
written: 2026-11-18
---
# Automated Decision-Making (Art 22 GDPR) and the "Right to Explanation"

## Overview
When an algorithm decides who gets a loan, a job interview or a benefit, people want to know why. Early commentary claimed the GDPR created a "right to explanation" of individual automated decisions. Wachter, Mittelstadt and Floridi (2017) 7 International Data Privacy Law 76 argued that no such binding right exists in the GDPR; at most there is a more limited "right to be informed" about how the system works. The EU AI Act (art 86) later added a narrower, separate explanation right. This is EU law; the academic argument is about the GDPR as it stood when adopted (the paper predates its application in 2018).

## The law

### 1. Article 22 GDPR
- **Art 22(1):** the data subject has the right not to be subject to "a decision based solely on automated processing, including profiling, which produces legal effects concerning him or her or similarly significantly affects him or her".
- **Art 22(2):** paragraph 1 does not apply if the decision (a) is necessary for entering into or performing a contract between data subject and controller; (b) is authorised by Union or Member State law which lays down suitable safeguards; or (c) is based on explicit consent.
- **Art 22(3):** in cases (a) and (c), the controller must implement suitable measures to safeguard rights, freedoms and legitimate interests, "at least the right to obtain human intervention on the part of the controller, to express his or her point of view and to contest the decision".
- **Art 22(4):** decisions under para 2 must not be based on special-category data (art 9(1)) unless art 9(2)(a) or (g) applies and suitable safeguards exist.
- Elements to analyse: (i) a *decision*; (ii) *solely* automated; (iii) *legal or similarly significant effect*. If any is missing, art 22 does not apply.

### 2. Information duties and access
- Arts 13(2)(f) and 14(2)(g) (notification) and art 15(1)(h) (access) require the controller to disclose "the existence of automated decision-making, including profiling, referred to in Article 22(1) and (4)" and, at least in those cases, "meaningful information about the logic involved, as well as the significance and the envisaged consequences of such processing for the data subject".
- **Recital 71** says safeguards should include specific information and the right to obtain human intervention, to express a view, "to obtain an explanation of the decision reached after such assessment" and to challenge the decision. Recitals are not legally binding.

### 3. The Wachter et al. argument
They distinguish two axes of "explanation":
- *System functionality* (logic, significance, envisaged consequences, general workings: for example the model's requirements, criteria and structure) versus *the rationale of a specific decision* (the reasons and weighting of features in this person's case).
- *Ex ante* (before the decision; can address only system functionality) versus *ex post* (after; can address either).

Their claims:
1. **Art 22(3) contains no right to explanation.** The binding safeguards are human intervention, expressing a view and contesting. "Explanation of the decision reached" appears only in non-binding Recital 71. The legislative history suggests deliberate placement there: the Parliament wanted a right to explanation in the operative text, the Council preferred it in a recital, the Commission included none, and the outcome was trilogue compromise.
2. **Notification duties (arts 13-14) are ex ante** and so can cover only system functionality. They are tied to art 22(1) and (4) only; the authors argue that the link claimed between them and the art 22(3) safeguards is not made in the GDPR.
3. **The right of access (art 15(1)(h)) gives a limited right to be informed.** The wording ("existence of", "logic involved", "significance", "envisaged consequences") is future-oriented and system-level, unlike Recital 71's reference to an explanation of the specific decision. They draw support from how Member States implemented the 1995 Directive's access right (for example the German SCHUFA judgments), which was mostly limited to system functionality. They concede the lack of an explicit time limit on invoking access means semantics alone cannot settle the question.
4. **Even if a right existed, its scope is narrow.** It would apply only to decisions "solely" automated with legal or similarly significant effects. Any meaningful (and arguably even nominal) human involvement could take a decision outside art 22, and it is unclear whether automated *preparation* of a decision acted on by a human counts. The art 22(3) safeguards also apply only to art 22(2)(a) and (c) decisions, not to those authorised by law under (b), where "suitable measures" are left to the authorising law.
5. **Prohibition or right to object?** Art 22 is ambiguous. Read as a *prohibition*, all automated decisions outside art 22(2) are barred; read as a *right to object*, controllers may proceed until the data subject objects. They say the prohibition reading favours data subjects and the right-to-object reading favours controllers, and that Member States could diverge.
6. **Recommendations:** add a right to explanation of specific decisions to binding art 22(3) (or via Member State law), clarify the key terms in art 15(1)(h), and consider the innovation cost of requiring interpretable models. The explanation, they note, may be necessary to make the right to contest meaningful.

### 4. The AI Act's explanation right (art 86)
Art 86(1) AI Act gives an "affected person" subject to a decision taken by a deployer on the basis of the output of a high-risk AI system listed in Annex III (excluding point 2, critical infrastructure) which produces legal effects or similarly significantly affects them adversely in terms of health, safety or fundamental rights, a right to obtain from the deployer "clear and meaningful explanations of the role of the AI system in the decision-making procedure and the main elements of the decision taken". It yields to Union or national law restrictions (art 86(2)) and applies only where the right is not otherwise provided for in Union law (art 86(3)). Note it covers decisions made *on the basis of* AI output, so it is not confined to "solely" automated decisions.

### 5. Related EDPB points
The EDPB opinion on AI models recalls that transparency under arts 12-14 includes, where automated decision-making occurs, meaningful information about the logic involved, and that information on AI processing should be accessible and understandable (para 63).

## Key authorities
- GDPR art 22(1)-(4); arts 13(2)(f), 14(2)(g), 15(1)(h); Recital 71.
- Wachter, Mittelstadt and Floridi, "Why a Right to Explanation of Automated Decision-Making Does Not Exist in the General Data Protection Regulation" (2017) 7 International Data Privacy Law 76.
- AI Act (Regulation (EU) 2024/1689) art 86.
- German SCHUFA judgments (BGH), discussed by Wachter et al. as evidence of narrow access rights under the 1995 Directive. The paper treats them as showing a strict reading of "solely".

## Debate and critique
- **Binding text versus aspirational recital.** The core dispute is how much weight Recital 71 carries. Wachter et al. emphasise that recitals are not binding and that the omission from art 22 looks intentional.
- **Prohibition versus right.** The practical effect of art 22 differs sharply depending on the reading; the authors flag the risk of the GDPR being "toothless".
- **Human-in-the-loop loophole.** If a rubber-stamping human removes the decision from art 22, the protection is easily evaded; the paper calls for clarity on what level of involvement counts.
- **Technical feasibility.** Complex probabilistic models may resist case-specific explanation; the authors suggest that expert or regulator-directed transparency may be more effective than disclosure to individuals, and that trade secrets limit access.
- **Counterpoint to consider.** The AI Act's art 86 shows the legislator later chose to create an explicit (but sector-limited) explanation right, which can be read as confirming the gap the authors identified.
- **Wider material.** The Solove overview and the "reasonable inferences" article (in raw/secondary) question whether individual-rights models can govern inference-based decisions; use them for essay breadth.

## Applying it to a problem question
1. Is there a *decision* with legal or similarly significant effect (credit, hiring, benefits, insurance)?
2. Is it *solely* automated? Probe whether the human reviewer has real authority and actually considers the case.
3. Does an art 22(2) exception apply (contract necessity, authorisation by law with safeguards, explicit consent)? If (a) or (c), are the art 22(3) safeguards (human intervention, view, contest) in place? Special-category data triggers art 22(4).
4. What information was given under arts 13-15: the existence of ADM and meaningful information about logic, significance and consequences?
5. Argue both sides on explanation: the Wachter reading (only functionality) versus a broader purposive reading tied to Recital 71 and the right to contest. Mention art 86 AI Act if the system is a listed high-risk system used by a deployer.
6. Traps: asserting a "GDPR right to explanation" as settled law; overlooking "solely"; ignoring that the AI Act is separate and has its own scope limits.

## Links
- gdpr-framework-for-ai
- gdpr-lawful-bases-and-consent
- data-subject-rights-and-erasure
- eu-ai-act
- ai-and-privacy-overview
