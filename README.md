# read4me

CLI tool that converts `.pdf`, `.epub`, and `.fb2` books into per-chapter MP3 audiobook files.

## Requirements

- Python 3.12+
- `uv`

## Non-Python Dependencies

Install these system tools (macOS/Homebrew):

```bash
brew install uv ocrmypdf tesseract tesseract-lang
```

Used for:
- `uv`: Python project/dependency runner.
- `ocrmypdf`: OCR fallback for scanned PDFs.
- `tesseract` + `tesseract-lang`: OCR engine and language data (`eng`, `rus`).

## Setup

```bash
uv sync
```

Create a local `.env` from the example:

```bash
cp .env.example .env
```

Set your OpenAI API key in `.env`:

```dotenv
READ4ME_OPENAI_API_KEY=your_key_here
READ4ME_LOG_LEVEL=INFO
```

## Commands

Show CLI help:

```bash
uv run read4me --help
```

Inspect detected chapters without generating audio:

```bash
uv run read4me inspect ./book.epub
```

List available TTS voices:

```bash
uv run read4me voices
```

Convert a book into per-chapter MP3 files:

```bash
uv run read4me convert ./book.epub --out ./out
```

Set metadata explicitly:

```bash
uv run read4me convert ./book.epub --out ./out \
  --title "Book Title" \
  --author "Author Name"
```

Rate-limit safer mode (one-by-one with larger gaps and retries):

```bash
uv run read4me convert ./book.epub --out ./out \
  --request-delay-seconds 2.5 \
  --max-retries-on-429 9 \
  --retry-delay-seconds 4.0
```

Set locale for non-English books (example: Russian):

```bash
uv run read4me convert ./book.fb2 --out ./out --locale ru-RU
```

Accent behavior:
- English locales (`en`, `en-*`): British accent.
- Other locales: natural native pronunciation (no forced British accent).

Cover artwork behavior:
- EPUB/FB2: embedded cover is extracted and embedded into MP3 tags.
- PDF: first page is rendered and embedded as cover artwork.
- If no embedded cover is found: a square fallback cover is generated from `title` + `author`.

Enable OCR fallback mode flag for PDFs:

```bash
uv run read4me convert ./book.pdf --out ./out --ocr-fallback
```

For scanned/image-only PDFs, install OCR tools first:
- `ocrmypdf`
- `tesseract` (with Russian language data if needed)

Example (Russian scanned PDF):

```bash
uv run read4me convert ./book.pdf --out ./out --locale ru-RU --ocr-fallback
```

## Troubleshooting

If conversion fails with:
- `DependencyError: cryptography>=3.1 is required for AES algorithm`

Run:

```bash
uv sync
```

This installs Python dependencies required by `pypdf` for encrypted/object-stream PDFs.

If conversion fails with:
- `ValueError: No extractable PDF text found`

The PDF is likely scanned/image-only. Retry with OCR:

```bash
uv run read4me convert ./book.pdf --out ./out --ocr-fallback
```

## Testing

```bash
uv run pytest -q
```
