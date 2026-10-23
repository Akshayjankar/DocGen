"""Extract Theme from a logo image (PNG/JPG/SVG)."""

from __future__ import annotations

import io

import numpy as np
from PIL import Image
from sklearn.cluster import KMeans

from app.models.theme import BorderSpec, Theme
from app.services.theme_engine.contrast import enforce_palette_aa
from app.services.theme_engine.derive import (
    chroma_of,
    complementary,
    delta_e,
    derive_palette,
    is_near_black,
    is_near_white,
    lab_chroma,
    rgb_to_lab,
)
from app.services.theme_engine.presets import font_pair_for_mood, get_preset


def _load_image(logo_bytes: bytes) -> Image.Image:
    # SVG → PNG via cairosvg when needed.
    if logo_bytes[:200].lstrip().startswith((b"<svg", b"<?xml")):
        try:
            import cairosvg

            png = cairosvg.svg2png(bytestring=logo_bytes, output_width=256)
            return Image.open(io.BytesIO(png)).convert("RGBA")
        except Exception:
            return Image.new("RGBA", (64, 64), (47, 93, 138, 255))

    img = Image.open(io.BytesIO(logo_bytes))
    if img.mode not in ("RGB", "RGBA"):
        img = img.convert("RGBA")
    elif img.mode == "RGB":
        img = img.convert("RGBA")
    # Downscale to ≤256px on longest side.
    w, h = img.size
    longest = max(w, h)
    if longest > 256:
        scale = 256 / longest
        img = img.resize((max(1, int(w * scale)), max(1, int(h * scale))), Image.Resampling.LANCZOS)
    return img


def _edge_mask(h: int, w: int) -> np.ndarray:
    """Boolean mask of edge pixels (outer 8%)."""
    margin_y = max(1, int(h * 0.08))
    margin_x = max(1, int(w * 0.08))
    mask = np.zeros((h, w), dtype=bool)
    mask[:margin_y, :] = True
    mask[-margin_y:, :] = True
    mask[:, :margin_x] = True
    mask[:, -margin_x:] = True
    return mask


def _filter_pixels(arr: np.ndarray) -> np.ndarray:
    """Drop transparent / near-white / near-black edge-dominant background pixels."""
    h, w, _ = arr.shape
    edge = _edge_mask(h, w)
    rgba = arr.reshape(-1, 4)
    edge_flat = edge.reshape(-1)

    keep: list[np.ndarray] = []
    for i, px in enumerate(rgba):
        r, g, b, a = int(px[0]), int(px[1]), int(px[2]), int(px[3])
        if a < 32:
            continue
        rgb = (r, g, b)
        if edge_flat[i] and (is_near_white(rgb) or is_near_black(rgb)):
            continue
        if a < 200 and (is_near_white(rgb) or is_near_black(rgb)):
            continue
        keep.append(np.array([r, g, b], dtype=np.float64))

    if len(keep) < 20:
        # Fallback: all non-transparent pixels.
        opaque = rgba[rgba[:, 3] >= 32][:, :3].astype(np.float64)
        return opaque if len(opaque) else np.array([[47.0, 93.0, 138.0]])
    return np.stack(keep)


def _cluster_colors(pixels: np.ndarray, k: int = 6) -> list[tuple[str, float, float]]:
    """Return list of (hex, population_weight, chroma) sorted by pop × chroma."""
    labs = np.array([rgb_to_lab((int(p[0]), int(p[1]), int(p[2]))) for p in pixels])
    # Cap k by distinct LAB bins to avoid sklearn ConvergenceWarning.
    lab_bins = np.unique(np.round(labs, 0), axis=0)
    k = max(1, min(k, len(pixels), len(lab_bins)))
    km = KMeans(n_clusters=k, n_init=10, random_state=42)
    labels = km.fit_predict(labs)
    centers = km.cluster_centers_

    # Merge clusters with ΔE < 12.
    merged: list[dict[str, float | np.ndarray]] = []
    for i, center in enumerate(centers):
        pop = float(np.sum(labels == i)) / len(labels)
        hex_c = _lab_center_to_hex(center)
        chroma = lab_chroma((float(center[0]), float(center[1]), float(center[2])))
        absorbed = False
        for m in merged:
            if delta_e(hex_c, str(m["hex"])) < 12:
                # Merge into larger.
                old_pop = float(m["pop"])
                new_pop = old_pop + pop
                m["center"] = (old_pop * m["center"] + pop * center) / new_pop  # type: ignore[operator]
                m["pop"] = new_pop
                m["hex"] = _lab_center_to_hex(m["center"])  # type: ignore[arg-type]
                m["chroma"] = lab_chroma(
                    (float(m["center"][0]), float(m["center"][1]), float(m["center"][2]))  # type: ignore[index]
                )
                absorbed = True
                break
        if not absorbed:
            merged.append({"hex": hex_c, "pop": pop, "chroma": chroma, "center": center})

    scored: list[tuple[str, float, float]] = []
    for m in merged:
        scored.append((str(m["hex"]), float(m["pop"]), float(m["chroma"])))
    scored.sort(key=lambda t: t[1] * max(t[2], 0.5), reverse=True)
    return scored


def _lab_center_to_hex(center: np.ndarray) -> str:
    from coloraide import Color

    c = Color("lab-d65", [float(center[0]), float(center[1]), float(center[2])])
    return c.convert("srgb").to_string(hex=True).upper()


def extract(logo_bytes: bytes, *, name: str = "Logo Theme", mood: str = "corporate") -> Theme:
    """logo bytes → Theme. Falls back to preset on low confidence."""
    try:
        img = _load_image(logo_bytes)
        arr = np.array(img)
        pixels = _filter_pixels(arr)
        clusters = _cluster_colors(pixels, k=6)

        # Low confidence: greyscale or < 2 usable clusters.
        saturated = [c for c in clusters if c[2] >= 8.0]
        if len(saturated) < 2 and len(clusters) < 2:
            theme = get_preset("neutral", mood=mood)
            theme.name = name
            return theme

        usable = saturated if saturated else clusters
        primary = usable[0][0]
        secondary = usable[1][0] if len(usable) > 1 else None

        # Accent = highest chroma remaining or complementary if monochrome.
        remaining = usable[2:] if len(usable) > 2 else []
        if remaining:
            accent = max(remaining, key=lambda t: t[2])[0]
        elif len(usable) == 1 or (len(usable) >= 2 and chroma_of(primary) < 5):
            accent = complementary(primary)
        else:
            accent = complementary(primary)

        palette = derive_palette(primary, secondary, accent)
        palette, report = enforce_palette_aa(palette)

        return Theme(
            name=name,
            palette=palette,
            fonts=font_pair_for_mood(mood),
            border=BorderSpec(
                style="single",
                width_pt=1.5,
                color=palette.primary,  # type: ignore[arg-type]
                offset_pt=24,
            ),
            logo_alt="Company logo",
            contrast=report,
            source="logo",
        )
    except Exception:
        theme = get_preset("neutral", mood=mood)
        theme.name = name
        theme.contrast.adjustments.append("Logo extraction failed; using preset")
        return theme
