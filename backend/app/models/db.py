"""SQLModel persistence models."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import JSON, Column
from sqlmodel import Field, SQLModel


def utcnow() -> datetime:
    return datetime.now(UTC)


class BrandKit(SQLModel, table=True):
    id: str = Field(primary_key=True)
    name: str
    logo_path: str | None = None
    # Dual logos live inside theme_json["logos"] (LogoSet); no separate column required.
    theme_json: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    footer: str = ""
    classification: str = "Internal"
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)


class DocumentRecord(SQLModel, table=True):
    id: str = Field(primary_key=True)
    job_id: str
    title: str
    doc_type: str
    mode: str
    docx_path: str | None = None
    pdf_path: str | None = None
    preserved_pct: float | None = None
    created_at: datetime = Field(default_factory=utcnow)
    expires_at: datetime | None = None
