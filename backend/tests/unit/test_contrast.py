"""WCAG contrast enforcement tests."""

from app.services.theme_engine.contrast import (
    contrast_ratio,
    enforce_palette_aa,
    ensure_contrast,
    meets_aa,
)
from app.services.theme_engine.derive import derive_palette


def test_black_on_white_passes_aa() -> None:
    assert meets_aa("#000000", "#FFFFFF")
    assert contrast_ratio("#000000", "#FFFFFF") >= 4.5


def test_ensure_contrast_fixes_light_gray() -> None:
    fixed, adj = ensure_contrast("#CCCCCC", "#FFFFFF", min_ratio=4.5)
    assert contrast_ratio(fixed, "#FFFFFF") >= 4.5
    assert adj  # should have adjusted


def test_enforce_palette_aa_all_pass() -> None:
    palette = derive_palette("#4A90D9", "#2C3E50", "#E67E22")
    fixed, report = enforce_palette_aa(palette)
    assert report.all_aa
    for pair in report.pairs:
        if "on surface" in pair.label.lower() or "Body" in pair.label or "Muted" in pair.label:
            assert pair.aa, pair
        if pair.label == "White on primary":
            assert pair.aa, pair
