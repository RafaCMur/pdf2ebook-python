# pdf2ebook

Convert PDFs to e-books with OCR on Linux, macOS, and Windows.

Transform scanned PDFs into readable e-books (EPUB, MOBI, AZW3, PDF) with searchable text. Perfect for books, papers, and documents.

## Features

- **OCR support**: 100+ languages via Tesseract
- **Multiple output formats**: EPUB, MOBI, AZW3, PDF, TXT, DOCX, FB2
- **Up to 99.9% compression**: 64MB PDF → 85KB EPUB
- **Interactive mode**: Choose format, languages, and output profile
- **Non-interactive mode**: Use `--yes` for scripts and automation
- **Smart defaults**: Auto-detect languages, sensible profiles
- **Cross-platform**: Linux, macOS, Windows (with external tools)
- **Zero Python dependencies**: Uses system tools (Tesseract, Calibre)
- **Robust**: Subprocess timeouts (600s OCR, 120s conversion) prevent hangs
- **Safe**: Output-exists warnings, clean Ctrl+C handling
- **Windows-ready**: Auto-detects ocrmypdf.exe, ebook-convert.exe, pdftotext.exe

## What's new in 0.3.0

- Subprocess timeouts: 600s for OCR (heavy books), 120s for pdftotext/ebook-convert
- KeyboardInterrupt handler with clean exit (130)
- Output-exists warning before overwrite
- ebook-convert args match bash: `--chapter-mark pagebreak`, `--mobi-ignore-margins`, `--page-breaks-before //h:h1`
- Added formats: txt, docx, fb2 (verified with ebook-convert)
- Output extension validation (rejects mismatched `-o file.X`)
- Dynamic banner: `pdf2ebook — PDF to {FORMAT^^} via OCR`
- `--quiet`/`-q` flag suppresses dependency list
- Windows binary resolution via `resolve_command()`
- Tiered OCR strategy preserved (exit code 6 retry with `--skip-text`)

## Installation

### Install via pip

```bash
pip install pdf2ebook
```

### Install from source

```bash
git clone https://github.com/yourusername/pdf2ebook.git
cd pdf2ebook
pip install .
```

### Install external dependencies

**Linux (Ubuntu/Debian):**
```bash
sudo apt install tesseract-ocr tesseract-ocr-spa tesseract-ocr-eng \
                 poppler-utils imagemagick calibre
```

**Linux (Arch):**
```bash
sudo pacman -S tesseract tesseract-data-eng tesseract-data-spa \
               poppler imagemagick calibre
```

**macOS:**
```bash
brew install tesseract tesseract-lang poppler imagemagick calibre
```

**Windows:**
- Install Tesseract from https://github.com/UB-Mannheim/tesseract/wiki
- Install poppler from https://github.com/oschwartz10612/poppler-windows/releases
- Install Calibre from https://calibre-ebook.com/download
- Or use WSL (recommended): `wsl --install`

## Usage

### Interactive mode

```bash
pdf2ebook book.pdf
```

You'll be prompted to choose:

1. **Output format**: EPUB (default), MOBI, AZW3, PDF, TXT, DOCX, FB2
2. **OCR languages**: Common languages (spa, eng, fra, deu, ita, por)
3. **Output profile**: Generic e-ink (default), Tablet, Color

### Non-interactive mode

```bash
# Default (EPUB, spa+eng, generic_eink)
pdf2ebook --yes book.pdf

# Specific format
pdf2ebook -f mobi book.pdf
pdf2ebook -f pdf book.pdf

# Custom languages
pdf2ebook -l "fra+eng" book.pdf

# Custom output
pdf2ebook -o output.epub book.pdf
```

### List available options

```bash
# List installed OCR languages
pdf2ebook --list-langs

# List output formats
pdf2ebook --list-formats

# List output profiles
pdf2ebook --list-profiles
```

## Output formats

### EPUB (default)

- Universal e-book format
- Works with most e-readers and apps
- Reflowable text
- **Compression: 99.9%** (64MB → 85KB)

### MOBI

- Amazon Kindle format
- Use for older Kindle devices
- **Compression: 99%+**

### AZW3

- Amazon Kindle format (newer)
- Better formatting support
- **Compression: 99%+**

### PDF

- Preserves layout
- Searchable text (via OCR)
- Larger file size
- **Compression: 70-90%**

### TXT

- Plain text output
- No formatting preserved
- Smallest file size
- **Compression: 99%+**

### DOCX

- Microsoft Word format
- Editable document
- Basic formatting
- **Compression: 99%+**

### FB2

- FictionBook XML format
- Popular in Eastern Europe
- Structured markup
- **Compression: 99%+**

## Real-world test results

### Large scanned book (64MB PDF)

| Metric | Value |
|--------|-------|
| **Input** | 64MB PDF (scanned book) |
| **Output** | 85.5KB EPUB |
| **Compression** | 99.9% |
| **Time** | 1m 55s |
| **OCR languages** | Spanish + English |
| **Text extracted** | 138,912 characters |
| **Pages processed** | 12 concurrent |

**Result**: Full book converted to readable e-book with searchable text, 99.9% smaller.

## How it works

1. **OCR** (OCRmyPDF): Adds searchable text layer to scanned PDF (600s timeout, tiered strategy with `--skip-text` fallback)
2. **Text extraction** (pdftotext): Extracts text from OCR'd PDF (120s timeout)
3. **Conversion** (Calibre): Converts text to e-book format with metadata (120s timeout)

All subprocess calls have timeouts to prevent hangs. Clean Ctrl+C handling ensures temp files are removed.

## OCR languages

### Common languages (interactive menu)

- `spa` - Spanish
- `eng` - English
- `fra` - French
- `deu` - German
- `ita` - Italian
- `por` - Portuguese

### All available languages

```bash
pdf2ebook --list-langs
```

Install additional languages:

```bash
# Ubuntu/Debian
sudo apt install tesseract-ocr-fra  # French
sudo apt install tesseract-ocr-deu  # German

# Or install all languages
sudo apt install tesseract-ocr-all
```

## Output profiles

Calibre output profiles optimize for different devices:

- `generic_eink` (default): 6" e-ink readers (Kindle, Kobo)
- `tablet`: Tablets and color screens
- `color`: Color e-readers
- `large_screen`: Large displays

## Environment variables

- `TMPDIR`: Override temp directory (default: `/tmp`)

## Requirements

- **Python 3.8+**
- **Tesseract** (`tesseract`): OCR engine
- **OCRmyPDF** (`ocrmypdf` or `ocrmypdf.exe` on Windows): PDF OCR processing
- **poppler-utils** (`pdftotext`, `pdftoppm`): Text extraction
- **ImageMagick** (`convert`): Image processing
- **Calibre** (`ebook-convert` or `ebook-convert.exe` on Windows): E-book conversion

## Troubleshooting

### "Command not found" errors

Install missing dependencies:

```bash
# Ubuntu/Debian
sudo apt install tesseract-ocr tesseract-ocr-spa tesseract-ocr-eng \
                 poppler-utils imagemagick calibre

# Or use --install flag
pdf2ebook --install
```

### OCR quality is poor

- Ensure PDF has good image quality (not too blurry)
- Try different languages: `pdf2ebook -l "spa+eng" book.pdf`
- Check Tesseract warnings in output

### Output file same as input

The script prevents overwriting input files. Use a different output path:

```bash
pdf2ebook -o output.epub input.pdf
```

### Non-PDF input gives error

pdf2ebook only accepts PDF files. For other formats:

```bash
# Convert DOCX to PDF first
libreoffice --headless --convert-to pdf document.docx

# Then convert to e-book
pdf2ebook document.pdf
```

### Conversion is slow

Large files take time (1-2 minutes for 64MB PDF). This is normal for OCR processing.

## Tips

### Transfer to e-reader

**Kindle**:
1. Convert to MOBI or AZW3
2. Use Calibre Connect or USB transfer
3. Or email to your Kindle address

**Kobo**:
1. Convert to EPUB
2. Use USB transfer or Calibre Connect

**Generic e-reader**:
1. Convert to EPUB
2. Use USB transfer

### Batch conversion

```bash
# Convert all PDFs in directory
for pdf in *.pdf; do
    pdf2ebook --yes "$pdf"
done
```

### Custom metadata

Edit the generated e-book with Calibre:

```bash
calibre ebook-edit output.epub
```

## License

MIT © 2026
