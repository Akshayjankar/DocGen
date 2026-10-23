#!/usr/bin/env python3
"""Write tiny distinct PNG logos for tests (stdlib only)."""

from __future__ import annotations

import struct
import zlib
from pathlib import Path


def _png_rgb(width: int, height: int, pixels: bytes) -> bytes:
    def chunk(tag: bytes, data: bytes) -> bytes:
        crc = zlib.crc32(tag + data) & 0xFFFFFFFF
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", crc)

    raw = b"".join(b"\x00" + pixels[y * width * 3 : (y + 1) * width * 3] for y in range(height))
    compressed = zlib.compress(raw, 9)
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", ihdr)
        + chunk(b"IDAT", compressed)
        + chunk(b"IEND", b"")
    )


def _fill(width: int, height: int, rgb: tuple[int, int, int]) -> bytes:
    r, g, b = rgb
    row = bytes([r, g, b] * width)
    return row * height


def _blue_drop(width: int, height: int) -> bytes:
    buf = bytearray(_fill(width, height, (245, 248, 255)))
    cx, cy = width // 2, height // 2 + 2
    for y in range(height):
        for x in range(width):
            dx = x - cx
            drop_y = cy + max(0, (y - cy) // 3)
            dy = y - drop_y
            if dx * dx + dy * dy <= (width // 3) ** 2:
                buf[(y * width + x) * 3 : (y * width + x) * 3 + 3] = bytes((30, 100, 220))
    return bytes(buf)


def _red_black_box(width: int, height: int) -> bytes:
    buf = bytearray(_fill(width, height, (240, 240, 240)))
    margin = 4
    for y in range(margin, height - margin):
        for x in range(margin, width - margin):
            if x < width // 2:
                buf[(y * width + x) * 3 : (y * width + x) * 3 + 3] = bytes((200, 40, 40))
            else:
                buf[(y * width + x) * 3 : (y * width + x) * 3 + 3] = bytes((20, 20, 20))
    return bytes(buf)


def _green_circle(width: int, height: int) -> bytes:
    buf = bytearray(_fill(width, height, (255, 255, 255)))
    cx, cy = width // 2, height // 2
    r2 = (min(width, height) // 2 - 3) ** 2
    for y in range(height):
        for x in range(width):
            if (x - cx) ** 2 + (y - cy) ** 2 <= r2:
                buf[(y * width + x) * 3 : (y * width + x) * 3 + 3] = bytes((40, 160, 90))
    return bytes(buf)


def main() -> None:
    out = Path(__file__).resolve().parent
    w, h = 32, 32
    specs = [
        ("blue_drop.png", _blue_drop(w, h)),
        ("red_n_black_box.png", _red_black_box(w, h)),
        ("green_circle.png", _green_circle(w, h)),
    ]
    for name, pixels in specs:
        (out / name).write_bytes(_png_rgb(w, h, pixels))
    print(f"Wrote {len(specs)} PNGs to {out}")


if __name__ == "__main__":
    main()
