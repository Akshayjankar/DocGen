"""Rule-based format suggestion (never auto-applies)."""

from __future__ import annotations

import re


def suggest_format(text: str) -> tuple[str, float]:
    """Return (format_id, confidence 0..1)."""
    t = text.lower()
    if "purpose" in t and "scope" in t and "procedure" in t:
        return "sop", 0.85
    if re.search(r"```|npm install|pip install|\$\s+\w+|terminal", t):
        return "setup_guide", 0.8
    if re.search(r"\b(attendees|action items|minutes)\b", t):
        return "meeting_minutes", 0.85
    if re.search(r"\b(pricing|timeline|proposal|prepared for|acceptance)\b", t):
        return "proposal", 0.75
    if re.search(r"\b(executive summary|findings)\b", t) or (
        "report" in t and "fixed" not in t
    ):
        return "report", 0.7
    if re.search(r"\b(added|fixed|improved|known issues|changelog)\b", t):
        return "release_notes", 0.8
    if re.search(r"\b(shall|policy|compliance|definitions)\b", t):
        return "policy", 0.7
    if "?" in text[:400]:
        return "memo", 0.55
    return "memo", 0.4
