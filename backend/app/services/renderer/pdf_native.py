"""Native branded PDF via PyMuPDF — Revision 2 layout (no LibreOffice)."""

from __future__ import annotations

from pathlib import Path

import pymupdf

from app.models.blocks import Block
from app.models.document import DocumentMeta, RenderOptions
from app.models.theme import LogoSet, Theme
from app.services.renderer.inline_md import parse_inline, strip_inline_markers
from app.services.renderer.layout import LayoutPlan, mm_to_pt, plan_layout
from app.services.theme_engine.logo import read_processed_bytes

# A4 defaults from LayoutSpec (overridden per-theme)
PAGE_W, PAGE_H = pymupdf.paper_size("a4")
BORDER = 20.0  # pt offset from edge
MARGIN_X = mm_to_pt(22)
MARGIN_TOP = mm_to_pt(28)
MARGIN_BOTTOM = mm_to_pt(24)
HEADER_ZONE = mm_to_pt(14)  # from top of page
HEADER_RULE_Y = mm_to_pt(27)
FOOTER_SAFE_GAP = mm_to_pt(8)
CONTENT_TOP = MARGIN_TOP + 8
CONTENT_BOTTOM = PAGE_H - MARGIN_BOTTOM
CONTENT_W = PAGE_W - 2 * MARGIN_X

_FONT_REG = "docgen-reg"
_FONT_BOLD = "docgen-bold"
_ARIAL = Path("/System/Library/Fonts/Supplemental/Arial.ttf")
_ARIAL_BOLD = Path("/System/Library/Fonts/Supplemental/Arial Bold.ttf")


def _rgb(hex_color: str) -> tuple[float, float, float]:
    h = hex_color.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    return (int(h[0:2], 16) / 255, int(h[2:4], 16) / 255, int(h[4:6], 16) / 255)


def _logo_bytes_for(theme: Theme, role: str, fallback: bytes | None) -> bytes | None:
    """Resolve logo bytes for a role. Corner NEVER falls back to cover unless same_for_both."""
    logos = theme.logos or LogoSet()
    if role == "cover":
        b = read_processed_bytes(logos.cover)
        if b:
            return b
        if logos.same_for_both:
            b = read_processed_bytes(logos.corner)
            if b:
                return b
        if theme.logo_path and Path(theme.logo_path).exists():
            return Path(theme.logo_path).read_bytes()
        return fallback
    if role == "corner":
        if logos.same_for_both:
            return (
                read_processed_bytes(logos.cover)
                or read_processed_bytes(logos.corner)
                or fallback
            )
        b = read_processed_bytes(logos.corner)
        if b:
            return b
        # No silent cover fallback (Revision 3 N1)
        return fallback
    return fallback


class _PdfBuilder:
    def __init__(
        self,
        theme: Theme,
        meta: DocumentMeta,
        cover_logo: bytes | None,
        corner_logo: bytes | None,
        plan: LayoutPlan,
    ) -> None:
        self.doc = pymupdf.open()
        self.theme = theme
        self.meta = meta
        self.cover_logo = cover_logo
        self.corner_logo = corner_logo
        self.plan = plan
        self.logos = theme.logos or LogoSet()
        p = theme.palette
        self.brand = _rgb(p.primary)
        self.brand_dark = _rgb(p.primary_dark)
        self.tint = _rgb(p.primary_tint)
        self.text = _rgb(p.text) if p.text else (0, 0, 0)
        self.muted = _rgb(p.muted)
        self.rule = _rgb(p.muted)
        self.page: pymupdf.Page | None = None
        self.y = CONTENT_TOP
        self.max_y = CONTENT_BOTTOM - 4
        self.heading_pages: list[tuple[str, int, int]] = []
        self._font_reg = "helv"
        self._font_bold = "hebo"
        self._use_arial = _ARIAL.exists() and _ARIAL_BOLD.exists()

    def _ensure_fonts(self, page: pymupdf.Page) -> None:
        if not self._use_arial:
            return
        try:
            page.insert_font(fontname=_FONT_REG, fontfile=str(_ARIAL))
            page.insert_font(fontname=_FONT_BOLD, fontfile=str(_ARIAL_BOLD))
            self._font_reg = _FONT_REG
            self._font_bold = _FONT_BOLD
        except Exception:
            self._use_arial = False
            self._font_reg = "helv"
            self._font_bold = "hebo"

    def _draw_border(self, page: pymupdf.Page) -> None:
        style = (self.theme.layout.border_style if self.theme.layout else None) or (
            self.theme.border.style if self.theme.border else "double"
        )
        if style == "none":
            return
        r1 = pymupdf.Rect(BORDER, BORDER, PAGE_W - BORDER, PAGE_H - BORDER)
        width = 0.6 if style == "hairline" else 1.25
        page.draw_rect(r1, color=self.brand, width=width)
        if style == "double":
            r2 = pymupdf.Rect(BORDER + 2.5, BORDER + 2.5, PAGE_W - BORDER - 2.5, PAGE_H - BORDER - 2.5)
            page.draw_rect(r2, color=self.brand, width=0.4)

    def _insert_logo(
        self,
        page: pymupdf.Page,
        data: bytes,
        *,
        x: float,
        y: float,
        max_w_mm: float,
        max_h_mm: float,
        align: str = "left",
        aspect: float = 1.0,
    ) -> pymupdf.Rect | None:
        """Edge-aligned, aspect-locked placement (never center a square in a wide box)."""
        max_w = mm_to_pt(max_w_mm)
        max_h = mm_to_pt(max_h_mm)
        aspect = aspect if aspect > 0.01 else 1.0
        h = max_h
        w = h * aspect
        if w > max_w:
            w = max_w
            h = w / aspect
        try:
            if align == "center":
                rect = pymupdf.Rect(x - w / 2, y, x + w / 2, y + h)
            elif align == "right":
                rect = pymupdf.Rect(x - w, y, x, y + h)
            else:
                rect = pymupdf.Rect(x, y, x + w, y + h)
            page.insert_image(rect, stream=data, keep_proportion=False)
            return rect
        except Exception:
            return None

    def _draw_header(self, page: pymupdf.Page, *, cover: bool = False) -> None:
        pages_mode = getattr(self.logos, "corner_pages", "all_except_cover") or "all_except_cover"
        if self.logos.show_corner_on_cover:
            pages_mode = "all"
        show_corner = pages_mode == "all" or (pages_mode == "all_except_cover" and not cover)
        if pages_mode == "none":
            show_corner = False

        logo_h_mm = float(getattr(self.logos, "corner_height_mm", 11.0) or 11.0)
        logo_w_mm = 38.0
        anchor = getattr(self.logos, "corner_anchor", "corner") or "corner"
        edge_mm = 14.0 if anchor == "corner" else 22.0
        edge_x = mm_to_pt(edge_mm)
        logo_top = mm_to_pt(14.0)
        label_h = mm_to_pt(logo_h_mm)

        aspect = 1.0
        if self.logos.corner and self.logos.corner.aspect:
            aspect = float(self.logos.corner.aspect)
        elif self.logos.same_for_both and self.logos.cover and self.logos.cover.aspect:
            aspect = float(self.logos.cover.aspect)

        if show_corner and self.corner_logo:
            if self.logos.corner_position == "right":
                self._insert_logo(
                    page,
                    self.corner_logo,
                    x=PAGE_W - edge_x,
                    y=logo_top,
                    max_w_mm=logo_w_mm,
                    max_h_mm=logo_h_mm,
                    align="right",
                    aspect=aspect,
                )
            else:
                self._insert_logo(
                    page,
                    self.corner_logo,
                    x=edge_x,
                    y=logo_top,
                    max_w_mm=logo_w_mm,
                    max_h_mm=logo_h_mm,
                    align="left",
                    aspect=aspect,
                )
            rule_left, rule_right = edge_x, PAGE_W - edge_x
        else:
            rule_left, rule_right = MARGIN_X, PAGE_W - MARGIN_X

        label = (self.meta.classification or "Internal").strip().upper()
        if self.logos.corner_position == "right" and show_corner:
            align = 0
            rect = pymupdf.Rect(MARGIN_X, logo_top, PAGE_W / 2, logo_top + label_h)
        else:
            align = 2
            rect = pymupdf.Rect(PAGE_W / 2, logo_top, PAGE_W - edge_x, logo_top + label_h)
        page.insert_textbox(
            rect,
            label,
            fontsize=8,
            fontname=self._font_reg,
            color=self.muted,
            align=align,
        )

        if not cover:
            rule_y = HEADER_RULE_Y
            rule_c = tuple(
                0.4 * a + 0.6 * b for a, b in zip(self.brand, (1.0, 1.0, 1.0), strict=True)
            )
            page.draw_line(
                pymupdf.Point(rule_left, rule_y),
                pymupdf.Point(rule_right, rule_y),
                color=rule_c,
                width=0.75,
            )

    def new_page(self, *, cover: bool = False) -> pymupdf.Page:
        page = self.doc.new_page(width=PAGE_W, height=PAGE_H)
        self._ensure_fonts(page)
        self._draw_border(page)
        self._draw_header(page, cover=cover)
        self.page = page
        self.y = CONTENT_TOP + (12 if cover else 4)
        return page

    def ensure(self, need: float) -> None:
        assert self.page is not None
        if self.y + need > self.max_y:
            self.new_page()

    def _run_font(self, *, bold: bool = False, italic: bool = False, code: bool = False) -> str:
        if code:
            return "cour"
        if bold:
            return self._font_bold
        if italic:
            return "heit"
        return self._font_reg

    def _textbox(
        self,
        text: str,
        *,
        fontsize: float,
        color: tuple[float, float, float],
        fontname: str | None = None,
        align: int = 0,
        indent: float = 0,
        max_width: float | None = None,
        space_after: float = 6,
        rich: bool = True,
    ) -> float:
        assert self.page is not None
        if not text.strip():
            return 0.0
        # Never emit soft hyphens
        text = text.replace("\u00ad", "").replace("\u2011", "-")
        if rich and fontname is None and align == 0:
            return self._rich_textbox(
                text,
                fontsize=fontsize,
                color=color,
                indent=indent,
                max_width=max_width,
                space_after=space_after,
            )
        fontname = fontname or self._font_reg
        plain = strip_inline_markers(text) if rich else text
        width = (max_width or CONTENT_W) - indent
        est_lines = max(1, int(len(plain) / max(20, width / (fontsize * 0.5))) + 1)
        height = est_lines * (fontsize * 1.45) + fontsize
        self.ensure(min(height, 200) + 2)
        rect = pymupdf.Rect(
            MARGIN_X + indent,
            self.y,
            MARGIN_X + indent + width,
            min(self.y + height + 20, self.max_y),
        )
        unused = self.page.insert_textbox(
            rect,
            plain,
            fontsize=fontsize,
            fontname=fontname,
            color=color,
            align=align,
        )
        used = rect.height - unused
        self.y += max(used, fontsize + 2) + space_after
        return used

    def _rich_textbox(
        self,
        text: str,
        *,
        fontsize: float,
        color: tuple[float, float, float],
        indent: float = 0,
        max_width: float | None = None,
        space_after: float = 6,
    ) -> float:
        """Word-wrap Markdown inline runs (bold/italic/code); markers omitted."""
        assert self.page is not None
        from app.services.renderer.inline_md import InlineRun

        width = (max_width or CONTENT_W) - indent
        line_h = fontsize * 1.45
        x0 = MARGIN_X + indent
        x_max = x0 + width
        y0 = self.y
        x = x0
        drew = False

        def new_line() -> None:
            nonlocal x
            self.y += line_h
            self.ensure(line_h + 2)
            x = x0

        def tokens_of(s: str) -> list[str]:
            out: list[str] = []
            buf = ""
            for ch in s:
                if ch == " ":
                    if buf:
                        out.append(buf)
                        buf = ""
                    out.append(" ")
                else:
                    buf += ch
            if buf:
                out.append(buf)
            return out

        self.ensure(line_h + 2)
        soft_lines = text.replace("\r\n", "\n").split("\n")
        for li, soft in enumerate(soft_lines):
            if li > 0:
                new_line()
            runs: list[InlineRun] = parse_inline(soft)
            if not runs and soft == "":
                continue
            if not runs:
                runs = [InlineRun(soft)]
            for ir in runs:
                font = self._run_font(bold=ir.bold, italic=ir.italic, code=ir.code)
                for tok in tokens_of(ir.text):
                    tw = self._text_width(tok, fontsize=fontsize, bold=ir.bold or ir.code)
                    if tok != " " and x > x0 and x + tw > x_max:
                        new_line()
                    if tok == " " and x <= x0 + 0.01:
                        continue
                    self.page.insert_text(
                        pymupdf.Point(x, self.y + fontsize),
                        tok,
                        fontsize=fontsize,
                        fontname=font,
                        color=color,
                    )
                    x += tw
                    drew = True
        used = max(fontsize + 2, (self.y - y0) + (fontsize if drew else 0))
        self.y = y0 + used + space_after
        return used

    def _section_heading(self, text: str, *, size: float = 20, level: int = 1) -> None:
        before = {1: 20, 2: 14, 3: 10}.get(level, 10)
        after = {1: 6, 2: 4, 3: 3}.get(level, 4)
        self.y += before * 0.35
        self.ensure(size + 28)
        clean = strip_inline_markers(text)
        self._textbox(
            clean,
            fontsize=size,
            color=self.brand_dark,
            fontname=self._font_bold,
            space_after=0,
            rich=False,
        )
        if level == 1:
            assert self.page is not None
            self.page.draw_line(
                pymupdf.Point(MARGIN_X, self.y + 2),
                pymupdf.Point(PAGE_W - MARGIN_X, self.y + 2),
                color=self.tint,
                width=0.5,
            )
            self.y += after + 4
        else:
            self.y += after

    def _clean_cell(self, text: str) -> str:
        return (
            (text or "")
            .replace("\u00ad", "")
            .replace("\u2011", "-")
            .replace("\u200b", "")
            .strip()
        )

    def _text_width(self, text: str, *, fontsize: float, bold: bool = False) -> float:
        """Measure rendered width; fall back to a conservative estimate."""
        if not text:
            return 0.0
        font = "hebo" if bold else "helv"
        try:
            return float(pymupdf.get_text_length(text, fontname=font, fontsize=fontsize))
        except Exception:
            return len(text) * fontsize * 0.55

    def _table_col_widths(
        self,
        headers: list[str],
        rows: list[list[str]],
        *,
        fontsize: float,
        pad: float,
        weights: list[float] | None,
    ) -> list[float]:
        cols = len(headers)
        if weights:
            tw = sum(weights) or 1.0
            return [CONTENT_W * (w / tw) for w in weights]

        # Content-aware widths so dates / prices aren't clipped in wide tables
        mins = [0.0] * cols
        for i, h in enumerate(headers):
            mins[i] = max(mins[i], self._text_width(h, fontsize=fontsize, bold=True))
        for row in rows:
            for i in range(cols):
                val = row[i] if i < len(row) else ""
                mins[i] = max(mins[i], self._text_width(val, fontsize=fontsize))

        # Padding + small breathing room; clamp so no column starves
        raw = [m + 2 * pad + 4 for m in mins]
        total = sum(raw) or 1.0
        if total <= CONTENT_W:
            # Distribute leftover space proportionally
            extra = CONTENT_W - total
            return [w + extra * (w / total) for w in raw]

        # Shrink proportionally but keep a floor so ISO dates (10 chars) fit
        floor = self._text_width("2026-01-05", fontsize=fontsize) + 2 * pad + 2
        floors = [min(max(floor * 0.55, CONTENT_W / (cols * 2.2)), w) for w in raw]
        # First pass: scale to fit
        scale = CONTENT_W / total
        scaled = [max(floors[i], raw[i] * scale) for i in range(cols)]
        # If floors blew the budget, scale everything uniformly
        s2 = CONTENT_W / (sum(scaled) or 1.0)
        return [w * s2 for w in scaled]

    def _draw_table(
        self,
        headers: list[str],
        rows: list[list[str]],
        *,
        col_weights: list[float] | None = None,
        show_header: bool | None = None,
    ) -> None:
        assert self.page is not None
        cols = max(len(headers), max((len(r) for r in rows), default=0), 1)
        headers = [self._clean_cell(h) for h in (headers + [""] * cols)[:cols]]
        norm_rows = [
            [self._clean_cell(c) for c in (list(r) + [""] * cols)[:cols]] for r in rows
        ]
        if show_header is None:
            show_header = any(h.strip() for h in headers)

        # Wider tables → smaller type so every column stays readable
        fs = 9.5 if cols <= 5 else (8.5 if cols <= 7 else 7.5)
        pad = mm_to_pt(1.4)
        col_ws = self._table_col_widths(
            headers, norm_rows, fontsize=fs, pad=pad, weights=col_weights
        )

        def cell_lines(text: str, width: float, *, bold: bool = False) -> int:
            avail = max(8.0, width - 2 * pad)
            if not text:
                return 1
            # Greedy wrap on spaces; never invent soft hyphens
            words = text.split(" ")
            lines = 1
            line_w = 0.0
            space_w = self._text_width(" ", fontsize=fs, bold=bold)
            for word in words:
                ww = self._text_width(word, fontsize=fs, bold=bold)
                if ww > avail:
                    # Hard-break overlong tokens by measured width
                    chunk = ""
                    for ch in word:
                        trial = chunk + ch
                        if self._text_width(trial, fontsize=fs, bold=bold) > avail and chunk:
                            lines += 1
                            chunk = ch
                        else:
                            chunk = trial
                    line_w = self._text_width(chunk, fontsize=fs, bold=bold)
                    continue
                need = ww if line_w == 0 else ww + space_w
                if line_w + need > avail and line_w > 0:
                    lines += 1
                    line_w = ww
                else:
                    line_w += need
            return max(1, lines)

        def row_height(cells: list[str], *, header: bool = False) -> float:
            bold = header
            lines = max(cell_lines(cells[i], col_ws[i], bold=bold) for i in range(cols))
            # Bold built-in fonts (hebo) need more vertical room than Arial metrics suggest
            return max(22.0, lines * (fs * 1.35) + 2 * pad + 6)

        header_h = row_height(headers, header=True) if show_header else 0.0
        body_heights = [row_height(r) for r in norm_rows]
        need = header_h + sum(body_heights) + 8
        self.ensure(min(need, 160))

        def _fill_cell(
            cell: pymupdf.Rect,
            text: str,
            *,
            fontsize: float,
            fontname: str,
            color: tuple[float, float, float],
            align: int = 0,
        ) -> None:
            """insert_textbox; if height is too tight (rc < 0), fall back to insert_text."""
            assert self.page is not None
            if not text:
                return
            box = cell + (pad, 3, -pad, -2)
            rc = self.page.insert_textbox(
                box,
                text,
                fontsize=fontsize,
                fontname=fontname,
                color=color,
                align=align,
            )
            if rc < 0:
                # Helvetica-Bold often needs a taller box than our estimate — draw baseline text
                self.page.insert_text(
                    pymupdf.Point(box.x0, min(box.y0 + fontsize + 1, box.y1 - 1)),
                    text[:120],
                    fontsize=fontsize,
                    fontname=fontname if fontname in ("helv", "hebo") else "helv",
                    color=color,
                )

        def draw_header_row(y: float) -> float:
            assert self.page is not None
            if not show_header:
                return y
            x = MARGIN_X
            for i, h in enumerate(headers):
                cell = pymupdf.Rect(x, y, x + col_ws[i], y + header_h)
                self.page.draw_rect(cell, color=self.brand, fill=self.brand, width=0.3)
                _fill_cell(
                    cell,
                    h,
                    fontsize=fs,
                    fontname=self._font_bold,
                    color=(1, 1, 1),
                )
                x += col_ws[i]
            return y + header_h

        y = draw_header_row(self.y)
        for r_i, cells in enumerate(norm_rows):
            rh = body_heights[r_i]
            if y + rh > self.max_y:
                self.new_page()
                y = draw_header_row(self.y)
            fill = self.tint if r_i % 2 == 0 else (1, 1, 1)
            x = MARGIN_X
            for c, val in enumerate(cells):
                cell = pymupdf.Rect(x, y, x + col_ws[c], y + rh)
                self.page.draw_rect(cell, color=self.rule, fill=fill, width=0.35)
                # Prefer regular weight in cells — bold built-ins overflow short boxes on Linux
                numeric = bool(val) and all(
                    ch.isdigit() or ch in ",.%$+- " for ch in val
                )
                _fill_cell(
                    cell,
                    val,
                    fontsize=fs,
                    fontname=self._font_reg,
                    color=self.text,
                    align=2 if numeric else 0,
                )
                x += col_ws[c]
            y += rh
        self.y = y + 14

    def cover(self) -> None:
        page = self.new_page(cover=True)
        # Center logo ~28% page height
        y = PAGE_H * 0.28 - mm_to_pt(21)
        if self.cover_logo:
            self._insert_logo(
                page,
                self.cover_logo,
                x=PAGE_W / 2,
                y=y,
                max_w_mm=70.0,
                max_h_mm=42.0,
                align="center",
            )
            y += mm_to_pt(42) + mm_to_pt(14)
        else:
            y = PAGE_H * 0.32

        title = (self.meta.title or "Untitled Document").strip()
        if self.theme.layout and self.theme.layout.force_title_uppercase:
            display = title.upper()
        else:
            display = title  # as typed
        page.insert_textbox(
            pymupdf.Rect(MARGIN_X, y, PAGE_W - MARGIN_X, y + 80),
            display,
            fontsize=30,
            fontname=self._font_bold,
            color=self.brand_dark,
            align=1,
        )
        y += 72

        # Accent bar 24mm × 3pt
        bar_w = mm_to_pt(24)
        page.draw_rect(
            pymupdf.Rect(PAGE_W / 2 - bar_w / 2, y, PAGE_W / 2 + bar_w / 2, y + 3),
            color=self.brand,
            fill=self.brand,
            width=0,
        )
        y += 18

        if self.meta.subtitle:
            page.insert_textbox(
                pymupdf.Rect(MARGIN_X + 20, y, PAGE_W - MARGIN_X - 20, y + 36),
                self.meta.subtitle,
                fontsize=13,
                fontname=self._font_reg,
                color=self.muted,
                align=1,
            )
            y += 40

        date_s = (self.meta.date or "").replace("\u00ad", "").replace("\u2011", "-")
        page.insert_textbox(
            pymupdf.Rect(MARGIN_X, y, PAGE_W - MARGIN_X, y + 24),
            f"Version {self.meta.version or '1.0'} · {date_s}".strip(" ·"),
            fontsize=11,
            fontname=self._font_reg,
            color=self.text,
            align=1,
        )
        y += 36

        # Release Notice in lower third (box must fit bold font ascent on Linux/hebo)
        y = max(y, PAGE_H * 0.58)
        rn_box = pymupdf.Rect(MARGIN_X, y, PAGE_W - MARGIN_X, y + 28)
        rn_rc = page.insert_textbox(
            rn_box,
            "Release Notice",
            fontsize=14,
            fontname=self._font_bold,
            color=self.brand_dark,
            align=1,
        )
        if rn_rc < 0:
            page.insert_text(
                pymupdf.Point(PAGE_W / 2 - 50, y + 16),
                "Release Notice",
                fontsize=14,
                fontname=self._font_reg,
                color=self.brand_dark,
            )
        y += 32
        self.y = y
        notice_rows = [[k, v] for k, v in self.plan.release_rows]
        self._draw_table(["", ""], notice_rows, col_weights=[0.38, 0.62], show_header=False)

        if self.plan.compact_revision_on_cover:
            self._section_heading("Revision History", size=14, level=2)
            self._draw_table(
                ["#", "Version", "Date", "Author", "Reason for Change"],
                self.plan.revision_rows,
                col_weights=[0.08, 0.14, 0.18, 0.22, 0.38],
            )

    def control_page(self) -> None:
        """Revision history and/or TOC on one document-control page."""
        self.new_page()
        if self.plan.include_revision_page:
            self._section_heading("Revision History", size=20, level=1)
            self._draw_table(
                ["#", "Version", "Date", "Author", "Reason for Change"],
                self.plan.revision_rows,
                col_weights=[0.08, 0.14, 0.18, 0.22, 0.38],
            )
        if self.plan.include_toc:
            self._section_heading("Table of Contents", size=20, level=1)

    def fill_toc(self, entries: list[tuple[str, int, int]]) -> None:
        assert self.page is not None
        for title, level, page_no in entries:
            if level > 2:
                continue
            self.ensure(18)
            indent = (max(level, 1) - 1) * 14
            left = MARGIN_X + indent
            title_s = title.replace("\u00ad", "")[:70]
            self.page.insert_text(
                pymupdf.Point(left, self.y + 11),
                title_s,
                fontsize=10.5 if level <= 1 else 10,
                fontname=self._font_bold if level <= 1 else self._font_reg,
                color=self.brand_dark if level <= 1 else self.text,
            )
            page_label = str(page_no) if page_no else ""
            tw = pymupdf.get_text_length(title_s, fontname="helv", fontsize=10.5)
            dots_x0 = left + tw + 6
            dots_x1 = PAGE_W - MARGIN_X - 28
            if dots_x1 > dots_x0 + 10:
                x = dots_x0
                while x < dots_x1:
                    self.page.draw_circle(
                        pymupdf.Point(x, self.y + 9),
                        0.55,
                        color=self.muted,
                        fill=self.muted,
                        width=0,
                    )
                    x += 4.5
            if page_label:
                self.page.insert_textbox(
                    pymupdf.Rect(PAGE_W - MARGIN_X - 26, self.y, PAGE_W - MARGIN_X, self.y + 16),
                    page_label,
                    fontsize=10.5,
                    fontname=self._font_reg,
                    color=self.text,
                    align=2,
                )
            self.y += 16

    def render_blocks(self, source: str, blocks: list[Block]) -> None:
        self.new_page()
        title_l = (self.meta.title or "").strip().lower()

        for block in blocks:
            if block.type == "page_break":
                self.new_page()
                continue

            if block.type == "divider":
                self.ensure(16)
                assert self.page is not None
                self.page.draw_line(
                    pymupdf.Point(MARGIN_X, self.y + 6),
                    pymupdf.Point(PAGE_W - MARGIN_X, self.y + 6),
                    color=self.rule,
                    width=0.7,
                )
                self.y += 16
                continue

            if block.type == "heading":
                level = min(max(block.level or 1, 1), 3)
                text = strip_inline_markers(
                    block.resolved_text(source).replace("\u00ad", "")
                )
                # Skip invented title H1
                if level == 1 and text.strip().lower() == title_l:
                    continue
                size = {1: 20, 2: 15, 3: 12.5}[level]
                self._section_heading(text, size=size, level=level)
                self.heading_pages.append((text, level, self.doc.page_count))
                continue

            if block.type in ("steps", "bullets"):
                items = block.resolved_items(source)
                for i, item in enumerate(items, start=1):
                    self.ensure(22)
                    assert self.page is not None
                    if block.type == "steps":
                        badge = pymupdf.Rect(MARGIN_X, self.y, MARGIN_X + 16, self.y + 16)
                        self.page.draw_rect(badge, color=self.brand, fill=self.brand, width=0)
                        self.page.insert_textbox(
                            badge,
                            str(i),
                            fontsize=8,
                            fontname=self._font_bold,
                            color=(1, 1, 1),
                            align=1,
                        )
                        self._textbox(item, fontsize=10.5, color=self.text, indent=22)
                    else:
                        self.page.insert_text(
                            pymupdf.Point(MARGIN_X + 4, self.y + 11),
                            "•",
                            fontsize=11,
                            fontname=self._font_bold,
                            color=self.brand,
                        )
                        self._textbox(item, fontsize=10.5, color=self.text, indent=16)
                continue

            if block.type in ("callout_info", "callout_warning", "callout_success"):
                body = strip_inline_markers(block.resolved_text(source))
                label = (block.label or block.type.replace("callout_", "")).upper()
                accent = {
                    "callout_info": _rgb(self.theme.palette.info),
                    "callout_warning": _rgb(self.theme.palette.warning),
                    "callout_success": _rgb(self.theme.palette.success),
                }[block.type]
                h = 36 + 12 * max(1, len(body) // 70)
                self.ensure(h + 8)
                assert self.page is not None
                rect = pymupdf.Rect(MARGIN_X, self.y, PAGE_W - MARGIN_X, self.y + h)
                self.page.draw_rect(rect, color=accent, fill=self.tint, width=0.5)
                self.page.draw_rect(
                    pymupdf.Rect(MARGIN_X, self.y, MARGIN_X + 3, self.y + h),
                    color=accent,
                    fill=accent,
                    width=0,
                )
                self.page.insert_textbox(
                    pymupdf.Rect(MARGIN_X + 12, self.y + 6, PAGE_W - MARGIN_X - 8, self.y + h - 4),
                    f"{label}\n{body}",
                    fontsize=10,
                    fontname=self._font_reg,
                    color=self.text,
                )
                self.y += h + 12
                continue

            if block.type == "code":
                code = block.resolved_text(source) or (block.text or "")
                lines = code.splitlines() or [""]
                label = block.label or "CODE"
                h = 20 + 11 * min(len(lines), 40)
                self.ensure(h + 6)
                assert self.page is not None
                rect = pymupdf.Rect(MARGIN_X, self.y, PAGE_W - MARGIN_X, self.y + h)
                self.page.draw_rect(rect, color=self.rule, fill=(0.97, 0.97, 0.98), width=0.5)
                self.page.insert_text(
                    pymupdf.Point(MARGIN_X + 8, self.y + 12),
                    label,
                    fontsize=7.5,
                    fontname=self._font_bold,
                    color=self.brand_dark,
                )
                yy = self.y + 24
                for ln in lines[:40]:
                    self.page.insert_text(
                        pymupdf.Point(MARGIN_X + 10, yy),
                        ln[:110],
                        fontsize=9,
                        fontname="cour",
                        color=self.text,
                    )
                    yy += 11
                self.y += h + 12
                continue

            if block.type == "table" and block.table:
                headers = list(block.table.headers)
                rows = [list(r) for r in block.table.rows]
                self._draw_table(headers, rows)
                continue

            if block.type == "quote":
                text = block.resolved_text(source)
                self.ensure(28)
                assert self.page is not None
                self.page.draw_rect(
                    pymupdf.Rect(MARGIN_X, self.y, MARGIN_X + 3, self.y + 18),
                    color=self.brand,
                    fill=self.brand,
                    width=0,
                )
                self._textbox(text, fontsize=10.5, color=self.muted, indent=12)
                continue

            text = block.resolved_text(source) or (block.text or "")
            if text.strip():
                self._textbox(text, fontsize=10.5, color=self.text)

    def finish_chrome(self) -> None:
        total = self.doc.page_count
        title = (self.meta.title or "Document").strip()[:60] or "Document"
        rule_y = PAGE_H - MARGIN_BOTTOM + 4
        # Keep footer ≥8 mm above bottom border
        text_bot = PAGE_H - BORDER - FOOTER_SAFE_GAP
        text_top = min(rule_y + 4, text_bot - 12)
        for i in range(total):
            page = self.doc[i]
            page.draw_line(
                pymupdf.Point(MARGIN_X, rule_y),
                pymupdf.Point(PAGE_W - MARGIN_X, rule_y),
                color=self.rule,
                width=0.5,
            )
            page.insert_textbox(
                pymupdf.Rect(MARGIN_X, text_top, PAGE_W * 0.62, text_bot),
                title,
                fontsize=8,
                fontname=self._font_reg,
                color=self.muted,
                align=0,
            )
            page.insert_textbox(
                pymupdf.Rect(PAGE_W * 0.55, text_top, PAGE_W - MARGIN_X, text_bot),
                f"Page {i + 1} of {total}",
                fontsize=8,
                fontname=self._font_reg,
                color=self.muted,
                align=2,
            )


def render_pdf_from_blocks(
    *,
    out_path: Path,
    source_text: str,
    blocks: list[Block],
    theme: Theme,
    meta: DocumentMeta,
    logo_bytes: bytes | None = None,
    corner_bytes: bytes | None = None,
    options: RenderOptions | None = None,
) -> Path:
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    options = options or RenderOptions()
    plan = plan_layout(
        blocks=blocks,
        source=source_text,
        meta=meta,
        options=options,
        layout=theme.layout,
    )

    cover_logo = _logo_bytes_for(theme, "cover", logo_bytes)
    corner_fallback = (
        logo_bytes
        if (theme.logos and theme.logos.same_for_both)
        else corner_bytes
    )
    corner_logo = _logo_bytes_for(theme, "corner", corner_fallback)
    if cover_logo is None and logo_bytes:
        cover_logo = logo_bytes
    if corner_logo is None and theme.logos and theme.logos.same_for_both and cover_logo:
        corner_logo = cover_logo

    # Pass 1: probe heading pages
    probe = _PdfBuilder(theme, meta, cover_logo, corner_logo, plan)
    if plan.include_cover:
        probe.cover()
    if plan.include_revision_page or plan.include_toc:
        probe.control_page()
        if plan.include_toc:
            probe.fill_toc([])  # placeholder space
    probe.render_blocks(source_text, blocks)
    heading_pages = list(probe.heading_pages)
    probe.doc.close()

    # Pass 2: final
    builder = _PdfBuilder(theme, meta, cover_logo, corner_logo, plan)
    if plan.include_cover:
        builder.cover()

    control_base = builder.doc.page_count + 1
    if plan.include_revision_page or plan.include_toc:
        builder.control_page()
        if plan.include_toc:
            # Body headings only — never front matter
            # Page numbers: body starts after cover (+ control)
            body_offset = builder.doc.page_count  # current pages before body
            toc_entries = [(t, lvl, p + body_offset) for (t, lvl, p) in heading_pages]
            # Recompute: heading_pages already absolute from probe; adjust by delta
            # Simpler: use probe page numbers shifted by (builder cover/control - probe cover/control)
            delta = 0  # same structure
            toc_entries = [(t, lvl, p + delta) for (t, lvl, p) in heading_pages]
            builder.fill_toc(toc_entries)

    builder.render_blocks(source_text, blocks)
    # Fix TOC page numbers after body known — second fill not needed if pages stable
    builder.finish_chrome()

    builder.doc.set_metadata(
        {
            "title": meta.title,
            "author": meta.author or "Docgen",
            "subject": meta.classification or "",
            "creator": "Docgen",
            "producer": "Docgen Native PDF",
        }
    )
    try:
        builder.doc.set_xml_metadata(
            '<?xml version="1.0"?><rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">'
            '<rdf:Description xmlns:dc="http://purl.org/dc/elements/1.1/">'
            "<dc:language>en-US</dc:language></rdf:Description></rdf:RDF>"
        )
    except Exception:
        pass
    builder.doc.save(str(out_path), garbage=3, deflate=True)
    builder.doc.close()
    _ = control_base
    return out_path


def render_pdf_from_docx_text_fallback(docx_path: Path, out_path: Path) -> Path:
    from uuid import uuid4

    from docx import Document

    from app.models.blocks import SourceSpan
    from app.services.theme_engine.presets import get_preset

    document = Document(str(docx_path))
    lines = [p.text for p in document.paragraphs if p.text.strip()]
    text = "\n\n".join(lines) or "Empty document"
    blocks = [
        Block(
            id=uuid4().hex[:12],
            type="paragraph",
            span=SourceSpan(start=0, end=len(text)),
            origin="source",
        )
    ]
    return render_pdf_from_blocks(
        out_path=out_path,
        source_text=text,
        blocks=blocks,
        theme=get_preset("neutral"),
        meta=DocumentMeta(title=docx_path.stem),
    )
