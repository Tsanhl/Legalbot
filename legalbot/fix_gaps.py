"""Fix knowledge gaps with Claude: find missing cases/Acts in official sources, download, index, report.

  python -m legalbot.fix_gaps            run on every open item in improvement/knowledge_gaps/
  python -m legalbot.fix_gaps --dry-run  only ask Claude for sources; download nothing

How it works (and why it is safe):
  1. Collect open gap items (missing authority / no answer) from improvement/knowledge_gaps/<date>/.
  2. Claude Code (`claude -p`, Sonnet, your Claude login) may only search the web and open pages on
     official sites. It returns a JSON list of the official URL for each missing authority. It cannot
     write files or run commands.
  3. This script downloads each URL itself (legislation.gov.uk / Find Case Law XML, EUR-Lex HTML) and
     extracts the real text with the same extractors as the Law folder; files land in
     kb/topics/<topic>/raw/<case_law|legislation>/ with `original: 'downloaded: <url>'`.
  4. Index rebuild (only new text is embedded); report in improvement/gap_fixes/<date>-<time>.md;
     each gap item is marked `status: fixed` or `status: needs-manual` with the reason.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import shutil
import subprocess
import tempfile
import urllib.error
import urllib.request
from pathlib import Path

import yaml

from . import config

OFFICIAL = ["legislation.gov.uk", "caselaw.nationalarchives.gov.uk", "eur-lex.europa.eu", "curia.europa.eu",
            "www.bailii.org", "www.gov.uk", "www.supremecourt.uk", "hudoc.echr.coe.int", "publications.europa.eu"]
ROOT = config.ROOT
MODEL = "opus"       # finds official sources and writes case notes
MAX_NOTES = 12       # case notes written per run when no official copy can be downloaded
BATCH = 20           # gap items per Claude request
IMP = config.path("review_queue")
STATUS = IMP / "gap_fixes" / "status.json"


def _status(**kw):
    STATUS.parent.mkdir(parents=True, exist_ok=True)
    cur = json.loads(STATUS.read_text()) if STATUS.exists() else {}
    cur.update(kw, updated=dt.datetime.now().isoformat(timespec="seconds"))
    STATUS.write_text(json.dumps(cur, indent=2))


def open_gaps() -> list[dict]:
    items = []
    for p in sorted((IMP / "knowledge_gaps").glob("*/*.md")):
        t = p.read_text(errors="ignore")
        if not t.startswith("status: open"):
            continue
        reason = re.search(r"^## Reason: (.*)$", t, re.M)
        q = re.search(r"## Question\n\n(.*?)\n\n## ", t, re.S)
        topics = re.search(r"^topics: (.*)$", t, re.M)
        details = re.findall(r"^- (?!\[S\d)(.+)$", t.split("## Sources it had")[0], re.M)
        items.append({"file": str(p.relative_to(ROOT)), "reason": reason.group(1) if reason else "",
                      "question": (q.group(1) if q else "").strip()[:600],
                      "topics": [x.strip() for x in (topics.group(1) if topics else "").split(",") if x.strip() not in ("", "-")],
                      "missing": details[:15]})
    return items


PROMPT = """You help maintain a UK/EU law study knowledge base. For each item below, the system could not find
some primary authority. Find the OFFICIAL source for each missing case, Act or instrument.

Rules:
- Only use these sites: {sites}.
- Prefer machine-readable URLs:
  * UK Acts/SIs: https://www.legislation.gov.uk/<type>/<year>/<number>/data.xml (latest consolidated version)
  * England & Wales / UK judgments: https://caselaw.nationalarchives.gov.uk/<court>/<year>/<num>/data.xml
  * EU judgments/legislation: https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:<celex>
- Verify each URL exists by opening it. Never guess a citation; if you cannot find an official copy, say so.
- Skip vague items that are not a specific authority (e.g. "more academic views", or sentences copied from an
  answer). Only list a case, Act, SI or EU instrument that a good answer to the item's question genuinely needs.
- Topic slug must be one of: {topics}.

Reply with ONLY a JSON array, each element:
{{"item": "<item file>", "authority": "<name as it should be titled>", "kind": "case_law|legislation",
  "topic": "<slug>", "citation": "<neutral or official citation>", "url": "<official url or empty>",
  "note": "<why not found / anything to check>"}}

Items:
{items}
"""


def titles_for(topics: set[str], limit: int = 30000) -> str:
    """Titles of the cases, Acts and notes already held in these areas (so Claude skips them)."""
    from .index import IDENTIFIERS
    out = []
    for t in sorted(topics):
        for p in sorted((config.path("kb") / "topics" / t).glob("**/*.md")):
            if p.name == "style.md" or not ({"case_law", "legislation", "notes"} & set(p.parts)):
                continue   # authorities and notes only (never course material)
            m = re.search(r"^title:\s*['\"]?(.+?)['\"]?\s*$", p.read_text(errors="ignore")[:600], re.M)
            title = m.group(1) if m else p.stem
            if not IDENTIFIERS.search(title) and not re.search(r"tutorial|handout|lecture|seminar", title, re.I):
                out.append(f"{t}: {title}")
    return "\n".join(out)[:limit]


def ask_claude(items: list[dict]) -> list[dict]:
    exe = shutil.which("claude") or str(Path.home() / ".local/bin/claude")
    topics = sorted(p.parent.name for p in (config.path("kb") / "topics").glob("*/manifest.yaml"))
    held = titles_for({t for it in items for t in it.get("topics") or []})
    prompt = PROMPT.format(sites=", ".join(OFFICIAL), topics=", ".join(topics),
                           items=json.dumps(items, indent=1, ensure_ascii=False)) + (
        "\nALREADY IN THE KNOWLEDGE BASE (do not list these, even when an item names them by a short name such as "
        "'Brown' or 'Dano'; statutes held as a whole Act cover all their sections):\n" + held if held else "")
    allowed = ["WebSearch"] + [f"WebFetch(domain:{d})" for d in OFFICIAL]
    env = {k: v for k, v in __import__("os").environ.items()
           if k not in {"ANTHROPIC_API_KEY", "CLAUDECODE", "CLAUDE_CODE_ENTRYPOINT", "CLAUDE_CODE_SSE_PORT"}}
    sandbox = ROOT / "data" / "llm_sandbox"
    sandbox.mkdir(parents=True, exist_ok=True)
    r = subprocess.run([exe, "-p", "--model", MODEL, "--output-format", "text",
                        "--allowedTools", *allowed, "--disallowedTools", "Bash", "Write", "Edit", "NotebookEdit"],
                       input=prompt, capture_output=True, text=True, timeout=1800, cwd=sandbox, env=env)
    if r.returncode != 0:
        raise RuntimeError(f"claude exited {r.returncode}: {r.stderr[-500:]}")
    m = re.search(r"\[\s*\{.*\}\s*\]", r.stdout, re.S)
    return json.loads(m.group(0)) if m else []


def download(url: str) -> tuple[Path, str]:
    """Fetch an official URL into a temp file with the right extension. Raises on bot walls."""
    from urllib.parse import urlparse
    if not any(urlparse(url).netloc.endswith(d.replace("www.", "")) for d in OFFICIAL):
        raise ValueError("not an allow-listed official site")
    headers = {"User-Agent": "Mozilla/5.0 (legal-study-bot; personal use)"}
    celex = re.search(r"CELEX(?::|%3A)([0-9A-Z()]+)", url, re.I)
    if "eur-lex.europa.eu" in url and celex:
        # EUR-Lex answers scripts with a bot check (HTTP 202); the EU Publications Office serves the same official text.
        url = f"http://publications.europa.eu/resource/celex/{celex.group(1)}"
        accepts = ["application/xhtml+xml", "text/html", "application/pdf"]  # it serves one format per request
    else:
        accepts = [None]
    for i, accept in enumerate(accepts):
        h = headers | ({"Accept": accept, "Accept-Language": "eng"} if accept else {})
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=h), timeout=120) as resp:
                if resp.status != 200:
                    raise RuntimeError(f"HTTP {resp.status} (site may block automated download)")
                data, ctype = resp.read(), resp.headers.get("Content-Type", "")
            break
        except urllib.error.HTTPError as e:
            if e.code != 404 or i == len(accepts) - 1:
                raise
    if len(data) < 3000:
        raise RuntimeError("page too short: probably a bot check; download it in a browser instead")
    ext = (".html" if "xhtml" in ctype or "html" in ctype else ".xml" if "xml" in ctype or url.endswith(".xml")
           else ".pdf" if "pdf" in ctype else ".html")
    tmp = Path(tempfile.mkdtemp(prefix="gapfix-")) / f"doc{ext}"
    tmp.write_bytes(data)
    return tmp, ext


_NOT_PARTY = {"r", "re", "the", "in", "ex", "parte", "v", "and", "of", "for", "secretary", "state", "regina", "rex",
              "on", "application", "ltd", "plc", "limited", "a", "an", "minor", "crown", "uk", "co"}


def judgment_matches(title: str, raw: str) -> bool:
    """A wrong neutral citation fetches a different case: compare the case name the National Archives gives
    (FRBRname in its XML) with the case we asked for. Other sources have no such field and pass."""
    m = re.search(r'<FRBRname value="([^"]+)"', raw[:50000])
    if not m or re.search(r"^[A-Z]{2,3} v |\bv The Crown\b", m.group(1)):   # anonymised titles can't be compared
        return True
    words = [w for w in re.findall(r"[A-Za-z][A-Za-z'’-]{2,}", title.split("[")[0]) if w.lower() not in _NOT_PARTY]
    return not words or any(w.lower() in m.group(1).lower() for w in words)


def save(found: dict) -> Path:
    from .ingest.extract import extract
    from .ingest.run import slug
    from .ingest.tidy import tidy_text
    tmp, ext = download(found["url"])
    raw = tmp.read_bytes()[:50000].decode("utf-8", "ignore")
    ex = extract(tmp)
    shutil.rmtree(tmp.parent, ignore_errors=True)
    if len(ex.body) < 1500:
        raise RuntimeError("extracted text too short")
    kind = "legislation" if found.get("kind") == "legislation" else "case_law"
    if kind == "case_law" and not judgment_matches(found["authority"], raw):
        raise RuntimeError("the downloaded judgment is a different case (wrong citation); find the right one by hand")
    fm = {"authority": kind, "title": found["authority"], "original": f"downloaded: {found['url']}",
          "citation": found.get("citation", ""), "topic": found["topic"], "extracted_at": dt.date.today().isoformat(),
          "note": "fetched by fix_gaps from an official source"}
    text = f"---\n{yaml.safe_dump(fm, sort_keys=False, allow_unicode=True)}---\n# {found['authority']}\n\n{ex.body}"
    out = config.path("kb") / "topics" / found["topic"] / "raw" / kind / f"{slug(found['authority'])}-official.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(tidy_text(text, is_act=kind == "legislation" and ext == ".pdf"))
    return out


def held_titles() -> str:
    """Lower-cased titles of everything already in the knowledge base."""
    out = []
    for p in (config.path("kb") / "topics").glob("*/**/*.md"):
        m = re.search(r"^title:\s*(.+)$", p.read_text(errors="ignore")[:800], re.M)
        out.append((m.group(1) if m else p.stem.replace("-", " ")).lower())
    return " | ".join(out)


def already_held(name: str, titles: str) -> bool:
    key = re.split(r"[(\[;]", name)[0].strip().lower().replace("’", "'")
    if len(key) > 8 and key in titles:
        return True
    if " v " not in key:            # "Re MB" style names: match the name after "re"
        m = re.match(r"re (\w+)", key)
        return bool(m) and len(m.group(1)) >= 2 and re.search(rf"\b{m.group(1)}\b re\b|\bre {m.group(1)}\b", titles) is not None
    skip = {"r", "the", "and", "ltd", "plc", "co", "others", "another"}
    a, b = ([w for w in re.findall(r"[a-z']+", side) if w not in skip] for side in key.split(" v ", 1))
    if not a or not b:
        return False
    return any(re.search(rf"\b{re.escape(a[0])}\b", t_) and re.search(rf"\b{re.escape(b[0])}\b", t_) and " v " in t_
               for t_ in titles.split(" | "))


NOTE_PROMPT = """Write a factual case note for a UK/EU law study knowledge base. No official copy of the judgment
could be downloaded, so build it from reliable secondary sources found with WebSearch/WebFetch (official court
pages, the National Archives, reputable case summaries, law-firm articles, Wikipedia) and your own knowledge.

Case: {authority} {citation}
Area (topic slug): {topic}
Why it was needed: {note}

Rules: every fact must be confirmed by at least two agreeing sources or be left out; never invent paragraph
pinpoints, page numbers, quotes or judges; no personal data, and no references to any university, module, course or
lecturer. 400-700 words.

Format (markdown):
---
title: <full case name and citation> (case note)
topic: {topic}
authority: notes
written: {today}
case_note: true
original_judgment_held: false
verified_against:
  - "<what it confirmed>: <url>"
---
# <title>

> <one-line caution: original judgment not read; check pinpoints against the report>

## Overview
## Facts
## Held
## Later treatment   (only if confirmed)
## Applying it to a problem question
## Links

If you cannot confirm the case well enough, do not write a note. Reply with ONLY JSON:
{{"ok": true, "slug": "<short-slug-with-year>", "markdown": "<the whole note>"}}  or  {{"ok": false, "reason": "..."}}"""


def _quote_title(md: str) -> str:
    """Case titles contain colons ("Re R (Wardship: Consent...)"), which break YAML unless quoted."""
    def q(m):
        v = m.group(2).strip()
        return m.group(0) if v[:1] in "'\"" else f"{m.group(1)}: {json.dumps(v, ensure_ascii=False)}"
    head, sep, rest = md[3:].partition("\n---")
    return "---" + re.sub(r"^(title|description):[ \t]*(.+)$", q, head, flags=re.M) + sep + rest


def write_case_note(found: dict) -> Path:
    """Fallback when no official copy can be downloaded: Opus writes a cross-checked case note."""
    from .index import IDENTIFIERS
    exe = shutil.which("claude") or str(Path.home() / ".local/bin/claude")
    env = {k: v for k, v in __import__("os").environ.items()
           if k not in {"ANTHROPIC_API_KEY", "CLAUDECODE", "CLAUDE_CODE_ENTRYPOINT", "CLAUDE_CODE_SSE_PORT"}}
    sandbox = ROOT / "data" / "llm_sandbox"
    sandbox.mkdir(parents=True, exist_ok=True)
    prompt = NOTE_PROMPT.format(authority=found.get("authority", ""), citation=found.get("citation", ""),
                                topic=found["topic"], note=found.get("note", ""), today=dt.date.today().isoformat())
    r = subprocess.run([exe, "-p", "--model", MODEL, "--output-format", "text", "--allowedTools", "WebSearch", "WebFetch",
                        "--disallowedTools", "Bash", "Write", "Edit", "NotebookEdit"],
                       input=prompt, capture_output=True, text=True, timeout=1200, cwd=sandbox, env=env)
    m = re.search(r"\{.*\}", r.stdout, re.S)
    if r.returncode != 0 or not m:
        raise RuntimeError(f"case-note writer failed: {(r.stderr or r.stdout)[-300:]}")
    out = json.loads(m.group(0))
    if not out.get("ok"):
        raise RuntimeError(f"no case note: {out.get('reason', '')[:200]}")
    md = out.get("markdown", "")
    if not md.startswith("---") or "original_judgment_held: false" not in md or len(md) < 1500:
        raise RuntimeError("case note malformed")
    if IDENTIFIERS.search(md):
        raise RuntimeError("case note contained course or personal identifiers; not saved")
    md = _quote_title(md)
    slug = re.sub(r"[^a-z0-9-]+", "-", out.get("slug", "").lower()).strip("-")[:70] or "case"
    slug = re.sub(r"^(case-)+", "", slug) or "case"   # the file gets "case-" below
    path = config.path("kb") / "topics" / found["topic"] / "notes" / f"case-{slug}.md"
    if path.exists():
        raise RuntimeError(f"note already exists: {path.name}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(md.rstrip() + "\n")
    return path


def _mark(item_file: str, status: str, why: str):
    p = ROOT / item_file
    if p.exists():
        t = p.read_text()
        p.write_text(re.sub(r"^status: \w+", f"status: {status}", t, count=1) + f"\n## Fix attempt {dt.date.today()}\n\n{why}\n")


def run(dry: bool = False) -> Path:
    items = open_gaps()
    _status(state="running", step="asking Claude for official sources", items=len(items))
    stamp = dt.datetime.now().strftime("%Y-%m-%d-%H%M")
    report = IMP / "gap_fixes" / f"{stamp}.md"
    L = [f"# Gap fix run {stamp}", "", f"{len(items)} open knowledge-gap items.", ""]
    if not items:
        L.append("Nothing to fix.")
    else:
        found, seen_names = [], set()
        for b in range(0, len(items), BATCH):   # small batches: better answers, and a failure loses one batch only
            _status(step=f"asking Claude for official sources ({b + 1}-{min(b + BATCH, len(items))} of {len(items)})")
            try:
                got = ask_claude(items[b: b + BATCH])
            except Exception as e:
                L.append(f"- batch {b // BATCH + 1} failed: {str(e)[:200]}")
                if "limit" in str(e).lower():
                    break
                continue
            for f in got:
                key = re.sub(r"\W+", " ", str(f.get("authority", "")).lower()).strip()
                if key and key not in seen_names:
                    seen_names.add(key)
                    found.append(f)
        added, manual, held = [], [], []
        titles = held_titles()
        _status(step=f"downloading {len(found)} sources")
        for f in found:
            name = f.get("authority", "?")
            if already_held(name, titles):
                held.append(f)
                continue
            if not f.get("url"):
                manual.append((f, f.get("note") or "no official copy found"))
                continue
            if dry:
                manual.append((f, "dry run: not downloaded"))
                continue
            try:
                out = save(f)
                added.append((f, out))
            except Exception as e:
                manual.append((f, f"{type(e).__name__}: {e}"))
        still = []
        for f, why in manual:   # no official copy: Opus writes a cross-checked case note instead
            if dry or f.get("kind") == "legislation" or sum(1 for _, o in added if "/notes/" in str(o)) >= MAX_NOTES:
                still.append((f, why))
                continue
            _status(step=f"writing case note: {f.get('authority', '')[:60]}")
            try:
                added.append((f, write_case_note(f)))
            except Exception as e:
                still.append((f, f"{why}; {e}"))
        manual = still
        L += ["## Added to the knowledge base", ""] + ([f"- **{f['authority']}** ({f.get('citation', '')}) → "
              f"`{o.relative_to(ROOT)}`" for f, o in added] or ["- none"])
        L += ["", "## Already in the knowledge base (retrieval missed them; not downloaded again)", ""] + \
             ([f"- {f.get('authority')}" for f in held] or ["- none"])
        L += ["", "## Needs you (download in a browser and save it to the Law folder, or check)", ""] + \
             ([f"- **{f.get('authority')}**: {why}" + (f" — {f['url']}" if f.get('url') else "") for f, why in manual] or ["- none"])
        by_item: dict[str, list] = {}
        for f, o in added:
            by_item.setdefault(f.get("item", ""), []).append(("added", f["authority"]))
        for f, why in manual:
            by_item.setdefault(f.get("item", ""), []).append(("manual", f"{f.get('authority')}: {why}"))
        for f in held:
            by_item.setdefault(f.get("item", ""), []).append(("added", f"{f.get('authority')} (already held)"))
        for it in items:
            res = by_item.get(it["file"], [])
            if res and all(k == "added" for k, _ in res):
                _mark(it["file"], "fixed", "Added: " + "; ".join(x for _, x in res))
            elif res:
                _mark(it["file"], "needs-manual", "\n".join(f"- {k}: {x}" for k, x in res))
        if added and not dry:
            _status(step="rebuilding index")
            from .retrieval.engine import RetrievalEngine
            RetrievalEngine().build()
            L += ["", "Index rebuilt. Restart the chat server (or it reloads on next start) to use the new sources."]
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text("\n".join(L) + "\n")
    from .obs.improve import write_daily
    write_daily()
    _status(state="done", step="finished", report=str(report.relative_to(ROOT)))
    return report


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    try:
        print("report:", run(a.dry_run))
    except Exception as e:
        _status(state="error", step=str(e)[:300])
        raise


if __name__ == "__main__":
    main()
