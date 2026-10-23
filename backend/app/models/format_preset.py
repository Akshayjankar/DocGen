"""FormatPreset — validated YAML document-type defaults (Revision 3 WP-C)."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class FormatHeader(BaseModel):
    logo: Literal["corner", "cover", "none"] = "corner"
    classification: bool = True


class FormatFooter(BaseModel):
    left: Literal["title", "doc_id", "none"] = "title"
    center: Literal["doc_id", "none", "date"] = "none"
    right: Literal["page_x_of_y", "none"] = "page_x_of_y"


class FormatLayout(BaseModel):
    cover_style: Literal["centered", "editorial", "minimal", "none"] = "centered"
    front_matter: list[str] = Field(default_factory=list)
    revision_history: Literal["auto", "cover", "page", "off"] = "auto"
    toc: Literal["auto", "on", "off"] = "auto"
    toc_depth: int = 2
    heading_numbering: Literal["none", "decimal", "legal"] = "none"
    header: FormatHeader = Field(default_factory=FormatHeader)
    footer: FormatFooter = Field(default_factory=FormatFooter)
    margins: Literal["normal", "narrow", "wide"] = "normal"


class FormatStyle(BaseModel):
    font_pair: Literal["modern", "editorial", "classic", "clean", "technical"] = "modern"
    table_style: Literal["striped", "plain"] = "striped"
    callout_style: Literal["bar", "box"] = "bar"


class FormatSection(BaseModel):
    title: str
    required: bool = False
    hint: str | None = None


class FormatStructurerRules(BaseModel):
    numbered_lines_as_steps: bool = True
    warn_prefix_as_callout: bool = True
    question_lines_as_headings: bool = False


class FormatStructurer(BaseModel):
    rules: FormatStructurerRules = Field(default_factory=FormatStructurerRules)
    hints: str = ""


class FormatLint(BaseModel):
    required_sections: list[str] = Field(default_factory=list)


class FormatPreset(BaseModel):
    id: str
    label: str
    description: str = ""
    layout: FormatLayout = Field(default_factory=FormatLayout)
    style: FormatStyle = Field(default_factory=FormatStyle)
    sections: list[FormatSection] = Field(default_factory=list)
    structurer: FormatStructurer = Field(default_factory=FormatStructurer)
    lint: FormatLint = Field(default_factory=FormatLint)
    sample: str = ""

    def as_public(self) -> dict[str, Any]:
        return self.model_dump()
