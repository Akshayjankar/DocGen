"""Theme extraction tests."""

import io

from PIL import Image

from app.services.theme_engine.extract import extract
from app.services.theme_engine.presets import get_preset


def _solid_png(rgb: tuple[int, int, int], size: int = 64) -> bytes:
    img = Image.new("RGB", (size, size), rgb)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def _brand_png() -> bytes:
    """Blue circle on transparent background."""
    img = Image.new("RGBA", (128, 128), (0, 0, 0, 0))
    pixels = img.load()
    assert pixels is not None
    cx, cy, r = 64, 64, 40
    for y in range(128):
        for x in range(128):
            if (x - cx) ** 2 + (y - cy) ** 2 <= r**2:
                pixels[x, y] = (30, 90, 180, 255)
    # Accent corner
    for y in range(10, 30):
        for x in range(90, 120):
            pixels[x, y] = (220, 100, 40, 255)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def test_extract_brand_logo_returns_logo_source() -> None:
    theme = extract(_brand_png(), name="TestCo")
    assert theme.source in ("logo", "preset")
    assert theme.contrast.all_aa
    assert theme.palette.primary.startswith("#")


def test_greyscale_falls_back_or_still_aa() -> None:
    theme = extract(_solid_png((128, 128, 128)))
    assert theme.contrast.all_aa


def test_preset_neutral() -> None:
    t = get_preset("neutral")
    assert t.source == "preset"
    assert t.palette.primary
