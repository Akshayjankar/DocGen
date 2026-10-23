"""Document request, meta, jobs."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator

from app.models.blocks import Block
from app.models.theme import Theme


class DocType(str, Enum):
    sop = "sop"
    report = "report"
    setup_guide = "setup_guide"
    release_notes = "release_notes"
    proposal = "proposal"
    policy = "policy"
    meeting_minutes = "meeting_minutes"
    memo = "memo"


def _clean_date(value: str) -> str:
    """Strip soft hyphens / non-breaking hyphens; prefer human date."""
    if not value:
        return value
    cleaned = value.replace("\u00ad", "").replace("\u2011", "-").strip()
    # ISO YYYY-MM-DD → "22 Oct 2026"
    if len(cleaned) >= 10 and cleaned[4] == "-" and cleaned[7] == "-":
        try:
            dt = datetime.strptime(cleaned[:10], "%Y-%m-%d")
            return f"{dt.day} {dt.strftime('%b %Y')}"
        except ValueError:
            return cleaned
    return cleaned


class DocumentMeta(BaseModel):
    title: str = "Untitled Document"
    version: str = "1.0"
    author: str = ""
    approver: str = ""
    reviewed_by: str = ""
    approved_by: str = ""
    document_id: str = ""
    classification: str = "Internal"
    date: str = Field(default_factory=lambda: datetime.utcnow().strftime("%Y-%m-%d"))
    subtitle: str = ""
    organization: str = ""
    subject: str = ""

    @field_validator("date", mode="before")
    @classmethod
    def _date(cls, v: object) -> object:
        if isinstance(v, str):
            return _clean_date(v)
        return v

    @property
    def doc_id(self) -> str:
        return self.document_id

    def effective_approver(self) -> str:
        return (self.approved_by or self.approver or "").strip()


class RenderOptions(BaseModel):
    cover: bool = True
    toc: bool | Literal["auto"] = "auto"
    revision_history: bool | Literal["auto"] = "auto"
    border: bool = True
    watermark: bool = False
    classification_label: bool = True
    redact_pii: bool = False
    page_numbers: bool = True
    cover_style: Literal["centered", "editorial", "minimal"] = "centered"


class DocumentRequest(BaseModel):
    text: str
    doc_type: DocType = DocType.sop
    mode: Literal["format_only", "improve"] = "format_only"
    theme: Theme | None = None
    brand_kit_id: str | None = None
    meta: DocumentMeta = Field(default_factory=DocumentMeta)
    options: RenderOptions = Field(default_factory=RenderOptions)


class JobStatus(str, Enum):
    queued = "queued"
    theme = "theme"
    ingest = "ingest"
    structure = "structure"
    verify = "verify"
    render_docx = "render_docx"
    render_pdf = "render_pdf"
    done = "done"
    failed = "failed"


class Job(BaseModel):
    id: str = Field(default_factory=lambda: uuid4().hex)
    status: JobStatus = JobStatus.queued
    progress: float = 0.0
    message: str = "Queued"
    error: str | None = None
    document_id: str | None = None
    blocks: list[Block] | None = None
    preserved_pct: float | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    extras: dict[str, Any] = Field(default_factory=dict)
