"""Knowledge-base loader shared by indexers.

Layout (one folder per area of law):

    kb/topics/<slug>/manifest.yaml     topic name, aliases, dates, source ledger
    kb/topics/<slug>/raw/**.md         extracted originals (legislation, case law, journals, lectures)
    kb/topics/<slug>/notes/**.md       our own rephrased knowledge (cites raw ids)

Every markdown file may start with YAML front matter (authority, original, citation, date).
Each heading becomes one Section with a stable id  "<slug>/<relpath>#<heading-slug>".
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

import yaml

MAX_SECTION_CHARS = 6000  # oversized sections are split into parts (FM3: wrong retrieval unit)
HEADING = re.compile(r"^(#{1,6})\s+(.+?)\s*#*\s*$")


@dataclass
class Section:
    id: str
    topic: str
    file: str
    heading_path: list[str]
    content: str
    kind: str                 # note | raw
    authority: str            # legislation | case_law | journal | lecture | note | feedback
    original_path: str = ""
    meta: dict = field(default_factory=dict)

    @property
    def title(self) -> str:
        return " > ".join(self.heading_path)


def slugify(text: str) -> str:
    s = re.sub(r"[^\w\s-]", "", text.lower()).strip()
    return re.sub(r"[\s_]+", "-", s)[:80] or "section"


def split_front_matter(text: str) -> tuple[dict, str]:
    if text.startswith("---\n"):
        end = text.find("\n---", 4)
        if end != -1:
            try:
                meta = yaml.safe_load(text[4:end]) or {}
            except yaml.YAMLError:
                meta = {}
            return meta, text[end + 4 :].lstrip("\n")
    return {}, text


def load_manifests(kb_root: Path) -> dict[str, dict]:
    out = {}
    for mf in sorted((kb_root / "topics").glob("*/manifest.yaml")):
        data = yaml.safe_load(mf.read_text()) or {}
        data.setdefault("slug", mf.parent.name)
        out[data["slug"]] = data
    return out


def parse_markdown(text: str, topic: str, rel: str, kind: str) -> list[Section]:
    meta, body = split_front_matter(text)
    authority = meta.get("authority") or ("note" if kind == "note" else "lecture")
    original = meta.get("original", "")
    doc_title = meta.get("title") or Path(rel).stem

    sections: list[Section] = []
    stack: list[tuple[int, str]] = []
    buf: list[str] = []
    seen: dict[str, int] = {}

    def flush():
        content = "\n".join(buf).strip()
        if not content:
            return
        path = [h for _, h in stack] or [doc_title]
        base = slugify(path[-1])
        if authority == "legislation" and doc_title.lower() not in " ".join(path).lower():
            path = [doc_title] + path   # "Land Registration Act 2002 > s 29 …", so the Act's name is always searchable
        n = seen.get(base, 0)
        seen[base] = n + 1
        anchor = base if n == 0 else f"{base}-{n + 1}"
        parts = _split_long(content)
        for i, part in enumerate(parts):
            sid = f"{topic}/{rel}#{anchor}" + (f"-p{i + 1}" if len(parts) > 1 else "")
            hp = path + ([f"part {i + 1}/{len(parts)}"] if len(parts) > 1 else [])
            sections.append(Section(sid, topic, rel, hp, part, kind, authority, original, meta))

    for line in body.splitlines():
        m = HEADING.match(line)
        if m:
            flush()
            buf = []
            level = len(m.group(1))
            while stack and stack[-1][0] >= level:
                stack.pop()
            stack.append((level, m.group(2)))
        else:
            buf.append(line)
    flush()
    return sections


def _split_long(content: str) -> list[str]:
    if len(content) <= MAX_SECTION_CHARS:
        return [content]
    parts, cur = [], ""
    for para in re.split(r"\n\s*\n", content):
        if cur and len(cur) + len(para) > MAX_SECTION_CHARS:
            parts.append(cur.strip())
            cur = ""
        cur += para + "\n\n"
    if cur.strip():
        parts.append(cur.strip())
    return parts


def load_sections(kb_root: Path) -> list[Section]:
    sections: list[Section] = []
    for topic_dir in sorted((kb_root / "topics").iterdir()):
        if not topic_dir.is_dir():
            continue
        topic = topic_dir.name
        for kind, sub in (("note", "notes"), ("raw", "raw")):
            base = topic_dir / sub
            if not base.exists():
                continue
            for md in sorted(base.rglob("*.md")):
                rel = f"{sub}/{md.relative_to(base).as_posix()}"
                sections.extend(parse_markdown(md.read_text(errors="ignore"), topic, rel, kind))
    return sections
