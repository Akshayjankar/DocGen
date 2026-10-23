# Docgen backend

Phase 1 core engine. CLI:

```bash
uv sync --all-extras
uv run python -m app.cli build --text in.md --logo logo.png --out out/ --no-pdf
uv run pytest
```
