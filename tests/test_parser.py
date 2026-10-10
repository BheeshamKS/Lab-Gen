"""
Unit tests for DocumentParser across all 10 original lab manuals.
"""

import unittest
from pathlib import Path
from labgenius.parser import ManualParser

REPO_ROOT = Path(__file__).resolve().parent.parent


class TestManualParser(unittest.TestCase):

    def test_dsa_lab_01(self):
        p = ManualParser(REPO_ROOT / "uploads" / "Data Structure Laboratory Manual L1.docx", subject="dsa")
        m = p.parse()
        self.assertEqual(len(m.tasks), 10)
        self.assertEqual(len(m.viva_questions), 10)

    def test_dsa_lab_02(self):
        p = ManualParser(REPO_ROOT / "uploads" / "Data Structure Laboratory Manual L2.docx", subject="dsa")
        m = p.parse()
        self.assertEqual(len(m.tasks), 4)
        self.assertEqual(len(m.analysis_questions), 6)

    def test_dsa_lab_03(self):
        p = ManualParser(REPO_ROOT / "uploads" / "Data Structure Laboratory Manual L3.docx", subject="dsa")
        m = p.parse()
        self.assertEqual(len(m.tasks), 8)
        self.assertEqual(len(m.observation_tables), 6)

    def test_dsa_lab_04(self):
        p = ManualParser(REPO_ROOT / "uploads" / "Data Structure Laboratory Manual L4.docx", subject="dsa")
        m = p.parse()
        self.assertEqual(len(m.tasks), 8)
        self.assertEqual(len(m.viva_questions), 8)
        self.assertEqual(len(m.analysis_questions), 3)

    def test_dsa_lab_05(self):
        p = ManualParser(REPO_ROOT / "uploads" / "Data Structure Laboratory Manual L5.docx", subject="dsa")
        m = p.parse()
        self.assertEqual(len(m.tasks), 7)
        self.assertEqual(len(m.viva_questions), 10)

    def test_dbms_lab_01(self):
        p = ManualParser(REPO_ROOT / "uploads" / "DBMS Lab 01.docx", subject="dbms")
        m = p.parse()
        self.assertEqual(len(m.tasks), 2)

    def test_dbms_lab_02(self):
        p = ManualParser(REPO_ROOT / "uploads" / "DBMS Lab 02.docx", subject="dbms")
        m = p.parse()
        self.assertEqual(len(m.tasks), 12)

    def test_dbms_lab_03(self):
        p = ManualParser(REPO_ROOT / "uploads" / "DBMS Lab 03.docx", subject="dbms")
        m = p.parse()
        self.assertEqual(len(m.tasks), 8)

    def test_dbms_lab_04(self):
        p = ManualParser(REPO_ROOT / "uploads" / "DBMS- Lab 04 edited.docx", subject="dbms")
        m = p.parse()
        self.assertEqual(len(m.tasks), 14)

    def test_dbms_lab_05(self):
        p = ManualParser(REPO_ROOT / "uploads" / "DBMS - Lab 05-edit.pdf", subject="dbms")
        m = p.parse()
        self.assertEqual(len(m.tasks), 6)

    def test_auto_detection_dbms(self):
        """Verifies auto-detecting DBMS subject without manual user specification."""
        p = ManualParser(REPO_ROOT / "uploads" / "DBMS Lab 03.docx")
        m = p.parse()
        self.assertIn("Database", m.course_name)
        self.assertEqual(m.tasks[0].language, "sql")

    def test_auto_detection_dsa(self):
        """Verifies auto-detecting DSA subject without manual user specification."""
        p = ManualParser(REPO_ROOT / "uploads" / "Data Structure Laboratory Manual L3.docx")
        m = p.parse()
        self.assertIn("Data Structure", m.course_name)
        self.assertEqual(m.tasks[0].language, "python")


if __name__ == "__main__":
    unittest.main()
