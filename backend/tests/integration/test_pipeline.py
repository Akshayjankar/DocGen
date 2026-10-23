"""End-to-end CLI pipeline without requiring LibreOffice."""

import io
from pathlib import Path

from PIL import Image

from app.models.document import DocType, DocumentMeta
from app.services.pipeline import build_document

SOP = """# Purpose

Describe the password reset process for support staff.

## Scope

All customer support engineers.

## Roles

Support Lead owns this procedure.

## Procedure

1. Verify the requester identity using two factors.
2. Open the admin console and locate the account.
3. Reset the password and notify the user securely.

## Records

Record the ticket ID and timestamp in the audit log.

Warning: Do not email passwords in plaintext.

```bash
sudo passwd alice
```
"""


def _logo() -> bytes:
    img = Image.new("RGBA", (96, 96), (0, 0, 0, 0))
    px = img.load()
    assert px is not None
    for y in range(20, 76):
        for x in range(20, 76):
            px[x, y] = (40, 100, 160, 255)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def test_pipeline_builds_valid_docx(tmp_path: Path) -> None:
    result = build_document(
        text=SOP,
        logo_bytes=_logo(),
        out_dir=tmp_path,
        doc_type=DocType.sop,
        mode="format_only",
        meta=DocumentMeta(title="Password Reset SOP", author="QA", version="1.0"),
        skip_pdf=True,
    )
    assert result.docx_path.exists()
    assert result.validation.ok
    assert result.validation.has_heading_styles
    assert result.validation.has_toc_field
    assert result.content_lock.preserved_pct == 100.0
    assert result.theme.contrast.all_aa
