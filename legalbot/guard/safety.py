"""Safety: query-intent isolation, untrusted-content isolation, tool policy.

1. User input is scanned for injection attempts (flagged, logged, not executed).
2. Retrieved KB text is UNTRUSTED data: wrapped in <document> tags with an explicit
   instruction that text inside documents is evidence, never instructions.
3. Tool policy: LLM providers run with NO tools (claude CLI --tools "", codex read-only sandbox).
   The model can only read the prompt we build and write text back.
"""
from __future__ import annotations

import re

INJECTION = [
    r"ignore (?:all |the )?(?:previous|prior|above) (?:instructions|rules)",
    r"disregard (?:the )?(?:system|previous) (?:prompt|instructions)",
    r"(?:reveal|print|show) (?:your |the )?(?:system prompt|hidden instructions)",
    r"you are now\b", r"developer mode", r"\bjailbreak\b",
    r"run (?:this|the following) (?:command|code)", r"<\s*/?\s*(?:system|document)\s*>",
]
_INJ = [re.compile(p, re.I) for p in INJECTION]


def scan_user_input(text: str) -> list[str]:
    return [f"possible_injection:{p.pattern[:40]}" for p in _INJ if p.search(text)]


def sanitize_document(text: str) -> tuple[str, bool]:
    """Neutralise tag-breaking and instruction-like lines inside retrieved documents."""
    flagged = any(p.search(text) for p in _INJ)
    text = re.sub(r"<\s*/?\s*(system|document|instructions?)\s*>", "[tag removed]", text, flags=re.I)
    return text, flagged


TOOL_POLICY = (
    "You have no tools. Do not attempt to browse, run code, read files or call functions. "
    "Answer only from the documents and conversation provided in this prompt."
)
