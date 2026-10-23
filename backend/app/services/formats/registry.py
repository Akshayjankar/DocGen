"""Load and validate format presets from YAML."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import yaml

from app.models.format_preset import FormatPreset

_FORMATS_DIR = Path(__file__).resolve().parents[2] / "templates" / "formats"


@lru_cache(maxsize=1)
def all_presets() -> dict[str, FormatPreset]:
    out: dict[str, FormatPreset] = {}
    if not _FORMATS_DIR.exists():
        return out
    for path in sorted(_FORMATS_DIR.glob("*.yaml")):
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        preset = FormatPreset.model_validate(data)
        out[preset.id] = preset
    return out


def get_preset(format_id: str) -> FormatPreset | None:
    return all_presets().get(format_id)


def list_presets() -> list[FormatPreset]:
    return list(all_presets().values())
