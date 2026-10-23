"""Heuristic Markdown/plain-text structurer — offline, no network."""

from __future__ import annotations

import re
from typing import Literal
from uuid import uuid4

from app.models.blocks import Block, SourceSpan, TableData
from app.models.document import DocType
from app.services.ingest.parse import NormalizedText

_HEADING = re.compile(r"^(#{1,3})\s+(.+)$")
_NUMBERED = re.compile(r"^(\d+)[.)]\s+(.+)$")
_BULLET = re.compile(r"^[-*•]\s+(.+)$")
_CALLOUT = re.compile(
    r"^(note|info|warning|caution|important|success|tip)\s*:\s*(.+)$",
    re.I,
)
_CODE_FENCE_OPEN = re.compile(r"^```(\w+)?\s*$")
_CODE_FENCE_CLOSE = re.compile(r"^```\s*$")
_TABLE_ROW = re.compile(r"^\|.+\|$")
_TABLE_SEP = re.compile(r"^\|[\s|:-]+\|$")
_HR = re.compile(r"^(-{3,}|\*{3,}|_{3,})\s*$")
_SHELL_LANGS = {"bash", "sh", "shell", "zsh", "powershell", "pwsh", "cmd"}


def _span(text: str, start: int, end: int) -> SourceSpan:
    return SourceSpan(start=start, end=end)


def _find_span(source: str, needle: str, search_from: int = 0) -> SourceSpan | None:
    idx = source.find(needle, search_from)
    if idx < 0:
        # Try stripped / collapsed whitespace variants.
        idx = source.find(needle.strip(), search_from)
    if idx < 0:
        return None
    return SourceSpan(start=idx, end=idx + len(needle if source[idx:].startswith(needle) else needle.strip()))


class RulesStructurer:
    """Parse Markdown-ish input into Block[] with source spans."""

    def structure(
        self,
        normalized: NormalizedText,
        doc_type: DocType,
        mode: Literal["format_only", "improve"] = "format_only",
    ) -> list[Block]:
        source = normalized.text
        lines = source.split("\n")
        blocks: list[Block] = []
        i = 0
        # Track absolute offsets.
        offsets: list[int] = []
        pos = 0
        for ln in lines:
            offsets.append(pos)
            pos += len(ln) + 1  # + newline (except maybe last — close enough)

        covered: list[tuple[int, int]] = []

        while i < len(lines):
            line = lines[i]
            stripped = line.strip()
            line_start = offsets[i]

            if not stripped:
                i += 1
                continue

            # Code fence
            m_open = _CODE_FENCE_OPEN.match(stripped)
            if m_open:
                lang = (m_open.group(1) or "").lower()
                j = i + 1
                body_lines: list[str] = []
                while j < len(lines) and not _CODE_FENCE_CLOSE.match(lines[j].strip()):
                    body_lines.append(lines[j])
                    j += 1
                end_line = j if j < len(lines) else j - 1
                end_off = offsets[end_line] + len(lines[end_line]) if end_line < len(lines) else len(source)
                # Include closing fence if present.
                if j < len(lines):
                    end_off = offsets[j] + len(lines[j])
                code_body = "\n".join(body_lines)
                code_start = offsets[i + 1] if i + 1 < len(lines) else line_start
                code_end = offsets[j] if j < len(lines) else len(source)
                # Prefer span over body only (exclude fences for content-lock of code text).
                span = SourceSpan(start=code_start, end=max(code_start, code_end - (0 if j >= len(lines) else 0)))
                # More precise: span covering just the code body.
                if body_lines:
                    span = SourceSpan(start=offsets[i + 1], end=offsets[j] if j < len(lines) else len(source))
                    # Trim trailing newline before closing fence.
                    if span.end > span.start and source[span.end - 1] == "\n":
                        span = SourceSpan(start=span.start, end=span.end - 1)
                label = "TERMINAL" if lang in _SHELL_LANGS else "FILE CONTENT"
                blocks.append(
                    Block(
                        id=uuid4().hex[:12],
                        type="code",
                        span=span,
                        text=code_body,
                        language=lang or None,
                        label=label,
                        origin="source",
                    )
                )
                covered.append((offsets[i], end_off))
                i = j + 1
                continue

            # Table
            if _TABLE_ROW.match(stripped):
                table_lines = [stripped]
                j = i + 1
                while j < len(lines) and _TABLE_ROW.match(lines[j].strip()):
                    table_lines.append(lines[j].strip())
                    j += 1
                headers, rows = _parse_table(table_lines)
                end_off = offsets[j - 1] + len(lines[j - 1])
                blocks.append(
                    Block(
                        id=uuid4().hex[:12],
                        type="table",
                        table=TableData(headers=headers, rows=rows),
                        text=source[line_start:end_off],
                        origin="source",
                    )
                )
                covered.append((line_start, end_off))
                i = j
                continue

            # Horizontal rule (--- / *** / ___)
            if _HR.match(stripped):
                blocks.append(
                    Block(
                        id=uuid4().hex[:12],
                        type="divider",
                        span=SourceSpan(
                            start=line_start + line.find(stripped),
                            end=line_start + line.find(stripped) + len(stripped),
                        ),
                        origin="source",
                    )
                )
                covered.append((line_start, line_start + len(line)))
                i += 1
                continue

            # Heading
            m_h = _HEADING.match(stripped)
            if m_h:
                level = len(m_h.group(1))
                title = m_h.group(2).strip()
                # Span points at title text inside the line.
                title_idx = line.find(title)
                span = SourceSpan(start=line_start + title_idx, end=line_start + title_idx + len(title))
                blocks.append(
                    Block(
                        id=uuid4().hex[:12],
                        type="heading",
                        level=level,
                        span=span,
                        origin="source",
                    )
                )
                covered.append((line_start, line_start + len(line)))
                i += 1
                continue

            # Memo: question lines that start a block become headings
            if (
                doc_type == DocType.memo
                and stripped.endswith("?")
                and len(stripped) < 120
                and not _NUMBERED.match(stripped)
            ):
                span = SourceSpan(
                    start=line_start + line.find(stripped),
                    end=line_start + line.find(stripped) + len(stripped),
                )
                blocks.append(
                    Block(
                        id=uuid4().hex[:12],
                        type="heading",
                        level=2,
                        span=span,
                        origin="source",
                    )
                )
                covered.append((line_start, line_start + len(line)))
                i += 1
                continue

            # ALL-CAPS short line as H2 (plain text heading heuristic)
            if (
                len(stripped) < 80
                and stripped.isupper()
                and any(c.isalpha() for c in stripped)
                and not _NUMBERED.match(stripped)
            ):
                span = SourceSpan(start=line_start + line.find(stripped), end=line_start + line.find(stripped) + len(stripped))
                blocks.append(
                    Block(
                        id=uuid4().hex[:12],
                        type="heading",
                        level=2,
                        span=span,
                        origin="source",
                    )
                )
                covered.append((line_start, line_start + len(line)))
                i += 1
                continue

            # Callout
            m_c = _CALLOUT.match(stripped)
            if m_c:
                kind = m_c.group(1).lower()
                body = m_c.group(2).strip()
                btype: Literal["callout_info", "callout_warning", "callout_success"]
                if kind in ("warning", "caution", "important"):
                    btype = "callout_warning"
                elif kind in ("success", "tip"):
                    btype = "callout_success"
                else:
                    btype = "callout_info"
                body_idx = line.lower().find(body.lower())
                if body_idx < 0:
                    body_idx = line.find(body)
                span = SourceSpan(start=line_start + max(0, body_idx), end=line_start + max(0, body_idx) + len(body))
                blocks.append(
                    Block(
                        id=uuid4().hex[:12],
                        type=btype,
                        span=span,
                        label=kind.upper(),
                        origin="source",
                    )
                )
                covered.append((line_start, line_start + len(line)))
                i += 1
                continue

            # Numbered steps (consecutive)
            m_n = _NUMBERED.match(stripped)
            if m_n:
                items: list[SourceSpan | str] = []
                j = i
                while j < len(lines):
                    sm = _NUMBERED.match(lines[j].strip())
                    if not sm:
                        break
                    item_text = sm.group(2).strip()
                    ls = offsets[j]
                    idx = lines[j].find(item_text)
                    items.append(SourceSpan(start=ls + idx, end=ls + idx + len(item_text)))
                    j += 1
                blocks.append(
                    Block(
                        id=uuid4().hex[:12],
                        type="steps",
                        items=items,
                        origin="source",
                    )
                )
                covered.append((offsets[i], offsets[j - 1] + len(lines[j - 1])))
                i = j
                continue

            # Bullets (consecutive)
            m_b = _BULLET.match(stripped)
            if m_b:
                items = []
                j = i
                while j < len(lines):
                    sm = _BULLET.match(lines[j].strip())
                    if not sm:
                        break
                    item_text = sm.group(1).strip()
                    ls = offsets[j]
                    idx = lines[j].find(item_text)
                    items.append(SourceSpan(start=ls + idx, end=ls + idx + len(item_text)))
                    j += 1
                blocks.append(
                    Block(
                        id=uuid4().hex[:12],
                        type="bullets",
                        items=items,
                        origin="source",
                    )
                )
                covered.append((offsets[i], offsets[j - 1] + len(lines[j - 1])))
                i = j
                continue

            # Paragraph: gather until blank
            para_lines = [stripped]
            j = i + 1
            while j < len(lines) and lines[j].strip() and not _is_structural(lines[j].strip()):
                para_lines.append(lines[j].strip())
                j += 1
            " ".join(para_lines)
            # Find para in source — use first line span expanded.
            first = stripped
            idx = source.find(first, line_start)
            if idx < 0:
                idx = line_start + (line.find(first) if first in line else 0)
            # End at last gathered line.
            last_line_idx = j - 1
            end = offsets[last_line_idx] + len(lines[last_line_idx])
            # Prefer contiguous span from first content to end of last line.
            span = SourceSpan(start=idx, end=end)
            # For multi-line, content-lock uses exact slice; normalize spaces in verifier.
            blocks.append(
                Block(
                    id=uuid4().hex[:12],
                    type="paragraph",
                    span=span,
                    origin="source",
                )
            )
            covered.append((line_start, end))
            i = j

        # Append any uncovered non-whitespace as paragraphs (nothing dropped).
        blocks = _append_uncovered(source, blocks, covered)
        _ = doc_type  # templates used by lint, not structure
        _ = mode
        return blocks


def _is_structural(stripped: str) -> bool:
    return bool(
        _HEADING.match(stripped)
        or _NUMBERED.match(stripped)
        or _BULLET.match(stripped)
        or _CALLOUT.match(stripped)
        or _CODE_FENCE_OPEN.match(stripped)
        or _TABLE_ROW.match(stripped)
        or _HR.match(stripped)
        or (len(stripped) < 80 and stripped.isupper() and any(c.isalpha() for c in stripped))
    )


def _parse_table(table_lines: list[str]) -> tuple[list[str], list[list[str]]]:
    def split_row(row: str) -> list[str]:
        # Keep empty cells (consecutive ||) — do not drop blanks
        return [c.strip() for c in row.strip().strip("|").split("|")]

    rows_raw = [ln for ln in table_lines if not _TABLE_SEP.match(ln)]
    if not rows_raw:
        return [], []
    headers = split_row(rows_raw[0])
    rows = [split_row(r) for r in rows_raw[1:]]
    cols = max(len(headers), max((len(r) for r in rows), default=0))
    headers = (headers + [""] * cols)[:cols]
    rows = [(r + [""] * cols)[:cols] for r in rows]
    return headers, rows


def _append_uncovered(
    source: str,
    blocks: list[Block],
    covered: list[tuple[int, int]],
) -> list[Block]:
    if not covered:
        return blocks
    covered_sorted = sorted(covered)
    merged: list[tuple[int, int]] = []
    for s, e in covered_sorted:
        if merged and s <= merged[-1][1] + 1:
            merged[-1] = (merged[-1][0], max(merged[-1][1], e))
        else:
            merged.append((s, e))

    gaps: list[tuple[int, int]] = []
    cursor = 0
    for s, e in merged:
        if cursor < s:
            gaps.append((cursor, s))
        cursor = max(cursor, e)
    if cursor < len(source):
        gaps.append((cursor, len(source)))

    for s, e in gaps:
        chunk = source[s:e]
        if not chunk.strip():
            continue
        # Skip pure markdown syntax leftovers (#, fences markers alone).
        stripped = chunk.strip()
        if stripped in ("```", "~~~") or re.fullmatch(r"#{1,6}", stripped):
            continue
        # Trim to content.
        leading = len(chunk) - len(chunk.lstrip())
        trailing = len(chunk) - len(chunk.rstrip())
        ns, ne = s + leading, e - trailing
        if ne <= ns:
            continue
        # Avoid duplicating text already fully inside a span block.
        already = False
        for b in blocks:
            if b.span and b.span.start <= ns and b.span.end >= ne:
                already = True
                break
        if already:
            continue
        blocks.append(
            Block(
                id=uuid4().hex[:12],
                type="paragraph",
                span=SourceSpan(start=ns, end=ne),
                origin="source",
            )
        )
    return blocks
