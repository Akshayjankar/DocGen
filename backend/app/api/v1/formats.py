"""Format presets API (Revision 3 WP-C)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.formats.registry import get_preset, list_presets
from app.services.formats.suggest import suggest_format

router = APIRouter(prefix="/formats", tags=["formats"])

_SAMPLES = Path(__file__).resolve().parents[2] / "templates" / "formats" / "samples"


class SuggestBody(BaseModel):
    text: str = Field(min_length=1)


@router.get("")
def get_formats() -> dict[str, Any]:
    return {"formats": [p.as_public() for p in list_presets()]}


@router.get("/{format_id}")
def get_format(format_id: str) -> dict[str, Any]:
    preset = get_preset(format_id)
    if not preset:
        raise HTTPException(404, f"Unknown format: {format_id}")
    data = preset.as_public()
    sample_path = _SAMPLES / Path(preset.sample).name if preset.sample else None
    if sample_path and sample_path.exists():
        data["sample_text"] = sample_path.read_text(encoding="utf-8")
    elif preset.sample:
        alt = Path(__file__).resolve().parents[2] / "templates" / "formats" / preset.sample
        if alt.exists():
            data["sample_text"] = alt.read_text(encoding="utf-8")
    return data


@router.post("/suggest")
def suggest(body: SuggestBody) -> dict[str, Any]:
    fmt_id, confidence = suggest_format(body.text)
    preset = get_preset(fmt_id)
    return {
        "format_id": fmt_id,
        "confidence": confidence,
        "label": preset.label if preset else fmt_id,
    }
