"""Post-extraction tidy-up for page-based PDF text.

1. Strip print boilerplate (Oxford Law Trove, Westlaw, "Page 3 of 22", scanner stamps).
2. Strip running headers repeated at the top of each "## p. N" page block.
3. For Acts of Parliament extracted from PDF, re-section by statutory section
   ("## s 20 Right to reject") instead of by page, so retrieval returns the section.

  python -m legalbot.ingest.tidy            tidy every raw/*.md in place (front matter kept)
  python -m legalbot.ingest.tidy --dry-run  report what would change
"""
from __future__ import annotations

import argparse
import re
from collections import Counter
from pathlib import Path

PAGE_HEAD = re.compile(r"^## pp?\. [\d-]+\s*$", re.M)
BOILER = [
    r"^Page \d+ of \d+\s*$",
    r"^Printed from Oxford Law Trove\..*$",
    r"^personal use \(for details see Privacy Policy and Legal Notice\)\.?\s*$",
    r"^Subscriber: .*; date: .*$",
    r"^Printed from Oxford Law Trove.*$",
    r"^Scanned with\s*$", r"^C[sS] ?CamScanner\S*\s*$",
    r"^© .*(Oxford University Press|Thomson Reuters|LexisNexis).*$",
    r"^Downloaded from .* on .*$",
]
BOILER_RE = re.compile("|".join(f"(?:{p})" for p in BOILER), re.M)
# a statutory section heading on its own line: "20 Right to reject", "9A Goods ..."
SECTION = re.compile(r"^(\d{1,3})([A-Z]{0,2})\s+([A-Z][^\n.;]{2,110})$")
SCHEDULE = re.compile(r"^SCHEDULE\s+(\d+[A-Z]?)\b.*$")


def _split(body: str) -> tuple[str, list[tuple[str, str]]]:
    """-> (text before first page head, [(head, page_text), ...])"""
    heads = list(PAGE_HEAD.finditer(body))
    if not heads:
        return body, []
    pre = body[: heads[0].start()]
    pages = []
    for i, m in enumerate(heads):
        end = heads[i + 1].start() if i + 1 < len(heads) else len(body)
        pages.append((m.group(0).strip(), body[m.end():end].strip("\n")))
    return pre, pages


def _strip_headers(pages: list[tuple[str, str]]) -> list[tuple[str, str]]:
    """Drop leading lines that recur at the top of many pages (running headers / page numbers)."""
    if len(pages) < 4:
        return pages
    lead = Counter()
    for _, t in pages:
        for ln in [l.strip() for l in t.splitlines() if l.strip()][:4]:
            lead[re.sub(r"\d+", "#", ln)] += 1
    common = {k for k, v in lead.items() if v >= max(3, 0.3 * len(pages))}
    out = []
    for h, t in pages:
        lines = t.splitlines()
        i = 0
        while i < len(lines) and i < 6 and (not lines[i].strip() or re.sub(r"\d+", "#", lines[i].strip()) in common
                                            or re.fullmatch(r"\d{1,4}", lines[i].strip())):
            i += 1
        out.append((h, "\n".join(lines[i:]).strip()))
    return out


OLD_BODY = re.compile(r"^(\d{1,3})([A-Z]{0,2})\.\s*[-\u2014\u2013]\s*(?:\(1\)|\(l\))?")   # "8.-(1) The price ..."
TOC_LINE = re.compile(r"^(\d{1,3}[A-Z]{0,2})\.\s+([A-Z][^\n]{2,110}?)\.?\s*$")


def _best_run(cands: list[tuple[int, int, str, str]], n_lines: int) -> list[tuple[int, int, str, str]]:
    """Candidates restart at 1 after a table of contents; keep the run with the most text under it."""
    runs, cur = [], []
    for c in cands:
        if cur and not (0 <= c[1] - cur[-1][1] <= 12):
            runs.append(cur); cur = []
        if cur and c[1] == cur[-1][1] and not c[2]:
            continue
        cur.append(c)
    if cur:
        runs.append(cur)
    def span(r):
        idx = [c[0] for c in r] + [n_lines]
        return sum(min(idx[k + 1] - idx[k], 400) for k in range(len(r)))  # lines of body per heading
    return max(runs, key=lambda r: (span(r) / max(len(r), 1) > 2, span(r)), default=[])


def resection_act(pages: list[tuple[str, str]]) -> str | None:
    """Join pages and split by statutory section. None if it does not look like an Act."""
    lines = "\n".join(t for _, t in pages).splitlines()
    toc = {}
    for ln in lines[:800]:
        m = TOC_LINE.match(ln.strip())
        if m and m.group(1) not in toc:
            toc[m.group(1)] = m.group(2).strip()
    modern, old = [], []
    for i, ln in enumerate(lines):
        st = ln.strip()
        m = SECTION.match(st)
        if m:
            modern.append((i, int(m.group(1)), m.group(2), m.group(3).strip()))
        m = OLD_BODY.match(st)
        if m:
            num = m.group(1) + m.group(2)
            old.append((i, int(m.group(1)), m.group(2), toc.get(num, "")))
    run_m, run_o = _best_run(modern, len(lines)), _best_run(old, len(lines))
    run, keep_line = (run_o, True) if len(run_o) > len(run_m) else (run_m, False)
    if len(run) < 5:
        return None
    heads = [(i, f"## s {n}{suf} {title}".rstrip()) for i, n, suf, title in run]
    last_i = run[-1][0]
    for i, ln in enumerate(lines):
        if i > last_i:
            sm = SCHEDULE.match(ln.strip())
            if sm:
                heads.append((i, f"## Schedule {sm.group(1)}"))
    heads.sort()
    out = ["\n".join(lines[: heads[0][0]]).strip()]
    for k, (i, h) in enumerate(heads):
        endi = heads[k + 1][0] if k + 1 < len(heads) else len(lines)
        body = lines[i:endi] if (keep_line and h.startswith("## s ")) else lines[i + 1:endi]
        out.append(h + "\n\n" + "\n".join(body).strip())
    return "\n\n".join(p for p in out if p.strip()) + "\n"


COMMENTS = re.compile(r"^## (?:Marker comments|Reading annotations)\n(.*?)(?=^## |\Z)", re.M | re.S)


def _filter_link_comments(text: str) -> str:
    """PDF link annotations (DOIs, keyword links, page refs) are not comments: keep only real notes."""
    m = COMMENTS.search(text)
    if not m:
        return text
    items = re.findall(r"^- (.*)$", m.group(1), re.M)
    real, seen = [], set()
    from collections import Counter as _C
    counts = _C(re.sub(r"^\[p\. \d+\]\s*", "", it).strip() for it in items)
    for it in items:
        body = re.sub(r"^\[p\. \d+\]\s*", "", it).strip()
        if re.fullmatch(r"(https?://|doi|www\.)\S*", body, re.I) or len(body.split()) < 5 or "Law Trove" in body \
                or re.fullmatch(r"[\d\s]+", body) or body.startswith(("View the", "Test yourself", "In the OUP", "Visit the")) \
                or counts[body] > 1 or (len(body.split()) < 10 and not re.search(r"[.?!:]", body)) or body in seen:
            continue
        seen.add(body)
        real.append(f"- {it}")
    block = ("## Reading annotations\n\n" + "\n\n".join(real) + "\n\n") if real else ""
    return text[: m.start()] + block + text[m.end():]


def tidy_text(text: str, is_act: bool = False) -> str:
    fm = ""
    if text.startswith("---\n"):
        end = text.find("\n---\n", 4)
        fm, text = text[: end + 5], text[end + 5:]
    text = BOILER_RE.sub("", text)
    text = _filter_link_comments(text)
    pre, pages = _split(text)
    if pages:
        pages = _strip_headers(pages)
        act = resection_act(pages) if is_act else None
        if act:
            text = pre.rstrip() + "\n\n" + act
        else:
            text = pre.rstrip() + "\n\n" + "\n\n".join(f"{h}\n\n{t}" for h, t in pages if len(t) >= 40) + "\n"
    text = re.sub(r"\n{3,}", "\n\n", text)
    return fm + text


def main():
    from .. import config
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    kb = config.path("kb")
    changed = acts = 0
    for md in sorted((kb / "topics").glob("*/raw/**/*.md")):
        t = md.read_text(errors="ignore")
        is_act = "/legislation/" in md.as_posix() and bool(PAGE_HEAD.search(t))
        u = tidy_text(t, is_act)
        if u != t:
            changed += 1
            acts += int(is_act and "\n## s " in u)
            if not args.dry_run:
                md.write_text(u)
    print(f"{'would change' if args.dry_run else 'changed'} {changed} files; {acts} Acts re-sectioned")


if __name__ == "__main__":
    main()
