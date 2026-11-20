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
import urllib.request
from pathlib import Path

import yaml

from . import config

OFFICIAL = ["legislation.gov.uk", "caselaw.nationalarchives.gov.uk", "eur-lex.europa.eu", "curia.europa.eu",
            "www.bailii.org", "www.gov.uk", "www.supremecourt.uk", "hudoc.echr.coe.int"]
ROOT = config.ROOT
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
- Skip vague items that are not a specific authority (e.g. "more academic views").
- Topic slug must be one of: {topics}.

Reply with ONLY a JSON array, each element:
{{"item": "<item file>", "authority": "<name as it should be titled>", "kind": "case_law|legislation",
  "topic": "<slug>", "citation": "<neutral or official citation>", "url": "<official url or empty>",
  "note": "<why not found / anything to check>"}}

Items:
{items}
"""


def ask_claude(items: list[dict]) -> list[dict]:
    exe = shutil.which("claude") or str(Path.home() / ".local/bin/claude")
    topics = sorted(p.parent.name for p in (config.path("kb") / "topics").glob("*/manifest.yaml"))
    prompt = PROMPT.format(sites=", ".join(OFFICIAL), topics=", ".join(topics),
                           items=json.dumps(items, indent=1, ensure_ascii=False))
    allowed = ["WebSearch"] + [f"WebFetch(domain:{d})" for d in OFFICIAL]
    env = {k: v for k, v in __import__("os").environ.items()
           if k not in {"ANTHROPIC_API_KEY", "CLAUDECODE", "CLAUDE_CODE_ENTRYPOINT", "CLAUDE_CODE_SSE_PORT"}}
    sandbox = ROOT / "data" / "llm_sandbox"
    sandbox.mkdir(parents=True, exist_ok=True)
    r = subprocess.run([exe, "-p", "--model", "sonnet", "--output-format", "text",
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
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (legal-study-bot; personal use)"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        if resp.status != 200:
            raise RuntimeError(f"HTTP {resp.status} (site may block automated download)")
        data, ctype = resp.read(), resp.headers.get("Content-Type", "")
    if len(data) < 3000:
        raise RuntimeError("page too short: probably a bot check; download it in a browser instead")
    ext = ".xml" if "xml" in ctype or url.endswith(".xml") else ".pdf" if "pdf" in ctype else ".html"
    tmp = Path(tempfile.mkdtemp(prefix="gapfix-")) / f"doc{ext}"
    tmp.write_bytes(data)
    return tmp, ext


def save(found: dict) -> Path:
    from .ingest.extract import extract
    from .ingest.run import slug
    from .ingest.tidy import tidy_text
    tmp, ext = download(found["url"])
    ex = extract(tmp)
    shutil.rmtree(tmp.parent, ignore_errors=True)
    if len(ex.body) < 1500:
        raise RuntimeError("extracted text too short")
    kind = "legislation" if found.get("kind") == "legislation" else "case_law"
    fm = {"authority": kind, "title": found["authority"], "original": f"downloaded: {found['url']}",
          "citation": found.get("citation", ""), "topic": found["topic"], "extracted_at": dt.date.today().isoformat(),
          "note": "fetched by fix_gaps from an official source"}
    text = f"---\n{yaml.safe_dump(fm, sort_keys=False, allow_unicode=True)}---\n# {found['authority']}\n\n{ex.body}"
    out = config.path("kb") / "topics" / found["topic"] / "raw" / kind / f"{slug(found['authority'])}-official.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(tidy_text(text, is_act=kind == "legislation" and ext == ".pdf"))
    return out


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
        found = ask_claude(items)
        added, manual = [], []
        _status(step=f"downloading {len(found)} sources")
        for f in found:
            name = f.get("authority", "?")
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
        L += ["## Added to the knowledge base", ""] + ([f"- **{f['authority']}** ({f.get('citation', '')}) → "
              f"`{o.relative_to(ROOT)}`" for f, o in added] or ["- none"])
        L += ["", "## Needs you (download in a browser and save it to the Law folder, or check)", ""] + \
             ([f"- **{f.get('authority')}**: {why}" + (f" — {f['url']}" if f.get('url') else "") for f, why in manual] or ["- none"])
        by_item: dict[str, list] = {}
        for f, o in added:
            by_item.setdefault(f.get("item", ""), []).append(("added", f["authority"]))
        for f, why in manual:
            by_item.setdefault(f.get("item", ""), []).append(("manual", f"{f.get('authority')}: {why}"))
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
