"""
End-to-End Workflow and State Isolation Integration Tests for LabGenius.
Tests the complete multi-lab pipeline across consecutive uploads.
"""

import unittest
from pathlib import Path
from fastapi.testclient import TestClient
from web_app import app, WORKSPACE_DIR

REPO_ROOT = Path(__file__).resolve().parent.parent


class TestWorkflowEndToEnd(unittest.TestCase):

    def setUp(self):
        self.client = TestClient(app)

    def test_01_health_and_index(self):
        """Verifies homepage serves correctly."""
        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)
        self.assertIn("LabGenius", res.text)
        self.assertIn("Auto-Detect", res.text)

    def test_02_full_pipeline_dbms_and_recompilation(self):
        """
        Tests uploading DBMS Lab 01, verifying tasks, making inline canvas edits,
        recompiling report, and checking exports.
        """
        # Ensure clean initial state
        self.client.post("/api/close-lab")

        manual_path = REPO_ROOT / "uploads" / "DBMS Lab 01.docx"
        with open(manual_path, "rb") as f:
            res = self.client.post(
                "/api/generate-lab",
                data={
                    "name": "Bheesham Kumar Sajnani",
                    "roll_number": "25F-DS-020",
                    "subject": "auto",
                    "formats": "docx,pdf",
                    "provider": "offline",
                },
                files={"manual_file": ("DBMS Lab 01.docx", f, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")}
            )

        data = res.json()
        self.assertTrue(data.get("success"), f"Pipeline generation failed: {data.get('error')}")
        self.assertEqual(data["course_name"], "Database Management Systems (DBMS)")
        self.assertEqual(len(data["tasks"]), 2)
        self.assertTrue(data.get("docx_url"))
        self.assertTrue(data.get("pdf_url"))

        # Check current lab endpoint
        curr = self.client.get("/api/current-lab").json()
        self.assertTrue(curr.get("success"))
        self.assertEqual(len(curr["tasks"]), 2)

        # Inline canvas edit and recompilation test
        save_res = self.client.post(
            "/api/save-document-canvas",
            json={
                "title": "UPDATED LAB 01 TITLE",
                "objectives": "Verified SQL Server connectivity and system properties.",
                "tasks": [
                    {"task_id": 1, "explanation": "Custom user inline explanation test for Task 1."},
                    {"task_id": 2, "explanation": "Custom user inline explanation test for Task 2."}
                ]
            }
        )
        save_data = save_res.json()
        self.assertTrue(save_data.get("success"))

    def test_03_consecutive_lab_state_isolation(self):
        """
        Verifies that uploading a DSA manual immediately after closing a DBMS lab
        does NOT leak any DBMS tasks, questions, or SQL tables into the DSA report.
        """
        # 1. Close active session
        close_res = self.client.post("/api/close-lab").json()
        self.assertTrue(close_res.get("success"))

        # Verify active session is wiped
        curr_after_close = self.client.get("/api/current-lab").json()
        self.assertFalse(curr_after_close.get("success"))

        # 2. Upload DSA Lab 02
        manual_path = REPO_ROOT / "uploads" / "Data Structure Laboratory Manual L2.docx"
        with open(manual_path, "rb") as f:
            res = self.client.post(
                "/api/generate-lab",
                data={
                    "name": "Bheesham Kumar Sajnani",
                    "roll_number": "25F-DS-020",
                    "subject": "auto",
                    "formats": "docx,pdf",
                    "provider": "offline",
                },
                files={"manual_file": ("Data Structure Laboratory Manual L2.docx", f, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")}
            )

        data = res.json()
        self.assertTrue(data.get("success"), f"Pipeline generation failed: {data.get('error')}")
        self.assertEqual(data["course_name"], "Data Structures and Algorithms")

        # Crucial State Isolation Checks:
        # DSA Lab 02 has 4 tasks (Singly Linked List)
        self.assertEqual(len(data["tasks"]), 4)
        for t in data["tasks"]:
            self.assertEqual(t["language"], "python")
            # Verify ZERO trace of SQL or DBMS tables
            self.assertNotIn("sql", t["code"].lower())
            self.assertNotIn("select", t["code"].lower())
            self.assertNotIn("student2", t["code"].lower())
            self.assertNotIn("employee", t["code"].lower())


if __name__ == "__main__":
    unittest.main()
