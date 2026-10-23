"""Structurer protocol."""

from __future__ import annotations

from typing import Literal, Protocol

from app.models.blocks import Block
from app.models.document import DocType
from app.services.ingest.parse import NormalizedText


class Structurer(Protocol):
    def structure(
        self,
        normalized: NormalizedText,
        doc_type: DocType,
        mode: Literal["format_only", "improve"] = "format_only",
    ) -> list[Block]: ...
