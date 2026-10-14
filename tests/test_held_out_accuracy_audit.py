"""Regression and Held-Out Generalization Test Suite.

Audits and verifies:
1. DSA Doubly Linked List (DOCX): parsing, multi-task DLL synthesis, execution.
2. DBMS Library Relational Schema (PDF): parsing, DDL + GROUP BY + JOIN SQL execution on SQLite.
3. Systems C Strings (TXT): Palindrome, word count, substring search without <string.h>.
4. Data Science Pandas & Stats (Markdown): Markdown parsing, observation tables, IQR outlier detection.
5. Malformed Metadata Manual (TXT): Quick sort, linear search (not bubble sort).
6. Provider Interface: solve_task / solve_tasks parity across providers.
7. Report Generator: Fallback monospace code and output rendering when screenshots are absent.
8. Recompile All Formats: Markdown and HTML report generation.
"""

import json
from pathlib import Path
import docx
import pytest

from labgenius.builder import DocumentBuilder
from labgenius.config import Config
from labgenius.ingestion import IngestionEngine
from labgenius.orchestrator import TaskOrchestrator
from labgenius.parser import LabTask, ManualParser, LabManual
from labgenius.runner import CodeRunner
from labgenius.solver import TaskSolution, TaskSolver
from labgenius.state import ManualInfo, SessionManager, StudentInfo
from labgenius.providers.base import BaseAIProvider
from labgenius.providers.gemini import GeminiProvider
import web_app

REPO_ROOT = Path(__file__).resolve().parent.parent
HELDOUT_DIR = REPO_ROOT / "evaluation_corpus" / "held_out"


@pytest.fixture
def test_cfg(tmp_path):
    cfg = Config()
    cfg.system.workspace_dir = tmp_path
    cfg.student.name = "Test Student"
    cfg.student.roll_number = "25F-DS-020"
    cfg.ai.provider = "offline"
    return cfg


def test_heldout_01_doubly_linked_list_pipeline(test_cfg):
    """Test HELDOUT_01 (DOCX): Doubly Linked List parsing, solving, and execution."""
    doc_path = HELDOUT_DIR / "held_out_01_dsa_doubly_linked_list.docx"
    assert doc_path.exists(), "HELDOUT_01 fixture missing"

    engine = IngestionEngine(test_cfg)
    manual, report = engine.ingest_file(doc_path)

    assert manual.lab_number == "07"
    assert len(manual.tasks) == 3
    assert len(manual.viva_questions) == 2
    assert len(manual.analysis_questions) == 2

    # Session & Orchestrator
    s_mgr = SessionManager(str(test_cfg.system.workspace_dir))
    s_info = StudentInfo(name=test_cfg.student.name, roll_number=test_cfg.student.roll_number)
    m_info = ManualInfo(file_name=doc_path.name, title=manual.title, course_name=manual.course_name, lab_number=manual.lab_number)
    sess = s_mgr.create_session(student_info=s_info, manual_info=m_info)
    sess.requirements = engine.to_session_requirements(manual)

    orchestrator = TaskOrchestrator(test_cfg)
    solutions, exec_results, _ = orchestrator.process_session(sess, manual)

    assert len(solutions) == 3
    for sol in solutions:
        assert "DoublyLinkedList" in sol.code or "prev" in sol.code
    for res in exec_results:
        assert res.success is True, f"Execution failed: {res.stderr}"


def test_heldout_02_dbms_library_pipeline(test_cfg):
    """Test HELDOUT_02 (PDF): Relational Library schema DDL, GROUP BY, and JOIN on SQLite."""
    doc_path = HELDOUT_DIR / "held_out_02_dbms_library_system.pdf"
    assert doc_path.exists(), "HELDOUT_02 fixture missing"

    engine = IngestionEngine(test_cfg)
    manual, report = engine.ingest_file(doc_path)

    assert manual.lab_number == "08"
    assert len(manual.tasks) == 3
    assert len(manual.viva_questions) == 2

    s_mgr = SessionManager(str(test_cfg.system.workspace_dir))
    s_info = StudentInfo(name=test_cfg.student.name, roll_number=test_cfg.student.roll_number)
    m_info = ManualInfo(file_name=doc_path.name, title=manual.title, course_name=manual.course_name, lab_number=manual.lab_number)
    sess = s_mgr.create_session(student_info=s_info, manual_info=m_info)
    sess.requirements = engine.to_session_requirements(manual)

    orchestrator = TaskOrchestrator(test_cfg)
    solutions, exec_results, _ = orchestrator.process_session(sess, manual)

    assert len(solutions) == 3
    for res in exec_results:
        assert res.success is True, f"SQL Execution failed: {res.stderr}"
        assert res.exit_code == 0


def test_heldout_03_systems_c_strings_pipeline(test_cfg):
    """Test HELDOUT_03 (TXT): C string operations without string.h."""
    doc_path = HELDOUT_DIR / "held_out_03_systems_c_strings.txt"
    assert doc_path.exists(), "HELDOUT_03 fixture missing"

    engine = IngestionEngine(test_cfg)
    manual, report = engine.ingest_file(doc_path)

    assert manual.lab_number == "09"
    assert len(manual.tasks) == 3

    s_mgr = SessionManager(str(test_cfg.system.workspace_dir))
    s_info = StudentInfo(name=test_cfg.student.name, roll_number=test_cfg.student.roll_number)
    m_info = ManualInfo(file_name=doc_path.name, title=manual.title, course_name=manual.course_name, lab_number=manual.lab_number)
    sess = s_mgr.create_session(student_info=s_info, manual_info=m_info)
    sess.requirements = engine.to_session_requirements(manual)

    orchestrator = TaskOrchestrator(test_cfg)
    solutions, exec_results, _ = orchestrator.process_session(sess, manual)

    assert len(solutions) == 3
    for sol in solutions:
        assert sol.language == "c"
        assert "<string.h>" not in sol.code
    for res in exec_results:
        assert res.success is True, f"C execution failed: {res.stderr}"


def test_heldout_04_pandas_markdown_pipeline(test_cfg):
    """Test HELDOUT_04 (Markdown): Pandas, NumPy IQR outlier detection, observation tables."""
    doc_path = HELDOUT_DIR / "held_out_04_data_science_pandas.md"
    assert doc_path.exists(), "HELDOUT_04 fixture missing"

    engine = IngestionEngine(test_cfg)
    manual, report = engine.ingest_file(doc_path)

    assert manual.lab_number == "10"
    assert len(manual.tasks) == 3
    assert len(manual.viva_questions) == 2
    assert len(manual.observation_tables) >= 1

    s_mgr = SessionManager(str(test_cfg.system.workspace_dir))
    s_info = StudentInfo(name=test_cfg.student.name, roll_number=test_cfg.student.roll_number)
    m_info = ManualInfo(file_name=doc_path.name, title=manual.title, course_name=manual.course_name, lab_number=manual.lab_number)
    sess = s_mgr.create_session(student_info=s_info, manual_info=m_info)
    sess.requirements = engine.to_session_requirements(manual)

    orchestrator = TaskOrchestrator(test_cfg)
    solutions, exec_results, _ = orchestrator.process_session(sess, manual)

    assert len(solutions) == 3
    for res in exec_results:
        assert res.success is True, f"Pandas execution failed: {res.stderr}"


def test_heldout_05_malformed_metadata_pipeline(test_cfg):
    """Test HELDOUT_05 (TXT): Ambiguous metadata, linear search (not bubble sort)."""
    doc_path = HELDOUT_DIR / "held_out_05_malformed_metadata.txt"
    assert doc_path.exists(), "HELDOUT_05 fixture missing"

    engine = IngestionEngine(test_cfg)
    manual, report = engine.ingest_file(doc_path)

    assert manual.lab_number == "01"
    assert len(manual.tasks) == 2

    s_mgr = SessionManager(str(test_cfg.system.workspace_dir))
    s_info = StudentInfo(name=test_cfg.student.name, roll_number=test_cfg.student.roll_number)
    m_info = ManualInfo(file_name=doc_path.name, title=manual.title, course_name=manual.course_name, lab_number=manual.lab_number)
    sess = s_mgr.create_session(student_info=s_info, manual_info=m_info)
    sess.requirements = engine.to_session_requirements(manual)

    orchestrator = TaskOrchestrator(test_cfg)
    solutions, exec_results, _ = orchestrator.process_session(sess, manual)

    assert len(solutions) == 2
    # Task 1 is Quick Sort
    assert "quick" in solutions[0].code.lower()
    # Task 2 is Linear Search (must NOT be bubble sort)
    assert "linear" in solutions[1].code.lower()
    assert "bubble" not in solutions[1].code.lower()
    for res in exec_results:
        assert res.success is True


from labgenius.sanitizer import DocumentSanitizer


def test_docx_code_output_fallback_preservation(test_cfg, tmp_path):
    """Verify that when screenshots are absent, build_report inserts monospace code and output."""
    builder = DocumentBuilder(test_cfg)
    manual = LabManual(
        file_path=Path("dummy.docx"),
        lab_number="01",
        title="Test Algorithm Verification",
        course_name="Computer Science",
        tasks=[LabTask(1, "Linear Search Implementation", "Find target in array", "python")],
    )
    sol = TaskSolution(1, "python", "print('Executed Test 123')", "Explanation text", {}, "task_01.py")
    runner = CodeRunner(test_cfg)
    res = runner.execute(sol)

    out_docx = tmp_path / "test_fallback.docx"
    # Pass empty screenshot list: (None, None)
    builder.build_report(manual, [sol], [res], [(None, None)], out_docx)

    assert out_docx.exists()
    doc_read = docx.Document(out_docx)
    full_text = "\n".join(p.text for p in doc_read.paragraphs)

    assert "Linear Search Implementation" in full_text
    assert "print('Executed Test 123')" in full_text
    assert "Executed Test 123" in full_text


def test_provider_adapter_solve_task_interface(test_cfg):
    """Test BaseProvider solve_task interface and GeminiProvider delegation."""
    provider = GeminiProvider(test_cfg)
    task = LabTask(1, "Reverse Array", "Reverse elements in place", "python")

    # In test environment without GEMINI_API_KEY, solve_task safely falls back to offline engine
    sol = provider.solve_task(task, lab_context="Array Algorithms")
    assert sol is not None
    assert sol.task_id == 1
    assert sol.code is not None


def test_recompile_all_formats_markdown_and_html(test_cfg, tmp_path, monkeypatch):
    """Verify web_app._recompile_all_formats generates md and html when requested."""
    monkeypatch.setattr(web_app, "OUTPUT_DIR", tmp_path)

    builder = DocumentBuilder(test_cfg)
    sanitizer = DocumentSanitizer(test_cfg)
    manual = LabManual(
        file_path=Path("dummy.docx"),
        lab_number="05",
        title="Array Algorithms",
        course_name="Data Structures",
        tasks=[LabTask(1, "Array Reversal", "Reverse an array in Python", "python")],
    )
    sol = TaskSolution(1, "python", "print('Reversed')", "Reversal test", {}, "task_01.py")
    runner = CodeRunner(test_cfg)
    res = runner.execute(sol)

    compiled = web_app._recompile_all_formats(
        builder=builder,
        sanitizer=sanitizer,
        lab_manual=manual,
        solutions=[sol],
        exec_results=[res],
        screenshots=[(None, None)],
        clean_lab="test_lab05",
        formats="docx,pdf,md,html",
    )

    assert compiled["docx"] == "test_lab05.docx"
    assert (tmp_path / "test_lab05.docx").exists()
    assert compiled["md"] == "test_lab05.md"
    assert (tmp_path / "test_lab05.md").exists()
    assert compiled["html"] == "test_lab05.html"
    assert (tmp_path / "test_lab05.html").exists()
