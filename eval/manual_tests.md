# Five test questions (send them in the chat, Type: Auto-detect)

After each answer: click **Sources (n)**, check the grounding tag, and use 👍 / 👎 with a comment. Comments land in
`improvement/user_feedback/<date>/`; anything the bot could not find lands in `improvement/knowledge_gaps/<date>/`.

## 1. Everyday, short (commercial / consumer) – expect ~200 words
> I bought a laptop from a shop in the UK 5 weeks ago and it keeps shutting down. The shop says I can only have it repaired. Is that right?

Look for: missing-facts block (business seller? delivery date?), "Yes/No, based on Consumer Rights Act 2015 s 22 / s 23 / s 24…",
the 30-day point (5 weeks = past the short-term right to reject, so repair/replacement first), practical steps, no OSCOLA.

## 2. Study question, short (trusts) – expect ~300 words
> What is the difference between knowing receipt and dishonest assistance?

Look for: answer in the first two sentences, elements of each with authority (e.g. *Royal Brunei v Tan*, *BCCI v Akindele*),
a comparison table or a clear contrast, the trusts law notes among the sources.

## 3. Problem question, medium (land law) – 1,000 words
> Maria contributed £40,000 to the purchase of a registered house held in the sole name of her son Sam. Sam granted his neighbour Priya an express right of way by deed, which was never registered. Sam later mortgaged the house to Northbank plc without telling Maria, who lives there. Sam has defaulted. Advise Northbank plc. (1,000 words)

Look for: no introduction; registered land identified; Priya's easement is equitable only and cannot override under
Sch 3 para 3 (a common error); Maria's interest under a resulting/constructive trust; overreaching
fails with one trustee; Sch 3 para 2 actual occupation **and its exceptions** (inquiry, obvious on inspection); a mini-conclusion per issue.

## 4. Essay, medium-long (law and medicine) – 1,500 words
> "The right to determine what shall be done with, or to, one's body is a fundamental right in our society." Critically examine the extent to which English law reflects this view. (1,500 words)

Look for: a qualified thesis in the first two sentences; terms defined; 2–3 examples (e.g. refusal of treatment,
children's refusals, assisted suicide); named academics on both sides; a counter-argument answered; MCA 2005 sections
explained, not just named; no out-of-scope material (no Montgomery negligence).

## 5. Problem question, long, multi-party (criminal law) – 1,500 words
> During a five-a-side league match, Dev skids into Leo "to stop him scoring", breaking Leo's nose. Marco shouts at Dev "I'm going to get you for that"; Dev backs away. Felix, enraged at a refereeing decision, swings a metal pole at Marco but drops it; it hits the referee, Ruth, who suffers a brain injury needing surgery. Discuss criminal liability and the defence of consent. (1,500 words)

Look for: party-by-party headings; every AR/MR element (direct v oblique intention, *Woollin* both limbs); level of harm argued
with case law / CPS charging standards (broken nose: ABH not GBH?); assault needs apprehension; **transferred malice**
(*Latimer*) for Ruth; consent: *Brown* and sport (*Barnes* factors); nothing on inchoate or accessorial liability.

### Then a follow-up (multi-turn)
After question 2, ask: **"and what remedy does the claimant get in each?"**: it should keep the trusts context.

---

# Five more: what students actually ask (`python scripts/run_manual_tests.py claude_cli r`)

| # | Request | A good answer |
|---|---|---|
| r1 | Summarise *Guest v Guest* in ~150 words for revision | Facts / decision / why it matters; expectation-based remedy, majority v Lord Leggatt's dissent; within the word count |
| r2 | Essay **plan** on abandoning *Keck* | Headings that argue, thesis, the cases and academics for each section; not a full essay |
| r3 | "Improve this paragraph" (a weak paragraph on *Dassonville* / *Keck*) | Rewritten in formal register, no contractions, cases cited precisely, plus a list of what changed (per the EU law style rules) |
| r4 | Landlord has not returned the deposit (England) | Missing facts first, direct answer with the rule, steps and deadlines; likely from web sources, logged as a gap |
| r5 | Key cases on actual occupation, short | *Boland*, *Link Lending*, *Chhokar*, *Stockholm Finance* etc., one line each, from the land law notes |
