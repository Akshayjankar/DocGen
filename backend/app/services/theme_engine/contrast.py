"""WCAG contrast checks and auto-adjust lightness."""

from __future__ import annotations

from coloraide import Color

from app.models.theme import ContrastPair, ContrastReport, Palette


def contrast_ratio(fg: str, bg: str) -> float:
    c1 = Color(fg)
    c2 = Color(bg)
    # coloraide ≥8: contrast(other, method=...) — WCAG 2.1 relative luminance
    try:
        return float(c1.contrast(c2, method="wcag21"))
    except Exception:
        return float(c1.contrast(c2))


def meets_aa(fg: str, bg: str, *, large: bool = False) -> bool:
    ratio = contrast_ratio(fg, bg)
    return ratio >= (3.0 if large else 4.5)


def meets_aaa(fg: str, bg: str, *, large: bool = False) -> bool:
    ratio = contrast_ratio(fg, bg)
    return ratio >= (4.5 if large else 7.0)


def _set_lightness(hex_color: str, delta_l: float) -> str:
    c = Color(hex_color).convert("oklch")
    l = float(c["l"]) + delta_l / 100.0
    c["l"] = max(0.0, min(1.0, l))
    return c.convert("srgb").to_string(hex=True).upper()


def ensure_contrast(fg: str, bg: str, *, min_ratio: float = 4.5) -> tuple[str, list[str]]:
    """Darken/lighten foreground until min_ratio vs background; return (fg, adjustments)."""
    adjustments: list[str] = []
    current = fg
    ratio = contrast_ratio(current, bg)
    if ratio >= min_ratio:
        return current, adjustments

    bg_l = float(Color(bg).convert("oklch")["l"])
    # Prefer darkening on light bg, lightening on dark bg.
    direction = -1.0 if bg_l > 0.5 else 1.0
    for step in range(1, 40):
        current = _set_lightness(fg, direction * step * 2)
        ratio = contrast_ratio(current, bg)
        if ratio >= min_ratio:
            adjustments.append(
                f"Adjusted {fg} → {current} for {ratio:.2f}:1 vs {bg} (target ≥ {min_ratio})"
            )
            return current, adjustments

    # Last resort: black or white.
    black_r = contrast_ratio("#000000", bg)
    white_r = contrast_ratio("#FFFFFF", bg)
    fallback = "#000000" if black_r >= white_r else "#FFFFFF"
    adjustments.append(f"Forced {fg} → {fallback} for contrast vs {bg}")
    return fallback, adjustments


def build_contrast_report(palette: Palette) -> ContrastReport:
    pairs_spec: list[tuple[str, str, str, bool]] = [
        ("Body text on surface", palette.text, palette.surface, False),
        ("Muted on surface", palette.muted, palette.surface, False),
        ("White on primary", "#FFFFFF", palette.primary, False),
        ("Primary on surface", palette.primary, palette.surface, True),
        ("Info on surface", palette.info, palette.surface, False),
        ("Warning on surface", palette.warning, palette.surface, False),
        ("Success on surface", palette.success, palette.surface, False),
        ("Danger on surface", palette.danger, palette.surface, False),
    ]
    pairs: list[ContrastPair] = []
    all_aa = True
    for label, fg, bg, large in pairs_spec:
        ratio = contrast_ratio(fg, bg)
        aa = ratio >= (3.0 if large else 4.5)
        aaa = ratio >= (4.5 if large else 7.0)
        all_aa = all_aa and aa
        pairs.append(
            ContrastPair(
                foreground=fg,  # type: ignore[arg-type]
                background=bg,  # type: ignore[arg-type]
                ratio=round(ratio, 2),
                aa=aa,
                aaa=aaa,
                label=label,
            )
        )
    return ContrastReport(pairs=pairs, all_aa=all_aa, adjustments=[])


def enforce_palette_aa(palette: Palette) -> tuple[Palette, ContrastReport]:
    """Mutate palette colors as needed so critical pairs pass AA."""
    adjustments: list[str] = []
    data = palette.model_dump()

    text, adj = ensure_contrast(data["text"], data["surface"], min_ratio=4.5)
    data["text"] = text
    adjustments.extend(adj)

    muted, adj = ensure_contrast(data["muted"], data["surface"], min_ratio=4.5)
    data["muted"] = muted
    adjustments.extend(adj)

    # Ensure white-on-primary OR darken primary so white works.
    white_ratio = contrast_ratio("#FFFFFF", data["primary"])
    if white_ratio < 4.5:
        darkened, adj = ensure_contrast("#FFFFFF", data["primary"], min_ratio=4.5)
        # ensure_contrast adjusts fg; we need to darken bg instead.
        primary = data["primary"]
        for step in range(1, 40):
            candidate = _set_lightness(primary, -step * 2)
            if contrast_ratio("#FFFFFF", candidate) >= 4.5:
                adjustments.append(
                    f"Darkened primary {primary} → {candidate} for white text contrast"
                )
                data["primary"] = candidate
                break
        else:
            data["primary"] = "#1A1A1A"
            adjustments.append("Forced primary to #1A1A1A for white text contrast")
        _ = darkened  # unused path marker

    for key in ("info", "warning", "success", "danger"):
        fixed, adj = ensure_contrast(data[key], data["surface"], min_ratio=4.5)
        data[key] = fixed
        adjustments.extend(adj)

    new_palette = Palette(**data)
    report = build_contrast_report(new_palette)
    report.adjustments = adjustments
    return new_palette, report
