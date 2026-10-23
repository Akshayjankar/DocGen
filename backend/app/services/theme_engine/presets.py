"""Curated neutral fallback palettes and font pairs."""

from __future__ import annotations

from app.models.theme import BorderSpec, ContrastReport, FontPair, Palette, Theme

# Fonts present in Word and our Docker image.
FONT_PAIRS: dict[str, FontPair] = {
    "corporate": FontPair(heading="Carlito", body="Carlito", mono="Liberation Mono"),
    "editorial": FontPair(heading="Liberation Serif", body="Liberation Sans", mono="Liberation Mono"),
    "technical": FontPair(heading="Liberation Sans", body="Liberation Sans", mono="Liberation Mono"),
    "friendly": FontPair(heading="Carlito", body="Carlito", mono="Liberation Mono"),
}

_NEUTRAL = Palette(
    primary="#2F5D8A",
    primary_dark="#1E3F5E",
    primary_tint="#D6E4F0",
    secondary="#5A6B7A",
    accent="#C4783A",
    text="#1A1A1A",
    muted="#5C5C5C",
    surface="#FFFFFF",
    info="#2B6CB0",
    warning="#B7791F",
    success="#276749",
    danger="#C53030",
)

_SLATE = Palette(
    primary="#334155",
    primary_dark="#1E293B",
    primary_tint="#E2E8F0",
    secondary="#64748B",
    accent="#0F766E",
    text="#0F172A",
    muted="#475569",
    surface="#FFFFFF",
    info="#1D4ED8",
    warning="#A16207",
    success="#166534",
    danger="#B91C1C",
)

_FOREST = Palette(
    primary="#2F5E3A",
    primary_dark="#1C3A24",
    primary_tint="#D8E8DC",
    secondary="#5C6B5E",
    accent="#8B6914",
    text="#1A1A1A",
    muted="#4A5568",
    surface="#FFFFFF",
    info="#2B6CB0",
    warning="#B7791F",
    success="#276749",
    danger="#C53030",
)

_PRESETS: dict[str, tuple[Palette, str]] = {
    "neutral": (_NEUTRAL, "corporate"),
    "slate": (_SLATE, "technical"),
    "forest": (_FOREST, "editorial"),
}


def get_preset(name: str = "neutral", mood: str | None = None) -> Theme:
    palette, default_mood = _PRESETS.get(name, _PRESETS["neutral"])
    fonts = FONT_PAIRS[mood or default_mood]
    return Theme(
        name=f"Preset · {name.title()}",
        palette=palette,
        fonts=fonts,
        border=BorderSpec(style="single", width_pt=1.5, color=palette.primary, offset_pt=24),
        logo_alt="Company logo",
        contrast=ContrastReport(all_aa=True, adjustments=["Using curated preset palette"]),
        source="preset",
    )


def list_presets() -> list[str]:
    return list(_PRESETS.keys())


def font_pair_for_mood(mood: str) -> FontPair:
    return FONT_PAIRS.get(mood, FONT_PAIRS["corporate"])
