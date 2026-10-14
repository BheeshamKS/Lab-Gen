"""
Source-to-Solution Baseline Evaluator.
Executes complete pipeline on held-out evaluation corpus and records
question-level correctness, extraction, execution, and document fidelity.
"""

import os
import json
import traceback
import docx
from pathlib import Path
from typing import Dict, Any, List

from labgenius.config import Config
from labgenius.parser import ManualParser, LabManual
from labgenius.ingestion import IngestionEngine
from labgenius.orchestrator import TaskOrchestrator
from labgenius.solver import TaskSolver, validate_code_syntax
from labgenius.runner import CodeRunner
from labgenius.validator import QualityValidator
from labgenius.builder import DocumentBuilder
from labgenius.state import LabSession, SessionManager

REPO_ROOT = Path(__file__).resolve().parent.parent
MANIFEST_PATH = REPO_ROOT / "evaluation_corpus" / "manifest.json"
REPORT_OUTPUT_PATH = REPO_ROOT / "evaluation_corpus" / "baseline_evaluation_report.json"


def evaluate_all():
    with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    held_out_list = manifest.get("held_out_evaluation_examples", [])
    report_data = {
        "evaluation_type": "baseline_pre_remediation",
        "held_out_documents_count": len(held_out_list),
        "results": [],
    }

    cfg = Config()
    cfg.student.name = "Bheesham Kumar Sajnani"
    cfg.student.roll_number = "25F-DS-020"
    cfg.ai.provider = "offline"  # Baseline offline deterministic engine

    ingest_engine = IngestionEngine(cfg)
    runner = CodeRunner(cfg)
    validator = QualityValidator()
    builder = DocumentBuilder(cfg)
    session_manager = SessionManager(str(cfg.system.workspace_dir))

    for item in held_out_list:
        doc_id = item["id"]
        file_rel = item["file"]
        file_path = REPO_ROOT / file_rel
        expected_tasks = item.get("expected_tasks", [])
        expected_tasks_count = item.get("expected_tasks_count", 0)
        expected_viva_count = item.get("expected_viva_count", 0)
        expected_analysis_count = item.get("expected_analysis_count", 0)
        expected_lab_num = item.get("expected_lab_number", "")

        doc_result = {
            "id": doc_id,
            "file": file_rel,
            "format": item["format"],
            "identification": {},
            "extraction": {},
            "solving": {},
            "execution": {},
            "report_generation": {},
            "question_level_results": [],
            "failures": [],
        }

        print(f"\n=======================================================")
        print(f"Evaluating: {doc_id} ({file_rel})")
        print(f"=======================================================")

        # 1. Parse & Ingest
        try:
            manual, extract_report = ingest_engine.ingest_file(file_path)
            doc_result["identification"] = {
                "detected_lab_number": manual.lab_number,
                "expected_lab_number": expected_lab_num,
                "lab_number_match": manual.lab_number == expected_lab_num,
                "detected_title": manual.title,
                "detected_course": manual.course_name,
            }
            extracted_task_titles = [t.title for t in manual.tasks]
            doc_result["extraction"] = {
                "extracted_task_count": len(manual.tasks),
                "expected_task_count": expected_tasks_count,
                "missing_tasks_count": max(0, expected_tasks_count - len(manual.tasks)),
                "extracted_task_titles": extracted_task_titles,
                "extracted_viva_count": len(manual.viva_questions),
                "expected_viva_count": expected_viva_count,
                "extracted_analysis_count": len(manual.analysis_questions),
                "expected_analysis_count": expected_analysis_count,
                "warnings": [w.message for w in extract_report.warnings],
                "errors": [e.message for e in extract_report.errors],
            }
        except Exception as e:
            err = f"Ingestion crashed: {e}"
            print(f"[-] {err}")
            doc_result["failures"].append({"stage": "ingestion", "error": err, "traceback": traceback.format_exc()})
            report_data["results"].append(doc_result)
            continue

        # 2. Requirement conversion & Session init
        try:
            from labgenius.state import StudentInfo, ManualInfo
            reqs = ingest_engine.to_session_requirements(manual)
            s_info = StudentInfo(name=cfg.student.name, roll_number=cfg.student.roll_number)
            m_info = ManualInfo(file_name=Path(file_path).name, title=manual.title, course_name=manual.course_name, lab_number=manual.lab_number)
            sess = session_manager.create_session(student_info=s_info, manual_info=m_info)
            sess.requirements = reqs
        except Exception as e:
            err = f"Session creation crashed: {e}"
            print(f"[-] {err}")
            doc_result["failures"].append({"stage": "session_init", "error": err, "traceback": traceback.format_exc()})
            report_data["results"].append(doc_result)
            continue

        # 3. Solve & Execute via TaskOrchestrator
        try:
            orchestrator = TaskOrchestrator(cfg)
            solutions, exec_results, quality_report = orchestrator.process_session(
                session=sess,
                manual=manual,
                custom_instructions="",
            )
            doc_result["solving"] = {
                "solutions_generated_count": len(solutions),
                "has_analysis_answers": len(manual.analysis_answers) > 0,
                "has_viva_answers": len(manual.viva_answers) > 0,
            }
        except Exception as e:
            err = f"TaskOrchestrator crashed: {e}"
            print(f"[-] {err}")
            doc_result["failures"].append({"stage": "orchestrator", "error": err, "traceback": traceback.format_exc()})
            report_data["results"].append(doc_result)
            continue

        # 4. Question-level correctness & execution analysis
        exec_pass_count = 0
        syntax_pass_count = 0
        task_relevance_count = 0

        for t_idx, (task, sol, res) in enumerate(zip(manual.tasks, solutions, exec_results)):
            syn_valid, syn_msg = validate_code_syntax(sol.code, sol.language)
            if syn_valid:
                syntax_pass_count += 1
            if res.success:
                exec_pass_count += 1

            # Check if generated code is actually relevant to the requested task title/description
            # (vs falling back to generic average or dummy records)
            keywords = [w.lower() for w in task.title.split() if len(w) > 3]
            code_lower = sol.code.lower()
            relevance = any(k in code_lower for k in keywords) or (task.language == "sql" and "select" in code_lower)
            if relevance:
                task_relevance_count += 1

            q_result = {
                "task_id": task.task_id,
                "title": task.title,
                "language": sol.language,
                "syntax_valid": syn_valid,
                "syntax_error": syn_msg if not syn_valid else None,
                "execution_success": res.success,
                "exit_code": res.exit_code,
                "stdout_snippet": res.stdout[:200] if res.stdout else "",
                "stderr_snippet": res.stderr[:200] if res.stderr else "",
                "code_snippet": sol.code[:200] if sol.code else "",
                "is_code_relevant": relevance,
            }
            doc_result["question_level_results"].append(q_result)

        doc_result["execution"] = {
            "total_tasks": len(manual.tasks),
            "syntax_pass_count": syntax_pass_count,
            "execution_pass_count": exec_pass_count,
            "relevant_code_count": task_relevance_count,
        }

        # 5. Document generation
        try:
            out_docx = Path(cfg.system.workspace_dir) / f"{doc_id}_out.docx"
            out_pdf = Path(cfg.system.workspace_dir) / f"{doc_id}_out.pdf"
            builder.build_report(manual, solutions, exec_results, [], out_docx)
            pdf_path = builder.build_pdf(out_docx, out_pdf)

            # Check docx content: verify that tasks are present in docx text
            doc_read = docx.Document(out_docx)
            doc_full_text = "\n".join(p.text for p in doc_read.paragraphs)

            doc_result["report_generation"] = {
                "docx_generated": out_docx.exists(),
                "docx_size_bytes": out_docx.stat().st_size if out_docx.exists() else 0,
                "pdf_generated": pdf_path is not None and pdf_path.exists(),
                "tasks_in_doc_text": [(f"Task {t.task_id:02d}" in doc_full_text or f"Task {t.task_id}" in doc_full_text) for t in manual.tasks],
                "analysis_in_doc": "PERFORMANCE ANALYSIS QUESTIONS & FINDINGS" in doc_full_text if manual.analysis_questions else None,
                "viva_in_doc": "VIVA QUESTIONS & BRIEF ANSWERS" in doc_full_text if manual.viva_questions else None,
            }
        except Exception as e:
            err = f"Report building crashed: {e}"
            print(f"[-] {err}")
            doc_result["failures"].append({"stage": "report_builder", "error": err, "traceback": traceback.format_exc()})

        report_data["results"].append(doc_result)

    with open(REPORT_OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(report_data, f, indent=2)

    print(f"\n=======================================================")
    print(f"Baseline report generated at: {REPORT_OUTPUT_PATH}")
    print(f"=======================================================")


if __name__ == "__main__":
    evaluate_all()
