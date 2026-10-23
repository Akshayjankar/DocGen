"""Derive full palette from primary/secondary/accent cluster colors."""

from __future__ import annotations

import math

from coloraide import Color

from app.models.theme import Palette


def _hex(c: Color) -> str:
    return c.convert("srgb").to_string(hex=True).upper()


def _oklch(hex_color: str) -> Color:
    return Color(hex_color).convert("oklch")


def _shift_l(hex_color: str, delta: float) -> str:
    c = _oklch(hex_color)
    c["l"] = max(0.0, min(1.0, float(c["l"]) + delta / 100.0))
    return _hex(c)


def _reduce_chroma(hex_color: str, factor: float = 0.45) -> str:
    c = _oklch(hex_color)
    c["c"] = float(c["c"]) * factor
    return _hex(c)


def _hue(hex_color: str) -> float:
    c = _oklch(hex_color)
    h = c["h"]
    return float(h) if h is not None else 0.0


def _hue_distance(a: float, b: float) -> float:
    d = abs(a - b) % 360
    return min(d, 360 - d)


def _semantic_away_from(primary: str, base_hue: float, name: str) -> str:
    """Pick a semantic hue ≥ 40° from primary."""
    targets = {
        "info": 250.0,
        "warning": 75.0,
        "success": 145.0,
        "danger": 25.0,
    }
    target = targets[name]
    ph = _hue(primary)
    if _hue_distance(ph, target) < 40:
        target = (ph + 80) % 360
    c = Color("oklch", [0.45, 0.12, target])
    return _hex(c)


def complementary(hex_color: str) -> str:
    c = _oklch(hex_color)
    h = c["h"]
    c["h"] = ((float(h) if h is not None else 0.0) + 180) % 360
    c["c"] = max(0.08, float(c["c"]))
    return _hex(c)


def derive_palette(
    primary: str,
    secondary: str | None = None,
    accent: str | None = None,
) -> Palette:
    secondary = secondary or _shift_l(_reduce_chroma(primary, 0.5), -8)
    accent = accent or complementary(primary)

    primary_dark = _shift_l(primary, -18)
    primary_tint = _reduce_chroma(_shift_l(primary, 45), 0.35)

    return Palette(
        primary=primary,  # type: ignore[arg-type]
        primary_dark=primary_dark,  # type: ignore[arg-type]
        primary_tint=primary_tint,  # type: ignore[arg-type]
        secondary=secondary,  # type: ignore[arg-type]
        accent=accent,  # type: ignore[arg-type]
        text="#1A1A1A",  # type: ignore[arg-type]
        muted="#5C5C5C",  # type: ignore[arg-type]
        surface="#FFFFFF",  # type: ignore[arg-type]
        info=_semantic_away_from(primary, 250, "info"),  # type: ignore[arg-type]
        warning=_semantic_away_from(primary, 75, "warning"),  # type: ignore[arg-type]
        success=_semantic_away_from(primary, 145, "success"),  # type: ignore[arg-type]
        danger=_semantic_away_from(primary, 25, "danger"),  # type: ignore[arg-type]
    )


def delta_e(a: str, b: str) -> float:
    """CIEDE2000 approximation via coloraide."""
    c1 = Color(a).convert("lab-d65")
    c2 = Color(b).convert("lab-d65")
    return float(c1.delta_e(c2, method="2000"))


def chroma_of(hex_color: str) -> float:
    c = Color(hex_color).convert("oklch")
    return float(c["c"])


def is_near_white(rgb: tuple[int, int, int], threshold: int = 245) -> bool:
    return all(c >= threshold for c in rgb)


def is_near_black(rgb: tuple[int, int, int], threshold: int = 15) -> bool:
    return all(c <= threshold for c in rgb)


def rgb_to_lab(rgb: tuple[int, int, int]) -> tuple[float, float, float]:
    c = Color("srgb", [rgb[0] / 255, rgb[1] / 255, rgb[2] / 255]).convert("lab-d65")
    return (float(c["l"]), float(c["a"]), float(c["b"]))


def lab_chroma(lab: tuple[float, float, float]) -> float:
    return math.sqrt(lab[1] ** 2 + lab[2] ** 2)
