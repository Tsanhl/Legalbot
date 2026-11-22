"""Training-loop helpers (no models, no server): where lessons are written and how they are traced back."""
import json
from pathlib import Path

import legalbot.train as T
from legalbot.fix_gaps import _quote_title, judgment_matches
from legalbot.query.processor import route_topics


def _sandbox(monkeypatch, tmp_path):
    monkeypatch.setattr(T, "_backup", lambda p, b: None)
    monkeypatch.setattr(T, "ERROR_BANK", tmp_path / "error_bank.jsonl")


def test_common_error_line_is_tagged_and_deduplicated(monkeypatch, tmp_path):
    _sandbox(monkeypatch, tmp_path)
    note = tmp_path / "note.md"
    note.write_text("---\ntitle: x\n---\n# X\n\n## Applying it\nText.\n")
    assert T._add_trap(note, "Do not attach the s 183 offence to s 177.", tmp_path, "run1/q05#0")
    assert not T._add_trap(note, "Do not attach the s 183 offence to s 177.", tmp_path, "run1/q05#0")
    text = note.read_text()
    assert "## Common errors to avoid" in text and text.count("s 183 offence") == 1
    assert "ref run1/q05#0]" in text


def test_checklist_items_go_into_the_checklist_section(monkeypatch, tmp_path):
    _sandbox(monkeypatch, tmp_path)
    f = tmp_path / "common.md"
    f.write_text(f"# Rules\n\n{T.CHECKLIST_HEADING}\n\n- one\n\n## Later section\n- other\n")
    T.REVIEW_REF[0] = "eval/reviews/x.md"
    assert T._add_checklist(f, ["two"], tmp_path) == ["two"]
    text = f.read_text()
    section = text.split(T.CHECKLIST_HEADING)[1].split("## Later section")[0]
    assert "- two [" in section and "ref eval/reviews/x.md" in section
    assert text.index("- two") < text.index("## Later section")


def test_error_bank_records_errors_and_feedback_with_refs(monkeypatch, tmp_path):
    _sandbox(monkeypatch, tmp_path)
    r = {"q": {"id": "q01", "areas": ["tax-law"], "type": "problem_question", "question": "Q?"},
         "grade": {"overall": 3, "mark": 62, "comment": "c", "errors": ["a -> b", "c -> d"],
                   "issues": [{"kind": "retrieval", "problem": "wrong passages"}]}, "bot_model": "sonnet"}
    T.bank_errors("run9", r, {1: {"verdict": "trap", "action": "common error added", "file": "kb/x.md"}})
    rows = [json.loads(l) for l in T.ERROR_BANK.read_text().splitlines()]
    assert [x["kind"] for x in rows] == ["feedback", "error", "error"]
    assert rows[2]["ref"] == "run9/q01#1" and rows[2]["verdict"] == "trap" and rows[1]["verdict"] == "unreviewed"
    assert rows[0]["issues"][0]["kind"] == "retrieval"


def test_rules_carry_a_ref(monkeypatch, tmp_path):
    monkeypatch.setattr(T, "ROOT", tmp_path)
    f = tmp_path / "kb" / "style" / "essay.md"
    f.parent.mkdir(parents=True)
    f.write_text("# Essay\n")
    T.RULE_REF[0] = "run1/q02,q03"
    T.append_rules(f, ["Answer the question set."], tmp_path / "backup")
    T.RULE_REF[0] = ""
    assert "ref run1/q02,q03]" in f.read_text()


def test_wrong_judgment_download_is_caught():
    tna = '<FRBRname value="{}"/>'
    assert not judgment_matches("Ilott v Mitson", tna.format("R v Secretary of State for the Home Department"))
    assert judgment_matches("Ilott v Mitson", tna.format("Ilott v The Blue Cross and others"))
    assert judgment_matches("R v Oye", tna.format("SO v The Crown"))          # anonymised: cannot compare
    assert judgment_matches("Any v Case", "<html>no TNA name</html>")


def test_case_note_titles_with_colons_are_quoted():
    md = "---\ntitle: Re R (A Minor) (Wardship: Consent) [1992] Fam 11\ntopic: x\n---\n# Body: text\n"
    out = _quote_title(md)
    assert 'title: "Re R (A Minor) (Wardship: Consent) [1992] Fam 11"' in out and "# Body: text" in out


def test_routing_matches_plurals():
    m = {"business-law": {"name": "Business Law", "aliases": ["director", "shareholder"]},
         "contract-law": {"name": "Contract Law", "aliases": ["contract"]}}
    r = route_topics("The directors and shareholders signed a contract", m)
    assert r[0] == "business-law"


def test_lessons_map_exists_and_names_every_place():
    text = (T.ROOT / "kb" / "LESSONS.md").read_text()
    for place in ("kb/style/common.md", "kb/topics/<area>/style.md", "## Common errors to avoid",
                  "eval/error_bank.jsonl", "eval/reviews/"):
        assert place in text
