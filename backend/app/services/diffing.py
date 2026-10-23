"""Block-level word diffs for Improve mode."""

from __future__ import annotations

import difflib
from typing import Any

from app.models.blocks import Block


def word_diff(original: str, revised: str) -> list[dict[str, str]]:
    """Return list of {op, text} where op in equal|delete|insert."""
    a = original.split()
    b = revised.split()
    sm = difflib.SequenceMatcher(a=a, b=b)
    parts: list[dict[str, str]] = []
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            parts.append({"op": "equal", "text": " ".join(a[i1:i2])})
        elif tag == "delete":
            parts.append({"op": "delete", "text": " ".join(a[i1:i2])})
        elif tag == "insert":
            parts.append({"op": "insert", "text": " ".join(b[j1:j2])})
        elif tag == "replace":
            parts.append({"op": "delete", "text": " ".join(a[i1:i2])})
            parts.append({"op": "insert", "text": " ".join(b[j1:j2])})
    return parts


def block_diffs(source: str, blocks: list[Block]) -> list[dict[str, Any]]:
    diffs: list[dict[str, Any]] = []
    for b in blocks:
        if b.origin != "rewritten" or not b.span or not b.text:
            continue
        original = b.span.extract(source)
        diffs.append(
            {
                "block_id": b.id,
                "type": b.type,
                "original": original,
                "revised": b.text,
                "accepted": None,
                "parts": word_diff(original, b.text),
            }
        )
    return diffs


def apply_diff_decisions(
    source: str,
    blocks: list[Block],
    decisions: dict[str, bool],
) -> list[Block]:
    """accepted=True keeps rewritten text; False reverts to span-only source."""
    out: list[Block] = []
    for b in blocks:
        if b.id not in decisions:
            out.append(b)
            continue
        if decisions[b.id]:
            out.append(b.model_copy(update={"origin": "rewritten"}))
        else:
            out.append(
                b.model_copy(update={"text": None, "origin": "source"})
            )
    return out
