"""Revision 3 WP-C: format presets validate and suggest correctly."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.models.format_preset import FormatPreset
from app.services.formats.registry import all_presets, get_preset, list_presets
from app.services.formats.suggest import suggest_format

SAMPLES = Path(__file__).resolve().parents[2] / "app" / "templates" / "formats" / "samples"
FIXTURE_INPUTS = Path(__file__).resolve().parents[1] / "fixtures" / "inputs"

EXPECTED_IDS = {
    "sop",
    "setup_guide",
    "report",
    "release_notes",
    "policy",
    "proposal",
    "meeting_minutes",
    "memo",
}


def test_all_yaml_presets_validate() -> None:
    presets = all_presets()
    assert set(presets.keys()) == EXPECTED_IDS
    for p in presets.values():
        assert isinstance(p, FormatPreset)
        assert p.id
        assert p.label


def test_list_presets_order_stable() -> None:
    assert len(list_presets()) == 8


@pytest.mark.parametrize(
    "fixture,expected",
    [
        ("sop.md", "sop"),
        ("setup_guide.md", "setup_guide"),
        ("report.md", "report"),
        ("release_notes.md", "release_notes"),
        ("policy.md", "policy"),
        ("proposal.md", "proposal"),
        ("minutes.md", "meeting_minutes"),
        ("memo.md", "memo"),
    ],
)
def test_suggest_fixtures(fixture: str, expected: str) -> None:
    path = SAMPLES / fixture
    if not path.exists():
        path = FIXTURE_INPUTS / fixture
    text = path.read_text(encoding="utf-8")
    fmt_id, conf = suggest_format(text)
    assert fmt_id == expected
    assert conf >= 0.4


def test_get_preset_unknown() -> None:
    assert get_preset("nope") is None
