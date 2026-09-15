"""
labgenius/doc_tools.py - Document Processing Engine for LabGenius Doc Tools.
Provides multi-format merging (PDF + DOCX in arbitrary sequences), format conversion,
PDF page extraction, and document text inspection.
"""

import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import List, Optional, Tuple, Dict, Any

from pypdf import PdfReader, PdfWriter
import docx
from docxcompose.composer import Composer


def _run_libreoffice_convert(input_path: Path, target_ext: str, out_dir: Path) -> Optional[Path]:
    """
    Converts a file to target_ext (e.g. 'pdf' or 'docx') using LibreOffice headless.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    target_ext_clean = target_ext.lstrip(".").lower()

    cmd = ["libreoffice", "--headless"]
    if target_ext_clean == "docx":
        cmd.extend(["--infilter=writer_pdf_import", "--convert-to", "docx"])
    else:
        cmd.extend(["--convert-to", target_ext_clean])

    cmd.extend([str(input_path), "--outdir", str(out_dir)])

    try:
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=60)
        expected_output = out_dir / f"{input_path.stem}.{target_ext_clean}"
        if expected_output.exists():
            return expected_output
        # Sometimes libreoffice replaces spaces or uses slightly different stem
        for f in out_dir.glob(f"*.{target_ext_clean}"):
            if f.is_file():
                return f
    except Exception as e:
        print(f"[-] LibreOffice conversion failed for {input_path.name}: {e}")
    return None


def merge_to_pdf(input_files: List[Path], output_path: Path, insert_page_break: bool = True) -> Dict[str, Any]:
    """
    Merges an ordered list of PDF and/or DOCX files into a single master PDF.
    DOCX files are automatically converted to PDF before stitching.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    pdf_writer = PdfWriter()
    temp_dir = Path(tempfile.mkdtemp(prefix="labgen_pdf_merge_"))

    try:
        for idx, file_path in enumerate(input_files):
            ext = file_path.suffix.lower()
            temp_pdf_to_read = None

            if ext == ".pdf":
                temp_pdf_to_read = file_path
            elif ext == ".docx":
                converted = _run_libreoffice_convert(file_path, "pdf", temp_dir / f"step_{idx}")
                if not converted or not converted.exists():
                    raise RuntimeError(f"Failed to convert Word document '{file_path.name}' to PDF for merging.")
                temp_pdf_to_read = converted
            else:
                raise ValueError(f"Unsupported file format '{ext}' for merging. Only .pdf and .docx are supported.")

            reader = PdfReader(str(temp_pdf_to_read))
            for page in reader.pages:
                pdf_writer.add_page(page)

        with open(output_path, "wb") as f_out:
            pdf_writer.write(f_out)

        total_pages = len(pdf_writer.pages)
        size_bytes = os.path.getsize(output_path)

        return {
            "success": True,
            "filename": output_path.name,
            "format": "pdf",
            "page_count": total_pages,
            "size_bytes": size_bytes,
            "size_formatted": _format_size(size_bytes),
        }
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def merge_to_docx(input_files: List[Path], output_path: Path, insert_page_break: bool = True) -> Dict[str, Any]:
    """
    Merges an ordered list of PDF and/or DOCX files into a single master DOCX.
    PDF files are automatically converted to DOCX before appending.
    """
    if not input_files:
        raise ValueError("No files provided for merging.")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    temp_dir = Path(tempfile.mkdtemp(prefix="labgen_docx_merge_"))

    try:
        # Step 1: Ensure all input files are converted to DOCX
        docx_paths: List[Path] = []
        for idx, file_path in enumerate(input_files):
            ext = file_path.suffix.lower()
            if ext == ".docx":
                # Copy to temp to avoid mutating original
                dest = temp_dir / f"doc_{idx}_{file_path.name}"
                shutil.copy2(file_path, dest)
                docx_paths.append(dest)
            elif ext == ".pdf":
                converted = _run_libreoffice_convert(file_path, "docx", temp_dir / f"pdf_step_{idx}")
                if not converted or not converted.exists():
                    raise RuntimeError(f"Failed to convert PDF document '{file_path.name}' to Word DOCX for merging.")
                docx_paths.append(converted)
            else:
                raise ValueError(f"Unsupported file format '{ext}' for merging. Only .pdf and .docx are supported.")

        # Step 2: Use docxcompose Composer to stitch all DOCX documents
        master_doc = docx.Document(str(docx_paths[0]))
        composer = Composer(master_doc)

        for next_docx in docx_paths[1:]:
            next_doc = docx.Document(str(next_docx))
            if insert_page_break:
                # Add page break before appending next doc
                master_doc.add_page_break()
            composer.append(next_doc)

        composer.save(str(output_path))
        size_bytes = os.path.getsize(output_path)
        final_doc = docx.Document(str(output_path))
        paragraph_count = len(final_doc.paragraphs)

        return {
            "success": True,
            "filename": output_path.name,
            "format": "docx",
            "paragraph_count": paragraph_count,
            "size_bytes": size_bytes,
            "size_formatted": _format_size(size_bytes),
        }
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def merge_documents(
    input_files: List[Path],
    output_format: str,
    output_path: Path,
    insert_page_break: bool = True,
) -> Dict[str, Any]:
    """
    Main entry point for merging arbitrary combinations of PDF and DOCX files.
    """
    target_format = output_format.strip().lower().lstrip(".")
    if target_format == "pdf":
        return merge_to_pdf(input_files, output_path, insert_page_break=insert_page_break)
    elif target_format == "docx":
        return merge_to_docx(input_files, output_path, insert_page_break=insert_page_break)
    else:
        raise ValueError(f"Invalid export format '{output_format}'. Supported formats are 'pdf' and 'docx'.")


def convert_document(input_file: Path, target_format: str, output_path: Path) -> Dict[str, Any]:
    """
    Converts a single document between PDF and DOCX.
    """
    target_clean = target_format.strip().lower().lstrip(".")
    temp_dir = Path(tempfile.mkdtemp(prefix="labgen_convert_"))

    try:
        converted = _run_libreoffice_convert(input_file, target_clean, temp_dir)
        if not converted or not converted.exists():
            raise RuntimeError(f"Failed to convert '{input_file.name}' to {target_clean.upper()}.")

        output_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(converted, output_path)

        size_bytes = os.path.getsize(output_path)
        return {
            "success": True,
            "filename": output_path.name,
            "format": target_clean,
            "size_bytes": size_bytes,
            "size_formatted": _format_size(size_bytes),
        }
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def extract_pdf_pages(input_pdf: Path, page_ranges_str: str, output_path: Path) -> Dict[str, Any]:
    """
    Extracts specified pages from a PDF (e.g. '1-3, 5, 8-10') and saves as a new PDF.
    1-indexed for user convenience.
    """
    reader = PdfReader(str(input_pdf))
    total_pages = len(reader.pages)
    selected_indices = _parse_page_ranges(page_ranges_str, total_pages)

    if not selected_indices:
        raise ValueError(f"No valid pages found in range '{page_ranges_str}'. Document has {total_pages} pages.")

    writer = PdfWriter()
    for idx in selected_indices:
        writer.add_page(reader.pages[idx])

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "wb") as f_out:
        writer.write(f_out)

    size_bytes = os.path.getsize(output_path)
    return {
        "success": True,
        "filename": output_path.name,
        "format": "pdf",
        "extracted_pages_count": len(selected_indices),
        "total_source_pages": total_pages,
        "size_bytes": size_bytes,
        "size_formatted": _format_size(size_bytes),
    }


def inspect_document(input_file: Path) -> Dict[str, Any]:
    """
    Inspects a PDF or DOCX and extracts clean text, word counts, and page/paragraph counts.
    """
    ext = input_file.suffix.lower()
    text_content = ""
    pages_count = 0
    paragraph_count = 0

    if ext == ".pdf":
        reader = PdfReader(str(input_file))
        pages_count = len(reader.pages)
        for page in reader.pages:
            t = page.extract_text()
            if t:
                text_content += t + "\n\n"
    elif ext == ".docx":
        doc = docx.Document(str(input_file))
        paragraph_count = len(doc.paragraphs)
        for p in doc.paragraphs:
            if p.text.strip():
                text_content += p.text + "\n"
        for table in doc.tables:
            for row in table.rows:
                row_text = " | ".join(cell.text.strip() for cell in row.cells if cell.text.strip())
                if row_text:
                    text_content += row_text + "\n"
    else:
        raise ValueError(f"Unsupported file format: {ext}")

    words = re.findall(r"\b\w+\b", text_content)
    word_count = len(words)
    char_count = len(text_content)
    size_bytes = os.path.getsize(input_file)

    # Preview first 1000 characters
    preview = text_content[:1200] + ("..." if len(text_content) > 1200 else "")

    return {
        "success": True,
        "filename": input_file.name,
        "format": ext.lstrip("."),
        "size_bytes": size_bytes,
        "size_formatted": _format_size(size_bytes),
        "word_count": word_count,
        "char_count": char_count,
        "page_count": pages_count,
        "paragraph_count": paragraph_count,
        "text_preview": preview,
    }


def _parse_page_ranges(range_str: str, max_pages: int) -> List[int]:
    """
    Parses strings like '1-3, 5, 7-9' into a sorted list of 0-based page indices.
    """
    indices = set()
    parts = [p.strip() for p in range_str.split(",") if p.strip()]
    for part in parts:
        if "-" in part:
            sub = part.split("-")
            if len(sub) == 2:
                try:
                    start = max(1, int(sub[0].strip()))
                    end = min(max_pages, int(sub[1].strip()))
                    if start <= end:
                        for i in range(start, end + 1):
                            indices.add(i - 1)
                except ValueError:
                    continue
        else:
            try:
                val = int(part)
                if 1 <= val <= max_pages:
                    indices.add(val - 1)
            except ValueError:
                continue
    return sorted(list(indices))


def _format_size(bytes_val: int) -> str:
    """Formats bytes into human readable KB or MB."""
    if bytes_val < 1024:
        return f"{bytes_val} B"
    elif bytes_val < 1024 * 1024:
        return f"{bytes_val / 1024:.1f} KB"
    else:
        return f"{bytes_val / (1024 * 1024):.2f} MB"
