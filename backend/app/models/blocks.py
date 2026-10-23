"""Semantic document blocks and source spans."""

from __future__ import annotations

from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, Field


class SourceSpan(BaseModel):
    start: int
    end: int

    def extract(self, text: str) -> str:
        return text[self.start : self.end]


BlockType = Literal[
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
]


class TableData(BaseModel):
    headers: list[str]
    rows: list[list[str]]
    header_spans: list[SourceSpan] | None = None
    row_spans: list[list[SourceSpan]] | None = None


class Block(BaseModel):
    id: str = Field(default_factory=lambda: uuid4().hex[:12])
    type: BlockType
    level: int | None = None
    span: SourceSpan | None = None
    text: str | None = None
    items: list[SourceSpan | str] | None = None
    table: TableData | None = None
    language: str | None = None
    label: str | None = None
    origin: Literal["source", "rewritten", "generated"] = "source"

    def resolved_text(self, source: str) -> str:
        """Prefer original source span in format-only; else stored text."""
        if self.span is not None:
            return self.span.extract(source)
        return self.text or ""

    def resolved_items(self, source: str) -> list[str]:
        if not self.items:
            return []
        out: list[str] = []
        for item in self.items:
            if isinstance(item, SourceSpan):
                out.append(item.extract(source))
            else:
                out.append(item)
        return out
