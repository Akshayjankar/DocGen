"""Normalize pasted text / files into offset-stable segments."""

from __future__ import annotations

import io
import re
from dataclasses import dataclass, field

from markdown_it import MarkdownIt


@dataclass
class Segment:
    id: str
    start: int
    end: int

    @property
    def text(self) -> str:
        return ""  # filled via parent; kept for typing clarity


@dataclass
class NormalizedText:
    text: str
    segments: list[Segment] = field(default_factory=list)
    language: str = "en"

    def segment_map(self) -> dict[str, Segment]:
        return {s.id: s for s in self.segments}

    def slice(self, start: int, end: int) -> str:
        return self.text[start:end]


_CODE_FENCE = re.compile(r"(```[\s\S]*?```)|(~~~[\s\S]*?~~~)")
_TABLE_BLOCK = re.compile(r"(?:^\|.+\|[ \t]*$\n?)+", re.MULTILINE)
_SENTENCE = re.compile(r"[^.!?\n]+[.!?]+|[^\n]+", re.MULTILINE)


def _normalize_newlines(raw: str) -> str:
    text = raw.replace("\r\n", "\n").replace("\r", "\n")
    # Preserve content; collapse only trailing spaces per line.
    lines = [ln.rstrip() for ln in text.split("\n")]
    return "\n".join(lines).strip() + ("\n" if text.endswith("\n") else "")


def _protected_ranges(text: str) -> list[tuple[int, int]]:
    ranges: list[tuple[int, int]] = []
    for rx in (_CODE_FENCE, _TABLE_BLOCK):
        for m in rx.finditer(text):
            ranges.append((m.start(), m.end()))
    ranges.sort()
    # Merge overlaps.
    merged: list[tuple[int, int]] = []
    for start, end in ranges:
        if merged and start <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], end))
        else:
            merged.append((start, end))
    return merged


def _in_ranges(pos: int, ranges: list[tuple[int, int]]) -> bool:
    return any(s <= pos < e for s, e in ranges)


def segment_text(text: str) -> list[Segment]:
    """Sentence/line segmentation; code fences and tables are single segments."""
    protected = _protected_ranges(text)
    segments: list[Segment] = []
    n = 0

    # Emit protected blocks and intervening content.
    cursor = 0
    blocks: list[tuple[int, int, bool]] = []
    for start, end in protected:
        if cursor < start:
            blocks.append((cursor, start, False))
        blocks.append((start, end, True))
        cursor = end
    if cursor < len(text):
        blocks.append((cursor, len(text), False))

    for start, end, is_protected in blocks:
        chunk = text[start:end]
        if not chunk.strip():
            continue
        if is_protected:
            segments.append(Segment(id=f"S{n}", start=start, end=end))
            n += 1
            continue
        # Split remaining by blank lines first, then sentences.
        parts = re.split(r"(\n\s*\n)", chunk)
        offset = start
        for part in parts:
            if not part or not part.strip():
                offset += len(part)
                continue
            if part.startswith("\n"):
                offset += len(part)
                continue
            for m in _SENTENCE.finditer(part):
                s = offset + m.start()
                e = offset + m.end()
                # Trim trailing whitespace from span end but keep content.
                while e > s and text[e - 1] in " \t":
                    e -= 1
                if e > s and text[s:e].strip():
                    # Skip leading whitespace in span.
                    while s < e and text[s] in " \t":
                        s += 1
                    segments.append(Segment(id=f"S{n}", start=s, end=e))
                    n += 1
            offset += len(part)

    if not segments and text.strip():
        segments.append(Segment(id="S0", start=0, end=len(text)))
    return segments


def _looks_like_csv_block(lines: list[str]) -> bool:
    if len(lines) < 2:
        return False
    # Prefer comma or tab delimited rows with a stable column count ≥ 2
    for sep in ("\t", ","):
        counts = [ln.count(sep) for ln in lines if ln.strip()]
        if not counts:
            continue
        if min(counts) >= 1 and max(counts) == min(counts):
            # Avoid treating prose with commas as CSV (require ≥3 columns or a header-ish first row)
            cols = counts[0] + 1
            if cols >= 3 or sep == "\t":
                return True
    return False


def _csv_lines_to_markdown(lines: list[str]) -> list[str]:
    import csv

    sample = "\n".join(lines)
    dialect = csv.excel
    if "\t" in lines[0] and lines[0].count("\t") >= lines[0].count(","):
        dialect = csv.excel_tab
    reader = csv.reader(io.StringIO(sample), dialect=dialect)
    rows = [[c.strip() for c in row] for row in reader if any(c.strip() for c in row)]
    if not rows:
        return lines
    cols = max(len(r) for r in rows)
    rows = [(r + [""] * cols)[:cols] for r in rows]
    md = ["| " + " | ".join(rows[0]) + " |", "| " + " | ".join(["---"] * cols) + " |"]
    for r in rows[1:]:
        md.append("| " + " | ".join(r) + " |")
    return md


def _promote_csv_tables(text: str) -> str:
    """Turn contiguous CSV/TSV blocks into markdown tables (keeps wording)."""
    lines = text.split("\n")
    out: list[str] = []
    i = 0
    while i < len(lines):
        # Already a markdown table — leave alone
        if lines[i].strip().startswith("|"):
            out.append(lines[i])
            i += 1
            continue
        # Gather a candidate delimited block
        j = i
        block: list[str] = []
        while j < len(lines) and lines[j].strip() and not lines[j].strip().startswith("|"):
            block.append(lines[j])
            j += 1
        if _looks_like_csv_block(block):
            out.extend(_csv_lines_to_markdown(block))
            i = j
            continue
        out.append(lines[i])
        i += 1
    return "\n".join(out)


def parse_text(raw: str, *, language: str = "en") -> NormalizedText:
    text = _normalize_newlines(raw)
    text = _promote_csv_tables(text)
    # Touch markdown-it so MD documents are accepted as plain text with structure later.
    _ = MarkdownIt()
    segs = segment_text(text)
    return NormalizedText(text=text, segments=segs, language=language)


def parse_bytes(data: bytes, filename: str = "input.txt") -> NormalizedText:
    lower = filename.lower()
    if lower.endswith(".docx"):
        return _parse_docx(data)
    # .md / .txt / .csv / unknown → decode as utf-8
    try:
        raw = data.decode("utf-8")
    except UnicodeDecodeError:
        raw = data.decode("latin-1")
    # Strip UTF-8 BOM from Excel CSV exports
    if raw.startswith("\ufeff"):
        raw = raw.lstrip("\ufeff")
    return parse_text(raw)


def _parse_docx(data: bytes) -> NormalizedText:
    from docx import Document

    doc = Document(io.BytesIO(data))
    parts: list[str] = []
    for p in doc.paragraphs:
        parts.append(p.text)
    for table in doc.tables:
        rows = []
        for row in table.rows:
            cells = [c.text.strip() for c in row.cells]
            rows.append("| " + " | ".join(cells) + " |")
        if rows:
            # Insert a markdown-ish separator after header.
            if len(rows) >= 1:
                cols = rows[0].count("|") - 1
                sep = "| " + " | ".join(["---"] * max(cols, 1)) + " |"
                parts.append(rows[0])
                parts.append(sep)
                parts.extend(rows[1:])
    raw = "\n\n".join(p for p in parts if p is not None)
    return parse_text(raw)
