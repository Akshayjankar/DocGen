"""Classical logo processing: validate, BG remove, trim, 2× export."""

from __future__ import annotations

import io
from pathlib import Path
from uuid import uuid4

import numpy as np
from PIL import Image

from app.models.theme import LogoAsset, LogoRole
from app.services.theme_engine.derive import delta_e


def _hex(rgb: tuple[int, int, int]) -> str:
    return f"#{rgb[0]:02X}{rgb[1]:02X}{rgb[2]:02X}"

_MAX_BYTES = 5 * 1024 * 1024
_MIME = {
    b"\x89PNG": "image/png",
    b"\xff\xd8\xff": "image/jpeg",
    b"RIFF": "image/webp",
}


def _detect_mime(data: bytes) -> str:
    head = data[:16]
    if head.startswith(b"\x89PNG"):
        return "image/png"
    if head.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if head[:4] == b"RIFF" and b"WEBP" in data[:16]:
        return "image/webp"
    if data[:200].lstrip().startswith((b"<svg", b"<?xml")):
        return "image/svg+xml"
    raise ValueError("Unsupported image format (need PNG/JPG/WebP/SVG)")


def _load(data: bytes) -> Image.Image:
    mime = _detect_mime(data)
    if mime == "image/svg+xml":
        import cairosvg

        png = cairosvg.svg2png(bytestring=data, output_width=512)
        return Image.open(io.BytesIO(png)).convert("RGBA")
    img = Image.open(io.BytesIO(data))
    if img.mode != "RGBA":
        img = img.convert("RGBA")
    # Strip EXIF by re-encoding through array
    return Image.fromarray(np.array(img))


def _edge_ring_uniform(arr: np.ndarray, delta_e_thresh: float = 6.0) -> tuple[bool, tuple[int, int, int] | None]:
    """True if ≥90% of 1-px edge ring shares one color (or transparent)."""
    h, w, _ = arr.shape
    if h < 3 or w < 3:
        return False, None
    ring_idx = []
    for x in range(w):
        ring_idx.append((0, x))
        ring_idx.append((h - 1, x))
    for y in range(1, h - 1):
        ring_idx.append((y, 0))
        ring_idx.append((y, w - 1))
    samples = [arr[y, x] for y, x in ring_idx]
    opaque = [tuple(map(int, s[:3])) for s in samples if int(s[3]) > 16]
    if len(opaque) < 0.1 * len(samples):
        return True, None  # mostly transparent
    # Mode color
    from collections import Counter

    mode_rgb, _count = Counter(opaque).most_common(1)[0]
    mode_h = _hex(mode_rgb)
    close = sum(1 for rgb in opaque if delta_e(_hex(rgb), mode_h) <= delta_e_thresh)
    if close / len(opaque) >= 0.90:
        return True, mode_rgb
    return False, None


def _flood_remove(arr: np.ndarray, bg: tuple[int, int, int], tolerance: int) -> np.ndarray:
    """Flood-fill from edges: make matching pixels transparent; 1px feather."""
    h, w, _ = arr.shape
    out = arr.copy()
    bg_h = _hex(bg)
    tol = max(0, min(30, tolerance))
    visited = np.zeros((h, w), dtype=bool)
    stack: list[tuple[int, int]] = []
    for x in range(w):
        stack.append((0, x))
        stack.append((h - 1, x))
    for y in range(h):
        stack.append((y, 0))
        stack.append((y, w - 1))

    match = np.zeros((h, w), dtype=bool)
    while stack:
        y, x = stack.pop()
        if y < 0 or y >= h or x < 0 or x >= w or visited[y, x]:
            continue
        visited[y, x] = True
        px = out[y, x]
        if int(px[3]) < 8:
            match[y, x] = True
            for dy, dx in ((0, 1), (0, -1), (1, 0), (-1, 0)):
                stack.append((y + dy, x + dx))
            continue
        rgb = (int(px[0]), int(px[1]), int(px[2]))
        if delta_e(_hex(rgb), bg_h) <= tol:
            match[y, x] = True
            for dy, dx in ((0, 1), (0, -1), (1, 0), (-1, 0)):
                stack.append((y + dy, x + dx))

    removed = int(match.sum())
    total = h * w
    if removed / total > 0.85:
        return arr  # abort — signal via unchanged

    out[match, 3] = 0
    # 1px feather without scipy
    padded = np.pad(match, 1, mode="constant")
    neigh = (
        padded[:-2, 1:-1]
        | padded[2:, 1:-1]
        | padded[1:-1, :-2]
        | padded[1:-1, 2:]
    )
    rim = neigh & ~match
    out[rim, 3] = (out[rim, 3].astype(np.float32) * 0.45).astype(np.uint8)
    return out


def _trim(arr: np.ndarray, pad_pct: float = 0.02) -> np.ndarray:
    alpha = arr[:, :, 3]
    ys, xs = np.where(alpha > 8)
    if len(xs) == 0:
        return arr
    y0, y1 = int(ys.min()), int(ys.max()) + 1
    x0, x1 = int(xs.min()), int(xs.max()) + 1
    ph = max(1, int((y1 - y0) * pad_pct))
    pw = max(1, int((x1 - x0) * pad_pct))
    y0, y1 = max(0, y0 - ph), min(arr.shape[0], y1 + ph)
    x0, x1 = max(0, x0 - pw), min(arr.shape[1], x1 + pw)
    return arr[y0:y1, x0:x1]


def _contrast_vs_white(arr: np.ndarray) -> float:
    opaque = arr[arr[:, :, 3] > 128][:, :3]
    if len(opaque) == 0:
        return 0.0
    # crude relative luminance contrast vs white
    mean = opaque.mean(axis=0) / 255.0
    lum = 0.2126 * mean[0] + 0.7152 * mean[1] + 0.0722 * mean[2]
    return (1.05) / (lum + 0.05)


def process_logo(
    data: bytes,
    *,
    role: LogoRole,
    filename: str = "logo.png",
    out_dir: Path,
    bg_tolerance: int = 10,
    max_width_mm: float | None = None,
    max_height_mm: float | None = None,
    alt_text: str = "Company logo",
    remove_bg: bool = True,
) -> tuple[LogoAsset, bytes]:
    """Validate, optionally remove BG, trim, write processed PNG; return asset + PNG bytes."""
    if len(data) > _MAX_BYTES:
        raise ValueError("Logo exceeds 5 MB limit")
    mime = _detect_mime(data)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    asset_id = uuid4().hex[:12]

    img = _load(data)
    arr = np.array(img)
    warnings: list[str] = []
    bg_state: str = "none"

    # Already transparent?
    edge_uniform, bg_rgb = _edge_ring_uniform(arr)
    alpha_edge = arr[0, :, 3].mean() < 8 or arr[-1, :, 3].mean() < 8
    if alpha_edge and (arr[:, :, 3] < 8).mean() > 0.05:
        bg_state = "was_transparent"
    elif remove_bg and edge_uniform and bg_rgb is not None:
        removed = _flood_remove(arr, bg_rgb, bg_tolerance)
        if np.array_equal(removed, arr):
            bg_state = "kept"
            warnings.append("bg_removal_aggressive")
        else:
            if _contrast_vs_white(removed) < 1.5:
                bg_state = "kept"
                warnings.append("bg_removal_aggressive")
            else:
                arr = removed
                bg_state = "removed"
    elif remove_bg and not edge_uniform:
        bg_state = "kept"

    arr = _trim(arr)
    h, w = arr.shape[:2]
    if w < 300 and h < 300:
        warnings.append("low_resolution")
    aspect = (w / h) if h else 1.0
    if aspect > 6 or aspect < 1 / 6:
        warnings.append("extreme_aspect")

    # Defaults by role
    if max_width_mm is None:
        max_width_mm = 70.0 if role == LogoRole.cover else 38.0
    if max_height_mm is None:
        max_height_mm = 42.0 if role == LogoRole.cover else 11.0

    # Export at 2× target px (~96 dpi baseline → 2×)
    target_w = int(max_width_mm / 25.4 * 96 * 2)
    target_h = int(max_height_mm / 25.4 * 96 * 2)
    scale = min(target_w / max(w, 1), target_h / max(h, 1), 4.0)
    nw, nh = max(1, int(w * scale)), max(1, int(h * scale))
    out_img = Image.fromarray(arr, "RGBA").resize((nw, nh), Image.Resampling.LANCZOS)

    original_path = out_dir / f"{asset_id}_orig.bin"
    original_path.write_bytes(data)
    processed_path = out_dir / f"{asset_id}_proc.png"
    buf = io.BytesIO()
    out_img.save(buf, format="PNG")
    png_bytes = buf.getvalue()
    processed_path.write_bytes(png_bytes)

    asset = LogoAsset(
        id=asset_id,
        role=role,
        filename=filename,
        mime=mime if mime != "image/svg+xml" else "image/png",
        width_px=nw,
        height_px=nh,
        aspect=nw / nh if nh else 1.0,
        original_path=str(original_path),
        processed_path=str(processed_path),
        background=bg_state,  # type: ignore[arg-type]
        bg_tolerance=bg_tolerance,
        max_width_mm=max_width_mm,
        max_height_mm=max_height_mm,
        alt_text=alt_text,
        warnings=warnings,
    )
    return asset, png_bytes


def read_processed_bytes(asset: LogoAsset | None) -> bytes | None:
    if not asset or not asset.processed_path:
        return None
    p = Path(asset.processed_path)
    if p.exists():
        return p.read_bytes()
    return None
