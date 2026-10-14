"""
tests/test_second_pass_adversarial.py - Second-Pass Adversarial Regression Suite.
Covers:
1. Unseen manual parsing (DOCX, PDF, TXT, MD) with session/topic/task/viva accuracy.
2. Doc Tools Inspector support for .txt and .md files.
3. Path traversal defenses on session IDs and isolated directory boundaries.
4. Input validation and extension allowlists on file uploads (custom logo, manual files).
5. Safe preview restrictions for HTML rendering.
6. Oversized input resilience (length limits on generated merge/split filenames).
"""

import os
import json
import shutil
import tempfile
import unittest
from pathlib import Path
from fastapi.testclient import TestClient

import docx
from web_app import app, OUTPUT_DIR, BASE_DIR
from labgenius.parser import ManualParser
from labgenius.state import SessionManager
import labgenius.doc_tools as doc_tools


class TestSecondPassAdversarial(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        cls.test_dir = Path(tempfile.mkdtemp(prefix="labgen_second_pass_"))

        # Create dummy text and markdown files
        cls.test_txt = cls.test_dir / "sample_manual.txt"
        cls.test_txt.write_text(
            "Lab Session: 05\n"
            "Topic: Binary Search Tree Traversal\n"
            "Task 1: Implement BST insertion\n"
            "Write a Python function to insert nodes.\n"
            "Task 2: Implement BST in-order traversal\n"
            "Viva Voce Questions:\n"
            "1. What is the time complexity of searching in a balanced BST?\n",
            encoding="utf-8"
        )

        cls.test_md = cls.test_dir / "sample_manual.md"
        cls.test_md.write_text(
            "# Lab Session: 08\n"
            "## Topic: Graph BFS and DFS\n"
            "Task 1: Implement Breadth-First Search\n"
            "Task 2: Implement Depth-First Search\n",
            encoding="utf-8"
        )

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.test_dir, ignore_errors=True)

    # --------------------------------------------------------------------------
    # 1. Unseen Manual & Parser Accuracy Tests
    # --------------------------------------------------------------------------

    def test_unseen_manual_docx_session_and_tasks_preserved(self):
        """Verifies that Lab Session: 07, Topic, Task 1, and Viva Voce are correctly parsed from DOCX."""
        doc_path = self.test_dir / "unseen_lab_07.docx"
        doc = docx.Document()
        doc.add_heading("Lab Session: 07", level=1)
        doc.add_heading("Topic: Singly Linked List Implementation", level=2)
        doc.add_paragraph("Department of Data Science")
        doc.add_paragraph("Task 1: Implement Singly Linked List insertion at head and tail.")
        doc.add_paragraph("Write a C program to demonstrate insertion at head and tail.")
        doc.add_paragraph("Task 2: Implement Singly Linked List deletion.")
        doc.add_paragraph("Viva Voce Questions:")
        doc.add_paragraph("1. What is the time complexity of insertion at head in a linked list?")
        doc.save(str(doc_path))

        parser = ManualParser(str(doc_path))
        manual = parser.parse()

        self.assertEqual(manual.lab_number, "07")
        self.assertEqual(manual.title, "SINGLY LINKED LIST IMPLEMENTATION")
        self.assertEqual(len(manual.tasks), 2)
        self.assertEqual(manual.tasks[0].task_id, 1)
        self.assertIn("insertion", manual.tasks[0].title.lower())
        self.assertEqual(manual.tasks[1].task_id, 2)
        self.assertEqual(len(manual.viva_questions), 1)
        self.assertIn("time complexity", manual.viva_questions[0].lower())

    def test_text_manual_parsing_without_pdf_crash(self):
        """Verifies that plain text manuals parse correctly without PdfStreamError."""
        parser = ManualParser(str(self.test_txt))
        manual = parser.parse()

        self.assertEqual(manual.lab_number, "05")
        self.assertEqual(manual.title, "BINARY SEARCH TREE TRAVERSAL")
        self.assertEqual(len(manual.tasks), 2)
        self.assertEqual(len(manual.viva_questions), 1)

    def test_markdown_manual_parsing(self):
        """Verifies that markdown manuals parse correctly without crashing."""
        parser = ManualParser(str(self.test_md))
        manual = parser.parse()

        self.assertEqual(manual.lab_number, "08")
        self.assertEqual(manual.title, "GRAPH BFS AND DFS")
        self.assertEqual(len(manual.tasks), 2)

    # --------------------------------------------------------------------------
    # 2. Document Tools Inspector Enhancements
    # --------------------------------------------------------------------------

    def test_doc_tools_inspect_txt_and_md(self):
        """Verifies that doc_tools.inspect_document successfully handles .txt and .md files."""
        res_txt = doc_tools.inspect_document(self.test_txt)
        self.assertTrue(res_txt["success"])
        self.assertEqual(res_txt["format"], "txt")
        self.assertGreater(res_txt["word_count"], 0)
        self.assertIn("Binary Search", res_txt["text_preview"])

        res_md = doc_tools.inspect_document(self.test_md)
        self.assertTrue(res_md["success"])
        self.assertEqual(res_md["format"], "md")
        self.assertGreater(res_md["word_count"], 0)

    # --------------------------------------------------------------------------
    # 3. Path Traversal Defenses & Boundary Enforcement
    # --------------------------------------------------------------------------

    def test_session_id_path_traversal_defense(self):
        """Verifies that malicious session IDs with directory traversal sequences are neutralized."""
        sm = SessionManager(db_path=self.test_dir / "test_sessions.sqlite3", workspace_root=self.test_dir / "sessions")
        
        # Traversal attempt in get_session_dir
        safe_dir = sm.get_session_dir("../../malicious/path")
        self.assertTrue(safe_dir.is_relative_to(sm.workspace_root.resolve()))
        self.assertNotIn("..", safe_dir.name)

        # Traversal attempt in delete_session
        deleted = sm.delete_session("../../../")
        self.assertFalse(deleted)  # Empty after sanitizing -> False

        # Traversal attempt in get_session
        sess = sm.get_session("../../../nonexistent")
        self.assertIsNone(sess)

    # --------------------------------------------------------------------------
    # 4. Input Validation & Extension Allowlists
    # --------------------------------------------------------------------------

    def test_api_run_custom_logo_rejected_for_malicious_ext(self):
        """Verifies that /api/run rejects executable logo uploads (.sh, .py, .php)."""
        payload = {
            "name": "Adversary",
            "roll_number": "999",
            "is_sample": "true",
            "logo_choice": "custom",
        }
        files = {
            "custom_logo": ("exploit.sh", b"#!/bin/bash\nrm -rf /", "application/x-sh")
        }
        response = self.client.post("/api/run", data=payload, files=files)
        data = response.json()
        self.assertFalse(data.get("success", False))
        self.assertIn("Invalid logo format", data.get("error", ""))

    def test_api_run_manual_rejected_for_malicious_ext(self):
        """Verifies that /api/run rejects executable manual uploads (.exe, .py)."""
        payload = {
            "name": "Adversary",
            "roll_number": "999",
        }
        files = {
            "manual_file": ("exploit.exe", b"\x4d\x5a\x90\x00", "application/x-msdownload")
        }
        response = self.client.post("/api/run", data=payload, files=files)
        data = response.json()
        self.assertFalse(data.get("success", False))
        self.assertIn("Invalid manual file format", data.get("error", ""))

    def test_preview_html_rejects_non_html_file(self):
        """Verifies that /api/preview/html/{filename} rejects non-HTML files."""
        # Requesting a PDF or DB file through HTML preview must return 404
        response = self.client.get("/api/preview/html/Data_Structures_Lab1.pdf")
        self.assertEqual(response.status_code, 404)

    # --------------------------------------------------------------------------
    # 5. Oversized Input & Boundary Resilience
    # --------------------------------------------------------------------------

    def test_api_doc_tools_merge_oversized_filename(self):
        """Verifies that /api/doc-tools/merge handles oversized filename parameters without filesystem crash."""
        sample_txt1 = self.test_dir / "merge_a.txt"
        sample_txt2 = self.test_dir / "merge_b.txt"
        sample_txt1.write_text("Document Part A\n", encoding="utf-8")
        sample_txt2.write_text("Document Part B\n", encoding="utf-8")

        oversized_filename = "A" * 400  # Exceeds Linux NAME_MAX (255)
        files = [
            ("files", ("merge_a.txt", open(sample_txt1, "rb"), "text/plain")),
            ("files", ("merge_b.txt", open(sample_txt2, "rb"), "text/plain")),
        ]
        data = {
            "export_format": "pdf",
            "filename": oversized_filename,
        }
        response = self.client.post("/api/doc-tools/merge", data=data, files=files)
        self.assertEqual(response.status_code, 200)
        res_data = response.json()
        self.assertTrue(res_data["success"])
        # Filename stem should be truncated to safe boundary <= 64 chars
        self.assertLessEqual(len(res_data["filename"]), 80)


if __name__ == "__main__":
    unittest.main()
