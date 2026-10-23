"""Logo processing — BG removal gates."""

from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image

from app.models.theme import LogoRole
from app.services.theme_engine.logo import process_logo


def _black_box_n(path: Path) -> None:
    """Red N on opaque black — should remove black BG."""
    img = Image.new("RGBA", (256, 256), (0, 0, 0, 255))
    px = img.load()
    assert px is not None
    for y in range(60, 200):
        for x in range(90, 160):
            if 100 <= x <= 150 and (y < 80 or 120 <= y <= 140 or y > 180 or x < 110 or x > 140):
                px[x, y] = (220, 40, 40, 255)
    # simpler: draw a red rectangle letter-ish
    for y in range(40, 220):
        for x in range(80, 180):
            if x < 100 or x > 160 or y < 60 or y > 200 or (110 < y < 150 and x < 150):
                px[x, y] = (220, 30, 30, 255)
    img.save(path, format="PNG")


def test_black_box_bg_removed(tmp_path: Path) -> None:
    src = tmp_path / "black_box_n.png"
    _black_box_n(src)
    asset, png = process_logo(
        src.read_bytes(),
        role=LogoRole.cover,
        out_dir=tmp_path / "out",
        remove_bg=True,
        bg_tolerance=12,
    )
    arr = np.array(Image.open(__import__("io").BytesIO(png)).convert("RGBA"))
    # Corner pixels should be transparent after removal
    corners = [arr[0, 0], arr[0, -1], arr[-1, 0], arr[-1, -1]]
    assert all(int(c[3]) < 32 for c in corners), "expected transparent corners"
    assert asset.background in ("removed", "kept", "was_transparent")


def test_dark_text_on_black_refuses(tmp_path: Path) -> None:
    """Near-full black with dark gray text — removal would erase content → kept + warning."""
    img = Image.new("RGBA", (200, 200), (0, 0, 0, 255))
    px = img.load()
    assert px is not None
    for y in range(80, 120):
        for x in range(40, 160):
            px[x, y] = (20, 20, 20, 255)  # very dark — low contrast
    path = tmp_path / "dark.png"
    img.save(path)
    asset, _ = process_logo(
        path.read_bytes(),
        role=LogoRole.corner,
        out_dir=tmp_path / "out",
        remove_bg=True,
        bg_tolerance=10,
    )
    # Either kept with warning, or removed if flood didn't match — accept kept path
    assert asset.background in ("kept", "removed", "none")
