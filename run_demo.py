#!/usr/bin/env python3
"""
LabGenius End-to-End Demonstration Script.
Executes sample Data Science lab manual, captures Pop!_OS terminal screenshots,
builds completed report, sanitizes metadata, and generates PDF.
"""

import sys
import subprocess
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
PYTHON = BASE_DIR / ".venv" / "bin" / "python"
if not PYTHON.exists():
    PYTHON = Path(sys.executable)

SAMPLE_MANUAL = BASE_DIR / "examples" / "sample_lab_manual.docx"


def main():
    print("\n" + "=" * 65)
    print("   LabGenius - Automated Academic Lab Completer & Styler")
    print("=" * 65)

    # 1. Ensure sample manual exists
    if not SAMPLE_MANUAL.exists():
        print("[+] Generating sample university lab manual...")
        from examples.generate_sample_manual import create_sample_manual
        create_sample_manual(SAMPLE_MANUAL)

    # 2. Run CLI
    print(f"[+] Executing LabGenius pipeline on: {SAMPLE_MANUAL.name}")
    cmd = [
        str(PYTHON), "-m", "labgenius.cli",
        "--manual", str(SAMPLE_MANUAL),
    ]
    res = subprocess.run(cmd, cwd=str(BASE_DIR))
    if res.returncode != 0:
        print("[-] Error occurred during pipeline execution.")
        sys.exit(res.returncode)

    # 3. Generate PDF via LibreOffice
    output_docx = BASE_DIR / "output" / "Completed_Lab_03_25F-DS-020.docx"
    if output_docx.exists():
        print("\n[+] Converting completed .docx report to PDF with LibreOffice...")
        subprocess.run(
            ["libreoffice", "--headless", "--convert-to", "pdf", str(output_docx), "--outdir", str(BASE_DIR / "output")],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        pdf_path = BASE_DIR / "output" / "Completed_Lab_03_25F-DS-020.pdf"
        if pdf_path.exists():
            print(f"[✓] PDF successfully generated: {pdf_path}")

    print("\n" + "=" * 65)
    print("   Demonstration Completed Successfully!")
    print(f"   • Completed Word Doc: {output_docx}")
    print("   • Start Web Dashboard: ./run_web.sh")
    print("   • Run on your own manual: python3 -m labgenius.cli --manual <your_manual.docx>")
    print("=" * 65 + "\n")


if __name__ == "__main__":
    main()
