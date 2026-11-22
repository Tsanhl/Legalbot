"""Give every shared primary source (general-law/) ONE area of law.

  python -m legalbot.ingest.sort_sources            propose: writes kb/source_topics.yaml (review it)
  python -m legalbot.ingest.sort_sources --apply    move the files into kb/topics/<topic>/raw/<authority>/

Signals, strongest first:
  1. the subject folder in the Law folder ("As Enacted/Land law" -> land-law)
  2. where the authority is USED: which module's notes and materials mention its name most (BM25 over the KB)
  3. the module's aliases in the title
Files with no clear winner go to `general-law` (a small, visible "unsorted" folder) instead of guessing.
kb/source_topics.yaml is read by the ingest, so future runs file them the same way; edit it to correct any entry.
"""
from __future__ import annotations

import argparse
import re
from collections import Counter
from pathlib import Path

import yaml

from .. import config

KB = config.path("kb")
MAP = KB / "source_topics.yaml"
SHARED = "general-law"   # unsorted primary sources land here; this sorts them into one area each

SUBJECT_FOLDERS = {  # "Official Legislation/United Kingdom/As Enacted/<subject>"
    "Civil litigation law": "civil-procedure", "Commercial law": "commercial-law", "Company law": "business-law",
    "Constitutional law": "constitutional-law", "Consumer law": "commercial-law", "Contract law": "contract-law",
    "Criminal evidence law": "criminal-law", "Criminal law": "criminal-law", "Employment law": "employment-law",
    "Family law": "family-law", "Financial services law": "financial-services-law",
    "Intellectual property law": "intellectual-property", "Land law": "land-law",
    "Professional negligence law": "tort-law", "Tort law": "tort-law", "Trusts law": "trusts-law",
    "Wills and succession law": "wills-succession",
}
NEW_TOPICS = {
    "civil-procedure": ("Civil Procedure and Litigation", ["civil procedure", "limitation", "litigation", "cpr"]),
    "constitutional-law": ("Constitutional and Public Law", ["constitutional", "judicial review", "human rights act", "parliament"]),
    "employment-law": ("Employment Law", ["employment", "employee", "employer", "minimum wage", "unfair dismissal", "worker", "wages"]),
    "family-law": ("Family Law", ["family law", "divorce", "children act", "marriage", "civil partnership", "child arrangements"]),
    "financial-services-law": ("Financial Services Law", ["financial services", "fca", "fsma", "payment services", "banking"]),
    "intellectual-property": ("Intellectual Property", ["copyright", "patent", "trade mark", "trademark", "intellectual property"]),
    "wills-succession": ("Wills and Succession", ["wills", "succession", "intestacy", "inheritance", "probate"]),
    "tax-law": ("Tax Law", ["income tax", "corporation tax", "taxation", "finance act", "hmrc", "revenue and customs", "vat"]),
    "general-law": ("General / Unsorted Primary Sources", []),
}


# What area of law a title belongs to beats where it happened to be used (+5 votes)
TITLE_RULES = [
    (r"(?:^|, )R\.? v\b|^R v |\bv R$|Criminal|Offences|Sentencing|Police|Theft|Fraud Act|Sexual Offences|Homicide|"
     r"Road Traffic|Modern Slavery|Misuse of Drugs|Serious Crime|Firearms", "criminal-law"),
    (r"\bCompan(?:y|ies)\b|Partnership|Insolvency|Corporate|Directors", "business-law"),
    (r"Carriage of Goods|Bills of Lading|Marine Insurance|Insurance Act|Sale of Goods|Supply of Goods|Consumer|"
     r"Factors Act|Bills of Exchange|Hire[- ]Purchase", "commercial-law"),
    (r"Pension|Occupational|Retirement", "pensions-law"),
    (r"Land Registration|Law of Property|Landlord|Tenant|Leasehold|Housing|Planning|Commonhold|Land Charges|Prescription",
     "land-law"),
    (r"Trustee|Trusts of Land|Charities|Variation of Trusts|Perpetuities", "trusts-law"),
    (r"Mental Capacity|Mental Health|Human Tissue|Abortion|Human Fertilisation|Suicide|NHS|Medical", "law-and-medicine"),
    (r"Competition|Enterprise Act|Digital Markets", "competition-law"),
    (r"Data Protection|GDPR|2016/679|Artificial Intelligence|Online Safety|Privacy", "ai-data-protection"),
    (r"Arbitration|Mediation", "international-commercial-mediation"),
    (r"Private International|Civil Jurisdiction|Rome I|Rome II|Brussels|Foreign Judgments|Recognition of", "private-international-law"),
    (r"Income Tax|Corporation Tax|Finance Act|Taxation|Revenue and Customs|Value Added Tax", "tax-law"),
    (r"Employment|Equal Pay|Minimum Wage|Working Time|Trade Union", "employment-law"),
    (r"Children Act|Matrimonial|Marriage|Civil Partnership|Family Law|Adoption", "family-law"),
    (r"Copyright|Patents?|Trade Marks?|Designs", "intellectual-property"),
    (r"Wills Act|Inheritance|Administration of Estates|Intestate|Succession", "wills-succession"),
    (r"Human Rights Act|Constitutional|Senior Courts|Supreme Court Act|Parliament", "constitutional-law"),
    (r"Limitation Act|Civil Procedure|Courts and Legal Services", "civil-procedure"),
    (r"Financial Services|Payment Services|Banking Act|Financial Conduct", "financial-services-law"),
    (r"Defamation|Occupiers|Liability Act|Negligence|Compensation Act|Fatal Accidents|Contributory|Animals Act", "tort-law"),
    (r"Contracts \(Rights of Third Parties\)|Misrepresentation|Unfair Contract|Law Reform \(Frustrated|Construction Contracts",
     "contract-law"),
]


def _front(t: str) -> dict:
    try:
        return yaml.safe_load(t.split("---")[1]) or {}
    except Exception:
        return {}


def propose() -> dict:
    from ..retrieval.engine import RetrievalEngine
    eng = RetrievalEngine()
    eng.load()
    manifests = eng.manifests
    out = {}
    files = sorted((KB / "topics" / SHARED / "raw").rglob("*.md"))
    # meaning signal: each module's notes -> centroid vector; each document -> mean of its chunk vectors
    import numpy as np
    vec = eng.vector
    ids, mat = vec._note_matrix()
    cent = {}
    for t in {vec.chunks[int(i)]["topic"] for i in ids}:
        sel = [j for j, i in enumerate(ids) if vec.chunks[int(i)]["topic"] == t]
        c = mat[sel].mean(axis=0)
        cent[t] = c / (np.linalg.norm(c) + 1e-9)
    by_file: dict[str, list[int]] = {}
    for i, ch in enumerate(vec.chunks):
        if ch["topic"] == SHARED:
            by_file.setdefault(ch["source"].split("#")[0], []).append(i)

    def meaning(file_id: str) -> list[tuple[str, float]]:
        cs = by_file.get(file_id, [])[:40]
        if not cs or not cent:
            return []
        v = np.vstack([vec.index.reconstruct(int(i)) for i in cs]).mean(axis=0)
        v = v / (np.linalg.norm(v) + 1e-9)
        return sorted(((t, float(v @ c)) for t, c in cent.items()), key=lambda x: -x[1])
    for p in files:
        fm = _front(p.read_text(errors="ignore"))
        orig, title = str(fm.get("original", "")), str(fm.get("title") or p.stem)
        topic, why = None, ""
        m = re.search(r"As Enacted/([^/]+)/", orig)
        if m and m.group(1) in SUBJECT_FOLDERS:
            topic, why = SUBJECT_FOLDERS[m.group(1)], f"subject folder '{m.group(1)}'"
        if not topic:
            # where is it used? search its name, count which modules the top hits belong to (excluding the shared pile)
            name = re.sub(r"\s*[\(\[]?\b(?:19|20)\d\d\b.*$", "", title)[:90] or title
            hits, _ = eng.bm25.search(f"{title[:120]}", 40, None)
            votes = Counter()
            for rank, h in enumerate(hits):
                s = eng.sections[h["idx"]]
                if s.topic in (SHARED, "general-law"):
                    continue
                votes[s.topic] += (2.0 if s.kind == "note" else 1.0) / (1 + rank / 10)
            low = title.lower()
            for slug, mf in manifests.items():
                if slug == SHARED:
                    continue
                if any(re.search(r"\b" + re.escape(str(a).lower()) + r"\b", low) for a in mf.get("aliases", []) if len(str(a)) > 4):
                    votes[slug] += 1.5
            for slug, (_, aliases) in NEW_TOPICS.items():
                if any(re.search(r"\b" + re.escape(a) + r"\b", low) for a in aliases):
                    votes[slug] += 2.0
            for pat, slug in TITLE_RULES:
                if re.search(pat, title) and not re.search(r"\(on the application of\)", title, re.I):
                    votes[slug] += 5.0
                    break
            file_id = f"{SHARED}/raw/{p.relative_to(KB / 'topics' / SHARED / 'raw').as_posix()}"
            mm = meaning(file_id)
            if mm:   # content closest to a module's notes: up to +3 votes, scaled by the margin over the runner-up
                (t1, s1), (t2, s2) = mm[0], mm[1]
                votes[t1] += 1.0 + min(2.0, (s1 - s2) * 40)
            if votes:
                (best, sb), *rest = votes.most_common(2) + [(None, 0)]
                second = rest[0][1] if rest else 0
                if sb >= 1.0 and sb > 1.15 * (second or 0.01):
                    topic, why = best, f"{best} ({sb:.1f} v {second:.1f}; meaning: {mm[0][0] if mm else '-'})"
                else:
                    why = "unclear: " + ", ".join(f"{k} {v:.1f}" for k, v in votes.most_common(3))
        out[p.relative_to(KB / "topics" / SHARED / "raw").as_posix()] = {
            "title": title[:120], "topic": topic or "general-law", "why": why or "no signal", "original": orig}
    return out


def apply(mapping: dict) -> tuple[int, Counter]:
    moved, per = 0, Counter()
    for rel, d in mapping.items():
        dst = KB / "topics" / d["topic"] / "raw" / rel
        here = [p for p in KB.glob(f"topics/*/raw/{rel}") if p != dst]   # wherever it is now
        if not here:
            continue
        src = here[0]
        dst.parent.mkdir(parents=True, exist_ok=True)
        t = src.read_text(errors="ignore")
        t = re.sub(r"^topic: .*$", f"topic: {d['topic']}", t, count=1, flags=re.M)
        dst.write_text(t)
        src.unlink()
        moved += 1
        per[d["topic"]] += 1
    return moved, per


def ensure_topics(topics: set[str]):
    """Create manifest + topic_map entries for any new area of law."""
    tm_path = KB / "topic_map.yaml"
    tm_text = tm_path.read_text()
    tm = yaml.safe_load(tm_text)
    add = []
    for slug in sorted(topics):
        if slug in tm["topics"]:
            continue
        name, aliases = NEW_TOPICS.get(slug, (slug.replace("-", " ").title(), []))
        add.append(f"  {slug}:\n    name: {name}\n    folders: []\n    aliases: [{', '.join(aliases)}]\n    jurisdiction: [UK]\n")
        mdir = KB / "topics" / slug
        mdir.mkdir(parents=True, exist_ok=True)
        if not (mdir / "manifest.yaml").exists():
            (mdir / "manifest.yaml").write_text(yaml.safe_dump(
                {"slug": slug, "name": name, "aliases": aliases, "jurisdiction": ["UK"], "law_folders": [],
                 "always_search": False}, sort_keys=False, allow_unicode=True))
    if add:
        i = tm_text.index("\n# Marked scripts")
        tm_path.write_text(tm_text[:i] + "\n" + "".join(add) + tm_text[i:])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    if not a.apply:
        old = (yaml.safe_load(MAP.read_text()) or {}) if MAP.exists() else {}
        mp = {**old, **propose()}   # keep earlier decisions; add / refresh the newly unsorted ones
        MAP.write_text("# Which area of law each shared primary source belongs to. Edit `topic` to correct one.\n"
                       + yaml.safe_dump(mp, sort_keys=True, allow_unicode=True, width=140))
        c = Counter(v["topic"] for v in mp.values())
        print(f"proposed {len(mp)} files -> {MAP.relative_to(config.ROOT)}")
        for k, v in c.most_common():
            print(f"  {v:4}  {k}")
        return
    mp = yaml.safe_load(MAP.read_text())
    ensure_topics({v["topic"] for v in mp.values()})
    n, per = apply(mp)
    print(f"moved {n} files"); [print(f"  {v:4}  {k}") for k, v in per.most_common()]


if __name__ == "__main__":
    main()
