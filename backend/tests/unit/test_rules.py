"""Rules structurer golden-ish tests (offline)."""

from app.models.document import DocType
from app.services.ingest.parse import parse_text
from app.services.structurer.rules import RulesStructurer
from app.services.verifier.content_lock import score

SAMPLE = """# Purpose

This SOP describes how to reset a user password safely.

## Scope

Applies to all support engineers.

## Procedure

1. Verify the requester identity.
2. Open the admin console.
3. Reset the password and notify the user.

Note: Never share temporary passwords over SMS.

```bash
sudo passwd alice
```

| Step | Owner |
| --- | --- |
| Verify | Support |
| Reset | Admin |
"""


def test_rules_detects_headings_steps_code_table_callout() -> None:
    norm = parse_text(SAMPLE)
    blocks = RulesStructurer().structure(norm, DocType.sop)
    types = {b.type for b in blocks}
    assert "heading" in types
    assert "steps" in types
    assert "code" in types
    assert "table" in types
    assert "callout_info" in types


def test_format_only_content_lock_100() -> None:
    norm = parse_text(SAMPLE)
    blocks = RulesStructurer().structure(norm, DocType.sop)
    result = score(norm.text, blocks, mode="format_only")
    assert result.preserved_pct == 100.0, result.missing
