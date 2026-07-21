"""Command-line interface for pdf2ebook"""
import argparse
import sys
import time
from pathlib import Path

from . import __version__
from .utils import (
    check_dependencies,
    get_missing_dependencies,
    print_dependency_error,
    install_dependencies,
    validate_input_file,
    get_output_path,
    check_output_conflict,
    validate_output_extension,
    warn_if_output_exists,
    list_available_languages,
    list_output_formats,
    list_output_profiles,
)
from .compressor import convert_pdf_to_ebook


def print_banner(format: str):
    """Print the pdf2ebook banner with format-aware label."""
    print("==========================================")
    print(f"  pdf2ebook — PDF to {format.upper()} via OCR")
    print("==========================================")
    print()


def interactive_mode_select_format() -> str:
    """Interactive mode: select output format"""
    formats = list_output_formats()
    
    print("Select output format:")
    for i, fmt in enumerate(formats, 1):
        default = " (default)" if fmt == "epub" else ""
        print(f"  [{i}] {fmt.upper()}{default}")
    print()
    
    while True:
        try:
            choice = input("Format [1-4] (default 1 - epub): ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nInterrupted. Cleaning up...")
            sys.exit(1)
        
        if not choice:
            return "epub"
        
        if choice.isdigit() and 1 <= int(choice) <= len(formats):
            return formats[int(choice) - 1]
        elif choice.lower() in formats:
            return choice.lower()
        else:
            print("Invalid option. Press Enter for default, or choose 1-4.", file=sys.stderr)


def interactive_mode_select_languages() -> str:
    """Interactive mode: select OCR languages"""
    available = list_available_languages()
    
    # Common languages
    common = ["spa", "eng", "fra", "deu", "ita", "por"]
    available_common = [lang for lang in common if lang in available]
    
    print("Select OCR languages:")
    print("  Common languages (installed):")
    for i, lang in enumerate(available_common, 1):
        print(f"    [{i}] {lang}")
    print()
    print("  Or enter custom language codes (e.g., spa+eng)")
    print("  Use --list-langs to see all available languages")
    print()
    
    while True:
        try:
            choice = input("Languages (default spa+eng): ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nInterrupted. Cleaning up...")
            sys.exit(1)
        
        if not choice:
            return "spa+eng"
        
        if choice.isdigit():
            idx = int(choice)
            if 1 <= idx <= len(available_common):
                return available_common[idx - 1]
        
        # Validate language codes
        langs = choice.split('+')
        valid = all(lang in available for lang in langs)
        
        if valid:
            return choice
        else:
            invalid = [lang for lang in langs if lang not in available]
            print(f"Invalid language(s): {', '.join(invalid)}", file=sys.stderr)
            print("Use --list-langs to see available languages", file=sys.stderr)


def interactive_mode_select_profile() -> str:
    """Interactive mode: select output profile"""
    profiles = [
        ("generic_eink", "Generic e-ink (6\" readers)"),
        ("tablet", "Tablet"),
        ("color", "Color e-reader"),
    ]
    
    print("Select output profile:")
    for i, (profile, desc) in enumerate(profiles, 1):
        default = " (default)" if profile == "generic_eink" else ""
        print(f"  [{i}] {desc}{default}")
    print()
    
    while True:
        try:
            choice = input("Profile [1-3] (default 1 - generic_eink): ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nInterrupted. Cleaning up...")
            sys.exit(1)
        
        if not choice:
            return "generic_eink"
        
        if choice.isdigit() and 1 <= int(choice) <= len(profiles):
            return profiles[int(choice) - 1][0]
        else:
            print("Invalid option. Press Enter for default, or choose 1-3.", file=sys.stderr)


def create_parser() -> argparse.ArgumentParser:
    """Create argument parser"""
    parser = argparse.ArgumentParser(
        prog="pdf2ebook",
        description="Convert PDFs to e-books with OCR",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  pdf2ebook book.pdf                    Interactive mode
  pdf2ebook -f epub book.pdf            EPUB format
  pdf2ebook -f mobi book.pdf            MOBI format (Kindle)
  pdf2ebook -l "fra+eng" book.pdf       French + English OCR
  pdf2ebook -o output.epub book.pdf     Custom output path
  pdf2ebook --list-langs                List available OCR languages
  pdf2ebook --list-formats              List output formats

Output formats:
  epub    Universal e-book format (default)
  mobi    Amazon Kindle format
  azw3    Amazon Kindle format (newer)
  pdf     Searchable PDF

Environment:
  TMPDIR            Override temp directory (default: /tmp)
"""
    )
    
    parser.add_argument(
        "input",
        nargs="?",
        help="Input PDF file"
    )
    
    parser.add_argument(
        "-f", "--format",
        choices=["epub", "mobi", "azw3", "pdf", "txt", "docx", "fb2"],
        help="Output format (default: epub)"
    )
    
    parser.add_argument(
        "-l", "--languages",
        help="OCR languages (e.g., spa+eng, fra+eng)"
    )
    
    parser.add_argument(
        "-p", "--profile",
        help="Output profile (e.g., generic_eink, tablet)"
    )
    
    parser.add_argument(
        "-o", "--output",
        type=Path,
        help="Output file path"
    )
    
    parser.add_argument(
        "-y", "--yes",
        action="store_true",
        help="Non-interactive: use defaults when no flags are given"
    )
    
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force OCR on all pages (rasterize text, matches bash behavior)"
    )
    
    parser.add_argument(
        "--skip-text",
        action="store_true",
        help="Skip OCR on pages with existing text (faster for mixed PDFs)"
    )
    
    parser.add_argument(
        "--no-clean",
        action="store_true",
        help="Disable image cleaning (unpaper, faster)"
    )
    
    parser.add_argument(
        "--no-deskew",
        action="store_true",
        help="Disable deskewing (faster, less accurate on skewed scans)"
    )
    
    parser.add_argument(
        "--list-langs",
        action="store_true",
        help="List available OCR languages"
    )
    
    parser.add_argument(
        "--list-formats",
        action="store_true",
        help="List output formats"
    )
    
    parser.add_argument(
        "--list-profiles",
        action="store_true",
        help="List output profiles"
    )
    
    parser.add_argument(
        "--install",
        action="store_true",
        help="Try to auto-install missing deps (Debian/Ubuntu)"
    )

    parser.add_argument(
        "-q", "--quiet",
        action="store_true",
        help="Suppress non-essential output"
    )

    parser.add_argument(
        "-V", "--version",
        action="version",
        version=f"%(prog)s {__version__}"
    )
    
    return parser


def main():
    """Main entry point"""
    parser = create_parser()
    args = parser.parse_args()

    try:
        _run(args, parser)
    except KeyboardInterrupt:
        print("\nInterrupted. Cleaning up...", file=sys.stderr)
        sys.exit(130)


def _run(args, parser):
    """Core logic, separated for KeyboardInterrupt handling."""
    # Handle --install
    if args.install:
        if not install_dependencies():
            sys.exit(1)
        return

    # Handle --list-langs
    if args.list_langs:
        langs = list_available_languages()
        print("Available OCR languages:")
        for lang in langs:
            print(f"  {lang}")
        return

    # Handle --list-formats
    if args.list_formats:
        formats = list_output_formats()
        print("Output formats:")
        for fmt in formats:
            print(f"  {fmt}")
        return

    # Handle --list-profiles
    if args.list_profiles:
        profiles = list_output_profiles()
        print("Output profiles:")
        for profile in profiles:
            print(f"  {profile}")
        return

    # Validate input
    if not args.input:
        parser.print_help()
        sys.exit(1)

    input_path = Path(args.input).resolve()

    # Validate input file
    error = validate_input_file(input_path)
    if error:
        print(f"ERROR: {error}", file=sys.stderr)
        sys.exit(1)

    # Determine format
    if args.format:
        format = args.format
    elif args.yes or not sys.stdin.isatty():
        format = "epub"
    else:
        format = interactive_mode_select_format()

    # Determine languages
    if args.languages:
        languages = args.languages
    elif args.yes or not sys.stdin.isatty():
        languages = "spa+eng"
    else:
        languages = interactive_mode_select_languages()

    # Determine profile
    if args.profile:
        profile = args.profile
    elif args.yes or not sys.stdin.isatty():
        profile = "generic_eink"
    else:
        profile = interactive_mode_select_profile()

    # Check dependencies
    deps = check_dependencies()
    missing = get_missing_dependencies(deps)

    if missing:
        print_dependency_error(missing)
        sys.exit(1)

    # Get output path
    output_path = get_output_path(input_path, args.output, format)

    # Validate output extension
    ext_error = validate_output_extension(output_path, format)
    if ext_error:
        print(f"ERROR: {ext_error}", file=sys.stderr)
        sys.exit(1)

    # Check for conflicts
    if check_output_conflict(input_path, output_path):
        print("ERROR: Output path is same as input path", file=sys.stderr)
        print("Use -o to specify a different output path", file=sys.stderr)
        sys.exit(1)

    # Warn if output exists
    warn_if_output_exists(output_path)

    # Print banner
    print_banner(format)
    print(f"Input file:  {input_path.name}")
    print(f"Output file: {output_path.name}")
    print(f"Format:      {format}")
    print(f"OCR langs:   {languages}")
    print(f"Profile:     {profile}")
    print()

    # Check dependencies
    if not args.quiet:
        print("Checking dependencies...")
        for dep, available in deps.items():
            status = "[OK]" if available else "[MISSING]"
            print(f"{status} {dep} found")
        print()
        print("All dependencies verified! Ready to convert.")
        print()

    # Convert
    start_time = time.time()

    result = convert_pdf_to_ebook(
        input_path, output_path, format, languages, profile,
        force_ocr=args.force,
        skip_text=args.skip_text,
        clean=not args.no_clean,
        deskew=not args.no_deskew
    )

    elapsed = time.time() - start_time

    if not result["success"]:
        print(f"\nERROR: {result['error']}", file=sys.stderr)
        sys.exit(1)

    print()
    print("==========================================")
    print("SUCCESS!")
    print("==========================================")
    print(f"Output saved as: {output_path}")
    print(f"Format:      {result['format']}")
    print(f"File size:   {result['output_size_human']}")
    print(f"Compression: {result['ratio']}")
    print(f"Time:        {elapsed:.1f}s")
    print()
    print("Your converted e-book is ready for reading!")
    print("Pro tip: Transfer to your device using Calibre Connect or drag/drop.")
    print("==========================================")


if __name__ == "__main__":
    main()
