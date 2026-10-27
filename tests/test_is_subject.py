"""
Unit and Integration Tests for Information Security (IS) Subject in LabGenius.
Tests parsing of IS manuals, solver logic, code execution, visual artifact synthesis,
document building, corpus integration, and web API endpoints.
"""

import os
import shutil
import tempfile
import zipfile
import unittest
from pathlib import Path
from PIL import Image
from fastapi.testclient import TestClient

from labgenius.parser import ManualParser, LabTask
from labgenius.solver import TaskSolver, TaskSolution, validate_code_syntax
from labgenius.is_solver import InformationSecuritySolver
from labgenius.runner import CodeRunner, ExecutionResult
from labgenius.capture import ScreenshotStudio
from labgenius.security_visuals import SecurityVisualStudio
from labgenius.builder import DocumentBuilder
from labgenius.corpus import ReferenceCorpus
from labgenius.config import Config
from web_app import app

REPO_ROOT = Path(__file__).resolve().parent.parent
IS_UPLOADS = REPO_ROOT / "uploads" / "IS"


class TestISManualParsing(unittest.TestCase):
    """Verifies that all IS lab manuals and Wireshark PDF are parsed correctly."""

    def test_01_parse_lab01(self):
        f = IS_UPLOADS / "Information Security Lab 01 (Introduction to Information Security).docx"
        if not f.exists():
            self.skipTest("Lab 01 file not present")
        parser = ManualParser(str(f))
        manual = parser.parse()
        self.assertEqual(manual.course_name, "Information Security (IS)")
        self.assertEqual(manual.lab_number, "01")
        self.assertEqual(len(manual.tasks), 3)
        self.assertEqual(manual.tasks[0].language, "python")

    def test_02_parse_lab02(self):
        f = IS_UPLOADS / "Information Security Lab 02 (Implementation of Data Integrity) (1).docx"
        if not f.exists():
            self.skipTest("Lab 02 file not present")
        parser = ManualParser(str(f))
        manual = parser.parse()
        self.assertEqual(manual.course_name, "Information Security (IS)")
        self.assertEqual(manual.lab_number, "02")
        self.assertEqual(len(manual.tasks), 3)

    def test_03_parse_lab03(self):
        f = IS_UPLOADS / "Information Security Lab 03 (Implementation of Caesar Cipher for Text Encryption and Decryption with a Fixed Shift of 3).docx"
        if not f.exists():
            self.skipTest("Lab 03 file not present")
        parser = ManualParser(str(f))
        manual = parser.parse()
        self.assertEqual(manual.course_name, "Information Security (IS)")
        self.assertEqual(manual.lab_number, "03")
        self.assertEqual(len(manual.tasks), 2)

    def test_04_parse_lab04(self):
        f = IS_UPLOADS / "Information Security Lab 04 (Symmetric Encryption) (1).docx"
        if not f.exists():
            self.skipTest("Lab 04 file not present")
        parser = ManualParser(str(f))
        manual = parser.parse()
        self.assertEqual(manual.course_name, "Information Security (IS)")
        self.assertEqual(manual.lab_number, "04")
        self.assertEqual(len(manual.tasks), 3)
        self.assertEqual(manual.tasks[0].language, "cpp")
        self.assertEqual(manual.tasks[1].language, "python")
        self.assertEqual(manual.tasks[2].language, "python")

    def test_05_parse_lab06(self):
        f = IS_UPLOADS / "Information Security Lab 06 (Anomaly Detection).docx"
        if not f.exists():
            self.skipTest("Lab 06 file not present")
        parser = ManualParser(str(f))
        manual = parser.parse()
        self.assertEqual(manual.course_name, "Information Security (IS)")
        self.assertEqual(manual.lab_number, "06")
        self.assertEqual(len(manual.tasks), 1)

    def test_06_parse_wireshark_pdf(self):
        f = IS_UPLOADS / "Wireshark_HTTP_v9.0.pdf"
        if not f.exists():
            self.skipTest("Wireshark PDF file not present")
        parser = ManualParser(str(f))
        manual = parser.parse()
        self.assertEqual(manual.course_name, "Information Security (IS)")
        self.assertEqual(len(manual.tasks), 5)
        # Verify 5 sections
        titles = [t.title.lower() for t in manual.tasks]
        self.assertTrue(any("basic" in t for t in titles))
        self.assertTrue(any("conditional" in t for t in titles))
        self.assertTrue(any("long" in t for t in titles))
        self.assertTrue(any("embedded" in t for t in titles))
        self.assertTrue(any("auth" in t for t in titles))


class TestISSolverAndSyntax(unittest.TestCase):
    """Verifies solver output and code syntax validation for IS tasks."""

    def setUp(self):
        self.cfg = Config.load()
        self.solver = TaskSolver(self.cfg)

    def test_security_task_detection(self):
        task1 = LabTask(task_id=1, title="Caesar cipher implementation", description="shift text by 3")
        self.assertTrue(InformationSecuritySolver.is_security_task(task1))

        task2 = LabTask(task_id=2, title="Data Integrity check", description="verify checksum")
        self.assertTrue(InformationSecuritySolver.is_security_task(task2))

        task3 = LabTask(task_id=3, title="Wireshark packet sniffing", description="inspect http traffic")
        self.assertTrue(InformationSecuritySolver.is_security_task(task3))

        task4 = LabTask(task_id=4, title="Binary Search Tree", description="insert and delete nodes")
        self.assertFalse(InformationSecuritySolver.is_security_task(task4, "Data Structures and Algorithms"))

    def test_solve_lab01_tasks(self):
        manual_path = IS_UPLOADS / "Information Security Lab 01 (Introduction to Information Security).docx"
        if not manual_path.exists():
            self.skipTest("Manual not found")
        parser = ManualParser(str(manual_path))
        manual = parser.parse()
        for task in manual.tasks:
            sol = self.solver.solve_task(task, lab_context=f"{manual.course_name} {manual.title}")
            self.assertIsNotNone(sol)
            self.assertTrue(len(sol.code) > 50)
            self.assertTrue(len(sol.explanation) > 30)
            valid, msg = validate_code_syntax(sol.code, sol.language)
            self.assertTrue(valid, f"Syntax error in Task {task.task_id}: {msg}")

    def test_solve_lab03_caesar(self):
        manual_path = IS_UPLOADS / "Information Security Lab 03 (Implementation of Caesar Cipher for Text Encryption and Decryption with a Fixed Shift of 3).docx"
        if not manual_path.exists():
            self.skipTest("Manual not found")
        parser = ManualParser(str(manual_path))
        manual = parser.parse()
        for task in manual.tasks:
            sol = self.solver.solve_task(task, lab_context=f"{manual.course_name} {manual.title}")
            self.assertIn("shift", sol.code.lower())
            valid, msg = validate_code_syntax(sol.code, sol.language)
            self.assertTrue(valid, msg)

    def test_solve_wireshark_questions(self):
        manual_path = IS_UPLOADS / "Wireshark_HTTP_v9.0.pdf"
        if not manual_path.exists():
            self.skipTest("Manual not found")
        parser = ManualParser(str(manual_path))
        manual = parser.parse()
        sol1 = self.solver.solve_task(manual.tasks[0], lab_context=f"{manual.course_name} {manual.title}")
        self.assertIn("Questions 1 through 7", sol1.explanation)
        self.assertIn("192.168.1.105", sol1.code)

    def test_distinct_solutions_across_tasks(self):
        # Lab 01 tasks 1, 2, 3 must have distinct solutions
        manual_path = IS_UPLOADS / "Information Security Lab 01 (Introduction to Information Security).docx"
        if not manual_path.exists():
            self.skipTest("Manual not found")
        parser = ManualParser(str(manual_path))
        manual = parser.parse()
        sols = [self.solver.solve_task(t, lab_context=f"{manual.course_name} {manual.title}") for t in manual.tasks]
        self.assertEqual(len(sols), 3)
        self.assertNotEqual(sols[0].code, sols[1].code)
        self.assertNotEqual(sols[1].code, sols[2].code)
        self.assertNotEqual(sols[0].code, sols[2].code)
        # Lab 04 tasks 1, 2, 3 must have distinct solutions and distinct languages (cpp, python, python)
        manual_path4 = IS_UPLOADS / "Information Security Lab 04 (Symmetric Encryption) (1).docx"
        if not manual_path4.exists():
            self.skipTest("Manual not found")
        parser4 = ManualParser(str(manual_path4))
        manual4 = parser4.parse()
        sols4 = [self.solver.solve_task(t, lab_context=f"{manual4.course_name} {manual4.title}") for t in manual4.tasks]
        self.assertEqual(len(sols4), 3)
        self.assertEqual(sols4[0].language, "cpp")
        self.assertEqual(sols4[1].language, "python")
        self.assertEqual(sols4[2].language, "python")
        self.assertIn("AES_set_encrypt_key", sols4[0].code)
        self.assertIn("MODE_CBC", sols4[1].code)
        self.assertIn("MODE_CFB", sols4[2].code)


class TestISCodeExecution(unittest.TestCase):
    """Verifies that generated code for IS tasks executes cleanly with exit code 0."""

    def setUp(self):
        self.cfg = Config.load()
        self.tmpdir = tempfile.mkdtemp()
        self.cfg.system.workspace_dir = self.tmpdir
        self.solver = TaskSolver(self.cfg)
        self.runner = CodeRunner(self.cfg)

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_execute_checksum(self):
        task = LabTask(task_id=1, title="Calculate Checksum and Verify Integrity", description="compute sum mod 256 and detect alterations")
        sol = self.solver.solve_task(task, lab_context="Information Security (IS) Lab 02 Data Integrity")
        res = self.runner.execute(sol)
        self.assertTrue(res.success, f"Execution failed: {res.stderr}")
        self.assertEqual(res.exit_code, 0)
        self.assertIn("checksum", res.stdout.lower())

    def test_execute_caesar(self):
        task = LabTask(task_id=1, title="Caesar Cipher with fixed shift of 3", description="encrypt and decrypt text")
        sol = self.solver.solve_task(task, lab_context="Information Security (IS) Lab 03 Caesar Cipher")
        res = self.runner.execute(sol)
        self.assertTrue(res.success, f"Execution failed: {res.stderr}")
        self.assertEqual(res.exit_code, 0)
        self.assertIn("ciphertext", res.stdout.lower())

    def test_execute_aes(self):
        task = LabTask(task_id=1, title="AES Symmetric Encryption CBC Mode", description="encrypt with AES CBC")
        sol = self.solver.solve_task(task, lab_context="Information Security (IS) Lab 04 Symmetric Encryption")
        res = self.runner.execute(sol)
        self.assertTrue(res.success, f"Execution failed: {res.stderr}")
        self.assertEqual(res.exit_code, 0)
        self.assertIn("aes", res.stdout.lower())

    def test_execute_anomaly_cpp(self):
        task = LabTask(task_id=1, title="Malware Anomaly Detection using Z-Score", description="compute mean, std, z-score in c++", language="cpp")
        sol = self.solver.solve_task(task, lab_context="Information Security (IS) Lab 06 Anomaly Detection")
        res = self.runner.execute(sol)
        self.assertTrue(res.success, f"Execution failed: {res.stderr}")
        self.assertEqual(res.exit_code, 0)
        self.assertIn("anomaly", res.stdout.lower())


class TestISVisualGenerators(unittest.TestCase):
    """Verifies that all visual artifact generators synthesize valid, high-resolution PNG images."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.tmppath = Path(self.tmpdir)

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_wireshark_scenarios(self):
        for scenario in ["http_basic", "http_conditional", "http_long_doc", "http_embedded", "http_auth"]:
            dest = self.tmppath / f"ws_{scenario}.png"
            out = SecurityVisualStudio.generate_wireshark_screenshot(dest, scenario=scenario)
            self.assertTrue(out.exists())
            with Image.open(out) as img:
                self.assertGreaterEqual(img.width, 800)
                self.assertGreaterEqual(img.height, 400)

    def test_checksum_flow_diagram(self):
        dest = self.tmppath / "checksum.png"
        out = SecurityVisualStudio.generate_checksum_flow_diagram(dest)
        self.assertTrue(out.exists())
        with Image.open(out) as img:
            self.assertGreaterEqual(img.width, 700)

    def test_caesar_wheel_diagram(self):
        dest = self.tmppath / "caesar.png"
        out = SecurityVisualStudio.generate_caesar_cipher_diagram(dest, shift=3)
        self.assertTrue(out.exists())
        with Image.open(out) as img:
            self.assertGreaterEqual(img.width, 700)

    def test_aes_architecture_diagram(self):
        dest = self.tmppath / "aes.png"
        out = SecurityVisualStudio.generate_aes_architecture_diagram(dest)
        self.assertTrue(out.exists())
        with Image.open(out) as img:
            self.assertGreaterEqual(img.width, 700)

    def test_anomaly_detection_plot(self):
        dest = self.tmppath / "anomaly.png"
        out = SecurityVisualStudio.generate_anomaly_detection_plot(dest)
        self.assertTrue(out.exists())
        with Image.open(out) as img:
            self.assertGreaterEqual(img.width, 700)

    def test_http_sequence_diagram(self):
        dest = self.tmppath / "sequence.png"
        out = SecurityVisualStudio.generate_http_sequence_diagram(dest)
        self.assertTrue(out.exists())
        with Image.open(out) as img:
            self.assertGreaterEqual(img.width, 700)


class TestISDocumentBuilder(unittest.TestCase):
    """Verifies that generated Word, Markdown, and HTML reports properly embed IS visual artifacts."""

    def setUp(self):
        self.cfg = Config.load()
        self.tmpdir = tempfile.mkdtemp()
        self.tmppath = Path(self.tmpdir)
        self.cfg.system.workspace_dir = self.tmpdir
        self.solver = TaskSolver(self.cfg)
        self.runner = CodeRunner(self.cfg)
        self.studio = ScreenshotStudio(self.cfg)
        self.builder = DocumentBuilder(self.cfg)

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_build_docx_with_visual_artifacts(self):
        manual_path = IS_UPLOADS / "Information Security Lab 02 (Implementation of Data Integrity) (1).docx"
        if not manual_path.exists():
            self.skipTest("Manual not found")
        parser = ManualParser(str(manual_path))
        manual = parser.parse()
        sols, res_list, shots = [], [], []
        for task in manual.tasks:
            sol = self.solver.solve_task(task, lab_context=f"{manual.course_name} {manual.title}")
            res = self.runner.execute(sol)
            c_img, o_img, d_img = self.studio.capture_task_artifacts(sol, res)
            sols.append(sol)
            res_list.append(res)
            shots.append((c_img, o_img, d_img))

        docx_out = self.tmppath / "report.docx"
        self.builder.build_report(manual, sols, res_list, shots, docx_out)
        self.assertTrue(docx_out.exists())
        self.assertGreater(docx_out.stat().st_size, 50000)

        # Inspect docx archive for embedded media
        with zipfile.ZipFile(docx_out) as z:
            media = [n for n in z.namelist() if n.startswith("word/media/")]
            self.assertGreaterEqual(len(media), 3, "Expected embedded code, output, and diagram images")

    def test_build_md_and_html_with_visual_artifacts(self):
        manual_path = IS_UPLOADS / "Information Security Lab 03 (Implementation of Caesar Cipher for Text Encryption and Decryption with a Fixed Shift of 3).docx"
        if not manual_path.exists():
            self.skipTest("Manual not found")
        parser = ManualParser(str(manual_path))
        manual = parser.parse()
        sols, res_list, shots = [], [], []
        for task in manual.tasks:
            sol = self.solver.solve_task(task, lab_context=f"{manual.course_name} {manual.title}")
            res = self.runner.execute(sol)
            c_img, o_img, d_img = self.studio.capture_task_artifacts(sol, res)
            sols.append(sol)
            res_list.append(res)
            shots.append((c_img, o_img, d_img))

        md_out = self.tmppath / "report.md"
        self.builder.build_markdown_report(manual, sols, res_list, shots, md_out)
        self.assertTrue(md_out.exists())
        md_text = md_out.read_text(encoding="utf-8")
        self.assertIn("![Visual Artifact]", md_text)

        html_out = self.tmppath / "report.html"
        self.builder.build_html_report(manual, sols, res_list, shots, html_out)
        self.assertTrue(html_out.exists())
        html_text = html_out.read_text(encoding="utf-8")
        self.assertIn("VISUAL DEMONSTRATION / PROTOCOL DISSECTION:", html_text)


class TestISCorpusIntegration(unittest.TestCase):
    """Verifies that reference corpus contains verified IS tasks and retrieves them properly."""

    def test_corpus_contains_is_entries(self):
        rc = ReferenceCorpus()
        is_entries = [e for e in rc.entries if e.subject == "is"]
        self.assertGreaterEqual(len(is_entries), 6)
        topics_and_keywords = [(e.topic + " " + " ".join(e.keywords)).lower() for e in is_entries]
        self.assertTrue(any("symmetric" in tk for tk in topics_and_keywords))
        self.assertTrue(any("caesar" in tk for tk in topics_and_keywords))
        self.assertTrue(any("aes" in tk for tk in topics_and_keywords))
        self.assertTrue(any("anomaly" in tk for tk in topics_and_keywords))
        self.assertTrue(any("wireshark" in tk or "http" in tk for tk in topics_and_keywords))

    def test_corpus_retrieval_for_is_query(self):
        rc = ReferenceCorpus()
        matches = rc.find_relevant_references("is", "Caesar Cipher Encryption", "shift letters by 3")
        self.assertGreater(len(matches), 0)
        self.assertEqual(matches[0].subject, "is")


class TestISWebAppApi(unittest.TestCase):
    """Verifies web endpoints with Information Security manuals."""

    def setUp(self):
        self.client = TestClient(app)

    def test_api_generate_lab_is_auto_detect(self):
        manual_path = IS_UPLOADS / "Information Security Lab 01 (Introduction to Information Security).docx"
        if not manual_path.exists():
            self.skipTest("Manual not found")

        self.client.post("/api/close-lab")
        with open(manual_path, "rb") as f:
            res = self.client.post(
                "/api/generate-lab",
                data={
                    "name": "Bheesham Kumar Sajnani",
                    "roll_number": "25F-DS-020",
                    "subject": "auto",
                    "formats": "docx,md,html",
                    "provider": "offline",
                },
                files={"manual_file": (manual_path.name, f, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")}
            )

        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data.get("success"), data.get("error"))
        self.assertEqual(data.get("course_name"), "Information Security (IS)")
        self.assertEqual(len(data.get("tasks", [])), 3)
        self.assertTrue(data.get("docx_url"))

    def test_api_generate_lab_is_explicit_subject(self):
        manual_path = IS_UPLOADS / "Information Security Lab 03 (Implementation of Caesar Cipher for Text Encryption and Decryption with a Fixed Shift of 3).docx"
        if not manual_path.exists():
            self.skipTest("Manual not found")

        self.client.post("/api/close-lab")
        with open(manual_path, "rb") as f:
            res = self.client.post(
                "/api/generate-lab",
                data={
                    "name": "Bheesham Kumar Sajnani",
                    "roll_number": "25F-DS-020",
                    "subject": "is",
                    "formats": "docx",
                    "provider": "offline",
                },
                files={"manual_file": (manual_path.name, f, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")}
            )

        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data.get("success"), data.get("error"))
        self.assertEqual(data.get("course_name"), "Information Security (IS)")
        self.assertEqual(len(data.get("tasks", [])), 2)


if __name__ == "__main__":
    unittest.main()
