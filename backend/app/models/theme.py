"""Theme, palette, fonts, border, logos, layout, contrast report."""

from __future__ import annotations

import re
from enum import Enum
from typing import Annotated, Literal
from uuid import uuid4

from pydantic import AfterValidator, BaseModel, Field, field_validator, model_validator

_HEX_RE = re.compile(r"^#[0-9A-Fa-f]{6}$")


def _normalize_hex(value: str) -> str:
    v = value.strip()
    if not v.startswith("#"):
        v = f"#{v}"
    if len(v) == 4:  # #RGB → #RRGGBB
        v = f"#{v[1] * 2}{v[2] * 2}{v[3] * 2}"
    if not _HEX_RE.match(v):
        raise ValueError(f"Invalid hex color: {value}")
    return v.upper()


HexColor = Annotated[str, AfterValidator(_normalize_hex)]


class Palette(BaseModel):
    """Semantic palette. Color roles: brand=primary, brand_deep=primary_dark,
    tint=primary_tint, ink=text, muted, rule≈muted/border."""

    primary: HexColor
    primary_dark: HexColor
    primary_tint: HexColor
    secondary: HexColor
    accent: HexColor
    text: HexColor
    muted: HexColor
    surface: HexColor
    info: HexColor
    warning: HexColor
    success: HexColor
    danger: HexColor

    @property
    def brand(self) -> str:
        return self.primary

    @property
    def brand_deep(self) -> str:
        return self.primary_dark

    @property
    def tint(self) -> str:
        return self.primary_tint

    @property
    def ink(self) -> str:
        return self.text

    @property
    def rule(self) -> str:
        return self.muted


class FontPair(BaseModel):
    heading: str
    body: str
    mono: str


class BorderSpec(BaseModel):
    style: Literal["none", "hairline", "single", "double", "thick-thin", "art-line"] = "double"
    width_pt: float = 1.25
    color: HexColor = "#1A1A1A"
    offset_pt: int = 20


class ContrastPair(BaseModel):
    foreground: HexColor
    background: HexColor
    ratio: float
    aa: bool
    aaa: bool
    label: str


class ContrastReport(BaseModel):
    pairs: list[ContrastPair] = Field(default_factory=list)
    all_aa: bool = True
    adjustments: list[str] = Field(default_factory=list)


class LogoRole(str, Enum):
    cover = "cover"
    corner = "corner"


class LogoAsset(BaseModel):
    id: str = Field(default_factory=lambda: uuid4().hex[:12])
    role: LogoRole
    filename: str = "logo.png"
    mime: str = "image/png"
    width_px: int = 0
    height_px: int = 0
    aspect: float = 1.0
    original_path: str = ""
    processed_path: str = ""
    background: Literal["none", "was_transparent", "removed", "kept"] = "none"
    bg_tolerance: int = 10
    max_width_mm: float = 70.0
    max_height_mm: float = 42.0
    alt_text: str = "Company logo"
    warnings: list[str] = Field(default_factory=list)

    @field_validator("bg_tolerance")
    @classmethod
    def _tol(cls, v: int) -> int:
        return max(0, min(30, int(v)))


class LogoSet(BaseModel):
    cover: LogoAsset | None = None
    corner: LogoAsset | None = None
    same_for_both: bool = False
    corner_position: Literal["left", "right"] = "left"
    corner_anchor: Literal["corner", "margin"] = "corner"
    corner_pages: Literal["all_except_cover", "all", "none"] = "all_except_cover"
    corner_height_mm: float = 11.0
    # Legacy (Rev2) — maps to corner_pages="all" when True
    show_corner_on_cover: bool = False
    palette_source: Literal["cover", "corner", "both"] = "cover"

    @model_validator(mode="after")
    def _legacy_show_on_cover(self) -> LogoSet:
        if self.show_corner_on_cover and self.corner_pages == "all_except_cover":
            self.corner_pages = "all"
        return self

    @field_validator("corner_height_mm")
    @classmethod
    def _height(cls, v: float) -> float:
        return max(6.0, min(16.0, float(v)))


class LayoutSpec(BaseModel):
    page_size: Literal["a4", "letter"] = "a4"
    margin_left_mm: float = 22.0
    margin_right_mm: float = 22.0
    margin_top_mm: float = 28.0
    margin_bottom_mm: float = 24.0
    cover_style: Literal["centered", "editorial", "minimal", "none"] = "centered"
    border_style: Literal["none", "hairline", "single", "double"] = "double"
    force_title_uppercase: bool = False
    date_format: Literal["human", "dmy", "mdy", "iso"] = "human"


class Theme(BaseModel):
    name: str
    palette: Palette
    fonts: FontPair
    border: BorderSpec = Field(default_factory=BorderSpec)
    logos: LogoSet = Field(default_factory=LogoSet)
    layout: LayoutSpec = Field(default_factory=LayoutSpec)
    # Legacy single-logo fields kept for API/CLI compatibility
    logo_path: str | None = None
    logo_alt: str = "Company logo"
    contrast: ContrastReport = Field(default_factory=ContrastReport)
    source: Literal["logo", "docx", "url", "preset", "manual"] = "preset"

    @model_validator(mode="after")
    def _sync_legacy_logo(self) -> Theme:
        if self.logos.cover and self.logos.cover.processed_path and not self.logo_path:
            self.logo_path = self.logos.cover.processed_path
        if self.logos.cover and self.logos.cover.alt_text:
            self.logo_alt = self.logos.cover.alt_text
        elif self.logo_path and not self.logos.cover:
            # Migrate legacy single path → cover asset stub
            self.logos.cover = LogoAsset(
                role=LogoRole.cover,
                processed_path=self.logo_path,
                original_path=self.logo_path,
                alt_text=self.logo_alt,
                max_width_mm=70.0,
                max_height_mm=42.0,
            )
        return self
