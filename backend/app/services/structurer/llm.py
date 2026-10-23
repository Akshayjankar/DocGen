"""Span-referencing LLM structurer with schema validation + rules fallback."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Literal
from uuid import uuid4

from app.models.blocks import Block, SourceSpan
from app.models.document import DocType
from app.services.ingest.parse import NormalizedText
from app.services.structurer.providers.router import ProviderRouter, cache_key_for
from app.services.structurer.rules import RulesStructurer

_PROMPTS = Path(__file__).parent / "prompts"

_VALID_TYPES = {
    "heading",
    "paragraph",
    "steps",
    "bullets",
    "table",
    "callout_info",
    "callout_warning",
    "callout_success",
    "code",
    "figure",
    "divider",
    "quote",
    "page_break",
}


def _load_prompt(doc_type: DocType, mode: str) -> str:
    if mode == "improve":
        path = _PROMPTS / "improve.md"
    else:
        path = _PROMPTS / f"{doc_type.value}.md"
        if not path.exists():
            path = _PROMPTS / "default.md"
    return path.read_text(encoding="utf-8")


def _segments_prompt(normalized: NormalizedText) -> str:
    lines = []
    for seg in normalized.segments:
        snippet = normalized.text[seg.start : seg.end].replace("\n", "\\n")
        if len(snippet) > 400:
            snippet = snippet[:400] + "…"
        lines.append(f"[{seg.id}] {snippet}")
    return "\n".join(lines)


class LLMStructurer:
    def __init__(self, router: ProviderRouter | None = None) -> None:
        self.router = router or ProviderRouter()
        self.fallback = RulesStructurer()
        self.last_provider: str | None = None

    async def structure(
        self,
        normalized: NormalizedText,
        doc_type: DocType,
        mode: Literal["format_only", "improve"] = "format_only",
    ) -> list[Block]:
        seg_map = normalized.segment_map()
        system = _load_prompt(doc_type, mode)
        user = (
            f"Document type: {doc_type.value}\nMode: {mode}\n\n"
            f"Segments:\n{_segments_prompt(normalized)}\n\n"
            "Return JSON now."
        )
        key = cache_key_for(normalized.text, doc_type.value, mode)

        last_err: str | None = None
        for attempt in range(3):
            try:
                raw = await self.router.complete_json(
                    system=system,
                    user=user if attempt == 0 else user + f"\n\nValidation error: {last_err}",
                    temperature=0.0,
                    cache_key=key if attempt == 0 else None,
                )
                self.last_provider = self.router.last_provider
                blocks = self._resolve(raw, seg_map, normalized, mode)
                blocks = self._append_missing(blocks, normalized, seg_map)
                return blocks
            except Exception as exc:  # noqa: BLE001
                last_err = str(exc)
                continue

        self.last_provider = "rules"
        return self.fallback.structure(normalized, doc_type, mode)

    def structure_sync(
        self,
        normalized: NormalizedText,
        doc_type: DocType,
        mode: Literal["format_only", "improve"] = "format_only",
    ) -> list[Block]:
        """Always rules (for sync CLI / offline)."""
        return self.fallback.structure(normalized, doc_type, mode)

    def _resolve(
        self,
        raw: dict[str, Any],
        seg_map: dict[str, Any],
        normalized: NormalizedText,
        mode: str,
    ) -> list[Block]:
        if "blocks" not in raw or not isinstance(raw["blocks"], list):
            raise ValueError("Missing blocks array")
        out: list[Block] = []
        for item in raw["blocks"]:
            if not isinstance(item, dict):
                raise ValueError("Block must be object")
            btype = item.get("type")
            if btype not in _VALID_TYPES:
                raise ValueError(f"Invalid type {btype}")
            ids = item.get("segment_ids") or item.get("segments") or []
            if not isinstance(ids, list):
                raise ValueError("segment_ids must be list")
            spans = []
            for sid in ids:
                if sid not in seg_map:
                    raise ValueError(f"Unknown segment {sid}")
                spans.append(seg_map[sid])

            if mode == "format_only" and item.get("text"):
                # Reject free text in format-only
                raise ValueError("Free text not allowed in format_only")

            if btype in ("steps", "bullets"):
                items: list[SourceSpan | str] = [
                    SourceSpan(start=s.start, end=s.end) for s in spans
                ]
                out.append(
                    Block(
                        id=uuid4().hex[:12],
                        type=btype,  # type: ignore[arg-type]
                        items=items,
                        origin="source",
                    )
                )
            elif btype in ("divider", "page_break"):
                out.append(Block(id=uuid4().hex[:12], type=btype, origin="generated"))  # type: ignore[arg-type]
            else:
                if not spans:
                    raise ValueError(f"{btype} requires segment_ids")
                span = SourceSpan(start=spans[0].start, end=spans[-1].end)
                origin = "source"
                text = None
                if mode == "improve" and item.get("text"):
                    text = str(item["text"])
                    origin = "rewritten"
                out.append(
                    Block(
                        id=uuid4().hex[:12],
                        type=btype,  # type: ignore[arg-type]
                        level=item.get("level"),
                        span=span,
                        text=text,
                        language=item.get("language"),
                        label=item.get("label"),
                        origin=origin,  # type: ignore[arg-type]
                    )
                )
        return out

    def _append_missing(
        self,
        blocks: list[Block],
        normalized: NormalizedText,
        seg_map: dict[str, Any],
    ) -> list[Block]:
        used: set[str] = set()
        for b in blocks:
            if b.span:
                for sid, seg in seg_map.items():
                    if seg.start >= b.span.start and seg.end <= b.span.end:
                        used.add(sid)
            if b.items:
                for item in b.items:
                    if isinstance(item, SourceSpan):
                        for sid, seg in seg_map.items():
                            if seg.start == item.start and seg.end == item.end:
                                used.add(sid)
        for sid, seg in seg_map.items():
            if sid in used:
                continue
            chunk = normalized.text[seg.start : seg.end].strip()
            if not chunk:
                continue
            blocks.append(
                Block(
                    id=uuid4().hex[:12],
                    type="paragraph",
                    span=SourceSpan(start=seg.start, end=seg.end),
                    origin="source",
                )
            )
        return blocks
