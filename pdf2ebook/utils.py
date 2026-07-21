"""Utility functions for pdf2ebook"""
import os
import sys
import shutil
import subprocess
from pathlib import Path
from typing import Optional, List


def check_command(cmd: str) -> bool:
    """Check if a command is available in PATH"""
    return shutil.which(cmd) is not None


def check_dependencies() -> dict:
    """Check required dependencies"""
    return {
        "pdftoppm": check_command("pdftoppm"),
        "pdftotext": check_command("pdftotext"),
        "ocrmypdf": check_command("ocrmypdf"),
        "ebook-convert": check_command("ebook-convert"),
    }


def get_missing_dependencies(deps: dict) -> list:
    """Get list of missing dependencies"""
    return [cmd for cmd, available in deps.items() if not available]


def print_dependency_error(missing: list):
    """Print error message for missing dependencies"""
    print("ERROR: Missing required dependencies:", file=sys.stderr)
    for cmd in missing:
        print(f"  - {cmd}", file=sys.stderr)
    print("\nInstall with:", file=sys.stderr)
    print("  Ubuntu/Debian: sudo apt install tesseract-ocr tesseract-ocr-spa tesseract-ocr-eng poppler-utils imagemagick calibre", file=sys.stderr)
    print("  macOS: brew install tesseract tesseract-lang poppler imagemagick calibre", file=sys.stderr)
    print("  Or use --install flag to auto-install (Debian/Ubuntu only)", file=sys.stderr)


def install_dependencies():
    """Try to install missing dependencies (Debian/Ubuntu only)"""
    if not check_command("apt"):
        print("ERROR: Auto-install only works on Debian/Ubuntu systems", file=sys.stderr)
        print("Please install manually:", file=sys.stderr)
        print("  sudo apt install tesseract-ocr tesseract-ocr-spa tesseract-ocr-eng poppler-utils imagemagick calibre", file=sys.stderr)
        return False
    
    packages = [
        "tesseract-ocr",
        "tesseract-ocr-spa",
        "tesseract-ocr-eng",
        "poppler-utils",
        "imagemagick",
        "calibre"
    ]
    
    print(f"Installing: {' '.join(packages)}")
    result = subprocess.run(
        ["sudo", "apt", "install", "-y"] + packages,
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        print("[OK] Dependencies installed successfully")
        return True
    else:
        print("ERROR: Installation failed", file=sys.stderr)
        print(result.stderr, file=sys.stderr)
        return False


def validate_input_file(input_path: Path) -> Optional[str]:
    """Validate input file exists and is a PDF"""
    if not input_path.exists():
        return f"File '{input_path}' not found"
    
    if not input_path.is_file():
        return f"'{input_path}' is not a file"
    
    ext = input_path.suffix.lower()
    if ext != ".pdf":
        return f"Unsupported file type: {ext} (only .pdf supported)"
    
    return None


def get_output_path(input_path: Path, output_path: Optional[Path] = None, 
                   format: str = "epub") -> Path:
    """Get output path, defaulting to <input>.<format>"""
    if output_path:
        return output_path
    
    stem = input_path.stem
    parent = input_path.parent
    return parent / f"{stem}.{format}"


def check_output_conflict(input_path: Path, output_path: Path) -> bool:
    """Check if output path would overwrite input"""
    try:
        input_resolved = input_path.resolve()
        output_resolved = output_path.resolve()
        return input_resolved == output_resolved
    except Exception:
        return False


def create_temp_file(suffix: str = "", prefix: str = "pdf2ebook_") -> Path:
    """Create a temporary file and return its path"""
    import tempfile
    fd, path = tempfile.mkstemp(suffix=suffix, prefix=prefix)
    os.close(fd)
    return Path(path)


def create_temp_dir(prefix: str = "pdf2ebook_") -> Path:
    """Create a temporary directory and return its path"""
    import tempfile
    return Path(tempfile.mkdtemp(prefix=prefix))


def cleanup_temp_files(temp_files: list):
    """Clean up temporary files"""
    for temp_file in temp_files:
        try:
            if isinstance(temp_file, Path):
                temp_file = str(temp_file)
            if os.path.exists(temp_file):
                if os.path.isdir(temp_file):
                    shutil.rmtree(temp_file)
                else:
                    os.remove(temp_file)
        except Exception as e:
            print(f"Warning: Could not remove temp file {temp_file}: {e}", file=sys.stderr)


def get_file_size(path: Path) -> str:
    """Get human-readable file size"""
    size = path.stat().st_size
    
    for unit in ['B', 'K', 'M', 'G']:
        if size < 1024.0:
            return f"{size:.0f}{unit}"
        size /= 1024.0
    
    return f"{size:.1f}T"


def calculate_compression_ratio(input_size: int, output_size: int) -> str:
    """Calculate compression ratio as percentage"""
    if input_size == 0:
        return "0%"
    
    ratio = (1 - output_size / input_size) * 100
    return f"{ratio:.1f}%"


def list_available_languages() -> List[str]:
    """List available OCR languages"""
    try:
        result = subprocess.run(
            ["tesseract", "--list-langs"],
            capture_output=True,
            text=True
        )
        
        # Parse output
        lines = result.stdout.strip().split('\n')
        langs = []
        for line in lines[1:]:  # Skip header
            line = line.strip()
            if line and not line.startswith(' '):
                langs.append(line)
        
        return sorted(langs)
    
    except Exception:
        return []


def list_output_formats() -> List[str]:
    """List supported output formats"""
    return ["epub", "mobi", "azw3", "pdf"]


def list_output_profiles() -> List[str]:
    """List Calibre output profiles"""
    return [
        "generic_eink",
        "generic_eink_hd",
        "generic_eink_large",
        "tablet",
        "color",
        "large_screen",
        "android",
        "ipad",
        "ipad3",
        "kindle",
        "kindle_dx",
        "kindle_fire",
        "kindle_pw",
        "kindle_voyage",
        "kobo_aura",
        "kobo_aura_hd",
        "kobo_glo",
        "nook_simple",
        "sony_prstouch",
    ]
