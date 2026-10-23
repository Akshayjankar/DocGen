"""DOCX header/footer with corner logo only (Revision 3 WP-A/B)."""

from __future__ import annotations

import io

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor

from app.models.document import DocumentMeta, RenderOptions
from app.models.theme import Theme
from app.services.renderer.dates import format_date
from app.services.renderer.oxml import add_page_number_fields, hex_to_word
from app.services.theme_engine.logo import read_processed_bytes


def _rgb(hex_color: str) -> RGBColor:
    h = hex_to_word(hex_color)
    return RGBColor(int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


def _set_cell_margins(cell, *, top: int = 0, bottom: int = 0, left: int = 0, right: int = 0) -> None:
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    tcMar = OxmlElement("w:tcMar")
    for edge, val in (("top", top), ("left", left), ("bottom", bottom), ("right", right)):
        node = OxmlElement(f"w:{edge}")
        node.set(qn("w:w"), str(val))
        node.set(qn("w:type"), "dxa")
        tcMar.append(node)
    tcPr.append(tcMar)


def _corner_bytes(theme: Theme) -> bytes | None:
    logos = theme.logos
    if logos.same_for_both:
        return read_processed_bytes(logos.cover) or read_processed_bytes(logos.corner)
    return read_processed_bytes(logos.corner)


def setup_header_footer(
    doc: Document,
    theme: Theme,
    meta: DocumentMeta,
    options: RenderOptions,
) -> None:
    """Header: corner logo (never cover unless same_for_both) + classification."""
    section = doc.sections[0]
    logos = theme.logos
    show_logo = logos.corner_pages != "none"

    header = section.header
    header.is_linked_to_previous = False
    # Clear default paragraph
    for p in list(header.paragraphs):
        p.clear()

    if show_logo:
        table = header.add_table(rows=1, cols=2, width=Inches(6.5))
        table.autofit = False
        left, right = table.rows[0].cells
        _set_cell_margins(left)
        _set_cell_margins(right)

        data = _corner_bytes(theme)
        height_mm = logos.corner_height_mm or 11.0
        if data and logos.corner_position != "right":
            para = left.paragraphs[0]
            run = para.add_run()
            # Aspect-locked: height fixed, width from aspect
            aspect = (logos.corner.aspect if logos.corner else 1.0) or 1.0
            if logos.same_for_both and logos.cover:
                aspect = logos.cover.aspect or aspect
            h_in = height_mm / 25.4
            w_in = min(38 / 25.4, h_in * aspect)
            try:
                run.add_picture(io.BytesIO(data), height=Inches(h_in), width=Inches(w_in))
            except Exception:
                pass
        elif data and logos.corner_position == "right":
            para = right.paragraphs[0]
            para.alignment = WD_ALIGN_PARAGRAPH.RIGHT
            run = para.add_run()
            aspect = (logos.corner.aspect if logos.corner else 1.0) or 1.0
            h_in = height_mm / 25.4
            w_in = min(38 / 25.4, h_in * aspect)
            try:
                run.add_picture(io.BytesIO(data), height=Inches(h_in), width=Inches(w_in))
            except Exception:
                pass

        label_cell = right if logos.corner_position != "right" else left
        if options.classification_label and meta.classification:
            lp = label_cell.paragraphs[0]
            if logos.corner_position != "right":
                lp.alignment = WD_ALIGN_PARAGRAPH.RIGHT
            run = lp.add_run(meta.classification.upper())
            run.font.size = Pt(8)
            run.font.color.rgb = _rgb(theme.palette.muted)
    else:
        hp = header.paragraphs[0] if header.paragraphs else header.add_paragraph()
        if options.classification_label and meta.classification:
            run = hp.add_run(meta.classification.upper())
            run.font.size = Pt(8)
            run.font.color.rgb = _rgb(theme.palette.muted)
            hp.alignment = WD_ALIGN_PARAGRAPH.RIGHT

    footer = section.footer
    footer.is_linked_to_previous = False
    fp = footer.paragraphs[0] if footer.paragraphs else footer.add_paragraph()
    fp.clear()
    title = (meta.title or "Document")[:60]
    date_s = format_date(meta.date or "", theme.layout)
    run = fp.add_run(f"{title}  ·  {date_s}  ·  ")
    run.font.size = Pt(8)
    run.font.color.rgb = _rgb(theme.palette.muted)
    if options.page_numbers:
        add_page_number_fields(fp)
