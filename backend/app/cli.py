"""CLI: python -m app.cli build --logo x.png --text in.md --out out/"""

from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from app import APP_NAME, __version__
from app.models.document import DocType, DocumentMeta, RenderOptions
from app.services.pipeline import build_document

app = typer.Typer(
    name="docgen",
    help=f"{APP_NAME} — branded documents from logo + text",
    no_args_is_help=True,
)
console = Console()


@app.command()
def version() -> None:
    """Print version."""
    console.print(f"{APP_NAME} {__version__}")


@app.command("build")
def build(  # noqa: B008 — Typer Option defaults are idiomatic
    text: Path | None = typer.Option(None, "--text", "-t", help="Input .txt/.md/.docx"),
    logo: Path | None = typer.Option(None, "--logo", "-l", help="Company logo image"),
    out: Path = typer.Option(Path("out"), "--out", "-o", help="Output directory"),
    title: str = typer.Option("Untitled Document", "--title"),
    doc_type: DocType = typer.Option(DocType.sop, "--type", "-d"),
    mode: str = typer.Option("format_only", "--mode", help="format_only | improve"),
    author: str = typer.Option("", "--author"),
    version_str: str = typer.Option("1.0", "--doc-version"),
    classification: str = typer.Option("Internal", "--classification"),
    no_pdf: bool = typer.Option(False, "--no-pdf", help="Skip PDF conversion"),
    redact_pii: bool = typer.Option(False, "--redact-pii"),
    paste: str | None = typer.Option(None, "--paste", help="Raw text instead of --text file"),
) -> None:
    """Build a branded DOCX (and PDF when LibreOffice is available)."""
    if text is None and paste is None:
        console.print("[red]Provide --text or --paste[/red]")
        raise typer.Exit(1)

    meta = DocumentMeta(
        title=title,
        author=author,
        version=version_str,
        classification=classification,
    )
    options = RenderOptions(redact_pii=redact_pii)

    result = build_document(
        text=paste,
        text_path=text,
        logo_path=logo,
        out_dir=out,
        doc_type=doc_type,
        mode=mode,
        meta=meta,
        options=options,
        redact_pii=redact_pii,
        skip_pdf=no_pdf,
    )

    table = Table(title=f"{APP_NAME} build result")
    table.add_column("Metric")
    table.add_column("Value")
    table.add_row("DOCX", str(result.docx_path))
    table.add_row("PDF", str(result.pdf_path) if result.pdf_path else "(skipped — no soffice)")
    table.add_row("Theme", f"{result.theme.name} ({result.theme.source})")
    table.add_row("Blocks", str(len(result.blocks)))
    table.add_row("Content preserved", f"{result.content_lock.preserved_pct}%")
    table.add_row("DOCX valid", "yes" if result.validation.ok else "no")
    table.add_row("Lint issues", str(len(result.lint)))
    table.add_row("WCAG AA", "yes" if result.theme.contrast.all_aa else "no")
    console.print(table)

    if result.content_lock.missing:
        console.print("[yellow]Missing content snippets:[/yellow]")
        for m in result.content_lock.missing[:10]:
            console.print(f"  - {m[:100]}")

    if mode == "format_only" and result.content_lock.preserved_pct < 100:
        console.print("[red]Content-lock failed (must be 100% in format_only)[/red]")
        raise typer.Exit(2)

    if not result.validation.ok:
        console.print("[red]DOCX validation errors:[/red]")
        for e in result.validation.errors:
            console.print(f"  - {e}")
        raise typer.Exit(3)


if __name__ == "__main__":
    app()
