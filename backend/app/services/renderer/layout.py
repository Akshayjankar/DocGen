"""Adaptive document layout decisions (Revision 2 §5.5)."""

from __future__ import annotations

from dataclasses import dataclass

from app.models.blocks import Block
from app.models.document import DocumentMeta, RenderOptions
from app.models.theme import LayoutSpec
from app.services.renderer.dates import format_date


@dataclass
class LayoutPlan:
    include_cover: bool
    include_toc: bool
    include_revision_page: bool
    compact_revision_on_cover: bool
    inject_title_h1: bool
    release_rows: list[tuple[str, str]]
    revision_rows: list[list[str]]


def _body_headings(blocks: list[Block], source: str, title: str) -> list[Block]:
    title_l = (title or "").strip().lower()
    out: list[Block] = []
    for b in blocks:
        if b.type != "heading":
            continue
        text = (b.resolved_text(source) if source else (b.text or "")).strip()
        if title_l and text.lower() == title_l:
            continue  # never invent / count title-as-H1
        out.append(b)
    return out


def release_notice_rows(
    meta: DocumentMeta,
    layout: LayoutSpec | None = None,
) -> list[tuple[str, str]]:
    """Only filled fields. Min: Name, Version, Date, Classification."""
    rows: list[tuple[str, str]] = [
        ("Name of Document", (meta.title or "Untitled Document").strip()),
        ("Version", (meta.version or "1.0").strip()),
        ("Date", format_date(meta.date or "", layout)),
        ("Classification", (meta.classification or "Internal").strip()),
    ]
    if meta.document_id.strip():
        rows.insert(1, ("Document ID", meta.document_id.strip()))
    if meta.author.strip():
        rows.append(("Prepared By", meta.author.strip()))
    if meta.reviewed_by.strip():
        rows.append(("Reviewed By", meta.reviewed_by.strip()))
    approver = meta.effective_approver()
    if approver:
        rows.append(("Approved By", approver))
    if meta.organization.strip():
        rows.append(("Organization", meta.organization.strip()))
    return [(k, v) for k, v in rows if v]


def revision_history_rows(
    meta: DocumentMeta,
    layout: LayoutSpec | None = None,
) -> list[list[str]]:
    """Exactly 5 columns: #, Version, Date, Author, Reason for Change."""
    return [
        [
            "1",
            meta.version or "1.0",
            format_date(meta.date or "", layout) or "—",
            meta.author.strip() or "—",
            "Initial release",
        ]
    ]


def plan_layout(
    *,
    blocks: list[Block],
    source: str,
    meta: DocumentMeta,
    options: RenderOptions | None = None,
    layout: LayoutSpec | None = None,
) -> LayoutPlan:
    options = options or RenderOptions()
    headings = _body_headings(blocks, source, meta.title)
    # Rough body size: < ~400 chars or no headings → compact
    body_chars = sum(len(b.resolved_text(source) or "") for b in blocks if b.type != "heading")
    small_body = body_chars < 800 and len(headings) < 3

    toc_opt = options.toc
    if toc_opt == "auto":
        include_toc = len(headings) >= 3
    else:
        include_toc = bool(toc_opt)

    rh_opt = options.revision_history
    if rh_opt == "auto":
        if small_body or not headings:
            include_revision_page = False
            compact_on_cover = True
        else:
            include_revision_page = True
            compact_on_cover = False
    elif rh_opt is True:
        include_revision_page = not small_body
        compact_on_cover = small_body
    else:
        include_revision_page = False
        compact_on_cover = False

    # When TOC + RH both on, they share a control page (include_revision_page True + toc)
    return LayoutPlan(
        include_cover=bool(options.cover),
        include_toc=include_toc,
        include_revision_page=include_revision_page,
        compact_revision_on_cover=compact_on_cover and bool(options.cover),
        inject_title_h1=False,  # never invent H1 = title
        release_rows=release_notice_rows(meta, layout),
        revision_rows=revision_history_rows(meta, layout),
    )


def mm(pt_per_inch: float = 72.0) -> float:
    """1 mm in PDF points."""
    return pt_per_inch / 25.4


def mm_to_pt(value_mm: float) -> float:
    return value_mm * mm()
