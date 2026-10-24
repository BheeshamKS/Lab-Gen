"""
Comprehensive Automated Tests for Human Writer Service.
Verifies document structure analysis, cover page protection, AI scoring,
code reference scrubbing, profile-driven humanization, metadata sanitization, and API endpoints.
"""

import os
import tempfile
import unittest
from pathlib import Path
import docx
from fastapi.testclient import TestClient
from pypdf import PdfReader

from labgenius.human_writer import (
    AIDetector,
    CoverPageDetector,
    HumanizationEngine,
    MetadataSanitizer,
    HumanWriterService,
    DocumentSegment,
)
from web_app import app


class TestHumanWriterService(unittest.TestCase):

    def setUp(self):
        self.client = TestClient(app)
        self.temp_dir = tempfile.TemporaryDirectory()
        self.test_dir = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_01_cover_page_detection_and_preservation(self):
        """Verifies that academic cover pages / title blocks are detected and strictly preserved."""
        cover_text = "DEPARTMENT OF COMPUTER SCIENCE\nStudent Name: Hamza Tariq | Roll Number: 22-CS-114\nCourse: Distributed Systems Lab Report"
        is_cov = CoverPageDetector.is_cover_segment(cover_text, segment_index=0, total_segments=10)
        self.assertTrue(is_cov, "Initial segment with academic metadata should be recognized as cover page")

        body_text = "Furthermore, this algorithm delves into the intricate tapestry of thread priority queues."
        is_not_cov = CoverPageDetector.is_cover_segment(body_text, segment_index=5, total_segments=10)
        self.assertFalse(is_not_cov, "Body text should not be classified as cover page")

        # Test preservation during humanization
        segments = [
            {"id": 1, "type": "cover", "text": cover_text, "is_cover_page": True, "ai_score": 0.02, "is_ai": False},
            {"id": 2, "type": "paragraph", "text": body_text, "is_cover_page": False, "ai_score": 0.85, "is_ai": True},
        ]
        res = HumanWriterService.humanize_document(segments, profile="academic_student")
        self.assertTrue(res["success"])
        # Cover page must be 100% identical
        self.assertEqual(res["humanized_segments"][0]["humanized_text"], cover_text)
        # Body text must be rewritten
        self.assertNotEqual(res["humanized_segments"][1]["humanized_text"], body_text)
        self.assertNotIn("delve", res["humanized_segments"][1]["humanized_text"].lower())

    def test_02_ai_detection_scoring(self):
        """Verifies that AI buzzwords and low burstiness result in high AI probability."""
        blatant_ai = (
            "Furthermore, it is important to note that this architecture delves into the intricate tapestry "
            "of mutual exclusion. Consequently, it serves as a testament to the seamless orchestration of daemons."
        )
        score, reasons, code_refs = AIDetector.evaluate_text(blatant_ai)
        self.assertGreaterEqual(score, 0.50, f"Expected high AI score for blatant text, got {score}")
        self.assertTrue(any("delve" in r.lower() for r in reasons))

        human_text = "We ran the test 5 times. The second run took 12ms, which was faster than the first."
        h_score, h_reasons, _ = AIDetector.evaluate_text(human_text)
        self.assertLess(h_score, 0.35, f"Expected low AI score for human text, got {h_score}")

    def test_03_code_reference_scrubbing(self):
        """Verifies that raw code variable names and prompt leakages are scrubbed from prose."""
        text_with_leaks = (
            "In our test, variable task_1_sol_thread_count_v2 facilitates synchronization. "
            "Also dataframe df_execution_latency_v2 demonstrates the latency."
        )
        leaks = AIDetector.detect_code_references(text_with_leaks)
        self.assertIn("task_1_sol_thread_count_v2", leaks)
        self.assertIn("df_execution_latency_v2", leaks)

        cleaned = HumanizationEngine.strip_code_references_in_prose(text_with_leaks)
        self.assertNotIn("task_1_sol_thread_count_v2", cleaned)
        self.assertNotIn("df_execution_latency_v2", cleaned)

    def test_04_profile_and_custom_prompt_humanization(self):
        """Verifies different humanization profiles execute correctly."""
        text = "Furthermore, it is crucial to understand that utilizing this method facilitates seamless performance."
        
        # Test concise profile
        concise_out = HumanizationEngine.humanize_segment_offline(text, profile="concise")
        self.assertNotIn("furthermore", concise_out.lower())
        self.assertNotIn("crucial to understand", concise_out.lower())

        # Test de_roboticizer
        derobot_out = HumanizationEngine.humanize_segment_offline(text, profile="de_roboticizer")
        self.assertNotIn("utilizing", derobot_out.lower())
        self.assertNotIn("seamless", derobot_out.lower())

    def test_05_metadata_sanitization_docx_and_pdf(self):
        """Verifies that generated documents have sanitized human metadata."""
        sample_segments = [
            {"id": 1, "type": "cover", "text": "Lab 01: Concurrency Report\nStudent: Hamza Tariq", "is_cover_page": True},
            {"id": 2, "type": "paragraph", "text": "We tested thread creation and mutex locks.", "is_cover_page": False},
        ]
        out_docx = self.test_dir / "sanitized_test.docx"
        HumanWriterService.build_exported_document(
            segments=sample_segments,
            output_format="docx",
            output_path=out_docx,
            author_name="Hamza Tariq",
            document_title="Concurrency Report",
        )
        self.assertTrue(out_docx.exists())

        # Inspect Word metadata
        doc = docx.Document(str(out_docx))
        props = doc.core_properties
        self.assertEqual(props.author, "Hamza Tariq")
        self.assertEqual(props.last_modified_by, "Hamza Tariq")
        self.assertEqual(props.title, "Concurrency Report")
        self.assertEqual(props.revision, 3)

        # Inspect PDF metadata
        out_pdf = self.test_dir / "sanitized_test.pdf"
        HumanWriterService.build_exported_document(
            segments=sample_segments,
            output_format="pdf",
            output_path=out_pdf,
            author_name="Hamza Tariq",
            document_title="Concurrency Report",
        )
        self.assertTrue(out_pdf.exists())
        reader = PdfReader(str(out_pdf))
        meta = reader.metadata
        self.assertEqual(meta.author, "Hamza Tariq")
        self.assertIn("Microsoft", str(meta.creator))

    def test_06_human_writer_api_endpoints(self):
        """Verifies the complete FastAPI endpoint workflow for Human Writer."""
        # 1. Sample endpoint
        resp_sample = self.client.get("/api/human-writer/sample")
        self.assertEqual(resp_sample.status_code, 200)
        sample_path = resp_sample.json()["path"]
        self.assertTrue(Path(sample_path).exists())

        # 2. Analyze endpoint
        resp_an = self.client.post("/api/human-writer/analyze", data={"filepath": sample_path})
        self.assertEqual(resp_an.status_code, 200)
        an_data = resp_an.json()["analysis"]
        self.assertTrue(an_data["cover_page_detected"])
        self.assertGreater(an_data["overall_ai_score"], 30.0)
        self.assertGreater(len(an_data["segments"]), 3)

        # 3. Humanize endpoint
        resp_hum = self.client.post("/api/human-writer/humanize", json={
            "segments": an_data["segments"],
            "profile": "de_roboticizer",
            "custom_instructions": "Make it sound like an engineering student",
        })
        self.assertEqual(resp_hum.status_code, 200)
        hum_data = resp_hum.json()
        self.assertTrue(hum_data["success"])
        self.assertGreater(hum_data["authenticity_score"], 80.0)

        # 4. Export endpoint
        resp_exp = self.client.post("/api/human-writer/export", json={
            "segments": hum_data["humanized_segments"],
            "format": "docx",
            "author_name": "Hamza Tariq",
            "title": "OS Lab Report",
        })
        self.assertEqual(resp_exp.status_code, 200)
        self.assertTrue(resp_exp.json()["success"])
        self.assertIn("download_url", resp_exp.json())

    def test_07_index_html_contains_human_writer_ui(self):
        """Verifies that web/index.html includes the rail button and Human Writer view elements."""
        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)
        html = res.text

        # Navigation rail button
        self.assertIn('id="rail-item-humanwriter"', html)
        self.assertIn('openNavHumanWriter()', html)

        # Main view workspace
        self.assertIn('id="view-humanwriter"', html)
        self.assertIn('id="hw-upload-card"', html)
        self.assertIn('id="hw-workspace"', html)
        self.assertIn('id="hw-guidance-prompt"', html)
        self.assertIn('id="hw-diff-workbench"', html)
        self.assertIn('id="btn-run-humanizer"', html)


if __name__ == "__main__":
    unittest.main()
