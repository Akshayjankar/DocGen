"""Markdown inline helpers for Format-only rendering.

Markers are presentation-only: source spans still cover the original text
(including ``**``), so content-lock is unchanged. Renderers omit markers and
apply bold/italic/code styling (or plain stripped text).
"""

from __future__ import annotations

import html
import re
from dataclasses import dataclass

_HR = re.compile(r"^(\s*)(-{3,}|\*{3,}|_{3,})(\s*)$")

# Order matters: longer delimiters first. Strikethrough ~~…~~ included.
_INLINE = re.compile(
    r"(~~(.+?)~~)"
    r"|(\*\*(.+?)\*\*)"
    r"|(__(.+?)__)"
    r"|(\*(.+?)\*)"
    r"|(_(.+?)_)"
    r"|(`([^`]+)`)"
)

# Invisible / hyphenation junk that causes glyph stacking in PDF viewers
_INVISIBLE = re.compile(
    "[\u00ad\u200b\u200c\u200d\u2060\ufeff\u180e\u034f]"
)

# Orphan markdown delimiter runs left after pair stripping
_ORPHAN_MARKERS = re.compile(r"(\*\*+|__+|~~+|`+)")


@dataclass(frozen=True)
class InlineRun:
    text: str
    bold: bool = False
    italic: bool = False
    code: bool = False
    strike: bool = False


def is_horizontal_rule(line: str) -> bool:
    return bool(_HR.match(line.strip()))


def sanitize_invisible(text: str) -> str:
    """Drop soft hyphens / zero-width chars that stack glyphs in PDF."""
    if not text:
        return ""
    t = _INVISIBLE.sub("", text)
    t = t.replace("\u2011", "-")  # non-breaking hyphen → ASCII
    return t


def parse_inline(text: str) -> list[InlineRun]:
    """Split into styled runs; markdown markers are dropped from output."""
    text = sanitize_invisible(text or "")
    if not text:
        return []
    runs: list[InlineRun] = []
    pos = 0
    for m in _INLINE.finditer(text):
        if m.start() > pos:
            runs.append(InlineRun(text[pos : m.start()]))
        if m.group(2) is not None:
            runs.append(InlineRun(m.group(2), strike=True))
        elif m.group(4) is not None:
            runs.append(InlineRun(m.group(4), bold=True))
        elif m.group(6) is not None:
            runs.append(InlineRun(m.group(6), bold=True))
        elif m.group(8) is not None:
            runs.append(InlineRun(m.group(8), italic=True))
        elif m.group(10) is not None:
            runs.append(InlineRun(m.group(10), italic=True))
        elif m.group(12) is not None:
            runs.append(InlineRun(m.group(12), code=True))
        pos = m.end()
    if pos < len(text):
        runs.append(InlineRun(text[pos:]))
    # Drop empties; strip leftover orphan delimiter tokens in plain runs
    cleaned: list[InlineRun] = []
    for r in runs:
        piece = r.text
        if not (r.bold or r.italic or r.code or r.strike):
            piece = _ORPHAN_MARKERS.sub("", piece)
        if piece:
            cleaned.append(
                InlineRun(piece, bold=r.bold, italic=r.italic, code=r.code, strike=r.strike)
            )
    return cleaned


def strip_inline_markers(text: str) -> str:
    """Plain display text: no markdown markers, no soft hyphens."""
    return "".join(r.text for r in parse_inline(text))


def display_text(text: str) -> str:
    """Canonical sanitizer for every PDF/DOCX text sink."""
    return strip_inline_markers(text or "")


def runs_to_html(text: str, *, fontsize: float, color_hex: str) -> str:
    """HTML fragment for PyMuPDF insert_htmlbox (bold/italic/code/strike)."""
    runs = parse_inline(text)
    if not runs:
        return ""
    parts: list[str] = []
    for r in runs:
        # Preserve newlines as <br/>
        chunks = r.text.split("\n")
        for i, chunk in enumerate(chunks):
            if i:
                parts.append("<br/>")
            t = html.escape(chunk)
            if not t:
                continue
            if r.code:
                t = f"<code>{t}</code>"
            if r.bold:
                t = f"<b>{t}</b>"
            if r.italic:
                t = f"<i>{t}</i>"
            if r.strike:
                t = f"<s>{t}</s>"
            parts.append(t)
    inner = "".join(parts)
    color = color_hex if color_hex.startswith("#") else f"#{color_hex}"
    return (
        f'<div style="font-size:{fontsize}pt;color:{color};'
        f'font-family:Helvetica,Arial,sans-serif;line-height:1.45;margin:0;">'
        f"{inner}</div>"
    )
