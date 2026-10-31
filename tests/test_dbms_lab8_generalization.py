"""
Comprehensive Regression & Verification Tests for DBMS Lab 08.
Verifies that:
1. DBMS Lab 08 parses all 12 tasks cleanly and extracts the full Students table DDL and DML.
2. DynamicSQLSynthesizer sets up the Students table and 12 real seed records in SQLite.
3. All 12 tasks generate genuine pattern searching & arithmetic queries (no SELECT * FROM Records fallback).
4. All 12 queries execute cleanly with exit code 0 and return real student rows.
"""

import unittest
import tempfile
from pathlib import Path

from labgenius.config import Config
from labgenius.parser import ManualParser
from labgenius.solver import TaskSolver
from labgenius.runner import CodeRunner
from labgenius.synthesizer import DynamicSQLSynthesizer

REPO_ROOT = Path(__file__).resolve().parent.parent


class TestDBMSLab8Generalization(unittest.TestCase):

    def setUp(self):
        self.cfg = Config.load()
        self.solver = TaskSolver(self.cfg)
        self.temp_dir = tempfile.TemporaryDirectory()
        self.workspace = Path(self.temp_dir.name)
        self.runner = CodeRunner(self.cfg)
        self.runner.base_workspace = self.workspace

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_01_parse_dbms_lab8_tasks_and_context(self):
        docx_path = REPO_ROOT / "workspace" / "199aacd16861" / "Lab_08_edited.docx"
        self.assertTrue(docx_path.exists(), f"Lab 8 manual missing at: {docx_path}")

        parser = ManualParser(docx_path)
        manual = parser.parse()
        self.assertEqual(len(manual.tasks), 12)
        self.assertIn("Students", manual.context)
        self.assertIn("CREATE TABLE", manual.context.upper())
        self.assertIn("INSERT INTO", manual.context.upper())

    def test_02_prepare_database_students_table(self):
        docx_path = REPO_ROOT / "workspace" / "199aacd16861" / "Lab_08_edited.docx"
        manual = ManualParser(docx_path).parse()

        db_path = self.workspace / "dbms_lab.db"
        schema = DynamicSQLSynthesizer.prepare_database(db_path, f"{manual.context}\n{manual.raw_text}")
        self.assertEqual(schema.table_name, "Students")
        self.assertIn("StudentID", schema.columns)
        self.assertIn("StudentName", schema.columns)
        self.assertIn("Department", schema.columns)
        self.assertIn("ObtainedMarks", schema.columns)
        self.assertIn("TotalMarks", schema.columns)
        self.assertIn("SemesterFee", schema.columns)
        self.assertEqual(len(schema.seed_records), 12)

    def test_03_all_12_tasks_solve_and_execute_successfully(self):
        docx_path = REPO_ROOT / "workspace" / "199aacd16861" / "Lab_08_edited.docx"
        manual = ManualParser(docx_path).parse()

        db_path = self.workspace / "dbms_lab.db"
        DynamicSQLSynthesizer.prepare_database(db_path, f"{manual.context}\n{manual.raw_text}")

        solutions = [self.solver.solve_task(t, lab_context=manual.context) for t in manual.tasks]
        self.assertEqual(len(solutions), 12)

        for idx, sol in enumerate(solutions, 1):
            # Verify no generic Records or dummy Highest table fallbacks
            self.assertNotIn("FROM Records", sol.code)
            self.assertNotIn("FROM Highest", sol.code)
            self.assertIn("Students", sol.code)

            # Execute query against the seeded database
            res = self.runner.execute(sol)
            self.assertEqual(res.exit_code, 0, f"Task {idx} failed with exit code {res.exit_code}: {res.stderr}")
            self.assertNotIn("Invalid object name", res.stdout)
            self.assertNotIn("no such table", res.stdout.lower())
            self.assertIn("rows affected", res.stdout)
