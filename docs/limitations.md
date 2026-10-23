# Limitations

- PDF is rendered **natively** with PyMuPDF from the same blocks/theme as the DOCX (`PDF_ENGINE=native`). Layout matches brand chrome without LibreOffice. Optional `PDF_ENGINE=libreoffice` converts the DOCX via `soffice` when installed.
- Phase 1 uses the **rules** structurer only (no LLM). Complex prose may get coarser block types.
- Cached TOC page numbers need a LibreOffice PDF pass; with the native engine, TOC page numbers are approximate / field-based in Word.
- URL theme extraction is SSRF-guarded stub until Phase 5.
- Free cloud LLM tiers (Phase 2) may train on prompts — Studio will warn; Confidential → Ollama only.
