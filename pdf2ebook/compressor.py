"""PDF to e-book conversion logic for pdf2ebook"""
import os
import subprocess
import sys
from pathlib import Path
from typing import Optional, Tuple

from .utils import (
    create_temp_file,
    create_temp_dir,
    get_file_size,
    calculate_compression_ratio,
    resolve_command,
)

OCR_TIMEOUT = 600
CONVERT_TIMEOUT = 120
STDERR_CAP = 4096


def _run_subprocess(cmd, timeout):
    """Run subprocess with timeout. Returns (success, stderr_text)."""
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return result.returncode == 0, result.stderr
    except subprocess.TimeoutExpired:
        return False, f"Command timed out after {timeout}s: {' '.join(str(c) for c in cmd)}"
    except Exception as e:
        return False, str(e)


def run_ocr(input_path: Path, output_path: Path, languages: str = "spa+eng",
            force_ocr: bool = False, skip_text: bool = False,
            clean: bool = True, deskew: bool = True) -> Tuple[bool, str]:
    """Run OCR on PDF to add searchable text layer

    Tiered strategy:
    - Default: deskew + clean (best for scanned books)
    - If exit code 6 (PriorOcrFoundError): retry with --skip-text
    - --force: rasterize everything (matches bash, handles garbage text)
    - --skip-text: preserve text, OCR image-only pages (fast for mixed PDFs)
    """
    ocrmypdf = resolve_command("ocrmypdf")
    if not ocrmypdf:
        return False, "ocrmypdf not found"

    cmd = [
        ocrmypdf,
        "--language", languages,
        "--output-type", "pdf",
        "--jobs", "4",
    ]

    if deskew:
        cmd.append("--deskew")

    if clean:
        cmd.append("--clean")

    if force_ocr:
        cmd.append("--force-ocr")
    elif skip_text:
        cmd.append("--skip-text")

    cmd.extend([str(input_path), str(output_path)])

    ok, err = _run_subprocess(cmd, OCR_TIMEOUT)

    if ok:
        return True, ""

    if err and "PriorOcrFoundError" in err and not force_ocr and not skip_text:
        print("  [INFO] PDF has existing text, retrying with --skip-text...")
        cmd_retry = [
            ocrmypdf,
            "--language", languages,
            "--output-type", "pdf",
            "--jobs", "4",
            "--skip-text",
        ]
        if deskew:
            cmd_retry.append("--deskew")
        if clean:
            cmd_retry.append("--clean")
        cmd_retry.extend([str(input_path), str(output_path)])
        ok, err = _run_subprocess(cmd_retry, OCR_TIMEOUT)
        return ok, err

    return False, err


def extract_text_from_pdf(input_path: Path, output_path: Path) -> Tuple[bool, str]:
    """Extract text from OCR'd PDF using pdftotext"""
    cmd = [
        "pdftotext",
        "-layout",
        str(input_path),
        str(output_path)
    ]
    return _run_subprocess(cmd, CONVERT_TIMEOUT)


def convert_to_ebook(text_path: Path, output_path: Path, format: str = "epub",
                     profile: str = "generic_eink", title: Optional[str] = None) -> Tuple[bool, str]:
    """Convert text file to e-book using Calibre"""
    cmd = [
        "ebook-convert",
        str(text_path),
        str(output_path),
        "--output-profile", profile,
        "--enable-heuristics",
        "--linearize-tables",
        "--chapter-mark", "pagebreak",
        "--page-breaks-before", "//h:h1",
    ]

    if title:
        cmd.extend(["--title", title])

    if format == "mobi":
        cmd.append("--mobi-ignore-margins")

    return _run_subprocess(cmd, CONVERT_TIMEOUT)


def convert_pdf_to_ebook(input_path: Path, output_path: Path,
                         format: str = "epub",
                         languages: str = "spa+eng",
                         profile: str = "generic_eink",
                         force_ocr: bool = False,
                         skip_text: bool = False,
                         clean: bool = True,
                         deskew: bool = True) -> dict:
    """Main conversion function: PDF -> OCR -> Text -> E-book"""
    temp_ocr_pdf = create_temp_file(suffix=".pdf")
    temp_text = create_temp_file(suffix=".txt")

    try:
        print("Step 1: Running OCR to add searchable text layer...")
        print("This may take several minutes depending on file size...")

        ok, err = run_ocr(input_path, temp_ocr_pdf, languages, force_ocr, skip_text, clean, deskew)
        if not ok:
            return {"success": False, "error": f"OCR failed: {err}"}

        print("[OK] OCR completed successfully!")

        print("Step 2: Extracting text layer from OCR'd PDF...")

        ok, err = extract_text_from_pdf(temp_ocr_pdf, temp_text)
        if not ok:
            return {"success": False, "error": f"Text extraction failed: {err}"}

        text_size = temp_text.stat().st_size
        if text_size < 100:
            return {"success": False, "error": f"Extracted text is too small (< 100 bytes). OCR likely failed for language '{languages}'."}

        print(f"[OK] Extracted {text_size} characters of text.")

        print(f"Step 3: Converting extracted text to {format.upper()}...")

        title = input_path.stem.replace('_', ' ').replace('-', ' ').title()

        ok, err = convert_to_ebook(temp_text, output_path, format, profile, title)
        if not ok:
            return {"success": False, "error": f"E-book conversion failed: {err}"}

        print(f"[OK] Conversion completed successfully!")

        input_size = input_path.stat().st_size
        output_size = output_path.stat().st_size
        ratio = calculate_compression_ratio(input_size, output_size)

        return {
            "success": True,
            "format": format,
            "languages": languages,
            "profile": profile,
            "input_size": input_size,
            "output_size": output_size,
            "ratio": ratio,
            "input_size_human": get_file_size(input_path),
            "output_size_human": get_file_size(output_path),
            "char_count": text_size,
        }

    finally:
        if temp_ocr_pdf.exists():
            temp_ocr_pdf.unlink()
        if temp_text.exists():
            temp_text.unlink()
