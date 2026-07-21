"""PDF to e-book conversion logic for pdf2ebook"""
import os
import subprocess
import sys
from pathlib import Path
from typing import Optional

from .utils import (
    create_temp_file,
    create_temp_dir,
    get_file_size,
    calculate_compression_ratio,
)


def run_ocr(input_path: Path, output_path: Path, languages: str = "spa+eng") -> bool:
    """Run OCR on PDF to add searchable text layer"""
    cmd = [
        "ocrmypdf",
        "--language", languages,
        "--output-type", "pdf",
        "--jobs", "4",
        "--skip-text",
        str(input_path),
        str(output_path)
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"OCR error: {result.stderr}", file=sys.stderr)
        return False
    
    return True


def extract_text_from_pdf(input_path: Path, output_path: Path) -> bool:
    """Extract text from OCR'd PDF using pdftotext"""
    cmd = [
        "pdftotext",
        "-layout",
        str(input_path),
        str(output_path)
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode == 0


def convert_to_ebook(text_path: Path, output_path: Path, format: str = "epub",
                    profile: str = "generic_eink", title: Optional[str] = None) -> bool:
    """Convert text file to e-book using Calibre"""
    cmd = [
        "ebook-convert",
        str(text_path),
        str(output_path),
        "--output-profile", profile,
        "--enable-heuristics",
        "--linearize-tables",
    ]
    
    if title:
        cmd.extend(["--title", title])
    
    # Format-specific options
    if format == "epub":
        cmd.extend(["--page-breaks-before", "//h:h1"])
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"Conversion error: {result.stderr}", file=sys.stderr)
        return False
    
    return True


def convert_pdf_to_ebook(input_path: Path, output_path: Path, 
                         format: str = "epub",
                         languages: str = "spa+eng",
                         profile: str = "generic_eink") -> dict:
    """Main conversion function: PDF → OCR → Text → E-book"""
    temp_ocr_pdf = create_temp_file(suffix=".pdf")
    temp_text = create_temp_file(suffix=".txt")
    
    try:
        # Step 1: OCR
        print("Step 1: Running OCR to add searchable text layer...")
        print("This may take several minutes depending on file size...")
        
        if not run_ocr(input_path, temp_ocr_pdf, languages):
            return {"success": False, "error": "OCR failed"}
        
        print("[OK] OCR completed successfully!")
        
        # Step 2: Extract text
        print("Step 2: Extracting text layer from OCR'd PDF...")
        
        if not extract_text_from_pdf(temp_ocr_pdf, temp_text):
            return {"success": False, "error": "Text extraction failed"}
        
        # Validate text is not empty
        text_size = temp_text.stat().st_size
        if text_size < 100:
            return {"success": False, "error": "Extracted text is too small (< 100 bytes)"}
        
        char_count = text_size
        print(f"[OK] Extracted {char_count} characters of text.")
        
        # Step 3: Convert to e-book
        print(f"Step 3: Converting extracted text to {format.upper()}...")
        
        title = input_path.stem.replace('_', ' ').replace('-', ' ').title()
        
        if not convert_to_ebook(temp_text, output_path, format, profile, title):
            return {"success": False, "error": "E-book conversion failed"}
        
        print(f"[OK] Conversion completed successfully!")
        
        # Get sizes
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
            "char_count": char_count,
        }
    
    finally:
        if temp_ocr_pdf.exists():
            temp_ocr_pdf.unlink()
        if temp_text.exists():
            temp_text.unlink()
