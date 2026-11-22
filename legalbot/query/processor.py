"""Query Processor: intent detection, topic routing, conversation-aware query rewriting, input safety.

Rule-based first (fast, free, debuggable). Every decision returns a reason string so the
debug trace shows *why* a question was classed as essay / problem question / general.
"""
from __future__ import annotations

import re

from ..guard.safety import scan_user_input

INTENT_RULES = {
    "essay": [
        r"\bcritically (?:discuss|evaluate|assess|analyse|analyze)\b", r"\bdiscuss\b", r"\bto what extent\b",
        r"\bevaluate\b", r"\bassess (?:whether|the)\b", r"\bcritically examine\b", r"\bexamine the (?:extent|view|claim)\b",
        r"\bmake the case (?:for|against)\b", r"\bshould (?:the law|english law|the courts)\b", r"\b\d{3,5}[- ]?words?\b.*\bessay\b", r"\bessay\b",
        r"^[\"“'].{20,}[\"”']\s*(?:discuss|evaluate)", r"\bdo you agree\b", r"\bhow far\b",
    ],
    "problem_question": [
        r"\badvise\b", r"\bproblem question\b", r"\bliable\b", r"\bliability of\b", r"\bwhat (?:claims|remedies)\b",
        r"\bclient\b", r"\bseeks? (?:your )?advice\b", r"\b(?:ltd|plc|llp)\b",
        r"\bdiscuss (?:any |the )?(?:criminal |civil |potential |possible )?(?:liabilit|claims?|remedies|offences)",
        r"\bconsider (?:the )?(?:liability|claims|remedies|rights) of\b",
        r"\b[A-Z][a-z]+ (?:wants|seeks|asks|claims|sues|agreed|signed|employed|owns)\b",
    ],
    "general": [
        r"\bsummari[sz]e\b", r"\bexplain\b", r"\bwhat is\b", r"\bwhat are\b", r"\bdefine\b", r"\bdefinition\b",
        r"\blist\b", r"\bcompare\b", r"\bdifference between\b", r"\bcase (?:summary|brief)\b", r"\bratio\b",
        r"\bkey cases\b", r"\boverview\b",
        # everyday "can I / my rights" questions from non-lawyers
        r"\bcan i\b", r"\bam i (?:allowed|entitled|able|liable)\b", r"\bdo i (?:have to|need to)\b",
        r"\bis it (?:legal|illegal|lawful)\b", r"\bmy rights?\b", r"\bwhat (?:can|should) i do\b",
        r"\b(?:refund|faulty|defective|broken|repair|replacement)\b",
    ],
}
LEGAL_HINTS = re.compile(
    r"\b(law|legal|act|section|s\.?\s?\d|article|art\.?\s?\d|case|court|v\.?\s|judg|statute|regulation|directive|"
    r"trust|tort|contract|liab|claim|pension|competition|essay|problem|oscola|lecture|seminar|"
    r"refund|faulty|defective|rights?|sue|landlord|tenant|employer|deposit|compensat|entitled|consumer|"
    r"warranty|guarantee|lease|will|inherit|divorce|police|arrest|data|gdpr)\w*",
    re.I,
)
FOLLOW_UP = re.compile(
    r"^(and|but|what about|how about|so|then|also|why|does (?:it|that|this)|is (?:it|that|this)|"
    r"(?:that|this|it|they|those|the (?:first|second|third|last|same|above))\b)", re.I,
)
PRONOUNS = re.compile(r"\b(it|that|this|they|them|those|these|he|she|the case|the act|the section|above)\b", re.I)
ENTITY = re.compile(
    r"(?:[A-Z][\w'&.-]+(?: [A-Z][\w'&.-]+)* v\.? [A-Z][\w'&.-]+(?: [A-Z][\w'&.-]+)*)"  # case names
    r"|(?:Article \d+[A-Z]?(?: TFEU| TEU| ECHR)?)"
    r"|(?:[A-Z][a-z]+(?: [A-Z][a-z]+)* Act \d{4})"
    r"|(?:\bs(?:ection)?\.? ?\d+[A-Z]?(?:\(\d+\))?)"
)


def classify_intent(text: str, forced: str = "") -> tuple[str, float, str]:
    if forced:
        return forced, 1.0, "forced by user"
    scores = {k: 0 for k in INTENT_RULES}
    hits: dict[str, list[str]] = {k: [] for k in INTENT_RULES}
    for intent, pats in INTENT_RULES.items():
        for p in pats:
            flags = 0 if "[A-Z]" in p else re.I
            if re.search(p, text, flags):
                scores[intent] += 1
                hits[intent].append(p)
    # several named people in a fact pattern => problem question (essay titles rarely name 3+ people)
    names = {m for m in re.findall(r"(?<![.!?]\s)(?<!^)\b([A-Z][a-z]{2,})\b", text)
             if m not in {"The", "In", "Discuss", "Advise", "English", "Act", "Court", "Article", "Law", "Critically", "Bank",
                          "Ltd", "Plc", "European", "Union", "Supreme", "House", "Lords", "UK", "EU"}}
    if len(names) >= 3:
        scores["problem_question"] += 2
    # long fact pattern with named parties => problem question
    if len(text.split()) > 120 and scores["problem_question"]:
        scores["problem_question"] += 1
    best = max(scores, key=scores.get)
    if scores[best] == 0:
        if not LEGAL_HINTS.search(text) and len(text.split()) < 40:
            return "out_of_scope", 0.5, "no legal signal"
        return "general", 0.4, "default"
    total = sum(scores.values())
    return best, round(scores[best] / total, 2), f"matched {hits[best][:3]}"


def route_topics(text: str, manifests: dict, forced: str = "") -> list[str]:
    if forced:
        return [forced]
    low = text.lower()
    scored = []
    for slug, m in manifests.items():
        terms = [m.get("name", slug), slug.replace("-", " ")] + list(m.get("aliases", []))
        # longer, more specific terms count more ("time-barred", "registered land" > "breach")
        n = sum(1 + 0.5 * len(re.findall(r"[\w']+", str(t))) for t in terms
                if t and re.search(r"\b" + re.escape(str(t).lower()) + r"(?:s|es)?\b", low))
        if n:
            scored.append((n, slug))
    scored.sort(reverse=True)
    return [s for _, s in scored[:3]]


def rewrite(message: str, history: list[dict]) -> tuple[str, bool]:
    """Conversation-aware rewrite: make follow-ups self-contained for retrieval."""
    if not history:
        return message, False
    short = len(message.split()) <= 14
    follow = bool(FOLLOW_UP.search(message.strip())) or (short and bool(PRONOUNS.search(message)))
    if not follow:
        return message, False
    last_user = next((h["content"] for h in reversed(history) if h["role"] == "user"), "")
    last_bot = next((h["content"] for h in reversed(history) if h["role"] == "assistant"), "")
    ents = []
    for src in (last_user, last_bot[:1500]):
        for m in ENTITY.findall(src):
            m = re.sub(r"^(?:In|The|See|Under|By|From|As) ", "", m)
            if m not in ents and m.lower() not in message.lower():
                ents.append(m)
    context = "; ".join(ents[:6]) if ents else last_user[:200]
    return f"{message} (in the context of: {context})", True


_LAY: list[dict] | None = None


def lay_concepts() -> list[dict]:
    """kb/lay_concepts.yaml, compiled once (everyday wording -> legal issue)."""
    global _LAY
    if _LAY is None:
        import yaml
        from .. import config
        p = config.path("kb") / "lay_concepts.yaml"
        data = (yaml.safe_load(p.read_text()) or {}) if p.exists() else {}
        _LAY = []
        for c in data.get("concepts", []):
            groups = [re.compile(r"\b(?:" + "|".join(str(w) for w in g) + r")\b", re.I) for g in c.get("when", [])]
            _LAY.append({**c, "_groups": groups})
    return _LAY


def legal_issue(text: str) -> list[dict]:
    """Concepts whose every trigger group matches the question."""
    return [c for c in lay_concepts() if c["_groups"] and all(g.search(text) for g in c["_groups"])]


class QueryProcessor:
    def __init__(self, manifests_fn, voter=None):
        self._manifests = manifests_fn  # callable -> dict, so manifests reload with the index
        self._voter = voter             # callable(query) -> {area: share} from the closest notes (optional)

    def process(self, message: str, history: list[dict], forced_intent: str = "", forced_topic: str = "") -> dict:
        flags = scan_user_input(message)
        rewritten, follow = rewrite(message, history)
        last_user = next((h["content"] for h in reversed(history) if h["role"] == "user"), "")
        intent, conf, reason = classify_intent(message, forced_intent)
        if follow and intent == "out_of_scope":
            intent, conf, reason = "general", 0.5, "follow-up in legal conversation"
        # everyday facts -> the legal issue they raise (so search and the reranker see legal terms, not just "laptop")
        issues = legal_issue(message + (" " + last_user if follow else ""))
        if issues:
            rewritten = f"{rewritten}\nLegal issue: " + " | ".join(c["legal"] for c in issues)
            if intent == "out_of_scope":
                intent, conf, reason = "general", 0.6, "everyday legal problem"
        topics = route_topics(rewritten + (" " + last_user if follow else ""), self._manifests(), forced_topic)
        if follow and not forced_topic:   # a follow-up stays in the module of the question it follows
            prev = route_topics(last_user, self._manifests())
            if prev:
                topics = prev
        for c in issues:
            if c.get("topic") and c["topic"] not in topics and not forced_topic:
                topics = [c["topic"]] + topics[:1]
        votes = {}
        if self._voter and not forced_topic:
            try:
                votes = self._voter(rewritten)
            except Exception:
                votes = {}
        if votes:
            ranked = list(votes.items())
            lead, share = ranked[0]
            if not topics:
                # no alias matched: take the areas the closest notes come from
                topics = [t for t, w in ranked if w >= 0.2][:3] or [lead]
            elif lead not in topics and share >= 0.45:
                # aliases matched, but the notes clearly point elsewhere (e.g. "consent" -> medical law
                # when the question is about criminal assault): put the notes' area first
                topics = [lead] + topics[:2]
        return {"intent": intent, "intent_confidence": conf, "intent_reason": reason, "topics": topics,
                "rewritten_query": rewritten, "is_follow_up": follow, "safety_flags": flags,
                "legal_issues": [c["name"] for c in issues]}
