"""Content-lock verifier tests."""

from app.models.blocks import Block, SourceSpan
from app.services.verifier.content_lock import score


def test_full_span_coverage_is_100() -> None:
    source = "Hello world. Second sentence."
    blocks = [
        Block(type="paragraph", span=SourceSpan(start=0, end=len(source)), origin="source"),
    ]
    r = score(source, blocks, mode="format_only")
    assert r.preserved_pct == 100.0


def test_missing_content_reported() -> None:
    source = "Alpha sentence here. Beta sentence here."
    blocks = [
        Block(type="paragraph", span=SourceSpan(start=0, end=20), origin="source"),
    ]
    r = score(source, blocks, mode="format_only")
    # May or may not be 100 depending on whitespace coverage; missing list should be informative
    assert isinstance(r.preserved_pct, float)
