# Content-Lock Guarantee

## Format-only

1. Ingest assigns stable character offsets on normalized text.
2. Structurer emits `Block.span` / `items: SourceSpan[]` — no free text.
3. Renderer calls `block.resolved_text(source)` to inject original wording.
4. Unreferenced segments are auto-appended as paragraphs (nothing dropped).
5. Verifier `content_lock.score` must return **100%**; anything less is a bug.

## Improve mode

Blocks may set `origin="rewritten"` with `text` plus original `span`. Diff UI accept/reject before export (Phase 2).
