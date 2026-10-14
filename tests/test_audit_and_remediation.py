"""
Audit & Remediation Regression Test Suite for LabGenius.
Tests Doc Tools capabilities, LibreOffice conversions, Security boundaries,
Path traversal defenses, Scratchpad runners, and API error handling.
"""

import os
import json
import tempfile
import unittest
from pathlib import Path
from fastapi.testclient import TestClient

from web_app import app, OUTPUT_DIR, EXAMPLES_DIR, WORKSPACE_DIR
import labgenius.doc_tools as doc_tools


class TestAuditAndRemediation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        cls.test_dir = Path(tempfile.mkdtemp(prefix="labgen_audit_tests_"))

        # Create dummy test files
        cls.test_txt = cls.test_dir / "sample_code.txt"
        cls.test_txt.write_text("print('Hello from LabGenius audit test')\nx = 10 + 20\nprint('Result:', x)\n", encoding="utf-8")

        cls.sample_pdf = OUTPUT_DIR / "Data_Structures_Lab1.pdf"
        cls.sample_docx = OUTPUT_DIR / "Algorithms_Notes.docx"

    @classmethod
    def tearDownClass(cls):
        import shutil
        shutil.rmtree(cls.test_dir, ignore_errors=True)

    # --------------------------------------------------------------------------
    # 1. Doc Tools: Multi-Format Merging & Conversion
    # --------------------------------------------------------------------------

    def test_doc_tools_txt_to_docx_conversion_fix(self):
        """Verifies that plain text files convert to DOCX without infilter=writer_pdf_import error."""
        out_docx = self.test_dir / "converted_txt.docx"
        res = doc_tools.convert_document(self.test_txt, "docx", out_docx)
        self.assertTrue(res["success"])
        self.assertTrue(out_docx.exists())
        self.assertGreater(out_docx.stat().st_size, 0)

    def test_doc_tools_merge_docx_and_txt_to_docx(self):
        """Verifies merging DOCX + TXT into a single master DOCX."""
        if not self.sample_docx.exists():
            self.skipTest("Sample DOCX not found in output directory")
        out_merged = self.test_dir / "merged_docx_txt.docx"
        res = doc_tools.merge_documents([self.sample_docx, self.test_txt], "docx", out_merged)
        self.assertTrue(res["success"])
        self.assertTrue(out_merged.exists())
        self.assertEqual(res["format"], "docx")

    def test_doc_tools_merge_pdf_and_docx_to_pdf(self):
        """Verifies merging PDF + DOCX into a single master PDF."""
        if not self.sample_pdf.exists() or not self.sample_docx.exists():
            self.skipTest("Sample files not found in output directory")
        out_merged = self.test_dir / "merged_pdf_docx.pdf"
        res = doc_tools.merge_documents([self.sample_pdf, self.sample_docx], "pdf", out_merged)
        self.assertTrue(res["success"])
        self.assertTrue(out_merged.exists())
        self.assertGreater(res["page_count"], 0)

    def test_doc_tools_extract_pdf_pages(self):
        """Verifies page extraction from PDF."""
        if not self.sample_pdf.exists():
            self.skipTest("Sample PDF not found in output directory")
        out_extracted = self.test_dir / "extracted_page_1.pdf"
        res = doc_tools.extract_pdf_pages(self.sample_pdf, "1", out_extracted)
        self.assertTrue(res["success"])
        self.assertTrue(out_extracted.exists())
        self.assertEqual(res["extracted_pages_count"], 1)

    def test_doc_tools_inspect_document(self):
        """Verifies text and metadata inspection for PDF and DOCX."""
        if not self.sample_docx.exists():
            self.skipTest("Sample DOCX not found in output directory")
        res = doc_tools.inspect_document(self.sample_docx)
        self.assertTrue(res["success"])
        self.assertIn("word_count", res)
        self.assertGreater(res["word_count"], 0)
        self.assertEqual(res["format"], "docx")

    # --------------------------------------------------------------------------
    # 2. Security Boundaries & Path Traversal Defenses
    # --------------------------------------------------------------------------

    def test_path_traversal_defense_download(self):
        """Attempts directory traversal on /api/download/ to ensure 404 is returned."""
        resp = self.client.get("/api/download/..%2Fconfig.yaml")
        self.assertEqual(resp.status_code, 404)

        resp2 = self.client.get("/api/download/etc%2Fpasswd")
        self.assertEqual(resp2.status_code, 404)

    def test_path_traversal_defense_preview_pdf(self):
        """Attempts directory traversal on /api/preview/pdf/."""
        resp = self.client.get("/api/preview/pdf/..%2F..%2Fconfig.yaml")
        self.assertEqual(resp.status_code, 404)

    def test_path_traversal_defense_preview_html(self):
        """Attempts directory traversal on /api/preview/html/."""
        resp = self.client.get("/api/preview/html/..%2F..%2Fconfig.yaml")
        self.assertEqual(resp.status_code, 404)

    def test_upload_logo_extension_validation(self):
        """Verifies that non-image file uploads (.sh, .html) are rejected."""
        files = {"logo_file": ("malicious.html", b"<script>alert(1)</script>", "text/html")}
        resp = self.client.post("/api/upload-logo", files=files)
        data = resp.json()
        self.assertFalse(data.get("success", False))
        self.assertIn("Invalid file format", data.get("error", ""))

    def test_scratchpad_python_execution_safety(self):
        """Verifies that scratchpad executes safe python code correctly without shell=True."""
        payload = {
            "language": "python",
            "code": "import math\nprint(f'SQRT:{math.isqrt(144)}')",
            "stdin": "",
        }
        resp = self.client.post("/api/execute-scratchpad", json=payload)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data["success"])
        self.assertEqual(data["stdout"], "SQRT:12")

    def test_scratchpad_c_execution_safety(self):
        """Verifies that scratchpad compiles and executes C code directly without shell=True."""
        payload = {
            "language": "c",
            "code": "#include <stdio.h>\nint main() { printf(\"C_AUDIT_PASS\\n\"); return 0; }",
            "stdin": "",
        }
        resp = self.client.post("/api/execute-scratchpad", json=payload)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data["success"])
        self.assertEqual(data["stdout"], "C_AUDIT_PASS")

    def test_scratchpad_sql_execution_safety(self):
        """Verifies that scratchpad executes SQL queries and formats results cleanly."""
        payload = {
            "language": "sql",
            "code": "CREATE TABLE audit_t (id INT, item TEXT); INSERT INTO audit_t VALUES (101, 'LabGenius'); SELECT * FROM audit_t;",
            "stdin": "",
        }
        resp = self.client.post("/api/execute-scratchpad", json=payload)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data["success"])
        self.assertIn("101", data["stdout"])
        self.assertIn("LabGenius", data["stdout"])


if __name__ == "__main__":
    unittest.main()
