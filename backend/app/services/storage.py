"""Temp file store with TTL auto-cleaner."""

from __future__ import annotations

import hashlib
import shutil
import time
from pathlib import Path

from app.config import get_settings


class Storage:
    def __init__(self, root: Path | None = None) -> None:
        settings = get_settings()
        self.root = root or (settings.data_dir / "jobs")
        self.root.mkdir(parents=True, exist_ok=True)
        self.ttl_seconds = settings.file_ttl_minutes * 60

    def job_dir(self, job_id: str) -> Path:
        d = self.root / job_id
        d.mkdir(parents=True, exist_ok=True)
        return d

    def save_bytes(self, job_id: str, data: bytes, suffix: str) -> Path:
        name = hashlib.sha256(data).hexdigest()[:24] + suffix
        path = self.job_dir(job_id) / name
        path.write_bytes(data)
        return path

    def cleanup_expired(self) -> int:
        settings = get_settings()
        if settings.store_history:
            return 0
        now = time.time()
        removed = 0
        for child in self.root.iterdir():
            if not child.is_dir():
                continue
            age = now - child.stat().st_mtime
            if age > self.ttl_seconds:
                shutil.rmtree(child, ignore_errors=True)
                removed += 1
        return removed


_storage: Storage | None = None


def get_storage() -> Storage:
    global _storage
    if _storage is None:
        _storage = Storage()
    return _storage
