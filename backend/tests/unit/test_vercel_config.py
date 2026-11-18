"""Tests for Vercel configuration adjustments."""

from __future__ import annotations

import os
from pathlib import Path
from unittest import mock

from app.config import Settings


def test_adjust_for_vercel_defaults() -> None:
    with mock.patch.dict(os.environ, {"VERCEL": "1"}, clear=False):
        settings = Settings()
        assert settings.database_url == "sqlite:////tmp/docgen.db"
        assert settings.data_dir == Path("/tmp/data")


def test_adjust_for_vercel_custom_url() -> None:
    with mock.patch.dict(
        os.environ,
        {"VERCEL": "1", "VERCEL_PROJECT_PRODUCTION_URL": "docgen-preview.vercel.app"},
        clear=False,
    ):
        settings = Settings()
        assert settings.frontend_origin == "https://docgen-preview.vercel.app"


def test_adjust_for_vercel_preserves_custom_db() -> None:
    with mock.patch.dict(
        os.environ,
        {"VERCEL": "1", "DATABASE_URL": "postgresql://user:pass@host/db"},
        clear=False,
    ):
        settings = Settings()
        assert settings.database_url == "postgresql://user:pass@host/db"
