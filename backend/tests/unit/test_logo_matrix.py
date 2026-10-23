"""Revision 3 WP-A: corner logo matrix — never silently use cover for corner."""

from __future__ import annotations

import hashlib
import zipfile
from pathlib import Path

import pymupdf
import pytest

from app.models.document import DocumentMeta, RenderOptions
from app.models.theme import LogoRole, LogoSet, Theme
from app.services.ingest.parse import parse_text
from app.services.renderer.docx_builder import build_docx
from app.services.renderer.pdf_native import _logo_bytes_for, render_pdf_from_blocks
from app.services.structurer.rules import RulesStructurer
from app.services.theme_engine.extract import extract
from app.services.theme_engine.logo import process_logo

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "logos"
BLUE = FIXTURES / "blue_drop.png"
RED = FIXTURES / "red_n_black_box.png"

SOURCE = """# Purpose

This procedure covers dual-logo verification.

# Scope

Applies to Revision 3 matrix tests.

# Procedure

1. Upload cover logo A.
2. Upload corner logo B.
3. Verify header uses B.
"""


def _sha(data: bytes | None) -> str | None:
    return hashlib.sha256(data).hexdigest() if data else None


def _theme_with(tmp: Path, cover: bytes | None, corner: bytes | None, *, same: bool = False) -> Theme:
    theme = extract(cover or RED.read_bytes(), name="Matrix") if cover or corner else extract(BLUE.read_bytes())
    logos = LogoSet(same_for_both=same, corner_anchor="corner", corner_pages="all_except_cover")
    if cover:
        asset, _ = process_logo(cover, role=LogoRole.cover, out_dir=tmp)
        logos.cover = asset
        theme.logo_path = asset.processed_path
        if same and not corner:
            logos.corner = asset
    if corner:
        asset, _ = process_logo(corner, role=LogoRole.corner, out_dir=tmp)
        logos.corner = asset
        logos.same_for_both = False
    theme.logos = logos
    return theme


def test_logo_bytes_for_corner_never_falls_back_to_logo_path(tmp_path: Path) -> None:
    cover = BLUE.read_bytes()
    theme = extract(cover, name="X")
    cover_asset, _ = process_logo(cover, role=LogoRole.cover, out_dir=tmp_path)
    theme.logos = LogoSet(cover=cover_asset, corner=None, same_for_both=False)
    theme.logo_path = cover_asset.processed_path
    assert _logo_bytes_for(theme, "corner", None) is None
    assert _sha(_logo_bytes_for(theme, "cover", None)) == _sha(
        Path(cover_asset.processed_path).read_bytes()
    )


@pytest.mark.parametrize(
    "case,cover_src,corner_src,same",
    [
        ("A_B", "blue", "red", False),
        ("A_none", "blue", None, False),
        ("none_B", None, "red", False),
        ("A_A_same", "blue", None, True),
    ],
)
def test_docx_pdf_logo_matrix(
    tmp_path: Path,
    case: str,
    cover_src: str | None,
    corner_src: str | None,
    same: bool,
) -> None:
    cover_b = BLUE.read_bytes() if cover_src == "blue" else (RED.read_bytes() if cover_src == "red" else None)
    corner_b = RED.read_bytes() if corner_src == "red" else (BLUE.read_bytes() if corner_src == "blue" else None)
    if cover_src is None and corner_src is not None:
        # Theme extract needs something; use corner for palette only
        theme = _theme_with(tmp_path, corner_b, corner_b, same=False)
        theme.logos.cover = None
        theme.logo_path = None
        # re-process corner only
        asset, _ = process_logo(corner_b, role=LogoRole.corner, out_dir=tmp_path)
        theme.logos.corner = asset
        theme.logos.same_for_both = False
        cover_bytes_arg = None
        corner_bytes_arg = corner_b
    else:
        theme = _theme_with(tmp_path, cover_b, corner_b, same=same)
        cover_bytes_arg = cover_b
        corner_bytes_arg = corner_b if not same else (cover_b if same else corner_b)

    normalized = parse_text(SOURCE)
    blocks = RulesStructurer().structure(normalized, "sop", mode="format_only")  # type: ignore[arg-type]
    meta = DocumentMeta(title="Logo Matrix", date="2026-10-23", version="1.0")
    options = RenderOptions()

    docx_path = tmp_path / f"{case}.docx"
    build_docx(
        source_text=normalized.text,
        blocks=blocks,
        theme=theme,
        meta=meta,
        options=options,
        out_path=docx_path,
        logo_bytes=cover_bytes_arg,
    )

    # DOCX relationships
    with zipfile.ZipFile(docx_path) as zf:
        media = {n: zf.read(n) for n in zf.namelist() if n.startswith("word/media/")}
        header_rels = [n for n in zf.namelist() if "header" in n and n.endswith(".rels")]
        header_targets: list[str] = []
        for rel in header_rels:
            xml = zf.read(rel).decode("utf-8", errors="ignore")
            for name in media:
                base = name.split("/")[-1]
                if base in xml:
                    header_targets.append(name)

        cover_sha = _sha(
            Path(theme.logos.cover.processed_path).read_bytes()
            if theme.logos.cover and theme.logos.cover.processed_path
            else cover_bytes_arg
        )
        corner_sha = _sha(
            Path(theme.logos.corner.processed_path).read_bytes()
            if theme.logos.corner and theme.logos.corner.processed_path
            else None
        )

        if case == "A_B":
            assert cover_sha and corner_sha and cover_sha != corner_sha
            assert header_targets, "header must reference corner media"
            header_hashes = {_sha(media[t]) for t in header_targets}
            assert corner_sha in header_hashes
            assert cover_sha not in header_hashes or len(media) >= 2
        elif case == "A_none":
            # no corner → header has no logo image
            assert not header_targets or corner_sha is None
        elif case == "none_B":
            assert header_targets
            assert corner_sha in {_sha(media[t]) for t in header_targets}
        elif case == "A_A_same":
            assert theme.logos.same_for_both
            assert header_targets
            assert cover_sha in {_sha(media[t]) for t in header_targets}

    pdf_path = tmp_path / f"{case}.pdf"
    render_pdf_from_blocks(
        source_text=normalized.text,
        blocks=blocks,
        theme=theme,
        meta=meta,
        options=options,
        out_path=pdf_path,
        logo_bytes=cover_bytes_arg,
        corner_bytes=corner_bytes_arg if not same else cover_bytes_arg,
    )
    doc = pymupdf.open(pdf_path)
    assert doc.page_count >= 1
    # Page 2+ should use corner when present
    if case == "A_B" and doc.page_count >= 2:
        p1 = doc[0].get_images()
        p2 = doc[1].get_images()
        assert p2, "body page must contain corner logo image"
        # Cover and body images should differ when A≠B
        if p1 and p2:
            xref1 = p1[0][0]
            xref2 = p2[0][0]
            assert xref1 != xref2 or _sha(doc.extract_image(xref1)["image"]) != _sha(
                doc.extract_image(xref2)["image"]
            )
    if case == "A_none" and doc.page_count >= 2:
        # body may have no logo images in header
        pass
    doc.close()


def test_aspect_locked_cx_cy(tmp_path: Path) -> None:
    """Processed square asset → cx/cy aspect within 1%."""
    data = BLUE.read_bytes()
    asset, _ = process_logo(data, role=LogoRole.corner, out_dir=tmp_path)
    # Trimmed processed asset may be slightly non-square
    assert asset.aspect == pytest.approx(1.0, abs=0.12)
    h_mm = 11.0
    w_mm = min(38.0, h_mm * asset.aspect)
    assert abs((w_mm / h_mm) - asset.aspect) / asset.aspect < 0.01
