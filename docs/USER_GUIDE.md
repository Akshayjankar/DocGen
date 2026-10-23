# Docgen — User Guide (first time)

Welcome. This guide explains **what Docgen does** and **how to use it**, without looking at the code.

---

## What is Docgen?

Docgen turns **rough notes** (pasted text, `.txt`, `.md`, or `.csv`) plus your **company logos** into a **branded Word document (.docx)** and a matching **PDF**.

Typical outputs: SOPs, setup guides, reports, policies, proposals, release notes, meeting minutes, and memos.

**One-line promise:** your wording stays yours (in Format mode); Docgen handles structure, branding, and layout.

---

## What you get in the finished document

- Cover page with your **cover logo** (optional styles by document type)
- Release notice and revision history (when the format calls for them)
- Table of contents (when there are enough headings)
- Themed headings, body text, striped tables, callouts, and code boxes
- Header with **corner logo** + classification label
- Footer with title / date / “Page X of Y”
- Branded page border

The **live paper** in Studio is meant to match what you export — what you see is what you download.

---

## Before you start (local app)

1. Start the API (port **8000**) and the web app (port **3000**) — see the project [README](../README.md).
2. Open **http://localhost:3000** in your browser.
3. Go to **Studio** (from the landing page or the header).

---

## Your first document (5 minutes)

### 1. Title and format

- Enter a **document title** in the top bar.
- Pick a **format** (SOP, Setup Guide, Report, Policy, …).  
  This chooses default layout: cover style, TOC, numbering, fonts — **not** your brand colors.

### 2. Mode: Format vs Improve

| Mode | What it does | When to use it |
|------|----------------|----------------|
| **Format** (recommended first) | Keeps every word you wrote. Only structures and brands the document. | Compliance, SOPs, “don’t change my text” |
| **Improve** | May suggest clearer wording. You **accept or reject** each change before export. | Drafts you want polished |

A short tip under the mode switch explains the active choice.

### 3. Logos

Upload two logos when you can:

| Slot | Where it appears |
|------|------------------|
| **Cover logo** | Centered on the cover page |
| **Corner logo** | Header on body pages (not the cover, by default) |

Optional controls:

- **Use cover for both** — same mark in cover and header
- **Hug corner / Align with text** — how close the header logo sits to the page edge
- **Left / Right**, size, and which pages show the corner logo

Upload a logo → Docgen samples colors into your theme (you can still tweak them in Brand & checks).

### 4. Your notes

Paste or type in **Your notes**, or upload `.txt` / `.md` / `.csv`.

Tips that work well:

- Use `# Heading` / `## Subheading` for structure  
- Markdown tables (`| Col | Col |`) or CSV — they become branded tables  
- `Note:` / `Warning:` lines become callouts  
- Numbered lists become procedure steps  
- Fenced code blocks become TERMINAL / FILE CONTENT boxes  

Leave notes empty and you’ll see a ghost skeleton for the selected format (preview only — never exported as real content).

### 5. Watch the live paper

The middle pane shows a **live preview** of the real PDF pages.

- It updates a short moment after you stop typing  
- Status moves from draft → exact  
- Page count and format name appear as you go  

### 6. Brand & checks

Open **Brand & checks** to:

- Adjust brand colors  
- See content-lock / lint hints  
- Turn **Ambient brand glow** on/off (dark Studio background tint from your palette)  
- Download when a press has finished  

### 7. Run press → download

Click **Run press** when you’re ready for a full job (especially for Improve mode and downloads).

Then download:

- **DOCX** — open in Word / Google Docs  
- **PDF** — share or print  

In Format mode, export can also come straight from the live preview session so paper and file stay aligned.

---

## Landing page extras

- **Chroma Drop** — drop a logo on the home page to sample a brand before Studio  
- **Library** — documents you save stay in **your browser only** (IndexedDB), not on a Docgen server by default  
- Open a Library item or a sample template into Studio via links/query params  

---

## Privacy (what to expect)

- Document text is **not** stored permanently by default  
- Temporary job files expire (TTL)  
- Optional PII redaction before cloud LLM calls  
- You can run fully offline with the rules structurer / local Ollama (see README)  
- Don’t put API keys in the frontend; only the API URL is public  

---

## Common first-time questions

**Why do cover and corner logos look different?**  
They’re meant to. Cover is the large center mark; corner is the small header mark. Upload two files, or enable “Use cover for both.”

**Why did my wide table look wrong before?**  
Very wide tables need careful column widths. Docgen sizes columns from content so dates and prices aren’t clipped. Prefer markdown tables or CSV.

**Does Format change my sentences?**  
No. Format only structures and styles. Improve may rewrite — and only keeps changes you accept.

**What does the format picker change?**  
Defaults for cover, front matter, TOC, numbering, and fonts. Your logos and colors stay independent. You can override layout options; “customized” settings can be reset to the preset.

**Can I use this without an LLM?**  
Yes. Format-only with the rules engine works offline. Cloud LLMs are optional and mainly help Improve / richer structuring when configured.

---

## Quick mental model

```
Your logos  →  brand colors + cover/corner placement
Your notes  →  structure (headings, tables, steps, callouts)
Format      →  which document “recipe” (SOP, Report, …)
Mode        →  lock wording (Format) or suggest edits (Improve)
Live paper  →  preview of the real PDF
Run press   →  finalize and download DOCX + PDF
```

That’s the whole product from a user’s seat. For setup and architecture, see [README.md](../README.md) and [architecture.md](architecture.md).
