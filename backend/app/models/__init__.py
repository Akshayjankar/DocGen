"""Pydantic / SQLModel data contracts."""

from app.models.blocks import Block, BlockType, SourceSpan, TableData
from app.models.document import (
    DocType,
    DocumentMeta,
    DocumentRequest,
    Job,
    JobStatus,
    RenderOptions,
)
from app.models.theme import (
    BorderSpec,
    ContrastPair,
    ContrastReport,
    FontPair,
    HexColor,
    Palette,
    Theme,
)

__all__ = [
    "Block",
    "BlockType",
    "BorderSpec",
    "ContrastPair",
    "ContrastReport",
    "DocType",
    "DocumentMeta",
    "DocumentRequest",
    "FontPair",
    "HexColor",
    "Job",
    "JobStatus",
    "Palette",
    "RenderOptions",
    "SourceSpan",
    "TableData",
    "Theme",
]
