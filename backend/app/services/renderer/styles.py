"""Apply Theme to document styles."""

from __future__ import annotations

from docx import Document
from docx.enum.style import WD_STYLE_TYPE
from docx.shared import Pt, RGBColor

from app.models.theme import Theme
from app.services.renderer.oxml import hex_to_word


def _rgb(hex_color: str) -> RGBColor:
    h = hex_to_word(hex_color)
    return RGBColor(int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


def apply_theme_styles(doc: Document, theme: Theme) -> None:
    styles = doc.styles
    p = theme.palette
    fonts = theme.fonts

    normal = styles["Normal"]
    normal.font.name = fonts.body
    normal.font.size = Pt(10.5)
    normal.font.color.rgb = _rgb(p.text)
    normal.paragraph_format.space_after = Pt(6)
    normal.paragraph_format.line_spacing = 1.45

    # Docgen Body — required for all body paragraphs (WP-E)
    for name in (
        "Docgen Body",
        "Docgen Heading 1",
        "Docgen Heading 2",
        "Docgen Heading 3",
        "Docgen Code",
        "Docgen Caption",
        "Docgen Callout Label",
    ):
        try:
            styles.add_style(name, WD_STYLE_TYPE.PARAGRAPH)
        except ValueError:
            pass

    body = styles["Docgen Body"]
    body.font.name = fonts.body
    body.font.size = Pt(10.5)
    body.font.color.rgb = _rgb(p.text)
    body.paragraph_format.space_after = Pt(6)
    body.paragraph_format.line_spacing = 1.45

    heading_sizes = {1: (20, 20, 6), 2: (15, 14, 4), 3: (12.5, 10, 3)}
    for level, (size, before, after) in heading_sizes.items():
        for style_name in (f"Heading {level}", f"Docgen Heading {level}"):
            style = styles[style_name]
            style.font.name = fonts.heading
            style.font.size = Pt(size)
            style.font.bold = True
            style.font.color.rgb = _rgb(p.primary_dark)
            style.paragraph_format.space_before = Pt(before)
            style.paragraph_format.space_after = Pt(after)

    code = styles["Docgen Code"]
    code.font.name = fonts.mono
    code.font.size = Pt(9)
    code.font.color.rgb = _rgb(p.text)

    caption = styles["Docgen Caption"]
    caption.font.name = fonts.body
    caption.font.size = Pt(9)
    caption.font.italic = True
    caption.font.color.rgb = _rgb(p.muted)

    label = styles["Docgen Callout Label"]
    label.font.name = fonts.heading
    label.font.size = Pt(9)
    label.font.bold = True
    label.font.color.rgb = _rgb(p.primary_dark)
