"""Document date formatting (Revision 3 WP-E)."""

from __future__ import annotations

from datetime import datetime

from app.models.theme import LayoutSpec


def clean_date_raw(value: str) -> str:
    return (value or "").replace("\u00ad", "").replace("\u2011", "-").strip()


def parse_date(value: str) -> datetime | None:
    v = clean_date_raw(value)
    if not v:
        return None
    for fmt in ("%Y-%m-%d", "%d %b %Y", "%d/%m/%Y", "%m/%d/%Y", "%d-%m-%Y"):
        try:
            return datetime.strptime(v[: len(fmt) + 4] if fmt == "%d %b %Y" else v[:10], fmt)
        except ValueError:
            continue
    # Try "23 Oct 2026"
    try:
        return datetime.strptime(v, "%d %b %Y")
    except ValueError:
        return None


def format_date(value: str, layout: LayoutSpec | None = None) -> str:
    """Apply LayoutSpec.date_format (default human: 23 Oct 2026)."""
    layout = layout or LayoutSpec()
    raw = clean_date_raw(value)
    dt = parse_date(raw)
    if dt is None:
        return raw
    fmt = layout.date_format
    if fmt == "iso":
        return dt.strftime("%Y-%m-%d")
    if fmt == "dmy":
        return dt.strftime("%d/%m/%Y")
    if fmt == "mdy":
        return dt.strftime("%m/%d/%Y")
    # human
    return f"{dt.day} {dt.strftime('%b %Y')}"
