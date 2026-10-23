"""Sentence-level content preservation score."""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from rapidfuzz import fuzz

from app.models.blocks import Block

_SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+|\n+")
_WS = re.compile(r"\s+")


def _norm(s: str) -> str:
    return _WS.sub(" ", s).strip().lower()


def _sentences(text: str) -> list[str]:
    parts = [p.strip() for p in _SENTENCE_SPLIT.split(text) if p.strip()]
    # Also keep significant short lines (headings without punctuation).
    if not parts and text.strip():
        return [text.strip()]
    return parts


@dataclass
class ContentLockResult:
    preserved_pct: float
    missing: list[str] = field(default_factory=list)
    added: list[str] = field(default_factory=list)
    matched: int = 0
    total_source: int = 0


def _block_texts(blocks: list[Block], source: str) -> list[str]:
    texts: list[str] = []
    for b in blocks:
        if b.type in ("divider", "page_break"):
            continue
        if b.type in ("steps", "bullets") and b.items:
            texts.extend(b.resolved_items(source))
        elif b.type == "table" and b.table:
            texts.extend(b.table.headers)
            for row in b.table.rows:
                texts.extend(row)
        else:
            t = b.resolved_text(source)
            if t:
                texts.append(t)
            elif b.text:
                texts.append(b.text)
    return texts


def score(
    source: str,
    blocks: list[Block],
    *,
    mode: str = "format_only",
    fuzzy_threshold: float = 90.0,
) -> ContentLockResult:
    """
    Format-only: exact normalized sentence coverage must be 100% by construction.
    Improve mode: report fuzzy matches and additions.
    """
    # Collect all text represented in blocks via spans (authoritative for format_only).
    covered_chars = set()
    for b in blocks:
        if b.span:
            for i in range(b.span.start, b.span.end):
                covered_chars.add(i)
        if b.items:
            for item in b.items:
                if hasattr(item, "start"):
                    for i in range(item.start, item.end):  # type: ignore[union-attr]
                        covered_chars.add(i)

    # Source sentences that have non-whitespace content.
    source_sents = _sentences(source)
    # Filter markdown syntax-only lines from "must preserve" set for scoring content.
    meaningful = []
    for s in source_sents:
        ns = _norm(s)
        if not ns:
            continue
        # Skip markdown chrome / list markers / separators that aren't user prose.
        if re.fullmatch(r"#{1,6}", ns):
            continue
        if ns.startswith("```"):
            continue
        if re.fullmatch(r"\|?[\s|:-]+\|?", ns):
            continue
        if re.fullmatch(r"\d+[.)]?", ns):  # bare "1." leftovers from split
            continue
        if re.fullmatch(r"[-*•]+", ns):
            continue
        meaningful.append(s)

    block_blob = "\n".join(_block_texts(blocks, source))
    block_sents = [_norm(s) for s in _sentences(block_blob)]
    block_set = set(block_sents)

    missing: list[str] = []
    matched = 0
    for s in meaningful:
        ns = _norm(s)
        # Strip leading markdown markers for comparison.
        ns_clean = re.sub(r"^#{1,3}\s+", "", ns)
        ns_clean = re.sub(r"^[-*•]\s+", "", ns_clean)
        ns_clean = re.sub(r"^\d+[.)]\s+", "", ns_clean)
        ns_clean = re.sub(
            r"^(note|info|warning|caution|important|success|tip)\s*:\s*",
            "",
            ns_clean,
        )

        found = False
        # Strip table pipes for comparison.
        ns_table = re.sub(r"\s*\|\s*", " ", ns_clean).strip()
        if ns_clean in block_set or ns in block_set or ns_table in block_set:
            found = True
        elif any(ns_clean and ns_clean in bs for bs in block_set):
            found = True
        elif ns_table and any(ns_table in bs for bs in block_set):
            found = True
        elif mode == "improve":
            for bs in block_set:
                if fuzz.ratio(ns_clean, bs) >= fuzzy_threshold:
                    found = True
                    break
        else:
            # Format-only: also accept if every non-ws char of sentence is in a span.
            idx = source.lower().find(s.lower())
            if idx >= 0:
                span_ok = all(
                    (c.isspace() or c in "#*`|>[]()-_+~.:=!" or c.isdigit() or (idx + i) in covered_chars)
                    for i, c in enumerate(s)
                )
                if span_ok:
                    found = True
            # Substring containment in resolved block text.
            blob_n = _norm(block_blob)
            if not found and ns_clean and ns_clean in blob_n:
                found = True
            if not found and ns_table and ns_table in blob_n:
                found = True
            # Table rows: all cell texts present in block output.
            if not found and "|" in s:
                cells = [c.strip() for c in s.strip().strip("|").split("|") if c.strip()]
                if cells and all(_norm(c) in blob_n for c in cells):
                    found = True

        if found:
            matched += 1
        else:
            missing.append(s)

    added: list[str] = []
    if mode == "improve":
        for bs in block_sents:
            if not any(fuzz.ratio(bs, _norm(s)) >= fuzzy_threshold for s in meaningful):
                if bs:
                    added.append(bs)

    total = max(len(meaningful), 1)
    pct = round(100.0 * matched / total, 2)
    # Format-only: ignore markdown chrome (#, `|`, fence ticks, list markers)
    # when proving span coverage; user wording lives in resolved spans/items.
    if mode == "format_only":
        ignorable = set("#*`|>[]()-_+~.:=!")
        content_idxs = [
            i
            for i, c in enumerate(source)
            if not c.isspace() and c not in ignorable and not c.isdigit()
        ]
        # Digits in list markers (1. 2.) are often outside item spans; still require
        # letter/content coverage. If all content chars are covered OR no missing
        # sentences → 100%.
        if content_idxs and all(i in covered_chars for i in content_idxs):
            pct = 100.0
            missing = []
        elif not missing:
            pct = 100.0
        elif matched == total:
            pct = 100.0
            missing = []

    return ContentLockResult(
        preserved_pct=pct,
        missing=missing,
        added=added,
        matched=matched,
        total_source=len(meaningful),
    )
