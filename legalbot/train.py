"""Automated training loop: test the bot like a real user, log feedback, tune instructions and retrieval, report.

  python -m legalbot.train --areas criminal-law,eu-law --per-area 5
  python -m legalbot.train --areas all --per-area 2 --cross 2      # plus 2 questions spanning several areas
  python -m legalbot.train --areas tort-law --per-area 3 --no-fix  # test and log only

One round (through your Claude login: Sonnet writes the questions and the bot answers with Sonnet; Opus marks
every answer for quality and legal accuracy against eval/marking_guide.md and writes the rules):
  1. ASK       a tester writes realistic questions (essay / problem question / everyday, mixed difficulty) for
               each area, and asks the real bot through the normal pipeline (retrieval -> prompt -> LLM -> checks).
  2. LOG       the tester grades every answer against a fixed checklist; the grade is saved exactly like a
               user's 👍/👎 (improvement/user_feedback/<date>/, marked `by: auto-tester`); missing law is filed
               in improvement/knowledge_gaps/ for the gap fixer.
  3. FIX       instruction problems become short rules, routed to the right file:
                 one area only               -> kb/topics/<area>/style.md
                 two or more areas / general -> kb/style/<essay|problem_question|general|common>.md
                 questions spanning areas    -> kb/style/cross_area.md
               routing misses (question sent to the wrong area) -> new aliases in kb/topics/<area>/manifest.yaml
  4. VALIDATE  questions that scored low are asked again; a file whose change made scores worse is restored.
               Retrieval metrics (eval/evalset.yaml) are measured before and after.
  5. RETRIEVAL missing cases / Acts are downloaded from official sources (legalbot.fix_gaps) and indexed.
  6. REPORT    improvement/training_runs/<date>-<time>/summary.md: scores, every change, and questions for you.

Nothing is committed or pushed; review summary.md and changes.md, then commit what you want to keep.
"""
from __future__ import annotations

import argparse
import asyncio
import datetime as dt
import json
import re
import shutil
import socket
import subprocess
import sys
import time
from pathlib import Path

import yaml

from . import config
from .llm.providers import generate
from .obs import improve
from .obs.trace import find_trace

ROOT = config.ROOT
KB = config.path("kb")
TESTER_MODEL = "sonnet"   # writes the test questions
GRADER_MODEL = "opus"     # marks answers (quality + accuracy) and writes rules; --grader-model to change
MARKING_GUIDE = ROOT / "eval" / "marking_guide.md"
TYPES = ("problem_question", "essay", "general")
TYPE_FILE = {"essay": "essay.md", "problem_question": "problem_question.md", "general": "general.md"}

CHECKLIST = """1. law: the rules stated are correct for the jurisdiction (England & Wales / UK / EU as relevant).
2. authorities: leading cases and statute sections are cited, real, correctly named, with pinpoints where expected.
3. coverage: every issue in the question is dealt with; nothing important is missing.
4. structure: follows the answer type (essay = thesis + argument + counter-argument + conclusion; problem question
   = issue by issue, every element, defences, remedies, conclusion; everyday = direct answer first, plain English,
   what to do next).
5. grounding: claims are supported by the cited passages; nothing invented; gaps admitted honestly.
6. word limit and length: within any limit set; not padded; not superficial."""


# ------------------------------------------------------------------ helpers
LIMIT_HIT = ""   # set when the Claude usage limit is reached: the run stops cleanly instead of failing every call


def ask_model(system: str, prompt: str, model: str | None = None) -> str:
    try:
        return "".join(generate("claude_cli", system, prompt, model=model or TESTER_MODEL))
    except Exception as e:
        hit_limit(e)
        raise


def hit_limit(e: Exception) -> bool:
    global LIMIT_HIT
    m = re.search(r"hit your [^\n]*?limit[^\n]*", str(e))
    if m and not LIMIT_HIT:
        LIMIT_HIT = m.group(0).strip()
    return bool(m)


def marking_guide() -> str:
    return MARKING_GUIDE.read_text() if MARKING_GUIDE.exists() else ""


def parse_json(text: str):
    text = re.sub(r"^```(?:json)?|```$", "", text.strip(), flags=re.M)
    pairs = sorted((("[", "]"), ("{", "}")), key=lambda oc: (text.find(oc[0]) == -1, text.find(oc[0])))
    for opener, closer in pairs:   # whichever bracket opens first is the outer value
        i, j = text.find(opener), text.rfind(closer)
        if i != -1 and j > i:
            try:
                return json.loads(text[i:j + 1])
            except json.JSONDecodeError:
                continue
    raise ValueError(f"no JSON in model output: {text[:300]}")


def areas_list(arg: str) -> list[str]:
    allowed = sorted(p.name for p in (KB / "topics").iterdir()
                     if p.is_dir() and not p.name.startswith("_") and (p / "manifest.yaml").exists()
                     and p.name not in ("official-sources", "assessment-skills"))
    if arg == "all":
        return allowed
    out = [a.strip() for a in arg.split(",") if a.strip()]
    bad = [a for a in out if a not in allowed]
    if bad:
        sys.exit(f"unknown area(s): {', '.join(bad)}\navailable: {', '.join(allowed)}")
    return out


def note_titles(area: str) -> list[str]:
    out = []
    for p in sorted((KB / "topics" / area / "notes").glob("*.md")):
        m = re.search(r"^title:\s*(.+)$", p.read_text(errors="ignore")[:600], re.M)
        out.append(m.group(1).strip() if m else p.stem)
    return out


def grpc_up() -> bool:
    g = config.load()["grpc"]
    with socket.socket() as s:
        s.settimeout(1)
        return s.connect_ex((g["host"], int(g["port"]))) == 0


# ------------------------------------------------------------------ 1. ask
QGEN_SYSTEM = ("You write realistic law questions for testing a UK/EU law study assistant. Write like real users: "
               "students preparing coursework or exams, and members of the public with everyday problems. "
               "Output JSON only.")


def make_questions(area: str, n: int, types: list[str], focus: list[str] | None = None) -> list[dict]:
    m = yaml.safe_load((KB / "topics" / area / "manifest.yaml").read_text())
    aim = ("" if not focus else "\nTEST THE SAME LAW as these mistakes found in earlier answers, with NEW facts and "
           "wording (do not copy or paraphrase old questions; the answer must apply the corrected rule):\n"
           + "\n".join(f"- {str(x)[:300]}" for x in focus[:8]) + "\n")
    prompt = f"""Area of law: {m.get('name', area)} ({area}). Jurisdiction: {m.get('jurisdiction', 'England & Wales')}.
Subtopics covered by the knowledge base:
{chr(10).join('- ' + t for t in note_titles(area)[:60]) or '- (no notes yet)'}

{aim}
Write {n} questions. Spread them across these answer types: {', '.join(types)}
(problem_question = a fact scenario asking for advice; essay = a critical statement to discuss, sometimes with a
word limit like "(1,500 words)"; general = an everyday question in plain words, no legal terms).
Mix difficulty: easy, medium, hard (hard = several issues, a recent development or a contested point).
Return a JSON list of objects: {{"type": ..., "difficulty": ..., "question": ...,
"expected": ["the key authorities or rules a good answer must use", ...]}}"""
    qs = parse_json(ask_model(QGEN_SYSTEM, prompt))
    return [dict(q, areas=[area]) for q in qs[:n]]


def make_cross_questions(areas: list[str], n: int) -> list[dict]:
    names = ", ".join(areas)
    prompt = f"""Write {n} questions that each need TWO or THREE of these areas of law to answer: {names}.
Typical: one set of facts giving claims in contract and tort, a crime with a civil claim, an EU law point inside a
UK dispute. Mostly problem questions, some everyday plain-English ones.
Return a JSON list: {{"type": "problem_question"|"general"|"essay", "difficulty": ..., "question": ...,
"areas": [the area slugs it spans, from: {names}], "expected": [...]}}"""
    return parse_json(ask_model(QGEN_SYSTEM, prompt))[:n]


async def ask_bot(orch, q: dict, bot_model: str) -> dict:
    events: dict = {"tokens": []}

    async def send(ev):
        if ev.get("type") == "token":
            events["tokens"].append(ev["text"])
        elif ev.get("type") == "reset":
            events["tokens"].clear()
        elif ev.get("type") in ("session", "done", "error", "mode"):
            events[ev["type"]] = ev

    msg = {"message": q["question"], "user_id": "auto-tester",
           "options": {"provider": "claude_cli", "model": bot_model, "strict": False}}
    t0 = time.time()
    for attempt in range(2):
        events.clear()
        events["tokens"] = []
        await orch.handle(msg, {}, send)
        if "error" not in events and "Generation failed" not in "".join(events["tokens"])[:200]:
            break
        await asyncio.sleep(5)
    done = events.get("done") or {}
    trace = find_trace(done.get("trace_id") or (events.get("session") or {}).get("trace_id") or "") or {}
    return {"answer": trace.get("answer") or "".join(events["tokens"]), "trace": trace,
            "session_id": (events.get("session") or {}).get("session_id"), "message_id": done.get("message_id"),
            "seconds": round(time.time() - t0)}


# ------------------------------------------------------------------ 2. grade + log
GRADE_SYSTEM = ("You are a strict, experienced UK law examiner and QA tester. You mark answers from a law study "
                "assistant against first-class (70+) undergraduate standard, check every statement of law for "
                "accuracy, and say precisely what to fix. Output JSON only.")


def grade(q: dict, res: dict) -> dict:
    t = res["trace"]
    srcs = "\n".join(f"- [{s.get('label')}] {s.get('id')} ({s.get('authority')})"
                     for s in (t.get("sources") or [])) or "- none"
    prompt = f"""QUESTION ({q['type']}, {q['difficulty']}; intended areas: {', '.join(q['areas'])}):
{q['question']}

WHAT A GOOD ANSWER NEEDS (from the question writer): {'; '.join(q.get('expected') or [])}

HOW THE BOT HANDLED IT: detected type = {t.get('intent')}; routed areas = {', '.join(t.get('topics') or []) or 'none'};
answer mode = {t.get('answer_mode')}; retrieval confidence = {t.get('confidence')}.
PASSAGES IT RETRIEVED:
{srcs}

TEXT OF THE STATUTES AND JUDGMENTS IT RETRIEVED (authoritative: where the answer matches this text, it is not an
error, even if your memory differs):
{primary_texts(t) or '(none)'}

ANSWER:
{res['answer'][:60000]}

CHECKLIST:
{CHECKLIST}

MARKING GUIDE (apply its bands; 5 = 70+ first-class quality, 4 = 65-69, 3 = 60-64, 2 = 50-59, 1 = below 50;
everyday questions are marked on clarity, correctness and usefulness, not academic depth):
{marking_guide()[:16000] or '(none)'}

SYSTEM-REQUIRED FEATURES (do not mark down): [background] tags on general-knowledge sentences, a one-line notice
that the answer is partly from general knowledge or the web, and a short 'Gaps in the knowledge base' list. A missing
citation is a smaller fault than an invented or unverifiable one; never suggest rules that push the bot to cite from
memory. Suggested rules must not contradict these:
{CORE_RULES}

ACCURACY CHECK: go through every case name, citation, section number and statement of law. A wrong rule, a case
cited for something it did not decide, an invented authority or a wrong section must be listed in "errors" and
pulls "law" and "overall" down hard. Do not list things that are merely incomplete there.

Return JSON:
{{"scores": {{"law": 1-5, "authorities": 1-5, "coverage": 1-5, "structure": 1-5, "grounding": 1-5, "length": 1-5}},
 "overall": 1-5, "mark": <estimated percentage, e.g. 64>, "comment": "2-4 sentences a user would write as feedback",
 "errors": ["each legal inaccuracy: what the answer said -> what is correct", ...],
 "relevant": ["labels of the retrieved passages that were genuinely on point, e.g. S1", ...],
 "issues": [{{"kind": "instruction"|"retrieval"|"routing"|"missing_law"|"model",
             "scope": "area"|"general"|"cross_area", "area": "<slug or empty>",
             "problem": "what went wrong, specifically", "rule": "for instruction issues: one short imperative
             rule that would prevent it", "aliases": ["for routing issues: 1-3 words users say for this area"],
             "missing": ["for missing_law: exact case names / Act and section the knowledge base lacked"]}}]}}
Use "retrieval" when the right material probably exists but the passages were off-topic; "missing_law" when an
authority the answer needed was not retrieved and was flagged or absent; "model" for one-off reasoning slips that
no rule would fix. No issues if the answer is good."""
    g = parse_json(ask_model(GRADE_SYSTEM, prompt, GRADER_MODEL))
    g["overall"] = float(g.get("overall") or 0)
    try:
        g["mark"] = float(g.get("mark") or 0)
    except (TypeError, ValueError):
        g["mark"] = 0.0
    return g


def log_feedback(store, q: dict, res: dict, g: dict) -> str | None:
    rating = 1 if g["overall"] >= 4 else -1
    kinds = sorted({i.get("kind", "") for i in g.get("issues") or []} - {""})
    if res.get("message_id") and res.get("session_id"):
        store.add_feedback(res["message_id"], res["session_id"], rating, ",".join(kinds), g.get("comment", ""))
    if not res["trace"]:
        return None
    p = improve.record_feedback(res["trace"], rating, f"[{g['overall']:.0f}/5] {g.get('comment', '')}",
                                ",".join(kinds), by=f"auto-tester ({TESTER_MODEL})")
    missing = [m for i in g.get("issues") or [] if i.get("kind") == "missing_law" for m in i.get("missing") or []]
    if missing:
        improve.record_gap(res["trace"], "tester: missing law", missing)
    return str(p.relative_to(ROOT))


# ------------------------------------------------------------------ 3. fix
LEARNED = "## Learned from testing"


def target_file(issue: dict, q: dict, multi_area_problems: set[str]) -> Path | None:
    scope = issue.get("scope") or "area"
    area = issue.get("area") or (q["areas"][0] if len(q["areas"]) == 1 else "")
    if scope == "cross_area" or (scope == "area" and len(q["areas"]) > 1 and not issue.get("area")):
        return KB / "style" / "cross_area.md"
    if scope == "general" or issue.get("problem_key") in multi_area_problems or not area:
        return KB / "style" / TYPE_FILE.get(q["type"], "common.md")
    return KB / "topics" / area / "style.md"


CORE_RULES = """The bot's fixed system rules, which style rules must never contradict or weaken:
- never invent a case, statute, section, quotation or date; name an authority only if it is in the documents or,
  where outside knowledge is allowed, the bot is certain of it;
- every sentence from general knowledge is tagged [background]; answers from web or general knowledge open with a
  one-line notice and end with a short 'Gaps in the knowledge base' list (these are required, never ban them);
- in strict / limited-material modes no outside knowledge at all: say what is missing;
- everyday questions get plain-English, practical answers, not academic treatment."""

RULES_SYSTEM = ("You maintain the answer-style rules of a UK law study assistant. You add only rules that are "
                "short, specific, correct in law, not already covered, and consistent with the existing rules and the "
                "bot's fixed system rules. Output JSON only.\n" + CORE_RULES)


EVERYDAY = "## Everyday questions (learned from testing)"
REJECTED: list[str] = []   # rules dropped because they named a case the notes do not have


def write_rules(path: Path, problems: list[dict], backup_dir: Path, everyday: bool = False) -> tuple[list[str], list[str]]:
    """Returns (rules added to this file, area-specific rules that belong in an area file instead)."""
    current = path.read_text() if path.exists() else ""
    general = path.parent.name == "style"
    scope = ("This file applies to EVERY area of law. Put any rule that is about one area's law (a named doctrine, "
             "Act, test or case) in \"area_rules\" instead of \"add\"." if general else
             "This file applies only to this area of law" + (", for everyday plain-English questions." if everyday else "."))
    prompt = f"""FILE: {path.relative_to(ROOT)}
CURRENT CONTENT:
{current[-12000:] or '(empty: new file)'}

PROBLEMS FOUND IN TEST ANSWERS (with the tester's suggested rule):
{chr(10).join(f"- {p['problem']} -> suggested: {p.get('rule', '')}" for p in problems)}

{scope}
Return JSON {{"add": ["rule", ...], "area_rules": ["rule", ...]}}: at most 5 rules in total, each one line,
imperative, general enough to apply to future questions (no facts of a particular test question). Leave out anything
the current content already says. Never add a rule that contradicts the current content or the fixed system rules
(e.g. banning [background] tags or the gaps list, or telling the bot to cite from memory); if a problem can only be
fixed that way, leave it out. Never state a rule of law you are not certain of. Empty lists if nothing is needed."""
    out = parse_json(ask_model(RULES_SYSTEM, prompt, GRADER_MODEL))
    add, d1 = verify_case_names([r.strip() for r in out.get("add") or [] if r.strip()][:5])
    area_rules, d2 = verify_case_names([r.strip() for r in out.get("area_rules") or [] if r.strip()][:5] if general else [])
    REJECTED.extend(f"{path.relative_to(ROOT)}: {r}" for r in d1 + d2)
    if add:
        append_rules(path, add, backup_dir, EVERYDAY if everyday and not general else LEARNED)
    return add, area_rules


CASE = re.compile(r"\b(?:R|Re|[A-Z][\w'&.-]+)(?: (?:[A-Z][\w'&.-]+|of|and|&|\(No \d+\)))* v (?:[A-Z][\w'&.-]+)(?: [A-Z][\w'&.-]+)*")
_NOTES_TEXT: list[str] = []


def verify_case_names(rules: list[str]) -> tuple[list[str], list[str]]:
    """A rule may name a case only if the knowledge-base notes already name it (the rule writer can misremember)."""
    if not _NOTES_TEXT:
        _NOTES_TEXT.append("\n".join(p.read_text(errors="ignore") for p in (KB / "topics").glob("*/notes/*.md")).lower())
    notes = _NOTES_TEXT[0]
    ok, dropped = [], []
    for r in rules:
        def known(c: str) -> bool:   # "Apply Hadley v Baxendale" -> also try "Hadley v Baxendale"
            w = c.split()
            return any(" ".join(w[i:]).lower() in notes for i in range(max(1, w.index("v"))))
        bad = [c for c in CASE.findall(r) if not known(c)]
        if not bad:
            ok.append(r)
            continue
        cleaned = r
        for c in bad:   # drop a parenthetical that cites it; otherwise the rule cannot be trusted
            cleaned = re.sub(r"\s*\([^()]*" + re.escape(c) + r"[^()]*\)", "", cleaned)
        if any(c in cleaned for c in bad):
            dropped.append(r)
        else:
            ok.append(cleaned)
    return ok, dropped


RULE_REF = [""]   # set by learn_rules: which run/questions a rule came from, so every rule can be traced back


def append_rules(path: Path, add: list[str], backup_dir: Path, heading: str = LEARNED) -> None:
    current = path.read_text() if path.exists() else ""
    backup_dir.mkdir(parents=True, exist_ok=True)
    rel = path.relative_to(ROOT)
    bk = backup_dir / str(rel).replace("/", "__")
    if not bk.exists():
        bk.write_text(current if path.exists() else "\x00missing")
    text = current or f"# {path.parent.name.replace('-', ' ').title()}: answer rules\n"
    tag = f"{dt.date.today().isoformat()}" + (f" · ref {RULE_REF[0]}" if RULE_REF[0] else "")
    new = "\n".join(f"- {r} [{tag}]" for r in add)
    if heading not in text:
        text = text.rstrip() + f"\n\n{heading}\n{new}\n"
    else:   # insert at the end of that section
        i = text.index(heading) + len(heading)
        j = text.find("\n## ", i)
        j = len(text) if j == -1 else j
        text = text[:j].rstrip() + "\n" + new + "\n" + text[j:]
    path.write_text(text)


def add_aliases(area: str, words: list[str], backup_dir: Path) -> list[str]:
    mf = KB / "topics" / area / "manifest.yaml"
    if not mf.exists():
        return []
    m = yaml.safe_load(mf.read_text())
    have = {str(a).lower() for a in m.get("aliases") or []}
    others = " | ".join(str(x).lower() for f in (KB / "topics").glob("*/manifest.yaml") if f != mf
                        for x in [*(yaml.safe_load(f.read_text()) or {}).get("aliases", []),
                                  (yaml.safe_load(f.read_text()) or {}).get("name", "")])
    generic = {"agreement", "police", "law", "legal", "court", "claim", "rights", "money", "help", "advice"}
    bl = KB / "alias_blocklist.yaml"   # keywords removed by hand: never added back
    generic |= {str(x).lower() for x in ((yaml.safe_load(bl.read_text()) or {}).get(area) or [])} if bl.exists() else set()
    new = []
    for w in (x.strip().lower() for x in words):
        if not (2 < len(w) < 40) or w in have or w in generic or w in new:
            continue
        if len(w.split()) == 1 and re.search(r"\b" + re.escape(w), others):
            continue   # a single word another area also uses would misroute questions
        new.append(w)
    new = new[:3]
    if new:
        backup_dir.mkdir(parents=True, exist_ok=True)
        bk = backup_dir / str(mf.relative_to(ROOT)).replace("/", "__")
        if not bk.exists():
            bk.write_text(mf.read_text())
        m["aliases"] = list(m.get("aliases") or []) + new
        mf.write_text(yaml.safe_dump(m, sort_keys=False, allow_unicode=True))
    return new


def restore(path: Path, backup_dir: Path) -> None:
    bk = backup_dir / str(path.relative_to(ROOT)).replace("/", "__")
    if bk.exists():
        old = bk.read_text()
        if old == "\x00missing":
            path.unlink(missing_ok=True)
        else:
            path.write_text(old)


def _backup(path: Path, backup_dir: Path) -> None:
    backup_dir.mkdir(parents=True, exist_ok=True)
    bk = backup_dir / str(path.relative_to(ROOT)).replace("/", "__")
    if not bk.exists():
        bk.write_text(path.read_text() if path.exists() else "\x00missing")


# ------------------------------------------------------------------ 3b. notes behind legal errors
MAX_NOTE_FIXES = 10   # notes changed per run (fixes + common-error lines up to 3x this)
NOTEFIX_SYSTEM = ("You maintain the notes of a UK/EU law study knowledge base. An examiner has listed legal errors in an "
                  "answer built from them. You verify each error against the statute and judgment text supplied, "
                  "then either correct a note that is wrong, or record the mistake as a short 'common error' line in "
                  "the most relevant note so future answers avoid it. You never invent authorities. Output JSON only.")
ERROR_BANK = ROOT / "eval" / "error_bank.jsonl"   # every marker-found error and what was done about it (local only)
TRAPS_HEADING = "## Common errors to avoid"
MAX_TRAPS_PER_NOTE = 15


def _section_text(source_id: str, limit: int = 1800) -> str:
    """Text of a retrieved passage ('topic/path.md#anchor'), read from the knowledge-base file."""
    topic, _, rest = source_id.partition("/")
    path, _, anchor = rest.partition("#")
    f = KB / "topics" / topic / path
    if not f.exists():
        return ""
    text = f.read_text(errors="ignore")
    if anchor and not anchor.startswith("p-"):
        for m in re.finditer(r"^#{1,4} (.+)$", text, re.M):
            if re.sub(r"[^a-z0-9]+", "-", m.group(1).lower()).strip("-")[:len(anchor)] == anchor[:80]:
                nxt = re.search(r"^#{1,4} ", text[m.end():], re.M)
                return text[m.start(): m.end() + (nxt.start() if nxt else len(text))][:limit]
    return ""


def primary_texts(trace: dict, limit: int = 9000) -> str:
    """Statute and judgment passages the bot retrieved, so the marker checks the answer against the actual words."""
    out, used = [], 0
    for s in trace.get("sources") or []:
        if s.get("authority") not in ("legislation", "case_law"):
            continue
        t = _section_text(str(s.get("id") or ""))
        if t and used + len(t) <= limit:
            out.append(f"[{s.get('label')}] {s.get('id')}\n{t}")
            used += len(t)
    return "\n\n".join(out)


def reviewed_refs() -> set[str]:
    """Error refs that already have a decision in the error bank (so they are not reviewed twice)."""
    out = set()
    for l in ERROR_BANK.read_text().splitlines() if ERROR_BANK.exists() else []:
        x = json.loads(l)
        if x.get("kind") == "error" and x.get("verdict") not in (None, "", "unreviewed") and x.get("ref"):
            out.add(x["ref"])
    return out


def bank_errors(run_id: str, r: dict, decisions: dict, only: set | None = None, feedback: bool = True) -> None:
    """Append every marker-found error to the error bank, with the action taken (a growing training/eval set)."""
    ERROR_BANK.parent.mkdir(parents=True, exist_ok=True)
    with ERROR_BANK.open("a") as fh:
        g = r["grade"]   # the marker's overall feedback: what kept this answer below 70+
        if feedback:
            fh.write(json.dumps({"kind": "feedback", "ref": f"{run_id}/{r['q']['id']}", "run": run_id, "qid": r["q"]["id"], "areas": r["q"]["areas"],
                                 "type": r["q"]["type"], "question": r["q"]["question"], "bot_model": r.get("bot_model", ""),
                                 "overall": g.get("overall"), "mark": g.get("mark"), "comment": g.get("comment", ""),
                                 "issues": [{k: i.get(k) for k in ("kind", "scope", "area", "problem", "rule")}
                                            for i in g.get("issues") or []],
                                 "date": dt.date.today().isoformat()}, ensure_ascii=False) + "\n")
        for i, e in enumerate(g.get("errors") or []):
            if only is not None and i not in only:
                continue
            d = decisions.get(i, {})
            fh.write(json.dumps({"kind": "error", "ref": f"{run_id}/{r['q']['id']}#{i}", "run": run_id, "qid": r["q"]["id"], "areas": r["q"]["areas"], "type": r["q"]["type"],
                                 "question": r["q"]["question"], "bot_model": r.get("bot_model", ""),
                                 "error": e, "verdict": d.get("verdict", "unreviewed"), "action": d.get("action", ""),
                                 "file": d.get("file", ""), "why": d.get("why", ""),
                                 "date": dt.date.today().isoformat()}, ensure_ascii=False) + "\n")


def _add_trap(f: Path, trap: str, backup_dir: Path, ref: str = "") -> bool:
    text = f.read_text()
    key = re.sub(r"\W+", " ", trap.lower())[:70]
    if key and key in re.sub(r"\W+", " ", text.lower()):
        return False
    m = re.search(rf"^{re.escape(TRAPS_HEADING)}\n(.*?)(?=^## |\Z)", text, re.M | re.S)
    if m and m.group(1).count("\n- ") + m.group(1).startswith("- ") >= MAX_TRAPS_PER_NOTE:
        return False
    _backup(f, backup_dir)
    line = f"- {trap.strip()} [{dt.date.today().isoformat()}" + (f" · ref {ref}" if ref else "") + "]\n"
    if m:
        text = text[:m.end(1)].rstrip("\n") + "\n" + line + text[m.end(1):]
    else:
        text = text.rstrip("\n") + f"\n\n{TRAPS_HEADING}\n\n" + line
    f.write_text(text)
    return True


def fix_notes_for_errors(results: list[dict], backup_dir: Path, run_id: str = "", cap: int = MAX_NOTE_FIXES * 3,
                         banked: bool = False) -> list[dict]:
    """Every legal error the marker found is feedback. Opus checks it against the statute/judgment text, then:
    'fix' a note that taught it, 'trap' (add a common-error line to the most relevant note when the note was right
    but the answer still got it wrong), or 'marker_wrong' (the sources show the answer was right). All logged."""
    fixes: list[dict] = []
    done = reviewed_refs()
    for r in results:
        all_errs = r["grade"].get("errors") or []
        todo = {i for i in range(len(all_errs)) if f"{run_id}/{r['q']['id']}#{i}" not in done}
        log = lambda dec, r=r, todo=todo: bank_errors(run_id, r, dec, todo, feedback=not banked)
        if not todo:
            if not banked:
                log({})   # still log the marker's feedback
            continue
        if len(fixes) >= cap:
            log({})
            continue
        errs = [(i, all_errs[i]) for i in sorted(todo)]
        tr = find_trace(r["trace_id"] or "") or {}
        files: list[Path] = []
        for s in tr.get("sources") or []:
            sid = str(s.get("id") or "")
            if "/notes/" in sid:
                topic, rest = sid.split("/", 1)
                f = KB / "topics" / topic / rest.split("#")[0]
                if f.exists() and f not in files:
                    files.append(f)
        area_notes = [f for a in r["q"]["areas"] for f in sorted((KB / "topics" / a / "notes").glob("*.md"))
                      if not f.name.startswith("case-")]
        texts = "\n\n".join(f"=== FILE {f.relative_to(ROOT)} ===\n{f.read_text()[:12000]}" for f in files[:4])
        prompt = f"""ERRORS an examiner found in an answer (numbered):
{json.dumps(errs, ensure_ascii=False, indent=1)}

STATUTE AND JUDGMENT TEXT THE ANSWER HAD (authoritative):
{primary_texts(tr) or '(none)'}

NOTES THE ANSWER WAS BUILT FROM:
{texts or '(none retrieved)'}

OTHER NOTES IN THIS AREA (file names; you may add a common-error line to one of them):
{chr(10).join(str(f.relative_to(ROOT)) for f in area_notes[:60]) or '(none)'}

For EACH error decide:
- "marker_wrong": the statute/judgment text above (or a note that you are sure is right) shows the answer was correct.
- "fix": a note above states the wrong proposition. Give a minimal correction.
- "trap": the error is real but no note states it wrongly. Write one line (max 45 words) for the most relevant note:
  the mistake to avoid and the correct position, with the authority (only authorities you are certain of).
- "none": too minor or a one-off (e.g. arithmetic on these facts only).
Return JSON {{"decisions": [{{"error": <number>, "verdict": "marker_wrong"|"fix"|"trap"|"none",
  "file": "<note path exactly as listed, for fix/trap>", "old": "<fix: exact text copied from the note, 20-400 chars>",
  "new": "<fix: corrected text>", "trap": "<trap: the one line>", "why": "<one line>"}}]}}"""
        try:
            out = parse_json(ask_model(NOTEFIX_SYSTEM, prompt, GRADER_MODEL))
        except Exception as e:
            log({})
            if hit_limit(e):
                break
            continue
        decisions = {}
        allowed = set(files) | set(area_notes)
        for d in (out.get("decisions") or []) if isinstance(out, dict) else []:
            try:
                i = int(d.get("error"))
            except (TypeError, ValueError):
                continue
            verdict = d.get("verdict") or "none"
            f = ROOT / str(d.get("file", "")).strip()
            rec = {"verdict": verdict, "why": d.get("why", "")}
            if verdict == "fix" and f in files:
                old, new = d.get("old") or "", d.get("new") or ""
                text = f.read_text()
                if old and new and old != new and text.count(old) == 1:
                    _backup(f, backup_dir)
                    f.write_text(text.replace(old, new, 1))
                    fixes.append({"kind": "fix", "file": str(f.relative_to(ROOT)), "old": old, "new": new,
                                  "why": d.get("why", ""), "qid": r["q"]["id"], "ref": f"{run_id}/{r['q']['id']}#{i}"})
                    rec |= {"action": "note corrected", "file": str(f.relative_to(ROOT))}
            elif verdict == "trap" and f in allowed and (d.get("trap") or "").strip():
                if _add_trap(f, d["trap"], backup_dir, f"{run_id}/{r['q']['id']}#{i}"):
                    fixes.append({"kind": "trap", "file": str(f.relative_to(ROOT)), "old": "", "new": d["trap"].strip(),
                                  "why": d.get("why", ""), "qid": r["q"]["id"]})
                    rec |= {"action": "common error added", "file": str(f.relative_to(ROOT))}
            decisions[i] = rec
        log(decisions)
    return fixes


# ------------------------------------------------------------------ 4b. tidy learned rules after a run
MAX_RULES_PER_SECTION = 12
TIDY_SYSTEM = ("You keep the answer-style rules of a UK law study assistant short and consistent. Output JSON only.\n"
               + CORE_RULES)
_LEARNED_SECTION = re.compile(r"(^## (?:Learned from testing|Everyday questions \(learned from testing\))[^\n]*\n)(.*?)(?=^## |\Z)",
                              re.M | re.S)


def tidy_rules(paths: list[Path], backup_dir: Path) -> list[str]:
    """Merge duplicates, drop vague or conflicting learned rules, cap each learned section."""
    notes = []
    for path in paths:
        if not path.exists():
            continue
        text = path.read_text()
        secs = list(_LEARNED_SECTION.finditer(text))
        if not secs:
            continue
        for m in reversed(secs):
            rules = [l for l in m.group(2).splitlines() if l.startswith("- ")]
            if len(rules) < 4:
                continue
            rest = text[:m.start()] + text[m.end():]
            prompt = f"""FILE: {path.relative_to(ROOT)}
OTHER CONTENT OF THE FILE (hand-written rules; do not repeat them):
{rest[-8000:]}

LEARNED RULES IN SECTION "{m.group(1).strip()}":
{chr(10).join(rules)}

Return JSON {{"rules": ["- rule [dates · ref ...]", ...]}}: the cleaned list. Merge duplicates (keep the bracketed
dates and refs of every merged rule, combined in one bracket),
delete rules that repeat the other content, are too vague to act on, are about one particular test question, or
conflict with the fixed system rules; keep every rule that adds something real. At most {MAX_RULES_PER_SECTION} rules.
Do not change any rule of law except to fix a clear error."""
            try:
                out = parse_json(ask_model(TIDY_SYSTEM, prompt, GRADER_MODEL))
            except Exception:
                continue
            new = [r.strip() for r in (out.get("rules") or []) if isinstance(r, str) and r.strip().startswith("- ")]
            if not new or new == rules:
                continue
            new, dropped = verify_case_names([r[2:] for r in new])
            new = [f"- {r}" for r in new][:MAX_RULES_PER_SECTION]
            _backup(path, backup_dir)
            body = "\n".join(new) + "\n\n"
            text = text[:m.start()] + m.group(1) + body + text[m.end():]
            notes.append(f"{path.relative_to(ROOT)} ({m.group(1).strip()[3:]}): {len(rules)} → {len(new)} rules")
        path.write_text(text)
    return notes


def weakest_areas(runs: list[str], n: int) -> list[str]:
    """Areas with the lowest average score in the given run folders (single-area questions only)."""
    by: dict[str, list[float]] = {}
    for run in runs:
        d = Path(run) if Path(run).is_absolute() else ROOT / run
        for line in (d / "grades.jsonl").read_text().splitlines() if (d / "grades.jsonl").exists() else []:
            r = json.loads(line)
            if len(r["q"]["areas"]) == 1:
                by.setdefault(r["q"]["areas"][0], []).append(float(r["grade"].get("overall") or 0))
    ranked = sorted(by, key=lambda k: (sum(by[k]) / len(by[k]), k))
    return ranked[:n]


def guard_questions(f: str, c: dict, results: list[dict], limit: int = 2) -> list[str]:
    """Other questions a rule file applies to (scored 4+ if possible): a change must not make them worse."""
    p = Path(f)
    if p.parts[:2] == ("kb", "topics"):
        fits = [r for r in results if p.parts[2] in r["q"]["areas"]]
    elif p.name == "cross_area.md":
        fits = [r for r in results if len(r["q"]["areas"]) > 1]
    elif p.name == "common.md":
        fits = [r for r in results if r["q"]["type"] in ("essay", "problem_question")]
    else:
        want = {v: k for k, v in TYPE_FILE.items()}.get(p.name)
        fits = [r for r in results if not want or r["q"]["type"] == want]
    fits = [r for r in fits if r["q"]["id"] not in c["qids"]]
    fits.sort(key=lambda r: -r["grade"]["overall"])
    return [r["q"]["id"] for r in fits[:limit]]


# ------------------------------------------------------------------ 4. validate (retrieval metrics)
def retrieval_metrics() -> dict:
    r = subprocess.run([sys.executable, "-c", "import json; from legalbot.evaluate import run; "
                        "print(json.dumps(run(8)['metrics'].get('all', {})))"],
                       cwd=ROOT, capture_output=True, text=True, timeout=1800)
    try:
        return json.loads(r.stdout.strip().splitlines()[-1])
    except Exception:
        return {"error": (r.stderr or r.stdout)[-300:]}


# ------------------------------------------------------------------ main loop
async def run(a) -> Path:
    from .chat.conversation_store import ConversationStore
    from .chat.orchestrator import Orchestrator

    stamp = dt.datetime.now().strftime("%Y-%m-%d-%H%M")
    out = config.path("review_queue") / "training_runs" / stamp
    out.mkdir(parents=True, exist_ok=True)
    backup = out / "backup"
    log = (out / "log.txt").open("a")

    def say(s):
        print(s, flush=True)
        log.write(s + "\n")
        log.flush()

    areas = areas_list(a.areas)
    if a.focus:   # spend this round on the weakest areas of earlier run(s)
        areas = weakest_areas(a.focus.split(","), a.focus_n)
        say("weakest areas: " + ", ".join(areas))
    types = [t for t in a.types.split(",") if t in TYPES] or list(TYPES)
    server = None
    if not grpc_up():
        say("starting search services (first start loads the models, about a minute)…")
        from .grpc_server import serve
        server, _ = serve(block=False)
    store = ConversationStore(config.path("db"))
    orch = Orchestrator(store)

    before = retrieval_metrics() if not a.no_fix else {}

    # 1. questions (or the same questions as an earlier run, to compare like with like)
    questions = []
    if a.replay:
        src = Path(a.replay)
        src = src if src.is_absolute() else ROOT / src
        questions = yaml.safe_load((src / "questions.yaml").read_text()) or []
        old = {json.loads(l)["q"]["id"]: json.loads(l)["grade"]["overall"]
               for l in (src / "grades.jsonl").read_text().splitlines() if l.strip()}
        for q in questions:
            q["previous_score"] = old.get(q.get("id"))
        if a.only:   # just some of them, e.g. --only q05,q13
            keep = set(a.only.split(","))
            questions = [q for q in questions if q.get("id") in keep]
        say(f"replaying {len(questions)} questions from {src.name}")
        areas = sorted({x for q in questions for x in q["areas"]})
    say(f"writing questions: {len(areas)} area(s) × {a.per_area}" + (f" + {a.cross} cross-area" if a.cross else "")) if not a.replay else None
    for ar in ([] if a.replay else areas):
        try:
            questions += make_questions(ar, a.per_area, types)
        except Exception as e:
            say(f"  question writer failed for {ar}: {e}")
            if hit_limit(e):
                break
    if a.cross and len(areas) > 1 and not a.replay and not LIMIT_HIT:
        try:
            questions += make_cross_questions(areas, a.cross)
        except Exception as e:
            say(f"  cross-area question writer failed: {e}")
    for i, q in enumerate(questions, 1):
        q["id"] = q.get("id") or f"q{i:02d}"
    (out / "questions.yaml").write_text(yaml.safe_dump(questions, sort_keys=False, allow_unicode=True))

    # 1-2. ask + grade + log
    results = []
    for q in questions:
        say(f"{q['id']} [{','.join(q['areas'])} · {q['type']} · {q['difficulty']}] asking…")
        try:
            res = await ask_bot(orch, q, a.bot_model)
            g = grade(q, res)
        except Exception as e:
            say(f"  failed: {e}")
            if hit_limit(e):
                say("usage limit reached: stopping; the answers marked so far are kept")
                break
            continue
        fb = log_feedback(store, q, res, g)
        say(f"  {g['overall']:.0f}/5 in {res['seconds']}s — {g.get('comment', '')[:160]}")
        results.append({"q": q, "answer": res["answer"], "trace_id": res["trace"].get("trace_id"), "bot_model": a.bot_model,
                        "routed": res["trace"].get("topics"), "mode": res["trace"].get("answer_mode"),
                        "grade": g, "feedback_file": fb})
    with (out / "grades.jsonl").open("w") as f:
        for r in results:
            f.write(json.dumps({k: v for k, v in r.items() if k != "answer"}, ensure_ascii=False) + "\n")

    changes: dict[str, dict] = {}
    note_fixes: list[dict] = []
    tidied: list[str] = []
    alias_changes: list[str] = []
    rechecks = []
    fixed_gaps = ""
    manual_needed: list[str] = []
    if LIMIT_HIT or a.no_fix:   # still keep every error the marker found
        for r in results:
            bank_errors(out.name, r, {})
    if LIMIT_HIT:
        say("no fixes this run (usage limit): run --learn-from on this folder once the limit resets")
    if not a.no_fix and results and not LIMIT_HIT:
        changes, alias_changes, issues = learn_rules(results, backup, say, out.name)

        # 3b. a note that taught a legal error is corrected (Opus), then re-indexed before the re-checks
        note_fixes = fix_notes_for_errors(results, backup, out.name)
        for fx in note_fixes:
            say(f"  {'corrected' if fx['kind'] == 'fix' else 'common error added to'} {fx['file']}: {fx['why'][:120]}")
        if note_fixes:
            subprocess.run([sys.executable, "-m", "legalbot.index", "build"], cwd=ROOT, capture_output=True, text=True)

        # 5. missing law -> official download + index (fix_gaps)
        if any(i.get("kind") == "missing_law" for _, i in issues) and not a.no_download:
            say("downloading missing law from official sources…")
            p = subprocess.run([sys.executable, "-m", "legalbot.fix_gaps"], cwd=ROOT, capture_output=True, text=True)
            fixed_gaps = (p.stdout.strip().splitlines() or ["(no output)"])[-1]
            say("  " + fixed_gaps)
            m = re.search(r"report: (.+\.md)", fixed_gaps)
            if m and Path(m.group(1)).exists():
                rep = Path(m.group(1)).read_text()
                got = len(re.findall(r"^- \*\*.+\*\* \(.+\) → ", rep, re.M))
                manual = rep.split("## Needs you", 1)[1] if "## Needs you" in rep else ""
                manual_items = re.findall(r"^- \*\*(.+?)\*\*", manual, re.M)
                fixed_gaps = (f"{got} downloaded and indexed; {len(manual_items)} need a manual download "
                              f"(see {Path(m.group(1)).relative_to(ROOT)})")
                manual_needed.extend(manual_items)

        # 4. validate: re-ask what the changes targeted; restore a file if its questions got worse
        touched = {qid for c in changes.values() for qid in c["qids"]}
        if alias_changes:
            touched |= {r["q"]["id"] for r in results for i in r["grade"].get("issues") or [] if i.get("kind") == "routing"}
        if fixed_gaps:
            touched |= {r["q"]["id"] for r in results for i in r["grade"].get("issues") or [] if i.get("kind") == "missing_law"}
        if note_fixes:
            touched |= {fx["qid"] for fx in note_fixes}
        guards = {f: guard_questions(f, c, results) for f, c in changes.items()}
        guard_ids = {q for g in guards.values() for q in g} - touched
        if a.max_rechecks and len(touched | guard_ids) > a.max_rechecks:
            # keep the questions most changes point at, plus one guard (saves tokens; the checkpoint catches the rest)
            weight: dict[str, int] = {}
            for c in changes.values():
                for q in c["qids"]:
                    weight[q] = weight.get(q, 0) + len(c["added"])
            for fx in note_fixes:
                weight[fx["qid"]] = weight.get(fx["qid"], 0) + 1
            keep = sorted(touched, key=lambda q: (-weight.get(q, 0), q))[: max(1, a.max_rechecks - 1)]
            guard_ids = set(sorted(guard_ids)[: a.max_rechecks - len(keep)])
            touched = set(keep)
            guards = {f: [q for q in g if q in guard_ids] for f, g in guards.items()}
        touched |= guard_ids
        by_id = {r["q"]["id"]: r for r in results}
        for qid in sorted(touched):
            r = by_id[qid]
            say(f"re-checking {qid}…")
            try:
                res = await ask_bot(orch, r["q"], a.bot_model)
                g2 = grade(r["q"], res)
            except Exception as e:
                say(f"  failed: {e}")
                if hit_limit(e):
                    break
                continue
            rechecks.append({"id": qid, "before": r["grade"]["overall"], "after": g2["overall"],
                             "comment": g2.get("comment", ""), "guard": qid in guard_ids})
            say(f"  {r['grade']['overall']:.0f} → {g2['overall']:.0f}")
        after_by = {c["id"]: c for c in rechecks}
        for f, c in changes.items():
            pairs = [(after_by[q]["before"], after_by[q]["after"]) for q in c["qids"] if q in after_by]
            gpairs = [(after_by[q]["before"], after_by[q]["after"]) for q in guards.get(f, []) if q in after_by]
            worse = pairs and sum(b for _, b in pairs) < sum(x for x, _ in pairs)
            hurt = any(b < x - 0.5 for x, b in gpairs)   # a guard question dropped a full point
            if worse or hurt:
                restore(ROOT / f, backup)
                c["reverted"] = True
                c["why_reverted"] = "its questions got worse" if worse else "it made another question worse"
                say(f"  {f}: {c['why_reverted']}, change reverted")
        # 4b. keep the learned rules short: merge, drop noise, cap (Opus)
        tidied = tidy_rules(sorted({ROOT / f for f, c in changes.items() if not c.get("reverted")}), backup)
        for x in tidied:
            say(f"  tidied {x}")
    after = retrieval_metrics() if not a.no_fix else {}
    added_cases = grow_evalset(out.name, results)
    if added_cases:
        say(f"added {added_cases} retrieval test case(s) to eval/evalset.yaml")
    if server:
        server.stop(0)

    # 6. report
    write_changes(out, changes, alias_changes, fixed_gaps, note_fixes, tidied)
    summary = write_summary(out, a, areas, results, changes, alias_changes, rechecks, before, after, fixed_gaps, manual_needed)
    say(f"\nsummary: {summary.relative_to(ROOT)}")
    return summary


def grow_evalset(run_id: str, results: list[dict]) -> int:
    """Good answers become retrieval regression tests: the passages the tester judged on point must keep
    coming back for the same question (measured by `python -m legalbot.evaluate` and step 4 of later runs)."""
    f = config.path("eval") / "evalset.yaml"
    cases = yaml.safe_load(f.read_text()) if f.exists() else []
    cases = cases or []
    have = {c.get("query") for c in cases}
    n = 0
    for r in results:
        g = r["grade"]
        if g["overall"] < 4 or r["q"]["question"] in have:
            continue
        lab = {s.get("label"): s.get("id") for s in (find_trace(r["trace_id"] or "") or {}).get("sources") or []}
        exp = sorted({lab[x].split("#")[0] for x in g.get("relevant") or [] if lab.get(x)})
        if not exp:
            continue
        cases.append({"id": f"auto-{run_id}-{r['q']['id']}", "category": "auto", "query": r["q"]["question"],
                      "topic": r["q"]["areas"][0] if len(r["q"]["areas"]) == 1 else None,
                      "expected_sources": exp[:5], "expected_behavior": "answer"})
        n += 1
    if n:
        head = "# Retrieval test set. Cases marked auto-* were added by `python -m legalbot.train` from answers graded 4+.\n"
        f.write_text(head + yaml.safe_dump(cases, sort_keys=False, allow_unicode=True, width=120))
    return n


def write_changes(out: Path, changes: dict, aliases: list[str], gaps: str, note_fixes=(), tidied=()) -> None:
    L = ["# Changes made in this run", ""]
    for f, c in changes.items():
        L += [f"## {f}" + (f"  (REVERTED: {c.get('why_reverted', 'scores went down')})" if c.get("reverted") else ""),
              f"From questions {', '.join(c['qids'])}:", ""] + [f"- {r}" for r in c["added"]] + [""]
    if note_fixes:
        L += ["## Notes corrected (they taught a legal error)", ""]
        for fx in [x for x in note_fixes if x.get("kind", "fix") == "fix"]:
            L += [f"- `{fx['file']}` (from {fx['qid']}): {fx['why']}", f"  - was: {fx['old'][:300]}",
                  f"  - now: {fx['new'][:300]}"]
        L += ["", "## Common errors added to notes (the note was right; the answer still got it wrong)", ""]
        for fx in [x for x in note_fixes if x.get("kind") == "trap"]:
            L += [f"- `{fx['file']}` (from {fx['qid']}): {fx['new'][:300]}"]
        L.append("")
    if tidied:
        L += ["## Learned rules tidied", ""] + [f"- {x}" for x in tidied] + [""]
    if aliases:
        L += ["## Area aliases (routing)", ""] + [f"- {x}" for x in aliases] + [""]
    if gaps:
        L += ["## Missing law", "", gaps, ""]
    if len(L) == 2:
        L.append("No changes.")
    L += ["Originals of every changed file are in `backup/` (restore by copying back)."]
    (out / "changes.md").write_text("\n".join(L) + "\n")


def write_summary(out, a, areas, results, changes, aliases, rechecks, before, after, gaps, manual=()) -> Path:
    n = len(results)
    avg = sum(r["grade"]["overall"] for r in results) / n if n else 0
    low = [r for r in results if r["grade"]["overall"] < 4]
    by_area: dict[str, list] = {}
    for r in results:
        by_area.setdefault(" + ".join(r["q"]["areas"]), []).append(r["grade"]["overall"])
    kinds: dict[str, int] = {}
    for r in results:
        for i in r["grade"].get("issues") or []:
            kinds[i.get("kind", "?")] = kinds.get(i.get("kind", "?"), 0) + 1
    rec = {c["id"]: c for c in rechecks}
    L = [f"# Training run {out.name}", "",
         f"Areas: {', '.join(areas)} · {n} questions answered · bot model `{a.bot_model}` · questions `{TESTER_MODEL}`"
         f" · marker `{GRADER_MODEL}`", "",
         "## Scores", "", f"- Average: **{avg:.1f} / 5** ({n - len(low)} good, {len(low)} below 4)"]
    marks = [r["grade"].get("mark") for r in results if r["grade"].get("mark")]
    if marks:
        L.append(f"- Estimated mark: **{sum(marks) / len(marks):.0f}%** average "
                 f"({sum(m >= 70 for m in marks)} at 70+, {sum(60 <= m < 70 for m in marks)} in the 60s, "
                 f"{sum(m < 60 for m in marks)} below 60)")
    errs = [(r["q"]["id"], e) for r in results for e in r["grade"].get("errors") or []]
    L.append(f"- Legal errors found: **{len(errs)}** in {len({q for q, _ in errs})} answers")
    prev = [r["q"].get("previous_score") for r in results if r["q"].get("previous_score") is not None]
    if prev:
        L.append(f"- Same questions in {a.replay}: **{sum(prev) / len(prev):.1f} / 5** before → **{avg:.1f}** now")
        old = Path(a.replay) / "summary.md"
        if old.exists() and f"marker `{GRADER_MODEL}`" not in old.read_text():
            L.append(f"  - note: the earlier run was marked by a different model; `{GRADER_MODEL}` with the marking guide "
                     "is stricter, so compare the problems listed rather than the raw scores")
    L += [f"- {k}: {sum(v) / len(v):.1f} ({len(v)} q)" for k, v in sorted(by_area.items())]
    L += ["", "Problems found: " + (", ".join(f"{k} {v}" for k, v in sorted(kinds.items())) or "none"), ""]
    if before or after:
        L += ["## Retrieval (eval/evalset.yaml)", "", f"- before: {before}", f"- after:  {after}", ""]
    L += ["## What changed", ""]
    for f, c in changes.items():
        L.append(f"- `{f}`: {len(c['added'])} rule(s)" + (f" — **reverted**, {c.get('why_reverted', 'scores went down')}" if c.get("reverted") else ""))
    L += [f"- aliases: {x}" for x in aliases]
    if gaps:
        L.append(f"- missing law: {gaps}")
    nf = [l for l in (out / "changes.md").read_text().splitlines() if l.startswith("- `")] if (out / "changes.md").exists() else []
    if "## Notes corrected" in ((out / "changes.md").read_text() if (out / "changes.md").exists() else ""):
        L.append(f"- notes corrected: {sum(1 for l in nf if '(from q' in l)} (see changes.md)")
    if not (changes or aliases or gaps):
        L.append("- nothing")
    L += ["", "Details and the exact rules added: [changes.md](changes.md). Every answer's grade: grades.jsonl.", "",
          "## Re-checks after the changes", ""]
    L += [f"- {c['id']}{' (guard)' if c.get('guard') else ''}: {c['before']:.0f} → {c['after']:.0f}  {c['comment'][:150]}"
          for c in rechecks] or ["- none"]
    L += ["", "## Needs you", ""]
    needs = []
    for r in low:
        rr = rec.get(r["q"]["id"])
        if rr and rr["after"] >= 4:
            continue
        ks = sorted({i.get("kind", "") for i in r["grade"].get("issues") or []})
        if set(ks) <= {"instruction", "routing"} and r["q"]["id"] in {q for c in changes.values() for q in c["qids"]}:
            continue
        needs.append(f"- **{r['q']['id']}** ({', '.join(r['q']['areas'])}, {r['q']['type']}) "
                     f"{r['grade']['overall']:.0f}/5 [{', '.join(ks) or 'no issue type'}]: {r['q']['question'][:140]}\n"
                     f"  - tester: {r['grade'].get('comment', '')[:300]}")
    if errs:
        needs.append("- **Legal errors the marker found** (check the rule or note behind each):\n"
                     + "\n".join(f"  - {q}: {e[:220]}" for q, e in errs[:12]))
    retr = [i["problem"] for r in results for i in r["grade"].get("issues") or [] if i.get("kind") == "retrieval"]
    if retr:
        needs.append("- **Retrieval found off-topic passages** (no automatic fix; a note or eval case may be needed):\n"
                     + "\n".join(f"  - {p[:200]}" for p in retr[:6]))
    if REJECTED:
        needs.append("- **Rules not added: they named a case the notes do not contain** (check and add by hand if right):\n"
                     + "\n".join(f"  - {x[:220]}" for x in REJECTED[:10]))
    if manual:
        needs.append("- **Law the gap fixer could not download** (official site blocked or no official copy); "
                     "save these to the Law folder and re-import:\n" + "\n".join(f"  - {x[:160]}" for x in manual[:15]))
    if LIMIT_HIT:
        needs.insert(0, f"- **Run stopped early: Claude usage limit** ({LIMIT_HIT}). {len(results)} answer(s) marked; "
                        "nothing was fixed from the unanswered ones. Re-run with `--replay` on this folder after the reset.")
    L += needs or ["- nothing: all answers scored 4+ or were fixed"]
    L += ["", "## Questions asked", ""]
    for r in results:
        L.append(f"- {r['q']['id']} [{r['grade']['overall']:.0f}/5] ({', '.join(r['q']['areas'])}, {r['q']['type']}, "
                 f"{r['q']['difficulty']}) {r['q']['question'][:160]}")
    L += ["", "Nothing was committed. Keep the changes: commit them. Undo one: copy its file back from `backup/`."]
    p = out / "summary.md"
    p.write_text("\n".join(L) + "\n")
    return p


def learn_rules(results: list[dict], backup: Path, say=print, run_id: str = "") -> tuple[dict, list[str], list]:
    """The marker's 'how to do better' issues become rules (style files) and routing aliases."""
    changes: dict[str, dict] = {}
    alias_changes: list[str] = []
    # 3. route instruction problems; a problem seen in 2+ areas counts as general
    issues = []
    for r in results:
        for i in r["grade"].get("issues") or []:
            i["problem_key"] = re.sub(r"\W+", " ", (i.get("rule") or i.get("problem") or "").lower())[:60]
            issues.append((r, i))
    seen: dict[str, set] = {}
    for r, i in issues:
        seen.setdefault(i["problem_key"], set()).update(r["q"]["areas"])
    multi = {k for k, v in seen.items() if len(v) > 1}
    buckets: dict[Path, list] = {}
    for r, i in issues:
        if i.get("kind") == "instruction":
            tf = target_file(i, r["q"], multi)
            if tf:
                buckets.setdefault(tf, []).append(i | {"qid": r["q"]["id"]})
        elif i.get("kind") == "routing" and i.get("aliases"):
            area = i.get("area") if i.get("area") in r["q"]["areas"] else r["q"]["areas"][0]
            if len(r["q"]["areas"]) > 1 and not i.get("area"):
                continue   # cross-area question: unclear which area the words belong to
            new = add_aliases(area, i["aliases"], backup)
            alias_changes += [f"{area}: + {w}" for w in new]
    qtype = {r["q"]["id"]: r["q"] for r in results}

    def note(f: Path, added: list[str], qids: list[str]):
        c = changes.setdefault(str(f.relative_to(ROOT)), {"added": [], "qids": []})
        c["added"] += added
        c["qids"] = sorted(set(c["qids"]) | set(qids))
        say(f"  {f.relative_to(ROOT)}: +{len(added)} rule(s)")

    for tf, probs in buckets.items():
        qids = sorted({p["qid"] for p in probs})
        RULE_REF[0] = f"{run_id}/{','.join(qids)}" if run_id else ""
        everyday = all(qtype[q]["type"] == "general" for q in qids)
        try:
            added, area_rules = write_rules(tf, probs, backup, everyday)
        except Exception as e:
            say(f"  rule writer failed for {tf.name}: {e}")
            continue
        if added:
            note(tf, added, qids)
        if area_rules:   # area-specific rules found while writing a general file
            areas_here = sorted({a for q in qids for a in qtype[q]["areas"]})
            if len(areas_here) == 1:
                af = KB / "topics" / areas_here[0] / "style.md"
                append_rules(af, area_rules, backup, EVERYDAY if everyday else LEARNED)
                note(af, area_rules, qids)

    return changes, alias_changes, issues


def learn_from(run_dir: str, rules: bool = True) -> Path:
    """Turn an earlier run's marked errors into note fixes / common-error lines, without re-asking anything."""
    d = Path(run_dir) if Path(run_dir).is_absolute() else ROOT / run_dir
    results = [json.loads(l) for l in (d / "grades.jsonl").read_text().splitlines() if l.strip()]
    backup = d / "backup_learn"
    changes, aliases, _ = learn_rules(results, backup, print, d.name) if rules else ({}, [], [])
    tidied = tidy_rules(sorted({ROOT / f for f in changes}), backup) if changes else []
    already = any(json.loads(l).get("run") == d.name and json.loads(l).get("kind") == "feedback"
                  for l in (ERROR_BANK.read_text().splitlines() if ERROR_BANK.exists() else []))
    fixes = fix_notes_for_errors(results, backup, d.name, cap=10 ** 6, banked=already)
    if fixes:
        subprocess.run([sys.executable, "-m", "legalbot.index", "build"], cwd=ROOT, capture_output=True, text=True)
    L = [f"# Learned from {d.name}", "", f"{sum(len(r['grade'].get('errors') or []) for r in results)} marker errors "
         f"reviewed; {sum(f['kind'] == 'fix' for f in fixes)} notes corrected, "
         f"{sum(f['kind'] == 'trap' for f in fixes)} common-error lines added. All logged in eval/error_bank.jsonl.", ""]
    for f, c in changes.items():
        L += [f"- rules: `{f}` (from {', '.join(c['qids'])})"] + [f"  - {x}" for x in c["added"]]
    L += [f"- alias: {x}" for x in aliases] + [f"- tidied: {x}" for x in tidied]
    for f in fixes:
        L.append(f"- {f['kind']}: `{f['file']}` ({f['qid']}): {f['new'][:250]}" + (f"  (was: {f['old'][:150]})" if f['old'] else ""))
    if LIMIT_HIT:
        L += ["", f"Stopped early: {LIMIT_HIT}"]
    L += ["", f"Originals are in `{backup.relative_to(ROOT)}/`."]
    rep = d / "learned.md"
    rep.write_text("\n".join(L) + "\n")
    print(f"report: {rep.relative_to(ROOT)}")
    return rep


BENCHMARK = ROOT / "eval" / "benchmark"          # fixed 24 questions for a manual like-for-like check (--replay)
PROGRESS = ROOT / "eval" / "progress.json"       # questions marked so far, checkpoint results


def _avg(run_dir: Path) -> tuple[int, float, float]:
    rows = [json.loads(l) for l in (run_dir / "grades.jsonl").read_text().splitlines() if l.strip()] \
        if (run_dir / "grades.jsonl").exists() else []
    if not rows:
        return 0, 0.0, 0.0
    return (len(rows), sum(r["grade"]["overall"] for r in rows) / len(rows),
            sum(float(r["grade"].get("mark") or 0) for r in rows) / len(rows))


def _round_areas(n: int) -> list[str]:
    """Half the weakest areas in recent runs, half the areas tested least recently."""
    runs = sorted((config.path("review_queue") / "training_runs").glob("*/grades.jsonl"))
    weak = weakest_areas([str(r.parent) for r in runs[-4:]], n // 2) if runs else []
    last: dict[str, str] = {}
    for g in runs:
        for l in g.read_text().splitlines():
            if l.strip():
                for ar in json.loads(l)["q"]["areas"]:
                    last[ar] = g.parent.name
    rest = sorted((x for x in areas_list("all") if x not in weak), key=lambda x: last.get(x, ""))
    return weak + rest[: n - len(weak)]


CHECKLIST_HEADING = "## Accuracy checklist (recurring errors found in testing)"
MAX_CHECKLIST = 20
REVIEW_SYSTEM = ("You review the errors a law study assistant made over many marked answers and find the recurring, "
                 "general patterns behind them. Output JSON only.\n" + CORE_RULES)


REVIEW_REF = ["review"]


def _checklist(path: Path) -> tuple[str, list[str]]:
    text = path.read_text()
    m = re.search(rf"^{re.escape(CHECKLIST_HEADING)}\n(.*?)(?=^## |\Z)", text, re.M | re.S)
    return text, (re.findall(r"^- .+$", m.group(1), re.M) if m else [])


def _add_checklist(path: Path, items: list[str], backup_dir: Path) -> list[str]:
    text, have = _checklist(path)
    room = MAX_CHECKLIST - len(have)
    items = [i.strip().lstrip("- ").strip() for i in items if i.strip()][:max(0, room)]
    if not items:
        return []
    _backup(path, backup_dir)
    add = "".join(f"- {i} [{dt.date.today().isoformat()} · ref {REVIEW_REF[0]}]\n" for i in items)
    m = re.search(rf"^{re.escape(CHECKLIST_HEADING)}\n(.*?)(?=^## |\Z)", text, re.M | re.S)
    if m:
        text = text[:m.end(1)].rstrip("\n") + "\n" + add + ("\n" if m.end(1) < len(text) else "") + text[m.end(1):]
    else:
        text = text.rstrip("\n") + f"\n\n{CHECKLIST_HEADING}\n\n" + add
    path.write_text(text)
    return items


def review_bank(runs: list[str], label: str) -> Path:
    """Checkpoint review of everything logged since the last checkpoint: recurring general patterns become
    accuracy-checklist items (instructions for every model); a report lists the weakest areas and topics."""
    rows: dict[tuple, dict] = {}
    for l in ERROR_BANK.read_text().splitlines() if ERROR_BANK.exists() else []:
        x = json.loads(l)
        if x.get("run") in runs:
            rows[(x.get("kind", "error"), x["run"], x["qid"], str(x.get("error", ""))[:80])] = x   # latest wins
    errs = [x for k, x in rows.items() if k[0] == "error"]
    fb = [x for k, x in rows.items() if k[0] == "feedback"]
    by_area: dict[str, int] = {}
    for x in errs:
        for ar in x["areas"]:
            by_area[ar] = by_area.get(ar, 0) + 1
    marks = [float(x.get("mark") or 0) for x in fb if x.get("mark")]
    retr = [(x["areas"], i.get("problem", "")) for x in fb for i in x.get("issues") or []
            if i.get("kind") in ("retrieval", "routing", "missing_law")]
    common, general = config.path("kb") / "style" / "common.md", config.path("kb") / "style" / "general.md"
    prompt = f"""ERRORS found by the examiner since the last checkpoint ({len(errs)}; area | verdict | error):
{chr(10).join(f"- {','.join(x['areas'])} | {x.get('verdict', '')} | {str(x['error'])[:260]}" for x in errs[:220])}

EXAMINER COMMENTS (what kept answers below 70+):
{chr(10).join(f"- {','.join(x['areas'])} {x.get('mark')}%: {str(x.get('comment', ''))[:300]}" for x in fb[:120])}

RETRIEVAL PROBLEMS (wrong passages, wrong area, law missing from the knowledge base):
{chr(10).join(f"- {','.join(a)}: {str(p)[:240]}" for a, p in retr[:80]) or '(none)'}

CURRENT CHECKLIST FOR ESSAYS AND PROBLEM QUESTIONS:
{chr(10).join(_checklist(common)[1]) or '(none)'}

CURRENT CHECKLIST FOR EVERYDAY ANSWERS:
{chr(10).join(_checklist(general)[1]) or '(none)'}

Find GENERAL patterns: the same kind of mistake in at least 3 answers across at least 2 areas, not already covered
by a checklist item. Ignore errors the verdict marks "marker_wrong". Do not write area-specific law. Return JSON
{{"common": ["new checklist item: one imperative sentence, max 40 words", ...(max 4)],
  "general": ["new everyday-answer item", ...(max 2)],
  "patterns": ["pattern: how often, which areas", ...(max 8)],
  "topics_to_strengthen": ["area: topic where notes need work", ...(max 8)],
  "retrieval_patterns": ["recurring retrieval problem: which areas, what was pulled instead, likely fix (a missing
   note, a routing word, a statute section not found)", ...(max 6)]}}"""
    out = parse_json(ask_model(REVIEW_SYSTEM, prompt, GRADER_MODEL))
    REVIEW_REF[0] = f"eval/reviews/{dt.date.today().isoformat()}-{label.replace(' ', '-')}.md"
    backup = ROOT / "eval" / "reviews" / f"backup-{dt.datetime.now():%Y%m%d-%H%M}"
    added_c = _add_checklist(common, out.get("common") or [], backup)
    added_g = _add_checklist(general, out.get("general") or [], backup)
    wrong = sum(1 for x in errs if x.get("verdict") == "marker_wrong")
    L = [f"# Checkpoint review: {label}", "",
         f"- Runs: {', '.join(runs)}", f"- Answers: {len(fb)}, average mark {sum(marks) / len(marks):.1f}%" if marks else "- Answers: 0",
         f"- Legal errors logged: {len(errs)} (marker wrong on {wrong})", "",
         "## Errors by area", ""] + [f"- {k}: {v}" for k, v in sorted(by_area.items(), key=lambda kv: -kv[1])] + \
        ["", "## Recurring patterns", ""] + [f"- {x}" for x in out.get("patterns") or []] + \
        ["", "## Added to the accuracy checklist", ""] + [f"- common.md: {x}" for x in added_c] + \
        [f"- general.md: {x}" for x in added_g] + (["- nothing new"] if not added_c + added_g else []) + \
        ["", "## Notes to strengthen next", ""] + [f"- {x}" for x in out.get("topics_to_strengthen") or []] + \
        ["", f"## Retrieval gaps ({len(retr)} logged: wrong passages, wrong area, missing law)", ""] + \
        [f"- {x}" for x in out.get("retrieval_patterns") or []] + \
        ["", f"Originals of changed style files: `{backup.relative_to(ROOT)}/`"]
    rep = ROOT / "eval" / "reviews" / f"{dt.date.today().isoformat()}-{label.replace(' ', '-')}.md"
    rep.parent.mkdir(parents=True, exist_ok=True)
    rep.write_text("\n".join(L) + "\n")
    return rep


def _bank_rows(runs: list[str]) -> tuple[list[dict], list[dict]]:
    rows: dict[tuple, dict] = {}
    for l in ERROR_BANK.read_text().splitlines() if ERROR_BANK.exists() else []:
        x = json.loads(l)
        if x.get("run") in runs:
            rows[(x.get("kind", "error"), x["run"], x["qid"], str(x.get("error", ""))[:80])] = x
    return ([x for k, x in rows.items() if k[0] == "error" and x.get("verdict") != "marker_wrong"],
            [x for k, x in rows.items() if k[0] == "feedback"])


async def checkpoint(a, runs: list[str], label: str, prog: dict) -> bool:
    """Measure on NEW questions: most aimed at the law the loop got wrong since the last checkpoint (same rules,
    new facts), the rest spread over other areas. Compared with those areas' marks before. Then learn from it."""
    errs, fb = _bank_rows(runs)
    by_area: dict[str, list] = {}
    for x in errs:
        if len(x["areas"]) == 1:
            by_area.setdefault(x["areas"][0], []).append(x["error"])
    targeted = sorted(by_area, key=lambda k: -len(by_area[k]))[: max(1, a.checkpoint_questions // 3)]
    spread = [x for x in _round_areas(len(areas_list("all"))) if x not in targeted][: a.checkpoint_questions - 2 * len(targeted)]
    types = [t for t in a.types.split(",") if t in TYPES] or list(TYPES)
    qs: list[dict] = []
    for ar in targeted:
        try:
            qs += [dict(q, targeted=True) for q in make_questions(ar, 2, types, by_area[ar])]
        except Exception as e:
            if hit_limit(e):
                return False
    for ar in spread:
        try:
            qs += make_questions(ar, 1, types)
        except Exception as e:
            if hit_limit(e):
                return False
    for i, q in enumerate(qs, 1):
        q["id"] = f"c{i:02d}"
    d = ROOT / "eval" / "checkpoints" / f"{dt.datetime.now():%Y-%m-%d-%H%M}"
    d.mkdir(parents=True, exist_ok=True)
    (d / "questions.yaml").write_text(yaml.safe_dump(qs, sort_keys=False, allow_unicode=True))
    (d / "grades.jsonl").write_text("")
    b = argparse.Namespace(**{**vars(a), "replay": str(d), "only": "", "no_fix": True, "focus": ""})
    out = (await run(b)).parent
    rows = [json.loads(l) for l in (out / "grades.jsonl").read_text().splitlines() if l.strip()]
    before: dict[str, list] = {}
    for x in fb:
        if len(x["areas"]) == 1 and x.get("mark"):
            before.setdefault(x["areas"][0], []).append(float(x["mark"]))
    now: dict[str, list] = {}
    for r in rows:
        now.setdefault(r["q"]["areas"][0], []).append(float(r["grade"].get("mark") or 0))
    avg = lambda v: round(sum(v) / len(v), 1) if v else None
    per_area = {ar: {"before": avg(before.get(ar, [])), "now": avg(v), "targeted": ar in targeted}
                for ar, v in now.items()}
    allm = [m for v in now.values() for m in v]
    prog["checkpoints"].append({"at": prog["marked"], "label": label, "run": out.name, "n": len(rows),
                                "mark": avg(allm), "targeted_mark": avg([m for ar in targeted for m in now.get(ar, [])]),
                                "targeted_before": avg([m for ar in targeted for m in before.get(ar, [])]),
                                "per_area": per_area, "date": dt.date.today().isoformat()})
    PROGRESS.write_text(json.dumps(prog, indent=1))
    L = [f"# Checkpoint {label}: new questions", "",
         f"{len(rows)} new questions ({sum(1 for r in rows if r['q'].get('targeted'))} aimed at the law answered "
         f"wrongly before). Average mark {avg(allm)}%.", "",
         "| Area | Aimed at past errors | Mark before (round answers) | Mark now (new questions) |", "|---|---|---|---|"]
    for ar, v in sorted(per_area.items(), key=lambda kv: not kv[1]["targeted"]):
        L.append(f"| {ar} | {'yes' if v['targeted'] else ''} | {v['before'] if v['before'] is not None else '-'} | {v['now']} |")
    (out / "checkpoint.md").write_text("\n".join(L) + "\n")
    print(f"checkpoint {label}: {len(rows)} new questions, {avg(allm)}%; targeted areas "
          f"{prog['checkpoints'][-1]['targeted_before']}% before -> {prog['checkpoints'][-1]['targeted_mark']}% now")
    if not LIMIT_HIT:
        learn_from(str(out))   # the checkpoint's own errors are feedback too
    return not LIMIT_HIT


def learn_site(limit: int = 30) -> Path | None:
    """Questions people asked on the website (not the auto-tester) are marked by Opus and learned from like a
    training round: every error logged, notes fixed, warnings and rules added."""
    prog = json.loads(PROGRESS.read_text()) if PROGRESS.exists() else {"marked": 0, "checkpoints": []}
    done = set(prog.get("site_done", []))
    todo = []
    for fp in sorted((config.path("debug") / "logs").glob("*.jsonl")):
        for l in fp.read_text(errors="ignore").splitlines():
            try:
                t = json.loads(l)
            except Exception:
                continue
            if (t.get("user_id") in ("auto-tester", None) or t.get("trace_id") in done or not t.get("answer")
                    or t.get("intent") == "out_of_scope" or len(str(t.get("question", ""))) < 12):
                continue
            todo.append(t)
    todo = todo[-limit:]
    if not todo:
        return None
    out = config.path("review_queue") / "training_runs" / f"{dt.datetime.now():%Y-%m-%d-%H%M}-site"
    out.mkdir(parents=True, exist_ok=True)
    rows, qs = [], []
    for i, t in enumerate(todo, 1):
        topics = [x for x in (t.get("topics") or []) if x] or ["general-law"]
        q = {"id": f"s{i:02d}", "areas": topics[:1], "type": t.get("intent") if t.get("intent") in TYPES else "general",
             "difficulty": "user", "question": t["question"], "expected": []}
        try:
            g = grade(q, {"answer": t["answer"], "trace": t})
        except Exception as e:
            if hit_limit(e):
                break
            continue
        qs.append(q)
        rows.append({"q": q, "trace_id": t["trace_id"], "bot_model": (t.get("provider_info") or {}).get("model", ""),
                     "routed": t.get("topics"), "mode": t.get("answer_mode"), "grade": g})
        done.add(t["trace_id"])
        print(f"site question {q['id']}: {g['overall']:.0f}/5 ({g.get('mark')}%) — {t['question'][:80]}")
    (out / "questions.yaml").write_text(yaml.safe_dump(qs, sort_keys=False, allow_unicode=True))
    (out / "grades.jsonl").write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows))
    prog["site_done"] = sorted(done)
    PROGRESS.parent.mkdir(parents=True, exist_ok=True)
    PROGRESS.write_text(json.dumps(prog, indent=1))
    if rows and not LIMIT_HIT:
        learn_from(str(out))
    return out


async def cycle(a) -> None:
    """Automated loop: rounds of new questions (ask, mark, log every error, fix notes, write rules, re-check).
    Every --checkpoint marked questions: review the logged errors (new checklist items), then measure on NEW
    questions aimed at the law that was answered wrongly, and learn from those too."""
    prog = json.loads(PROGRESS.read_text()) if PROGRESS.exists() else {"marked": 0, "checkpoints": []}
    prog.setdefault("runs_since_checkpoint", [])
    target = prog["marked"] + a.cycle
    while prog["marked"] < target and not LIMIT_HIT:
        site = learn_site()   # questions asked on the website since the last round are marked and learned first
        if site:
            prog = json.loads(PROGRESS.read_text())
            prog.setdefault("runs_since_checkpoint", []).append(site.name)
            PROGRESS.write_text(json.dumps(prog, indent=1))
        areas = _round_areas(a.round_areas)
        r = argparse.Namespace(**{**vars(a), "areas": ",".join(areas), "replay": "", "only": "", "focus": "",
                                  "no_fix": False})
        out = (await run(r)).parent
        n, avg, mark = _avg(out)
        before = prog["marked"]
        prog["marked"] += n
        prog["runs_since_checkpoint"].append(out.name)
        PROGRESS.write_text(json.dumps(prog, indent=1))
        print(f"round {out.name}: {n} questions, {avg:.2f}/5, {mark:.1f}% — total marked {prog['marked']}")
        if n == 0:
            break
        if prog["marked"] // a.checkpoint > before // a.checkpoint:
            label = f"after {prog['marked']}"
            try:
                rep = review_bank(prog["runs_since_checkpoint"], label)
                print(f"review: {rep.relative_to(ROOT)}")
            except Exception as e:
                print(f"review failed: {e}")
                if hit_limit(e):
                    break
            ok = await checkpoint(a, prog["runs_since_checkpoint"], label, prog)
            prog["runs_since_checkpoint"] = []
            PROGRESS.write_text(json.dumps(prog, indent=1))
            if not ok:
                break
    if LIMIT_HIT:
        print(f"stopped: {LIMIT_HIT}. Re-run the same command after the reset; progress is kept in {PROGRESS.name}.")


def main():
    global GRADER_MODEL
    ap = argparse.ArgumentParser(description="Automated test-and-improve loop (Sonnet questions, Opus marker).")
    ap.add_argument("--areas", default="all", help="comma-separated area slugs, or 'all'")
    ap.add_argument("--replay", default="", help="ask the same questions as an earlier run (its folder)")
    ap.add_argument("--cycle", type=int, default=0, help="automated loop: mark this many new questions in rounds, "
                    "learning after each round; every --checkpoint questions: review + new targeted questions")
    ap.add_argument("--max-rechecks", type=int, default=5, help="re-ask at most this many questions after a round's "
                    "changes (0 = all)")
    ap.add_argument("--checkpoint", type=int, default=100, help="review + test on new questions every N marked questions")
    ap.add_argument("--checkpoint-questions", type=int, default=20, help="new questions asked at each checkpoint")
    ap.add_argument("--round-areas", type=int, default=6, help="areas per round in --cycle (half weakest, half least tested)")
    ap.add_argument("--learn-from", default="", help="an earlier run folder: turn its marked errors into note fixes "
                    "and common-error lines (no questions asked)")
    ap.add_argument("--from-site", action="store_true", help="mark the questions asked on the website and learn "
                    "from them (the cycle does this before every round)")
    ap.add_argument("--no-rules", action="store_true", help="with --learn-from: notes only (the run already wrote its rules)")
    ap.add_argument("--only", default="", help="with --replay: only these question ids, e.g. q05,q13")
    ap.add_argument("--per-area", type=int, default=3, help="questions per area")
    ap.add_argument("--cross", type=int, default=0, help="extra questions spanning 2-3 of the areas")
    ap.add_argument("--types", default="problem_question,essay,general", help="answer types to test")
    ap.add_argument("--bot-model", default=TESTER_MODEL, help="model the bot answers with (default sonnet)")
    ap.add_argument("--focus", default="", help="comma-separated earlier run folders: test only their weakest areas")
    ap.add_argument("--focus-n", type=int, default=7, help="how many weakest areas --focus picks (default 7)")
    ap.add_argument("--grader-model", default=GRADER_MODEL, help="model that marks answers and writes rules (default opus)")
    ap.add_argument("--no-fix", action="store_true", help="test and log only; change nothing")
    ap.add_argument("--no-download", action="store_true", help="do not download missing law")
    a = ap.parse_args()
    GRADER_MODEL = a.grader_model
    if a.learn_from:
        learn_from(a.learn_from, rules=not a.no_rules)
        return
    if a.from_site:
        print(learn_site() or "no new website questions")
        return
    if a.cycle:
        asyncio.run(cycle(a))
        return
    asyncio.run(run(a))


if __name__ == "__main__":
    main()
