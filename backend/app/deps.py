"""Shared FastAPI dependencies: DB and rate limit."""

from __future__ import annotations

from collections.abc import Generator
from typing import Annotated

from fastapi import Depends
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlmodel import Session, SQLModel, create_engine

from app.config import Settings, get_settings
from app.models import db as _db  # noqa: F401 — register SQLModel tables

_engine = None


def get_engine():
    global _engine
    if _engine is None:
        settings = get_settings()
        url = settings.database_url
        connect_args = {"check_same_thread": False} if url.startswith("sqlite") else {}
        _engine = create_engine(url, connect_args=connect_args)
        SQLModel.metadata.create_all(_engine)
    return _engine


def get_db() -> Generator[Session, None, None]:
    with Session(get_engine()) as session:
        yield session


limiter = Limiter(key_func=get_remote_address, default_limits=[])


SettingsDep = Annotated[Settings, Depends(get_settings)]
DbDep = Annotated[Session, Depends(get_db)]
