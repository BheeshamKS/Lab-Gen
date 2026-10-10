"""
Unit Tests for QualityValidator and IngestionEngine.
Verifies requirement tracking, extraction completeness validation,
crash detection, and buzzword filtering.
"""

import unittest
from pathlib import Path

from labgenius.ingestion import IngestionEngine
from labgenius.validator import QualityValidator
from labgenius.parser import LabManual, LabTask
from labgenius.solver import TaskSolution
from labgenius.runner import ExecutionResult

REPO_ROOT = Path(__file__).resolve().parent.parent


class TestValidatorAndIngestion(unittest.TestCase):

    def test_01_ingest_and_validate_lab_06(self):
        engine = IngestionEngine()
        manual, report = engine.ingest_file(
            REPO_ROOT / "uploads" / "Data Structure Laboratory Manual L6.docx",
            subject="dsa",
        )
        self.assertTrue(report.is_valid)
        self.assertEqual(len(report.errors), 0)
        self.assertEqual(len(manual.tasks), 1)
        self.assertEqual(len(manual.analysis_questions), 6)

        reqs = engine.to_session_requirements(manual)
        self.assertEqual(len(reqs), 7)

    def test_02_validator_detects_empty_tasks(self):
        empty_manual = LabManual(
            file_path=Path("dummy.docx"),
            title="Empty Manual",
            course_name="CS",
            lab_number="01",
            tasks=[],
        )
        report = QualityValidator.validate_extraction(empty_manual)
        self.assertFalse(report.is_valid)
        self.assertTrue(any("No lab tasks were extracted" in e.message for e in report.errors))

    def test_03_validator_detects_execution_crash(self):
        sol = TaskSolution(
            task_id=1,
            language="python",
            code="x = 10 / 0",
            explanation="Div zero",
            discussion_answers={},
            file_name="task_01.py",
        )
        res = ExecutionResult(
            task_id=1,
            command_str="python task_01.py",
            stdout="",
            stderr="Traceback (most recent call last):\nZeroDivisionError: division by zero",
            exit_code=1,
            execution_time=0.1,
            output_files={},
            work_dir=Path("/tmp"),
            success=False,
        )
        report = QualityValidator.validate_execution(sol, res)
        self.assertFalse(report.is_valid)
        self.assertTrue(any("exited with non-zero exit code" in e.message for e in report.errors))
        self.assertTrue(any("contains error crash trace" in e.message for e in report.errors))

    def test_04_validator_detects_ai_buzzwords(self):
        buzz_text = "In this lab, we delve deeply into sorting algorithms, which play a pivotal and crucial role."
        report = QualityValidator.validate_text_for_ai_buzzwords(buzz_text, context_label="Task Explanation")
        self.assertTrue(len(report.warnings) >= 2)
        warn_msgs = [w.message for w in report.warnings]
        self.assertTrue(any("delve" in m for m in warn_msgs))
        self.assertTrue(any("pivotal" in m for m in warn_msgs))


if __name__ == "__main__":
    unittest.main()
