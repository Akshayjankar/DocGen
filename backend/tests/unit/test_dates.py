"""Revision 3 WP-E: date format option."""

from __future__ import annotations

from app.models.theme import LayoutSpec
from app.services.renderer.dates import format_date


def test_human_default() -> None:
    assert format_date("2026-10-23") == "23 Oct 2026"


def test_iso_dmy_mdy() -> None:
    assert format_date("2026-10-23", LayoutSpec(date_format="iso")) == "2026-10-23"
    assert format_date("2026-10-23", LayoutSpec(date_format="dmy")) == "23/10/2026"
    assert format_date("2026-10-23", LayoutSpec(date_format="mdy")) == "10/23/2026"


def test_strips_soft_hyphen() -> None:
    assert "\u00ad" not in format_date("2026\u00ad-10-23")
