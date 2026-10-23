"""Two-pass TOC: render → extract heading pages from PDF → rebuild cached TOC."""

from __future__ import annotations

from pathlib import Path

from docx import Document

from app.services.renderer.oxml import insert_cached_toc
from app.services.renderer.pdf import PdfConversionError, convert_to_pdf


def extract_heading_pages(pdf_path: Path) -> list[tuple[str, int, int]]:
    """Return (title, level, page) using PyMuPDF TOC / text heuristics."""
    import fitz  # PyMuPDF

    doc = fitz.open(pdf_path)
    toc = doc.get_toc()
    entries: list[tuple[str, int, int]] = []
    if toc:
        for level, title, page in toc:
            if 1 <= level <= 3:
                entries.append((title.strip(), level, int(page)))
        doc.close()
        return entries

    # Fallback: scan for large fonts as headings.
    for page_idx in range(len(doc)):
        page = doc[page_idx]
        blocks = page.get_text("dict")["blocks"]
        for block in blocks:
            if block.get("type") != 0:
                continue
            for line in block.get("lines", []):
                spans = line.get("spans", [])
                if not spans:
                    continue
                size = max(s.get("size", 0) for s in spans)
                text = "".join(s.get("text", "") for s in spans).strip()
                if not text or len(text) > 120:
                    continue
                if size >= 16:
                    entries.append((text, 1, page_idx + 1))
                elif size >= 13:
                    entries.append((text, 2, page_idx + 1))
    doc.close()
    return entries


def fill_cached_toc(docx_path: Path, entries: list[tuple[str, int, int]]) -> None:
    doc = Document(str(docx_path))
    # Find paragraph that contains TOC field instruction.
    for para in doc.paragraphs:
        xml = para._p.xml
        if "TOC" in xml and "instrText" in xml:
            insert_cached_toc(para, entries)
            break
    doc.save(str(docx_path))


def two_pass_toc(docx_path: Path, work_dir: Path | None = None) -> Path | None:
    """
    Convert once, extract TOC pages, rewrite DOCX, convert again.
    Returns final PDF path or None if LibreOffice unavailable.
    """
    work_dir = work_dir or docx_path.parent
    try:
        pdf1 = convert_to_pdf(docx_path, out_dir=work_dir)
    except PdfConversionError:
        return None

    entries = extract_heading_pages(pdf1)
    if entries:
        fill_cached_toc(docx_path, entries)

    try:
        pdf_final = convert_to_pdf(docx_path, out_dir=work_dir)
    except PdfConversionError:
        return pdf1
    return pdf_final
