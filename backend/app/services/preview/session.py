"""PreviewSession — shared structure for live paper + export (WP3)."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from pathlib import Path
from threading import Lock
from uuid import uuid4

from app.models.blocks import Block
from app.models.document import DocumentMeta, RenderOptions
from app.models.theme import Theme


@dataclass
class PreviewSession:
    id: str
    source_text: str
    blocks: list[Block]
    theme: Theme
    meta: DocumentMeta
    options: RenderOptions
    structured_by: str = "rules"
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    docx_path: Path | None = None
    pdf_path: Path | None = None
    page_pngs: list[Path] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    duration_ms: float = 0.0
    text_hash: str = ""


class PreviewStore:
    def __init__(self) -> None:
        self._lock = Lock()
        self._sessions: dict[str, PreviewSession] = {}

    def create(self, session: PreviewSession) -> PreviewSession:
        with self._lock:
            self._sessions[session.id] = session
            return session

    def get(self, preview_id: str) -> PreviewSession | None:
        with self._lock:
            return self._sessions.get(preview_id)

    def update(self, session: PreviewSession) -> PreviewSession:
        with self._lock:
            session.updated_at = time.time()
            self._sessions[session.id] = session
            return session

    def delete(self, preview_id: str) -> None:
        with self._lock:
            self._sessions.pop(preview_id, None)


preview_store = PreviewStore()


def new_preview_id() -> str:
    return uuid4().hex
