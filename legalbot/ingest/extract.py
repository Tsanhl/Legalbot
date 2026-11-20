"""Text extraction: original file -> (markdown body with headings, metadata).

Retrieval units by format (FM3: get the unit right at extraction time):
  pdf   one "## p. N" section per page (short pages merged) -> page pinpoints for OSCOLA
  docx  Word heading styles become markdown headings; comments extracted (feedback)
  pptx  "## Slide N: <title>" with slide text + speaker notes
  xml   legislation.gov.uk CLML -> "## s N <title>"; Akoma Ntoso judgments -> numbered paragraphs
  html  judgments -> headings + numbered paragraph groups
"""
from __future__ import annotations

import html as htmllib
import re
import zipfile
from html.parser import HTMLParser
from pathlib import Path
from xml.etree import ElementTree as ET

MIN_PAGE_CHARS = 700
MAX_OCR_PAGES = 400


class Extracted:
    def __init__(self, body: str, meta: dict | None = None, comments: list[str] | None = None):
        self.body = body
        self.meta = meta or {}
        self.comments = comments or []


def extract(path: Path) -> Extracted:
    ext = path.suffix.lower()
    if ext == ".pdf":
        return _pdf(path)
    if ext == ".docx":
        return _docx(path)
    if ext == ".pptx":
        return _pptx(path)
    if ext == ".xml":
        return _xml(path)
    if ext in (".html", ".htm"):
        return _html(path.read_text(errors="ignore"))
    if ext in (".txt", ".md"):
        return Extracted(path.read_text(errors="ignore"))
    raise ValueError(f"unsupported {ext}")


def clean(text: str) -> str:
    text = text.replace("\x00", "").replace("\r\n", "\n").replace("\r", "\n").replace("­", "")
    text = re.sub(r"-\n(?=[a-z])", "", text)            # de-hyphenate line breaks
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


# ---------------------------------------------------------------- PDF
def _pdf(path: Path) -> Extracted:
    import pypdfium2 as pdfium

    doc = pdfium.PdfDocument(str(path))
    pages = []
    ocr_pages = 0
    try:
        for i in range(len(doc)):
            tp = doc[i].get_textpage()
            pages.append(clean(tp.get_text_range()))
        scanned = len(pages) > 0 and sum(len(p) for p in pages) / len(pages) < 100
        if scanned and len(pages) <= MAX_OCR_PAGES:
            for i, t in enumerate(pages):
                if len(t) < 100:
                    o = _ocr(doc[i])
                    if o:
                        pages[i] = o
                        ocr_pages += 1
    finally:
        doc.close()
    parts, buf, start = [], "", 1
    for i, t in enumerate(pages, 1):
        if not buf:
            start = i
        buf += ("\n\n" if buf else "") + t
        if len(buf) >= MIN_PAGE_CHARS or i == len(pages):
            label = f"p. {start}" if start == i else f"pp. {start}-{i}"
            if buf.strip():
                parts.append(f"## {label}\n\n{buf}")
            buf = ""
    chars = sum(len(p) for p in pages)
    return Extracted("\n\n".join(parts), {"pages": len(pages), "chars": chars, "ocr_pages": ocr_pages,
                                          "needs_ocr": len(pages) > 0 and chars / len(pages) < 100},
                     _pdf_annotations(path))


def _ocr(page) -> str:
    """macOS Vision OCR (local, via ocrmac). Returns '' if unavailable."""
    try:
        from ocrmac import ocrmac
        img = page.render(scale=2).to_pil()
        lines = ocrmac.OCR(img, recognition_level="accurate").recognize()
        # sort top-to-bottom (Vision bbox origin is bottom-left), keep reading order
        lines.sort(key=lambda r: (-round(r[2][1] + r[2][3], 2), r[2][0]))
        return clean("\n".join(r[0] for r in lines))
    except Exception:
        return ""


def _pdf_annotations(path: Path) -> list[str]:
    """Marker comments (sticky notes / highlights with text) — the substance of a marked script."""
    try:
        from pypdf import PdfReader
        out = []
        for n, page in enumerate(PdfReader(str(path)).pages, 1):
            for a in page.get("/Annots") or []:
                a = a.get_object()
                txt = a.get("/Contents")
                if txt and str(txt).strip():
                    out.append(f"[p. {n}] {str(txt).strip()}")
        return out
    except Exception:
        return []


# ---------------------------------------------------------------- DOCX
def _docx(path: Path) -> Extracted:
    import docx

    d = docx.Document(str(path))
    lines = []
    for p in d.paragraphs:
        t = p.text.strip()
        if not t:
            continue
        style = (p.style.name or "").lower() if p.style is not None else ""
        m = re.match(r"heading (\d)", style)
        if m:
            lines.append("#" * min(int(m.group(1)) + 1, 6) + " " + t)
        elif style == "title":
            lines.append("# " + t)
        else:
            lines.append(t)
    for table in d.tables:
        for row in table.rows:
            cells = [c.text.strip() for c in row.cells if c.text.strip()]
            if cells:
                lines.append(" | ".join(dict.fromkeys(cells)))
    body = "\n\n".join(lines)
    return Extracted(body, {"chars": len(body)}, _docx_comments(path))


def _docx_comments(path: Path) -> list[str]:
    try:
        with zipfile.ZipFile(path) as z:
            if "word/comments.xml" not in z.namelist():
                return []
            root = ET.fromstring(z.read("word/comments.xml"))
        ns = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
        out = []
        for c in root.iter(f"{ns}comment"):
            txt = "".join(t.text or "" for t in c.iter(f"{ns}t")).strip()
            if txt:
                out.append(txt)
        return out
    except Exception:
        return []


# ---------------------------------------------------------------- PPTX
def _pptx(path: Path) -> Extracted:
    from pptx import Presentation

    prs = Presentation(str(path))
    parts = []
    for n, slide in enumerate(prs.slides, 1):
        title = ""
        texts = []
        for shape in slide.shapes:
            if not shape.has_text_frame:
                continue
            t = clean(shape.text_frame.text)
            if not t:
                continue
            if shape == getattr(slide.shapes, "title", None) and not title:
                title = t.replace("\n", " ")[:120]
            else:
                texts.append(t)
        notes = ""
        if slide.has_notes_slide:
            notes = clean(slide.notes_slide.notes_text_frame.text or "")
        body = "\n\n".join(texts) + (f"\n\nSpeaker notes: {notes}" if notes else "")
        if body.strip() or title:
            parts.append(f"## Slide {n}{': ' + title if title else ''}\n\n{body}")
    text = "\n\n".join(parts)
    return Extracted(text, {"slides": len(prs.slides), "chars": len(text)})


# ---------------------------------------------------------------- XML
def _local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _text(el) -> str:
    return clean(" ".join(t.strip() for t in el.itertext() if t.strip()))


def _xml(path: Path) -> Extracted:
    root = ET.parse(str(path)).getroot()
    if _local(root.tag) == "Legislation":
        return _clml(root)
    if _local(root.tag) == "akomaNtoso":
        return _akn(root)
    return Extracted(_text(root), {"chars": 0})


def _clml(root) -> Extracted:
    meta = {}
    for el in root.iter():
        n = _local(el.tag)
        if n == "title" and "title" not in meta and el.text:
            meta["title"] = el.text.strip()
        elif n == "valid" and el.text:
            meta["version_date"] = el.text.strip()
        elif n == "identifier" and el.text and "legislation.gov.uk" in el.text:
            meta["url"] = el.text.strip()
    meta["restrict_extent"] = root.get("RestrictExtent", "")
    parts = []
    skip = {"Commentaries", "Metadata", "Contents"}

    def walk(el, path):
        n = _local(el.tag)
        if n in skip:
            return
        if n == "P1" and "P1group" not in path:
            num = next((_text(c) for c in el if _local(c.tag) == "Pnumber"), "")
            parts.append(f"## s {num}\n\n{_strip_commentary_refs(_text(el))}")
            return
        if n == "P1group":
            title = next((_text(c) for c in el if _local(c.tag) == "Title"), "")
            num = next((_text(p) for p in el.iter() if _local(p.tag) == "Pnumber"), "")
            body = "".join(_clml_text(c, "P1group") for c in el if _local(c.tag) not in ("Title",))
            body = re.sub(r"[ \t]+", " ", re.sub(r"\s*\n\s*", "\n", body)).strip()
            heading = f"s {num} {title}".strip() if num else (title or "Provision")
            parts.append(f"## {heading}\n\n{_strip_commentary_refs(body)}")
            return
        if n in ("Part", "Chapter", "Schedule"):
            num = next((_text(c) for c in el if _local(c.tag) == "Number"), "")
            title = next((_text(c) for c in el if _local(c.tag) == "Title"), "")
            if num or title:
                parts.append(f"# {num} {title}".strip())
        for c in el:
            walk(c, path + [n])

    walk(root, [])
    if not parts:  # single-section extracts without P1group
        parts.append(f"## {meta.get('title', 'Provision')}\n\n{_strip_commentary_refs(_body_text(root))}")
    body = "\n\n".join(parts)
    meta["chars"] = len(body)
    return Extracted(body, meta)


def _body_text(root) -> str:
    for el in root.iter():
        if _local(el.tag) in ("Body", "Primary", "Secondary"):
            return _text(el)
    return _text(root)


def _clml_text(el, parent: str = "") -> str:
    """CLML text with subsection numbering: P2 -> (1), P3 -> (a), P4 -> (i)."""
    n = _local(el.tag)
    if n in ("Commentaries", "CommentaryRef", "Title") and parent:
        return ""
    out = []
    if n == "Pnumber":
        num = "".join(el.itertext()).strip()
        return f"\n({num}) " if parent in ("P2", "P3", "P4", "P5") else ""
    if el.text and n not in ("Pnumber",):
        out.append(el.text)
    for c in el:
        out.append(_clml_text(c, n))
        if c.tail:
            out.append(c.tail)
    if n in ("Text",):
        out.append(" ")
    return "".join(out)


def _strip_commentary_refs(t: str) -> str:
    return re.sub(r"\bF\d+\b\s?", "", t)


def _akn(root) -> Extracted:
    meta = {}
    for el in root.iter():
        n = _local(el.tag)
        if n == "FRBRname" and "title" not in meta:
            meta["title"] = el.get("value", "")
        elif n == "neutralCitation" and el.text:
            meta["citation"] = el.text.strip()
        elif n == "FRBRdate" and "date" not in meta:
            meta["date"] = el.get("date", "")
    paras = []
    nested = {id(d) for el in root.iter() if _local(el.tag) == "paragraph"
              for d in el.iter() if d is not el and _local(d.tag) == "paragraph"}
    for el in root.iter():
        if _local(el.tag) == "paragraph" and id(el) not in nested:
            num = next((_text(c) for c in el if _local(c.tag) == "num"), "")
            body = " ".join(_text(c) for c in el if _local(c.tag) != "num")
            if body:
                paras.append((num, body))
    body = _group_paragraphs(paras) if paras else _text(root)
    meta["chars"] = len(body)
    return Extracted(body, meta)


def _group_paragraphs(paras: list[tuple[str, str]], target: int = 2500) -> str:
    out, buf, first, last = [], [], None, None
    for num, body in paras:
        first = first or num
        last = num
        buf.append(f"{num} {body}".strip())
        if sum(len(b) for b in buf) >= target:
            out.append(f"## paras {first}–{last}\n\n" + "\n\n".join(buf))
            buf, first = [], None
    if buf:
        out.append(f"## paras {first}–{last}\n\n" + "\n\n".join(buf))
    return "\n\n".join(out)


# ---------------------------------------------------------------- HTML
class _H(HTMLParser):
    SKIP = {"script", "style", "nav", "header", "footer", "noscript", "button", "form"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.out, self.skip, self.cur = [], 0, ""
        self.heading = None

    def handle_starttag(self, tag, attrs):
        if tag in self.SKIP:
            self.skip += 1
        elif tag in ("p", "div", "li", "br", "tr", "blockquote"):
            self._flush()
        elif tag in ("h1", "h2", "h3", "h4"):
            self._flush()
            self.heading = tag

    def handle_endtag(self, tag):
        if tag in self.SKIP and self.skip:
            self.skip -= 1
        elif tag in ("h1", "h2", "h3", "h4") and self.heading:
            t = self.cur.strip()
            if t:
                self.out.append(("#" * (int(tag[1]) + 1)) + " " + t)
            self.cur, self.heading = "", None
        elif tag in ("p", "div", "li", "tr", "blockquote"):
            self._flush()

    def handle_data(self, data):
        if not self.skip:
            self.cur += data

    def _flush(self):
        t = re.sub(r"\s+", " ", self.cur).strip()
        if t and not self.heading:
            self.out.append(t)
            self.cur = ""


def _html(raw: str) -> Extracted:
    title = re.search(r"<title>(.*?)</title>", raw, re.S | re.I)
    p = _H()
    p.feed(raw)
    p._flush()
    lines = [l for l in p.out if not re.search(r"cookies|skip to main content|^print$|^download", l, re.I)]
    # group numbered paragraphs ("1.", "[12]") into retrieval-sized sections
    paras, prose = [], []
    pending_num = None
    for l in lines:
        if l.startswith("#"):
            (paras[-1:] and paras.__setitem__(-1, (paras[-1][0], paras[-1][1] + "\n" + l))) if paras else prose.append(l)
            continue
        bare = re.match(r"^\[?(\d{1,4})[.\]]?$", l)
        if bare:
            pending_num = bare.group(1)
            continue
        m = re.match(r"^\[?(\d{1,4})[.\]]\s+(.*)", l)
        if pending_num:
            paras.append((pending_num, l))
            pending_num = None
        elif m:
            paras.append((m.group(1), m.group(2)))
        elif paras:
            paras[-1] = (paras[-1][0], paras[-1][1] + "\n" + l)
        else:
            prose.append(l)
    body = "\n\n".join(prose) + ("\n\n" + _group_paragraphs(paras) if paras else "")
    meta = {"title": htmllib.unescape(title.group(1).strip()) if title else "", "chars": len(body)}
    cit = re.search(r"\[(?:19|20)\d\d\] (?:UKSC|UKHL|EWCA (?:Civ|Crim)|EWHC|UKPC) \d+(?: \([A-Za-z]+\))?", raw)
    if cit:
        meta["citation"] = cit.group(0)
    return Extracted(body, meta)
