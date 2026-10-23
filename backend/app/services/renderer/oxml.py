"""Raw OXML helpers: TOC field, page borders, PAGE/NUMPAGES, shading."""

from __future__ import annotations

from docx.oxml import OxmlElement
from docx.oxml.ns import qn


def hex_to_word(color: str) -> str:
    return color.lstrip("#").upper()


def set_cell_shading(cell, color: str) -> None:
    tc = cell._tc
    tc_pr = tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:fill"), hex_to_word(color))
    shd.set(qn("w:val"), "clear")
    tc_pr.append(shd)


def set_run_shading(run, color: str) -> None:
    r_pr = run._r.get_or_add_rPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:fill"), hex_to_word(color))
    shd.set(qn("w:val"), "clear")
    r_pr.append(shd)


def add_page_number_fields(paragraph) -> None:
    """Insert 'Page X of Y' using PAGE / NUMPAGES fields."""
    paragraph.add_run("Page ")
    _add_field(paragraph, "PAGE")
    paragraph.add_run(" of ")
    _add_field(paragraph, "NUMPAGES")


def _add_field(paragraph, instr: str) -> None:
    run = paragraph.add_run()
    fld_char_begin = OxmlElement("w:fldChar")
    fld_char_begin.set(qn("w:fldCharType"), "begin")
    run._r.append(fld_char_begin)

    run2 = paragraph.add_run()
    instr_text = OxmlElement("w:instrText")
    instr_text.set(qn("xml:space"), "preserve")
    instr_text.text = f" {instr} "
    run2._r.append(instr_text)

    run3 = paragraph.add_run()
    fld_char_sep = OxmlElement("w:fldChar")
    fld_char_sep.set(qn("w:fldCharType"), "separate")
    run3._r.append(fld_char_sep)

    paragraph.add_run("1")
    run5 = paragraph.add_run()
    fld_char_end = OxmlElement("w:fldChar")
    fld_char_end.set(qn("w:fldCharType"), "end")
    run5._r.append(fld_char_end)


def add_toc_field(paragraph) -> None:
    """Real TOC field: TOC \\o \"1-3\" \\h \\z \\u"""
    run = paragraph.add_run()
    fld_begin = OxmlElement("w:fldChar")
    fld_begin.set(qn("w:fldCharType"), "begin")
    run._r.append(fld_begin)

    run2 = paragraph.add_run()
    instr = OxmlElement("w:instrText")
    instr.set(qn("xml:space"), "preserve")
    instr.text = ' TOC \\o "1-3" \\h \\z \\u '
    run2._r.append(instr)

    run3 = paragraph.add_run()
    fld_sep = OxmlElement("w:fldChar")
    fld_sep.set(qn("w:fldCharType"), "separate")
    run3._r.append(fld_sep)

    # Placeholder entries replaced by toc_pass with cached page numbers.
    paragraph.add_run("[Table of Contents — update fields or open in Word]")
    run5 = paragraph.add_run()
    fld_end = OxmlElement("w:fldChar")
    fld_end.set(qn("w:fldCharType"), "end")
    run5._r.append(fld_end)


def insert_cached_toc(paragraph, entries: list[tuple[str, int, int]]) -> None:
    """
    Replace paragraph content with a TOC field that includes cached entries.
    entries: list of (title, level, page_number)
    """
    p = paragraph._p
    for child in list(p):
        if child.tag.endswith("}r"):
            p.remove(child)

    def add_run_el(text: str | None = None):
        r = OxmlElement("w:r")
        if text is not None:
            t = OxmlElement("w:t")
            t.set(qn("xml:space"), "preserve")
            t.text = text
            r.append(t)
        p.append(r)
        return r

    r = add_run_el()
    fld_begin = OxmlElement("w:fldChar")
    fld_begin.set(qn("w:fldCharType"), "begin")
    r.append(fld_begin)

    r2 = add_run_el()
    instr = OxmlElement("w:instrText")
    instr.set(qn("xml:space"), "preserve")
    instr.text = ' TOC \\o "1-3" \\h \\z \\u '
    r2.append(instr)

    r3 = add_run_el()
    fld_sep = OxmlElement("w:fldChar")
    fld_sep.set(qn("w:fldCharType"), "separate")
    r3.append(fld_sep)

    for title, level, page in entries:
        indent = "    " * max(0, level - 1)
        add_run_el(f"{indent}{title}")
        # Dot leader + page
        r_tab = add_run_el()
        tab = OxmlElement("w:tab")
        r_tab.append(tab)
        add_run_el(str(page))
        # Soft line break between entries
        r_br = add_run_el()
        br = OxmlElement("w:br")
        r_br.append(br)

    r_end = add_run_el()
    fld_end = OxmlElement("w:fldChar")
    fld_end.set(qn("w:fldCharType"), "end")
    r_end.append(fld_end)


def set_page_border(section, color: str, width_pt: float = 1.5, offset_pt: int = 24) -> None:
    """Add w:pgBorders to section."""
    sect_pr = section._sectPr
    # Remove existing pgBorders
    for child in list(sect_pr):
        if child.tag == qn("w:pgBorders"):
            sect_pr.remove(child)

    pg_borders = OxmlElement("w:pgBorders")
    pg_borders.set(qn("w:offsetFrom"), "page")
    eighths = str(int(width_pt * 8))  # eighths of a point
    offset = str(int(offset_pt))
    for edge in ("top", "left", "bottom", "right"):
        border = OxmlElement(f"w:{edge}")
        border.set(qn("w:val"), "single")
        border.set(qn("w:sz"), eighths)
        border.set(qn("w:space"), offset)
        border.set(qn("w:color"), hex_to_word(color))
        pg_borders.append(border)
    sect_pr.append(pg_borders)


def set_left_cell_border(cell, color: str, width_pt: float = 12) -> None:
    tc = cell._tc
    tc_pr = tc.get_or_add_tcPr()
    tc_borders = OxmlElement("w:tcBorders")
    for edge in ("top", "left", "bottom", "right"):
        b = OxmlElement(f"w:{edge}")
        if edge == "left":
            b.set(qn("w:val"), "single")
            b.set(qn("w:sz"), str(int(width_pt * 8)))
            b.set(qn("w:color"), hex_to_word(color))
        else:
            b.set(qn("w:val"), "nil")
        tc_borders.append(b)
    tc_pr.append(tc_borders)


def add_seq_field(paragraph, name: str = "Figure") -> None:
    run = paragraph.add_run()
    fld_begin = OxmlElement("w:fldChar")
    fld_begin.set(qn("w:fldCharType"), "begin")
    run._r.append(fld_begin)
    run2 = paragraph.add_run()
    instr = OxmlElement("w:instrText")
    instr.set(qn("xml:space"), "preserve")
    instr.text = f" SEQ {name} \\* ARABIC "
    run2._r.append(instr)
    run3 = paragraph.add_run()
    fld_sep = OxmlElement("w:fldChar")
    fld_sep.set(qn("w:fldCharType"), "separate")
    run3._r.append(fld_sep)
    paragraph.add_run("1")
    run5 = paragraph.add_run()
    fld_end = OxmlElement("w:fldChar")
    fld_end.set(qn("w:fldCharType"), "end")
    run5._r.append(fld_end)
