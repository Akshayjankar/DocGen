"""Apply FormatPreset defaults onto Theme + RenderOptions (user overrides win)."""

from __future__ import annotations

from app.models.document import RenderOptions
from app.models.format_preset import FormatPreset
from app.models.theme import Theme


def apply_preset(
    preset: FormatPreset,
    theme: Theme,
    options: RenderOptions,
    *,
    touched: set[str] | None = None,
) -> tuple[Theme, RenderOptions]:
    """Merge preset layout/style into theme/options. Keys in `touched` are left alone."""
    touched = touched or set()
    layout = theme.layout
    if "cover_style" not in touched:
        layout.cover_style = preset.layout.cover_style  # type: ignore[assignment]
    if "border_style" not in touched and preset.layout.margins:
        pass  # margins map kept as theme defaults for now

    if "cover" not in touched:
        options.cover = preset.layout.cover_style != "none"
    if "toc" not in touched:
        toc = preset.layout.toc
        if toc == "auto":
            options.toc = "auto"
        elif toc == "on":
            options.toc = True
        else:
            options.toc = False
    if "revision_history" not in touched:
        rh = preset.layout.revision_history
        if rh in ("off",):
            options.revision_history = False
        elif rh in ("page", "cover"):
            options.revision_history = True
        else:
            options.revision_history = "auto"

    # Font pair hint → theme fonts names (deterministic map)
    if "font_pair" not in touched:
        pair = preset.style.font_pair
        mapping = {
            "modern": ("Carlito", "Carlito"),
            "editorial": ("Georgia", "Georgia"),
            "classic": ("Times New Roman", "Times New Roman"),
            "clean": ("Carlito", "Carlito"),
            "technical": ("Consolas", "Carlito"),
        }
        h, b = mapping.get(pair, ("Carlito", "Carlito"))
        theme.fonts.heading = h
        theme.fonts.body = b

    theme.layout = layout
    return theme, options
