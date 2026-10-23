"""Inline Markdown + HR parsing for Format-only rendering."""

from app.models.document import DocType
from app.services.ingest.parse import parse_text
from app.services.renderer.inline_md import (
    is_horizontal_rule,
    parse_inline,
    strip_inline_markers,
)
from app.services.structurer.rules import RulesStructurer
from app.services.verifier.content_lock import score


def test_parse_bold_italic_code() -> None:
    runs = parse_inline("See **no internet** and *local* plus `ssh` end.")
    texts = [r.text for r in runs]
    assert "no internet" in texts
    assert "**" not in "".join(texts)
    bold = next(r for r in runs if r.text == "no internet")
    assert bold.bold and not bold.italic
    italic = next(r for r in runs if r.text == "local")
    assert italic.italic and not italic.bold
    code = next(r for r in runs if r.text == "ssh")
    assert code.code


def test_strip_and_hr() -> None:
    assert strip_inline_markers("**What this folder is**") == "What this folder is"
    assert is_horizontal_rule("---")
    assert is_horizontal_rule("***")
    assert not is_horizontal_rule("| --- | --- |")


def test_rules_emits_divider_and_keeps_lock() -> None:
    src = """# Title

**What this folder is (Phase 0):** notes.

---

Works **offline**.
"""
    norm = parse_text(src)
    blocks = RulesStructurer().structure(norm, DocType.sop)
    types = [b.type for b in blocks]
    assert "divider" in types
    # Markers stay in source spans — content lock still 100%
    result = score(norm.text, blocks, mode="format_only")
    assert result.preserved_pct == 100.0, result.missing
    # Paragraph resolution still contains markers (presentation strips them)
    paras = [b.resolved_text(norm.text) for b in blocks if b.type == "paragraph"]
    assert any("**" in p for p in paras)
