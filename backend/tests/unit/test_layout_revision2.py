"""Revision 2 #B.4 — tiny input → 2 pages, no TOC, no auto H1, title as typed."""

from __future__ import annotations

from pathlib import Path
from uuid import uuid4

import pymupdf

from app.models.blocks import Block, SourceSpan
from app.models.document import DocumentMeta, RenderOptions
from app.services.renderer.layout import plan_layout, release_notice_rows
from app.services.renderer.pdf_native import render_pdf_from_blocks
from app.services.theme_engine.presets import get_preset


def test_release_notice_skips_empty_fields() -> None:
    meta = DocumentMeta(title="Nwertlif", author="", approver="")
    rows = release_notice_rows(meta)
    labels = [r[0] for r in rows]
    assert "Prepared By" not in labels
    assert "Approved By" not in labels
    assert "Name of Document" in labels


def test_tiny_document_two_pages(tmp_path: Path) -> None:
    source = "Hii I am NEtflic"
    blocks = [
        Block(
            id=uuid4().hex[:12],
            type="paragraph",
            span=SourceSpan(start=0, end=len(source)),
            origin="source",
        )
    ]
    meta = DocumentMeta(title="Nwertlif", classification="Internal")
    plan = plan_layout(
        blocks=blocks, source=source, meta=meta, options=RenderOptions(toc="auto")
    )
    assert plan.include_toc is False
    assert plan.inject_title_h1 is False

    out = tmp_path / "tiny.pdf"
    render_pdf_from_blocks(
        out_path=out,
        source_text=source,
        blocks=blocks,
        theme=get_preset("neutral"),
        meta=meta,
        options=RenderOptions(),
    )
    doc = pymupdf.open(out)
    assert doc.page_count == 2, f"expected 2 pages, got {doc.page_count}"
    def _norm(t: str) -> str:
        return t.replace("\xa0", " ").replace("\u00ad", "")

    cover = _norm(doc[0].get_text())
    assert "NWERTLIF" not in cover  # as typed, not forced uppercase
    assert "Nwertlif" in cover
    assert "Table of Contents" not in cover
    body = _norm(doc[1].get_text())
    assert body.count("Nwertlif") <= 2
    assert "Hii I am NEtflic" in body
    assert "\u00ad" not in cover and "\u00ad" not in body
    doc.close()


def test_revision_five_columns(tmp_path: Path) -> None:
    source = "# One\n\nA\n\n# Two\n\nB\n\n# Three\n\nC\n\n# Four\n\nD"
    from app.services.ingest.parse import parse_text
    from app.services.structurer.rules import RulesStructurer

    blocks = RulesStructurer().structure(parse_text(source), doc_type="sop")
    meta = DocumentMeta(title="Long Enough", author="Ada")
    out = tmp_path / "rev.pdf"
    render_pdf_from_blocks(
        out_path=out,
        source_text=source,
        blocks=blocks,
        theme=get_preset("neutral"),
        meta=meta,
        options=RenderOptions(toc=True, revision_history=True),
    )
    doc = pymupdf.open(out)
    text = "\n".join(page.get_text() for page in doc).replace("\xa0", " ")
    assert "Reason" in text and "Change" in text
    assert "Reviewed By" not in text
    # 5-col header markers
    assert "#" in text and "Author" in text
    doc.close()
