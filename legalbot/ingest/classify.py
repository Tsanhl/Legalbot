"""Classify each original file: role (what we do with it) + authority (what kind of source it is).

role:
  evidence   -> kb/topics/<slug>/raw/<authority>/   (indexed, citable)
  feedback   -> kb/feedback/                         (marker feedback; shapes answer style, not indexed)
  question   -> kb/questions/                        (assessment questions; for eval set + style)
  guidance   -> kb/guidance/                         (OSCOLA, essay tips, exam technique)
  own_work   -> skipped (your drafts / answers must not become evidence) - listed in review report
  admin      -> skipped (receipts, submission info)

Rules are filename + folder heuristics, printed with a reason so the review report can show why.
"""
from __future__ import annotations

import re
from pathlib import PurePosixPath

R = lambda p: re.compile(p, re.I)  # noqa: E731


def _personal() -> tuple[str, str]:
    """Your name(s) and student ID come from ~/.config/legalbot/pii.yaml (outside the project, never uploaded)."""
    try:
        import yaml
        from .. import config
        import os
        from pathlib import Path
        p = Path(os.environ.get("LEGALBOT_PII", Path.home() / ".config" / "legalbot" / "pii.yaml"))
        rules = (yaml.safe_load(p.read_text()) or {}).get("pii") or []
    except Exception:
        rules = []
    ids = [re.escape(r["pattern"].lower()) for r in rules if r.get("replace") == "[student-id]"]
    names = [r"[\s_.-]+".join(map(re.escape, r["pattern"].lower().split())) for r in rules if r.get("replace") == "[student]"]
    return "|".join(ids + [r"\[student-id\]"]), "|".join(names + [r"\[student\]"])


_IDS, _NAMES = _personal()

ADMIN = R(r"receipt|similarity-|turnitin|submission information|ethics form|deadlines and core|module fair|induction")
FEEDBACK = R(r"feedback|feedforward|gen feedback|general feedback")
OWN_FEEDBACK_REWRITE = R(r"refined|base[d]? on feedback")
QUESTION = R(r"question|^exam[_ ]|[_ ]exam[_ ]|exam_|essay title|essay questions|choice of .* question|^\d+ exam")
GUIDANCE = R(r"model answer|oscola|checklist|essay writing|exam skills|examination issues|feedback lecture|writing tips|"
             r"how to answer|marking criteria|assessment criteria")
DRAFT_FOLDER = R(r"(^|/)(previous version|drafts?|old work|older|old versions?)(/|$)")
ASSESSMENT_FOLDER = R(r"summative|formative|\bexams?\b|final dissertation|dissertation/latest|essay(/|$)")
OWN_NAME = R(r"\b(v|ver|version)\s?\.?\d|draft|\(all\)|\bq\d|\bfinal\b|\bbib\b|bibliography|\bms\b|- ms|"
             r"amended|marked|refined|^ai[-, ]|\bai\b-|" + _IDS + r"|my answer|initial|"
             r"^essay|^formative\b|^summative\b|part [ab] v\d|content part|chapter \d")
STUDENT_NAME = R(_NAMES)
VERSIONED = R(r"\bv(er)?\s?\d|_v\d")
STUDENT_SCRIPT = R(r"(" + _IDS + r").*law\d{4}")

CASE = R(r"\sv\.?\s|\[(19|20)\d\d\]|\b(ewca|ewhc|uksc|ukhl|ukpc|ecli|curia|ecr)\b|case [ct]-\d|^case\b|judgment")
LEGISLATION = R(r"\bact\b(\s\d{4})?|regulations?\b|directive|\btreaty\b|\btfeu\b|\bteu\b|convention\b|statutory|"
                r"\bsi \d|\brules\b|\border \d{4}|\bcode of practice|charter")
JOURNAL = R("[“\"'‘].{15,}[”\"'’]|" r"\bclj\b|\bmlr\b|\bojls\b|journal|review|\bl\.?q\.?r\b|yearbook|quarterly|cml rev|el rev|\(\d{4}\)\s?\d+|law rev\b|\bconv\b|\bjbl\b|\blmclq\b|\bcrim lr\b|\bpl\b \d|law review"
            r"\bstud(ies|y)\b|harvard|cambridge law|modern law|oxford journal|ssrn|working paper|blog")
TEXTBOOK = R(r"law trove|edition|\bedn\b|university press|\boup\b|informa|law concentrate|\(eds?\.?\)|hart|routledge|"
             r"sweet|textbook|handbook of|chapter|cheshire|briggs|hudson|pollard|weir|faull")
LECTURE = R(r"lecture|seminar|slides|tutorial|topic \d|handout|week \d|^l\d+|notes|summary|unit \d|reading list|"
            r"handbook|workshop|revision|recap")


def classify(rel: str, ext: str) -> tuple[str, str, str]:
    """Return (role, authority, reason). `rel` is the path relative to the Law folder."""
    p = PurePosixPath(rel)
    name, folder = p.stem, str(p.parent)
    low = rel.lower()

    if ADMIN.search(name):
        return "admin", "", "admin filename"
    if GUIDANCE.search(name) or folder.lower().startswith("assessment guidance"):
        return "guidance", "guidance", "guidance filename/folder"
    if FEEDBACK.search(name):
        if OWN_FEEDBACK_REWRITE.search(name):
            return "own_work", "", "own rewrite after feedback"
        return "feedback", "feedback", "feedback filename"
    if STUDENT_SCRIPT.search(name) and ext == ".pdf" and not name.lower().startswith(("ai-", "ai ")):
        return "student_script", "feedback", "your script: feedback if the PDF has marker annotations, else own work"
    if DRAFT_FOLDER.search(folder):
        return "own_work", "", "draft/previous-version folder"
    if STUDENT_NAME.search(name):
        return "own_work", "", "your name in filename"
    if QUESTION.search(name) and not CASE.search(name) and not JOURNAL.search(name) and not VERSIONED.search(name):
        return "question", "question", "question/exam paper filename"

    in_assessment = bool(ASSESSMENT_FOLDER.search(folder))
    authority = source_authority(name, folder, ext)
    if in_assessment:
        # research material inside assessment folders is kept; your own answer files are not
        if ext in (".docx", ".doc") and not CITED.search(name):
            return "own_work", "", "docx in assessment folder without a citation-like title"
        if OWN_NAME.search(name):
            return "own_work", "", "own-work filename in assessment folder"
    elif OWN_NAME.search(name) and ext in (".docx", ".doc") and authority in ("secondary",):
        return "own_work", "", "draft-like docx filename"
    return "evidence", authority, f"authority={authority}"


CITED = R("[\u201c\"'\u2018].{15,}[\u201d\"'\u2019]|\\(\\d{4}\\)|\\[\\d{4}\\]|\\sv\\.?\\s|case [ct]-|\\bact \\d{4}")
JOURNAL_FIRST = R("[\u201c\u2018].{15,}[\u201d\u2019]|\\b(conv|jbl|clj|mlr|lqr|ojls|cml rev|el rev|crim lr)\\b|law journal|law review|in (the )?[a-z ]*(law|legal) (review|quarterly|journal|studies)")


COMMENTARY = R(r"overview|framework|step towards|brave new|defences|blaming|consultation|response|analysis|critique|"
                r"implications|towards?|reform|perspective|lessons|guide to|introduction to|explained|law firm|"
                r"commentary|report|- |: ")


def source_authority(name: str, folder: str, ext: str) -> str:
    f = folder.lower()
    if "judgment" in f:
        return "case_law"
    if JOURNAL_FIRST.search(name):
        return "journal"
    if ext == ".xml" or "/legislation" in f or "regulations" in f.split("/")[-1]:
        return "legislation"
    if "judgments" in f or "cases" in f.split("/")[-1]:
        return "case_law"
    if "journal" in f:
        return "journal"
    if CASE.search(name) or (len(name) < 40 and re.search(r"\bcase\b", name, re.I)):
        return "case_law"
    if LEGISLATION.search(name) and not JOURNAL.search(name) and len(name) <= 70 and not COMMENTARY.search(name):
        return "legislation"
    if COMMENTARY.search(name) and LEGISLATION.search(name):
        return "secondary"
    if JOURNAL.search(name):
        return "journal"
    if TEXTBOOK.search(name) or TEXTBOOK.search(folder.split("/")[-1]):
        return "textbook"
    if ext in (".pptx", ".ppt") or LECTURE.search(name) or LECTURE.search(folder.split("/")[-1]):
        return "lecture"
    return "secondary"
