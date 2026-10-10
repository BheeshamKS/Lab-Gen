"""
Tests for 4-Step Wizard API and Lab 6 Benchmark in LabGenius.
Verifies /api/extract-manual, pre-generation task modification,
/api/generate-from-session, and end-to-end report generation for Lab 6.
"""

import unittest
from pathlib import Path
from fastapi.testclient import TestClient

from web_app import app, session_manager

REPO_ROOT = Path(__file__).resolve().parent.parent


class TestWizardAndLab6(unittest.TestCase):

    def setUp(self):
        self.client = TestClient(app)

    def test_01_extract_manual_and_generate_pipeline(self):
        """Verifies Step 1 (extract-manual) -> Step 2 (review/edit) -> Step 3 (generate-from-session)."""
        manual_path = REPO_ROOT / "uploads" / "Data Structure Laboratory Manual L6.docx"
        self.assertTrue(manual_path.exists(), f"Manual not found: {manual_path}")

        # Step 1: Extract manual
        with open(manual_path, "rb") as f:
            extract_res = self.client.post(
                "/api/extract-manual",
                data={
                    "name": "Bheesham Kumar Sajnani",
                    "roll_number": "25F-DS-020",
                    "section": "25F-DS",
                    "subject": "dsa",
                },
                files={"manual_file": (manual_path.name, f, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")}
            )

        self.assertEqual(extract_res.status_code, 200)
        ext_data = extract_res.json()
        self.assertTrue(ext_data.get("success"), f"Extraction failed: {ext_data.get('error')}")
        sid = ext_data["session_id"]
        self.assertIsNotNone(sid)

        # Assert extracted content
        self.assertEqual(len(ext_data["tasks"]), 1)
        self.assertEqual(len(ext_data["analysis_questions"]), 6)

        # Step 2: Modify a task in review stage
        tasks = ext_data["tasks"]
        tasks[0]["title"] = "Custom Binary Search Benchmark"
        tasks[0]["description"] = "Empirical comparative timing of iterative vs recursive binary search."

        # Step 3: Generate from modified session
        gen_res = self.client.post(
            "/api/generate-from-session",
            json={
                "session_id": sid,
                "provider": "offline",
                "formats": "docx,pdf",
                "tasks": tasks,
                "analysis_questions": [q["question"] for q in ext_data["analysis_questions"]],
            }
        )

        self.assertEqual(gen_res.status_code, 200)
        gen_data = gen_res.json()
        self.assertTrue(gen_data.get("success"), f"Generation failed: {gen_data.get('error')}")
        self.assertEqual(len(gen_data["tasks"]), 1)
        self.assertEqual(gen_data["tasks"][0]["title"], "Custom Binary Search Benchmark")
        self.assertEqual(len(gen_data["analysis_answers"]), 6)
        self.assertTrue(gen_data.get("docx_url"))
        self.assertTrue(gen_data.get("pdf_url"))

        # Verify quality validation gate passed cleanly
        val_rep = gen_data.get("validation_report")
        self.assertIsNotNone(val_rep)
        self.assertTrue(val_rep.get("is_valid"))
        self.assertEqual(len(val_rep.get("errors", [])), 0)


if __name__ == "__main__":
    unittest.main()
