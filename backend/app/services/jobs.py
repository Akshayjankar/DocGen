"""In-memory job registry with SSE event queues."""

from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import uuid4

from app.models.blocks import Block
from app.models.document import JobStatus
from app.models.theme import Theme


@dataclass
class JobRecord:
    id: str
    status: JobStatus = JobStatus.queued
    progress: float = 0.0
    message: str = "Queued"
    error: str | None = None
    document_id: str | None = None
    blocks: list[Block] = field(default_factory=list)
    theme: Theme | None = None
    preserved_pct: float | None = None
    source_text: str = ""
    docx_path: str | None = None
    pdf_path: str | None = None
    lint: list[dict[str, Any]] = field(default_factory=list)
    diffs: list[dict[str, Any]] = field(default_factory=list)
    meta: dict[str, Any] = field(default_factory=dict)
    options: dict[str, Any] = field(default_factory=dict)
    mode: str = "format_only"
    doc_type: str = "sop"
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    subscribers: list[asyncio.Queue[str]] = field(default_factory=list)

    def to_public(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "status": self.status.value,
            "progress": self.progress,
            "message": self.message,
            "error": self.error,
            "document_id": self.document_id or self.id,
            "preserved_pct": self.preserved_pct,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


class JobStore:
    def __init__(self) -> None:
        self._jobs: dict[str, JobRecord] = {}

    def create(self) -> JobRecord:
        job = JobRecord(id=uuid4().hex)
        self._jobs[job.id] = job
        return job

    def get(self, job_id: str) -> JobRecord | None:
        return self._jobs.get(job_id)

    def _event_payload(self, job: JobRecord) -> str:
        return json.dumps(
            {
                "status": job.status.value,
                "progress": job.progress,
                "message": job.message,
                "document_id": job.document_id or job.id,
                "preserved_pct": job.preserved_pct,
                "error": job.error,
                "lint": job.lint,
                "diffs": job.diffs,
            }
        )

    async def emit(self, job: JobRecord, status: JobStatus, progress: float, message: str) -> None:
        job.status = status
        job.progress = progress
        job.message = message
        job.updated_at = datetime.utcnow()
        payload = self._event_payload(job)
        dead: list[asyncio.Queue[str]] = []
        for q in job.subscribers:
            try:
                q.put_nowait(payload)
            except Exception:
                dead.append(q)
        for q in dead:
            job.subscribers.remove(q)

    def subscribe(self, job: JobRecord) -> asyncio.Queue[str]:
        q: asyncio.Queue[str] = asyncio.Queue()
        job.subscribers.append(q)
        # Seed current state (includes lint/diffs when already computed)
        q.put_nowait(self._event_payload(job))
        return q


job_store = JobStore()
