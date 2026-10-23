"""Lightweight Markdown inline + HR helpers for Format-only rendering.

Markers are presentation-only: source spans still cover the original text
(including ``**``), so content-lock is unchanged. Renderers omit markers and
apply bold/italic/code styling.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

_HR = re.compile(r"^(\s*)(-{3,}|\*{3,}|_{3,})(\s*)$")
# **bold**, __bold__, *italic*, _italic_, `code` (non-greedy, no nested)
_INLINE = re.compile(
    r"(\*\*(.+?)\*\*)"
    r"|(__(.+?)__)"
    r"|(\*(.+?)\*)"
    r"|(_(.+?)_)"
    r"|(`([^`]+)`)"
)


@dataclass(frozen=True)
class InlineRun:
    text: str
    bold: bool = False
    italic: bool = False
    code: bool = False


def is_horizontal_rule(line: str) -> bool:
    return bool(_HR.match(line.strip()))


def parse_inline(text: str) -> list[InlineRun]:
    """Split a line into styled runs; markdown markers are dropped from output."""
    if not text:
        return []
    runs: list[InlineRun] = []
    pos = 0
    for m in _INLINE.finditer(text):
        if m.start() > pos:
            runs.append(InlineRun(text[pos : m.start()]))
        if m.group(2) is not None:
            runs.append(InlineRun(m.group(2), bold=True))
        elif m.group(4) is not None:
            runs.append(InlineRun(m.group(4), bold=True))
        elif m.group(6) is not None:
            runs.append(InlineRun(m.group(6), italic=True))
        elif m.group(8) is not None:
            runs.append(InlineRun(m.group(8), italic=True))
        elif m.group(10) is not None:
            runs.append(InlineRun(m.group(10), code=True))
        pos = m.end()
    if pos < len(text):
        runs.append(InlineRun(text[pos:]))
    # Merge empties away
    return [r for r in runs if r.text]


def strip_inline_markers(text: str) -> str:
    """Plain text without markdown markers (for length estimates / TOC)."""
    return "".join(r.text for r in parse_inline(text))
