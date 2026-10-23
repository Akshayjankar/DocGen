"""Extract theme colors/fonts from a sample .docx/.dotx."""

from __future__ import annotations

import io
import zipfile
from xml.etree import ElementTree as ET

from app.models.theme import BorderSpec, Theme
from app.services.theme_engine.contrast import enforce_palette_aa
from app.services.theme_engine.derive import derive_palette
from app.services.theme_engine.presets import font_pair_for_mood, get_preset

_NS = {
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
}


def _srgb_to_hex(srgb: str | None) -> str | None:
    if not srgb or len(srgb) < 6:
        return None
    return f"#{srgb[:6].upper()}"


def from_docx(file_bytes: bytes, *, name: str = "From Document", mood: str = "corporate") -> Theme:
    try:
        with zipfile.ZipFile(io.BytesIO(file_bytes)) as zf:
            theme_xml = None
            for path in zf.namelist():
                if path.endswith("theme/theme1.xml"):
                    theme_xml = zf.read(path)
                    break
            if theme_xml is None:
                return get_preset("neutral", mood=mood)

            root = ET.fromstring(theme_xml)
            colors: dict[str, str] = {}
            for scheme in root.findall(".//a:clrScheme", _NS):
                for child in list(scheme):
                    tag = child.tag.split("}")[-1]
                    srgb = child.find(".//a:srgbClr", _NS)
                    if srgb is not None:
                        hx = _srgb_to_hex(srgb.get("val"))
                        if hx:
                            colors[tag] = hx

            primary = colors.get("accent1") or colors.get("dk1") or "#2F5D8A"
            secondary = colors.get("accent2") or colors.get("dk2")
            accent = colors.get("accent3") or colors.get("accent4")

            heading = "Carlito"
            body = "Carlito"
            for font_scheme in root.findall(".//a:fontScheme", _NS):
                major = font_scheme.find("a:majorFont/a:latin", _NS)
                minor = font_scheme.find("a:minorFont/a:latin", _NS)
                if major is not None and major.get("typeface"):
                    heading = major.get("typeface") or heading
                if minor is not None and minor.get("typeface"):
                    body = minor.get("typeface") or body

            palette = derive_palette(primary, secondary, accent)
            palette, report = enforce_palette_aa(palette)
            fonts = font_pair_for_mood(mood)
            fonts = fonts.model_copy(update={"heading": heading, "body": body})

            return Theme(
                name=name,
                palette=palette,
                fonts=fonts,
                border=BorderSpec(color=palette.primary),  # type: ignore[arg-type]
                contrast=report,
                source="docx",
            )
    except Exception:
        t = get_preset("neutral", mood=mood)
        t.name = name
        t.contrast.adjustments.append("DOCX theme parse failed; using preset")
        return t


# silence unused if zipfile imported at top — keep zipfile used
_ = zipfile
