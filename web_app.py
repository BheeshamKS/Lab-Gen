"""
FastAPI Server & Web Application for LabGenius.
Provides a modern, interactive dashboard for lab completion, live screenshots, and report download.
"""

import os
import time
import shutil
import json
import re
import tempfile
import uuid
from pathlib import Path
from typing import Optional, List
import uvicorn
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Body
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

from labgenius.config import Config
from labgenius.parser import ManualParser, LabTask
from labgenius.solver import TaskSolver, AntiAIFilter
from labgenius.runner import CodeRunner
from labgenius.capture import ScreenshotStudio
from labgenius.builder import DocumentBuilder
from labgenius.sanitizer import DocumentSanitizer
from labgenius.validator import QualityValidator, ValidationReport
from labgenius.ingestion import IngestionEngine
from labgenius.orchestrator import TaskOrchestrator
from labgenius.state import (
    default_session_manager,
    LabSession,
    Requirement,
    RequirementType,
    RequirementStatus,
    StudentInfo,
    ManualInfo,
    SessionArtifacts,
)
from labgenius.themes import get_theme, list_public_themes
import labgenius.doc_tools as doc_tools

app = FastAPI(title="LabGenius Web App", version="1.0.0")

BASE_DIR = Path(__file__).resolve().parent
WEB_DIR = BASE_DIR / "web"
OUTPUT_DIR = BASE_DIR / "output"
WORKSPACE_DIR = BASE_DIR / "workspace"
EXAMPLES_DIR = BASE_DIR / "examples"
UPLOADS_DIR = BASE_DIR / "uploads"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
WORKSPACE_DIR.mkdir(parents=True, exist_ok=True)
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)

# Mount static web files, workspace, and uploads
app.mount("/static", StaticFiles(directory=str(WEB_DIR)), name="static")
app.mount("/workspace", StaticFiles(directory=str(WORKSPACE_DIR)), name="workspace")
app.mount("/uploads", StaticFiles(directory=str(UPLOADS_DIR)), name="uploads")


@app.middleware("http")
async def add_no_cache_headers(request, call_next):
    response = await call_next(request)
    path = request.url.path
    if (
        path.startswith("/workspace")
        or path.startswith("/uploads")
        or path.startswith("/api/")
        or path.startswith("/static/app.js")
        or path == "/"
    ):
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
    return response


session_manager = default_session_manager


def _get_active_session_data(session_id: Optional[str] = None) -> Optional[dict]:
    """Retrieve runtime state dictionary for a specific or the active session."""
    return session_manager.get_live_data(session_id, "session_data")


def _set_session_data(session_id: str, data: dict) -> None:
    """Store runtime state dictionary for a specific session."""
    session_manager.set_live_data(session_id, "session_data", data)


def _get_last_result(session_id: Optional[str] = None) -> Optional[dict]:
    """Retrieve cached result payload for a specific or the active session."""
    return session_manager.get_live_data(session_id, "last_result")


def _set_last_result(res: dict, session_id: Optional[str] = None) -> dict:
    """Cache result payload for a specific session or active session."""
    if res and res.get("success"):
        sid = session_id or res.get("session_id") or session_manager.get_active_session_id()
        if sid:
            session_manager.set_live_data(sid, "last_result", res)
            sess = session_manager.get_session(sid)
            if sess:
                sess.artifacts.docx_filename = res.get("filename")
                sess.artifacts.docx_url = res.get("docx_url")
                sess.artifacts.pdf_filename = res.get("pdf_filename")
                sess.artifacts.pdf_url = res.get("pdf_url")
                sess.artifacts.md_filename = res.get("md_filename")
                sess.artifacts.html_filename = res.get("html_filename")
                sess.provider_used = res.get("provider_used", "offline")
                sess.status = "completed"
                session_manager.save_session(sess)
    return res


class _CurrentLabProxy(dict):
    """Backwards-compatible proxy mapping legacy CURRENT_LAB accesses to isolated active session state."""
    def _data(self):
        return _get_active_session_data() or {}

    def __getitem__(self, item):
        d = self._data()
        if item not in d:
            raise KeyError(item)
        return d[item]

    def __setitem__(self, key, value):
        sid = session_manager.get_active_session_id()
        if not sid:
            sid = "default"
            session_manager.set_active_session_id(sid)
        data = _get_active_session_data(sid) or {}
        data[key] = value
        _set_session_data(sid, data)

    def get(self, key, default=None):
        return self._data().get(key, default)

    def __contains__(self, item):
        return item in self._data()

    def __bool__(self):
        return bool(self._data())

    def clear(self):
        sid = session_manager.get_active_session_id()
        if sid:
            _set_session_data(sid, {})


class _LastResultProxy(dict):
    """Backwards-compatible proxy mapping legacy LAST_RESULT accesses to isolated active session state."""
    def _data(self):
        return _get_last_result() or {}

    def __getitem__(self, item):
        d = self._data()
        if item not in d:
            raise KeyError(item)
        return d[item]

    def get(self, key, default=None):
        return self._data().get(key, default)

    def __contains__(self, item):
        return item in self._data()

    def __bool__(self):
        return bool(self._data())

    def clear(self):
        sid = session_manager.get_active_session_id()
        if sid:
            session_manager.set_live_data(sid, "last_result", {})


CURRENT_LAB = _CurrentLabProxy()
LAST_RESULT = _LastResultProxy()


@app.get("/", response_class=HTMLResponse)
async def serve_index():
    index_path = WEB_DIR / "index.html"
    if not index_path.exists():
        raise HTTPException(status_code=404, detail="Index file not found")
    content = index_path.read_text(encoding="utf-8")
    last_res = _get_last_result()
    if last_res and last_res.get("success"):
        hydration_script = f"<script>window.__INITIAL_LAB__ = {json.dumps(last_res)};</script>"
        content = content.replace("</head>", f"  {hydration_script}\n</head>")
    response = HTMLResponse(content=content)
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response


@app.get("/api/sample-manual")
async def get_sample_manual():
    sample_file = EXAMPLES_DIR / "Lab 03 manual.docx"
    if not sample_file.exists():
        sample_file = EXAMPLES_DIR / "sample_lab_manual.docx"
    if not sample_file.exists():
        from examples.generate_sample_manual import create_sample_manual
        create_sample_manual(sample_file)
    return {
        "success": True,
        "filename": sample_file.name,
        "path": str(sample_file.resolve()),
    }


@app.get("/api/themes")
async def get_available_themes():
    """Returns the list of public screenshot and document themes."""
    active = get_theme()
    return {
        "success": True,
        "active_theme": active.id if not active.is_secret else "modern-dark",
        "is_custom_env": active.is_secret,
        "themes": list_public_themes(),
    }


def _build_tasks_response(tasks, solutions, exec_results, screenshots):
    tasks_response = []
    for idx, task in enumerate(tasks):
        sol = next((s for s in solutions if s.task_id == task.task_id), solutions[idx] if idx < len(solutions) else None)
        res = next((r for r in exec_results if r.task_id == task.task_id), exec_results[idx] if idx < len(exec_results) else None)
        code_img, out_img = screenshots[idx] if idx < len(screenshots) else (None, None)

        ts = int(time.time() * 1000)
        code_url = f"/{code_img.resolve().relative_to(BASE_DIR.resolve()).as_posix()}?t={ts}" if code_img and code_img.exists() else ""
        out_url = f"/{out_img.resolve().relative_to(BASE_DIR.resolve()).as_posix()}?t={ts}" if out_img and out_img.exists() else ""

        tasks_response.append({
            "task_id": task.task_id,
            "title": task.title,
            "description": task.description,
            "language": task.language,
            "code": sol.code if sol else "",
            "explanation": sol.explanation if sol else "",
            "answers": sol.discussion_answers if sol else {},
            "code_screenshot_url": code_url,
            "output_screenshot_url": out_url,
            "screenshot_url": out_url or code_url,
            "success": res.success if res else True,
        })
    return tasks_response


def _format_lab_title(lab_manual) -> str:
    """Formats lab title cleanly without duplicate prefixes."""
    if not lab_manual.title:
        return f"Lab #{lab_manual.lab_number}" if lab_manual.lab_number else "Lab Report"
    title_clean = lab_manual.title.strip()
    lower = title_clean.lower()
    if lower.startswith("lab #") or lower.startswith("lab ") or lower.startswith("lab#"):
        return title_clean
    return f"Lab #{lab_manual.lab_number}: {title_clean}" if lab_manual.lab_number else title_clean


def _recompile_all_formats(builder, sanitizer, lab_manual, solutions, exec_results, screenshots, clean_lab, formats="docx,pdf"):
    out_doc_path = OUTPUT_DIR / f"{clean_lab}.docx"
    out_pdf_path = OUTPUT_DIR / f"{clean_lab}.pdf"
    out_md_path = OUTPUT_DIR / f"{clean_lab}.md"
    out_html_path = OUTPUT_DIR / f"{clean_lab}.html"

    # 1. Build DOCX & Sanitize
    builder.build_report(lab_manual, solutions, exec_results, screenshots, out_doc_path)
    sanitizer.sanitize_docx(out_doc_path)
    verification = sanitizer.verify_sanitization(out_doc_path)

    # 2. Build PDF via LibreOffice
    pdf_res = None
    if not formats or "pdf" in formats.lower():
        pdf_res = builder.build_pdf(out_doc_path, out_pdf_path)

    # 3. Build Markdown if requested
    md_res = None
    if formats and ("md" in formats.lower() or "markdown" in formats.lower()):
        try:
            md_res = builder.build_markdown_report(lab_manual, solutions, exec_results, screenshots, out_md_path)
        except Exception as e:
            logger.warning(f"Markdown report generation failed: {e}")

    # 4. Build HTML if requested
    html_res = None
    if formats and "html" in formats.lower():
        try:
            html_res = builder.build_html_report(lab_manual, solutions, exec_results, screenshots, out_html_path)
        except Exception as e:
            logger.warning(f"HTML report generation failed: {e}")

    return {
        "docx": out_doc_path.name,
        "pdf": out_pdf_path.name if (pdf_res and pdf_res.exists()) else None,
        "md": out_md_path.name if (md_res and md_res.exists()) else None,
        "html": out_html_path.name if (html_res and html_res.exists()) else None,
        "verification": verification,
    }


def _build_lab_result_payload(compiled_files, lab_manual, tasks_response, cfg, session_id=None, message=None, validation_report=None):
    course_name_val = lab_manual.course_name or cfg.student.department or "Data Science"
    viva_list = []
    if getattr(lab_manual, "viva_answers", None):
        for q, a in lab_manual.viva_answers:
            viva_list.append({"question": q, "answer": a})
    elif getattr(lab_manual, "viva_questions", None):
        for q in lab_manual.viva_questions:
            viva_list.append({"question": q, "answer": ""})

    analysis_list = []
    if getattr(lab_manual, "analysis_answers", None):
        for q, a in lab_manual.analysis_answers:
            analysis_list.append({"question": q, "answer": a})
    elif getattr(lab_manual, "analysis_questions", None):
        for q in lab_manual.analysis_questions:
            analysis_list.append({"question": q, "answer": ""})

    sid = session_id or session_manager.get_active_session_id()
    payload = {
        "success": True,
        "session_id": sid,
        "filename": compiled_files["docx"],
        "pdf_filename": compiled_files["pdf"],
        "docx_url": f"/api/download/{compiled_files['docx']}" if compiled_files.get("docx") else None,
        "pdf_url": f"/api/preview/pdf/{compiled_files['pdf']}" if compiled_files.get("pdf") else None,
        "md_filename": compiled_files["md"],
        "html_filename": compiled_files["html"],
        "lab_title": _format_lab_title(lab_manual),
        "course_name": course_name_val,
        "tasks": tasks_response,
        "viva_answers": viva_list,
        "analysis_answers": analysis_list,
        "observation_tables": getattr(lab_manual, "observation_tables", []) or [],
        "metadata": compiled_files.get("verification"),
        "has_pdf": bool(compiled_files.get("pdf")),
        "provider_used": getattr(lab_manual, "_provider_used", "offline"),
        "custom_instructions": getattr(lab_manual, "_custom_instructions", "") or "",
        "custom_instructions_applied": bool(getattr(lab_manual, "_custom_instructions", "")),
        "validation_report": validation_report or {"is_valid": True, "errors": [], "warnings": []},
    }
    if message:
        payload["message"] = message
    return _set_last_result(payload, session_id=sid)


@app.post("/api/run")
@app.post("/api/generate-lab")
async def run_lab(
    manual_file: Optional[UploadFile] = File(None),
    is_sample: Optional[str] = Form(None),
    sample_path: Optional[str] = Form(None),
    name: Optional[str] = Form(None),
    roll_number: Optional[str] = Form(None),
    section: Optional[str] = Form(None),
    department: Optional[str] = Form(None),
    instructor: Optional[str] = Form(None),
    include_instructor: Optional[str] = Form("false"),
    provider: Optional[str] = Form(None),
    api_key: Optional[str] = Form(None),
    theme: Optional[str] = Form(None),
    instructions: Optional[str] = Form(None),
    formats: Optional[str] = Form(None),
    username: Optional[str] = Form(None),
    hostname: Optional[str] = Form(None),
    subject: Optional[str] = Form(None),
    custom_subject: Optional[str] = Form(None),
    include_logo: Optional[str] = Form("true"),
    logo_choice: Optional[str] = Form("dawood"),
    custom_logo: Optional[UploadFile] = File(None),
    session_id: Optional[str] = Form(None),
):
    sid = session_id or uuid.uuid4().hex[:12]
    session_dir = session_manager.get_session_dir(sid)
    session_manager.set_active_session_id(sid)

    # Clean only this session's isolated workspace directory
    if session_dir.exists():
        shutil.rmtree(session_dir, ignore_errors=True)
    session_dir.mkdir(parents=True, exist_ok=True)

    try:
        sub_raw = (subject or "auto").strip().lower()
        if sub_raw == "other" and (not custom_subject or not custom_subject.strip()):
            return {
                "success": False,
                "error": "Please enter your custom Subject / Course name."
            }

        if sub_raw == "dbms":
            sub_clean = "dbms"
            course_name_val = "Database Management Systems (DBMS)"
        elif sub_raw == "dsa":
            sub_clean = "dsa"
            course_name_val = "Data Structures and Algorithms"
        elif sub_raw == "other":
            sub_clean = "other"
            course_name_val = custom_subject.strip()
        else:
            sub_clean = "auto"
            course_name_val = "Auto-Detect"

        # Load and configure
        cfg = Config.load()
        cfg.system.workspace_dir = str(session_dir)
        if department and department.strip():
            cfg.student.department = department.strip()
        elif not cfg.student.department:
            cfg.student.department = "Data Science"
        if name:
            cfg.student.name = name
        if roll_number:
            cfg.student.roll_number = roll_number
        if section:
            cfg.student.section = section
        if username and username.strip():
            cfg.system.username = username.strip()
        if hostname and hostname.strip():
            cfg.system.hostname = hostname.strip()

        # Logo toggle & choice
        is_logo_enabled = bool(include_logo and include_logo.lower() in ["true", "1", "yes", "on"])
        cfg.student.include_logo = is_logo_enabled
        cfg.student.logo_choice = logo_choice or "dawood"

        # Instructor toggle: off by default, zero trace if off
        is_inst_enabled = bool(include_instructor and include_instructor.lower() in ["true", "1", "yes", "on"])
        cfg.student.include_instructor = is_inst_enabled
        if is_inst_enabled and instructor:
            cfg.student.instructor = instructor.strip()
        else:
            cfg.student.instructor = ""
        if provider:
            if provider == "gemini-pro":
                cfg.ai.provider = "gemini"
                cfg.ai.model = "gemini-2.5-pro"
            elif provider == "gemini-flash":
                cfg.ai.provider = "gemini"
                cfg.ai.model = "gemini-2.5-flash"
            elif provider == "gemini-1.5-pro":
                cfg.ai.provider = "gemini"
                cfg.ai.model = "gemini-1.5-pro"
            elif provider in ["groq", "groq-llama-70b"]:
                cfg.ai.provider = "groq"
                cfg.ai.model = "llama-3.3-70b-versatile"
            elif provider == "groq-8b":
                cfg.ai.provider = "groq"
                cfg.ai.model = "llama-3.1-8b-instant"
            else:
                cfg.ai.provider = provider
        if api_key:
            cfg.ai.api_key = api_key
        if theme:
            if theme == "env_default":
                cfg.terminal.theme = get_theme().id
            else:
                cfg.terminal.theme = theme
        else:
            cfg.terminal.theme = get_theme().id

        # Graceful fallback to Smart Offline if Groq is requested without an API key
        if cfg.ai.provider == "groq" and not (cfg.ai.api_key or os.environ.get("GROQ_API_KEY")):
            cfg.ai.provider = "offline"

        # Validate AI provider key if Groq selected
        if cfg.ai.provider == "groq":
            groq_key = cfg.ai.api_key or os.environ.get("GROQ_API_KEY")
            if not groq_key:
                return {
                    "success": False,
                    "error": (
                        "Groq Cloud API Key is required when Groq is selected. "
                        "Please paste your free Groq API key (starts with 'gsk_...') in the settings, "
                        "or export GROQ_API_KEY in terminal, or select 'Smart Offline Demo Mode'."
                    )
                }

        upload_target_dir = BASE_DIR / "uploads"
        upload_target_dir.mkdir(parents=True, exist_ok=True)

        if custom_logo and custom_logo.filename:
            logo_ext = Path(custom_logo.filename).suffix.lower() or ".png"
            if logo_ext not in [".png", ".jpg", ".jpeg", ".webp"]:
                return {"success": False, "error": "Invalid logo format. Allowed: .png, .jpg, .jpeg, .webp"}
            logo_save_path = upload_target_dir / f"custom_logo{logo_ext}"
            with open(logo_save_path, "wb") as buf:
                shutil.copyfileobj(custom_logo.file, buf)
            cfg.student.custom_logo_path = str(logo_save_path)
            cfg.student.logo_choice = "custom"
        elif logo_choice == "custom":
            for ext in [".png", ".jpg", ".jpeg"]:
                candidate = upload_target_dir / f"custom_logo{ext}"
                if candidate.exists():
                    cfg.student.custom_logo_path = str(candidate)
                    break

        if is_sample and is_sample.lower() == "true":
            if sample_path:
                cand = (BASE_DIR / sample_path).resolve() if not Path(sample_path).is_absolute() else Path(sample_path).resolve()
                if cand.is_relative_to(BASE_DIR.resolve()) and cand.exists():
                    target_manual_path = cand
                else:
                    target_manual_path = EXAMPLES_DIR / "sample_lab_manual.docx"
            else:
                target_manual_path = EXAMPLES_DIR / "sample_lab_manual.docx"
        elif manual_file and manual_file.filename:
            safe_manual_name = Path(manual_file.filename).name
            manual_ext = Path(manual_file.filename).suffix.lower()
            if manual_ext not in [".docx", ".pdf", ".txt", ".md", ".doc"]:
                return {"success": False, "error": f"Invalid manual file format '{manual_ext}'. Supported: .docx, .pdf, .txt, .md, .doc"}
            target_manual_path = session_dir / safe_manual_name
            with open(target_manual_path, "wb") as buffer:
                shutil.copyfileobj(manual_file.file, buffer)
        else:
            raise HTTPException(status_code=400, detail="No manual file uploaded or selected.")

        # 1. Parse Manual
        parser_subject = None if sub_clean == "auto" else sub_clean
        parser_course = None if course_name_val == "Auto-Detect" else course_name_val
        parser_obj = ManualParser(str(target_manual_path), subject=parser_subject, subject_name=parser_course)
        lab_manual = parser_obj.parse()
        if sub_clean == "auto":
            if lab_manual.course_name and any(k in lab_manual.course_name.lower() for k in ["database", "dbms", "sql"]):
                course_name_val = "Database Management Systems (DBMS)"
            elif lab_manual.course_name and any(k in lab_manual.course_name.lower() for k in ["data structure", "algorithm", "dsa"]):
                course_name_val = "Data Structures and Algorithms"
            else:
                course_name_val = lab_manual.course_name or "Computer Science Lab"
        lab_manual.course_name = course_name_val

        if not lab_manual.tasks:
            return {
                "success": False,
                "error": f"No lab tasks could be detected in '{target_manual_path.name}'. Please check the manual format."
            }

        # 2. Modules
        provider_mode = "Smart Offline (Deterministic Rules)"
        if cfg.ai.provider == "gemini" and (cfg.ai.api_key or os.environ.get("GEMINI_API_KEY")):
            provider_mode = f"Google Gemini ({cfg.ai.model or '2.5-pro'})"
        elif cfg.ai.provider == "groq" and (cfg.ai.api_key or os.environ.get("GROQ_API_KEY")):
            provider_mode = f"Groq Cloud ({cfg.ai.model or 'llama-3.3-70b'})"
        elif cfg.ai.provider in ["openai", "openrouter"] and (cfg.ai.api_key or os.environ.get("OPENAI_API_KEY")):
            provider_mode = f"OpenAI ({cfg.ai.model or 'gpt-4o-mini'})"
        elif cfg.ai.provider == "ollama":
            provider_mode = f"Ollama ({cfg.ai.ollama_model})"
        lab_manual._provider_used = provider_mode
        lab_manual._custom_instructions = instructions.strip() if instructions else ""

        # Create persistent LabSession early
        sess = session_manager.create_session(
            student_info=StudentInfo(
                name=cfg.student.name,
                roll_number=cfg.student.roll_number,
                section=cfg.student.section,
                department=cfg.student.department,
                university=cfg.student.university,
                semester=cfg.student.semester,
                instructor=cfg.student.instructor,
                include_instructor=cfg.student.include_instructor,
                include_logo=cfg.student.include_logo,
                logo_choice=cfg.student.logo_choice,
                custom_logo_path=cfg.student.custom_logo_path,
            ),
            manual_info=ManualInfo(
                file_path=str(target_manual_path) if "target_manual_path" in locals() and target_manual_path else "",
                file_name=target_manual_path.name if "target_manual_path" in locals() and target_manual_path else "",
                title=lab_manual.title or "",
                course_name=lab_manual.course_name or "",
                lab_number=str(lab_manual.lab_number or ""),
                objectives=getattr(lab_manual, "objectives", []) or [],
                raw_text=getattr(lab_manual, "raw_text", "") or "",
                context=getattr(lab_manual, "context", "") or "",
                viva_questions=getattr(lab_manual, "viva_questions", []) or [],
                analysis_questions=getattr(lab_manual, "analysis_questions", []) or [],
                observation_tables=getattr(lab_manual, "observation_tables", []) or [],
            ),
            session_id=sid,
        )

        reqs = []
        for t in lab_manual.tasks:
            reqs.append(Requirement(
                id=f"task_{t.task_id}",
                task_id=t.task_id,
                type=RequirementType.TASK,
                title=t.title or f"Task {t.task_id}",
                description=t.description or "",
                language=t.language or "c",
                status=RequirementStatus.PENDING,
                sample_input=t.sample_input,
                expected_output=t.expected_output,
            ))
        for idx, q in enumerate(getattr(lab_manual, "analysis_questions", []) or [], 1):
            reqs.append(Requirement(
                id=f"analysis_{idx}",
                task_id=idx,
                type=RequirementType.ANALYSIS_QUESTION,
                title=f"Analysis Question {idx}",
                description=q,
                status=RequirementStatus.PENDING,
            ))
        for idx, q in enumerate(getattr(lab_manual, "viva_questions", []) or [], 1):
            reqs.append(Requirement(
                id=f"viva_{idx}",
                task_id=idx,
                type=RequirementType.VIVA_QUESTION,
                title=f"Viva Question {idx}",
                description=q,
                status=RequirementStatus.PENDING,
            ))
        sess.requirements = reqs
        session_manager.save_session(sess)

        # 3. Solve & Execute using TaskOrchestrator
        orchestrator = TaskOrchestrator(cfg)
        solutions, exec_results, validation_report = orchestrator.process_session(
            session=sess,
            manual=lab_manual,
            custom_instructions=instructions or "",
        )

        studio = ScreenshotStudio(cfg)
        builder = DocumentBuilder(cfg)
        sanitizer = DocumentSanitizer(cfg)

        screenshots = []
        for sol, res in zip(solutions, exec_results):
            code_img, out_img = studio.capture_task_screenshots(sol, res)
            screenshots.append((code_img, out_img))

        # Populate Observation Tables if present in manual
        if getattr(lab_manual, "observation_tables", None):
            solver_tmp = TaskSolver(cfg)
            lab_manual.observation_tables = solver_tmp.populate_observation_tables(
                lab_manual.observation_tables,
                exec_results=exec_results
            )

        clean_lab = f"LAB{lab_manual.lab_number}_completed" if lab_manual.lab_number else "Completed_Lab_Report"

        # 4. Compile all formats (.docx, .pdf, .md, .html)
        compiled_files = _recompile_all_formats(
            builder, sanitizer, lab_manual, solutions, exec_results, screenshots, clean_lab, formats=formats or "docx,pdf"
        )

        # 5. Store isolated session data for post-generation refinements
        session_data = {
            "manual": lab_manual,
            "solutions": solutions,
            "exec_results": exec_results,
            "screenshots": screenshots,
            "cfg": cfg,
            "clean_lab": clean_lab,
            "instructions": instructions,
        }
        _set_session_data(sid, session_data)

        sess.artifacts = SessionArtifacts(
            docx_path=str(OUTPUT_DIR / compiled_files["docx"]) if compiled_files.get("docx") else None,
            pdf_path=str(OUTPUT_DIR / compiled_files["pdf"]) if compiled_files.get("pdf") else None,
        )
        session_manager.save_session(sess)

        tasks_response = _build_tasks_response(lab_manual.tasks, solutions, exec_results, screenshots)

        return _build_lab_result_payload(compiled_files, lab_manual, tasks_response, cfg, session_id=sid, validation_report=validation_report.model_dump() if validation_report else None)

    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"success": False, "error": str(e)}


@app.post("/api/extract-manual")
async def extract_manual(
    manual_file: Optional[UploadFile] = File(None),
    is_sample: Optional[str] = Form(None),
    sample_path: Optional[str] = Form(None),
    name: Optional[str] = Form(None),
    roll_number: Optional[str] = Form(None),
    section: Optional[str] = Form(None),
    department: Optional[str] = Form(None),
    instructor: Optional[str] = Form(None),
    include_instructor: Optional[str] = Form("false"),
    subject: Optional[str] = Form(None),
    custom_subject: Optional[str] = Form(None),
    include_logo: Optional[str] = Form("true"),
    logo_choice: Optional[str] = Form("dawood"),
    custom_logo: Optional[UploadFile] = File(None),
    session_id: Optional[str] = Form(None),
):
    """
    Step 1 -> Step 2 of Wizard:
    Extracts tasks, requirements, analysis questions, and viva questions from the manual
    WITHOUT executing them, returning structured data for student inspection and review.
    """
    sid = session_id or uuid.uuid4().hex[:12]
    session_dir = session_manager.get_session_dir(sid)
    session_manager.set_active_session_id(sid)

    try:
        sub_raw = (subject or "auto").strip().lower()
        if sub_raw == "other" and (not custom_subject or not custom_subject.strip()):
            return {
                "success": False,
                "error": "Please enter your custom Subject / Course name."
            }

        if sub_raw == "dbms":
            sub_clean = "dbms"
            course_name_val = "Database Management Systems (DBMS)"
        elif sub_raw == "dsa":
            sub_clean = "dsa"
            course_name_val = "Data Structures and Algorithms"
        elif sub_raw == "other":
            sub_clean = "other"
            course_name_val = custom_subject.strip()
        else:
            sub_clean = "auto"
            course_name_val = "Auto-Detect"

        cfg = Config.load()
        cfg.system.workspace_dir = str(session_dir)
        if department and department.strip():
            cfg.student.department = department.strip()
        elif not cfg.student.department:
            cfg.student.department = "Data Science"
        if name:
            cfg.student.name = name
        if roll_number:
            cfg.student.roll_number = roll_number
        if section:
            cfg.student.section = section

        is_logo_enabled = bool(include_logo and include_logo.lower() in ["true", "1", "yes", "on"])
        cfg.student.include_logo = is_logo_enabled
        cfg.student.logo_choice = logo_choice or "dawood"

        is_inst_enabled = bool(include_instructor and include_instructor.lower() in ["true", "1", "yes", "on"])
        cfg.student.include_instructor = is_inst_enabled
        if is_inst_enabled and instructor:
            cfg.student.instructor = instructor.strip()
        else:
            cfg.student.instructor = ""

        # Handle manual file saving
        if is_sample and is_sample.lower() == "true":
            if sample_path:
                cand = (BASE_DIR / sample_path).resolve() if not Path(sample_path).is_absolute() else Path(sample_path).resolve()
                if cand.is_relative_to(BASE_DIR.resolve()) and cand.exists():
                    target_manual_path = cand
                else:
                    target_manual_path = EXAMPLES_DIR / "Lab 03 manual.docx"
            else:
                target_manual_path = EXAMPLES_DIR / "Lab 03 manual.docx"
            if not target_manual_path.exists():
                target_manual_path = EXAMPLES_DIR / "sample_lab_manual.docx"
            if not target_manual_path.exists():
                from examples.generate_sample_manual import create_sample_manual
                create_sample_manual(target_manual_path)
        elif manual_file and manual_file.filename:
            safe_manual_name = Path(manual_file.filename).name
            manual_ext = Path(manual_file.filename).suffix.lower()
            if manual_ext not in [".docx", ".pdf", ".txt", ".md", ".doc"]:
                raise HTTPException(status_code=400, detail=f"Invalid manual file format '{manual_ext}'. Supported: .docx, .pdf, .txt, .md, .doc")
            target_manual_path = session_dir / safe_manual_name
            with open(target_manual_path, "wb") as buffer:
                shutil.copyfileobj(manual_file.file, buffer)
        else:
            raise HTTPException(status_code=400, detail="No manual file uploaded or selected.")

        # Parse Manual
        parser_subject = None if sub_clean == "auto" else sub_clean
        parser_course = None if course_name_val == "Auto-Detect" else course_name_val
        parser_obj = ManualParser(str(target_manual_path), subject=parser_subject, subject_name=parser_course)
        lab_manual = parser_obj.parse()
        if sub_clean == "auto":
            if lab_manual.course_name and any(k in lab_manual.course_name.lower() for k in ["database", "dbms", "sql"]):
                course_name_val = "Database Management Systems (DBMS)"
            elif lab_manual.course_name and any(k in lab_manual.course_name.lower() for k in ["data structure", "algorithm", "dsa"]):
                course_name_val = "Data Structures and Algorithms"
            else:
                course_name_val = lab_manual.course_name or "Computer Science Lab"
        lab_manual.course_name = course_name_val

        # Create session and requirements
        sess = session_manager.create_session(
            student_info=StudentInfo(
                name=cfg.student.name,
                roll_number=cfg.student.roll_number,
                section=cfg.student.section,
                department=cfg.student.department,
                university=cfg.student.university,
                semester=cfg.student.semester,
                instructor=cfg.student.instructor,
                include_instructor=cfg.student.include_instructor,
                include_logo=cfg.student.include_logo,
                logo_choice=cfg.student.logo_choice,
                custom_logo_path=cfg.student.custom_logo_path,
            ),
            manual_info=ManualInfo(
                file_path=str(target_manual_path),
                file_name=target_manual_path.name,
                title=lab_manual.title or "",
                course_name=lab_manual.course_name or "",
                lab_number=str(lab_manual.lab_number or ""),
                objectives=getattr(lab_manual, "objectives", []) or [],
                raw_text=getattr(lab_manual, "raw_text", "") or "",
                context=getattr(lab_manual, "context", "") or "",
                viva_questions=getattr(lab_manual, "viva_questions", []) or [],
                analysis_questions=getattr(lab_manual, "analysis_questions", []) or [],
                observation_tables=getattr(lab_manual, "observation_tables", []) or [],
            ),
            session_id=sid,
        )

        reqs = []
        for t in lab_manual.tasks:
            reqs.append(Requirement(
                id=f"task_{t.task_id}",
                task_id=t.task_id,
                type=RequirementType.TASK,
                title=t.title or f"Task {t.task_id}",
                description=t.description or "",
                language=t.language or "c",
                status=RequirementStatus.PENDING,
                sample_input=t.sample_input,
                expected_output=t.expected_output,
            ))
        for idx, q in enumerate(getattr(lab_manual, "analysis_questions", []) or [], 1):
            reqs.append(Requirement(
                id=f"analysis_{idx}",
                task_id=idx,
                type=RequirementType.ANALYSIS_QUESTION,
                title=f"Analysis Question {idx}",
                description=q,
                status=RequirementStatus.PENDING,
            ))
        for idx, q in enumerate(getattr(lab_manual, "viva_questions", []) or [], 1):
            reqs.append(Requirement(
                id=f"viva_{idx}",
                task_id=idx,
                type=RequirementType.VIVA_QUESTION,
                title=f"Viva Question {idx}",
                description=q,
                status=RequirementStatus.PENDING,
            ))
        sess.requirements = reqs
        session_manager.save_session(sess)

        # Store in live cache
        _set_session_data(sid, {
            "manual": lab_manual,
            "cfg": cfg,
            "target_manual_path": target_manual_path,
        })

        return {
            "success": True,
            "session_id": sid,
            "manual": {
                "title": _format_lab_title(lab_manual),
                "lab_number": lab_manual.lab_number,
                "course_name": lab_manual.course_name,
                "objectives": getattr(lab_manual, "objectives", []) or [],
                "tools": getattr(lab_manual, "tools", []) or [],
                "task_count": len(lab_manual.tasks),
                "analysis_count": len(getattr(lab_manual, "analysis_questions", []) or []),
                "viva_count": len(getattr(lab_manual, "viva_questions", []) or []),
            },
            "tasks": [
                {
                    "task_id": t.task_id,
                    "title": t.title,
                    "description": t.description,
                    "language": t.language,
                    "sample_input": t.sample_input,
                    "expected_output": t.expected_output,
                }
                for t in lab_manual.tasks
            ],
            "analysis_questions": [
                {"id": idx, "question": q}
                for idx, q in enumerate(getattr(lab_manual, "analysis_questions", []) or [], 1)
            ],
            "viva_questions": [
                {"id": idx, "question": q}
                for idx, q in enumerate(getattr(lab_manual, "viva_questions", []) or [], 1)
            ],
            "requirements": [r.model_dump() for r in sess.requirements],
        }

    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"success": False, "error": str(e)}


@app.post("/api/generate-from-session")
async def generate_from_session(payload: dict = Body(...)):
    """
    Step 3 of Wizard:
    Takes confirmed or edited requirements from a previously extracted session,
    executes orchestration, captures screenshots, and builds reports.
    """
    try:
        sid = payload.get("session_id")
        if not sid:
            raise HTTPException(status_code=400, detail="session_id is required")

        sess = session_manager.get_session(sid)
        if not sess:
            raise HTTPException(status_code=404, detail=f"Session {sid} not found")

        session_dir = session_manager.get_session_dir(sid)
        session_data = _get_active_session_data(sid) or {}
        lab_manual = session_data.get("manual")
        cfg = session_data.get("cfg") or Config.load()
        cfg.system.workspace_dir = str(session_dir)

        provider = payload.get("provider")
        api_key = payload.get("api_key")
        theme = payload.get("theme")
        instructions = payload.get("instructions") or ""
        formats = payload.get("formats") or "docx,pdf"

        if provider:
            if provider == "gemini-pro":
                cfg.ai.provider = "gemini"
                cfg.ai.model = "gemini-2.5-pro"
            elif provider == "gemini-flash":
                cfg.ai.provider = "gemini"
                cfg.ai.model = "gemini-2.5-flash"
            elif provider == "gemini-1.5-pro":
                cfg.ai.provider = "gemini"
                cfg.ai.model = "gemini-1.5-pro"
            elif provider in ["groq", "groq-llama-70b"]:
                cfg.ai.provider = "groq"
                cfg.ai.model = "llama-3.3-70b-versatile"
            elif provider == "groq-8b":
                cfg.ai.provider = "groq"
                cfg.ai.model = "llama-3.1-8b-instant"
            else:
                cfg.ai.provider = provider
        if api_key:
            cfg.ai.api_key = api_key
        if theme:
            if theme == "env_default":
                cfg.terminal.theme = get_theme().id
            else:
                cfg.terminal.theme = theme
        else:
            cfg.terminal.theme = get_theme().id

        # Graceful fallback to Smart Offline if Groq is requested without an API key
        if cfg.ai.provider == "groq" and not (cfg.ai.api_key or os.environ.get("GROQ_API_KEY")):
            cfg.ai.provider = "offline"

        if not lab_manual:
            file_path = sess.manual_info.file_path
            if file_path and Path(file_path).exists():
                parser_obj = ManualParser(file_path, subject_name=sess.manual_info.course_name)
                lab_manual = parser_obj.parse()
            else:
                raise HTTPException(status_code=400, detail="Lab manual data not found for session.")

        # Apply any task edits from review step
        if "tasks" in payload and isinstance(payload["tasks"], list):
            updated_tasks = []
            for t in payload["tasks"]:
                updated_tasks.append(LabTask(
                    task_id=int(t.get("task_id", len(updated_tasks) + 1)),
                    title=t.get("title", f"Task {len(updated_tasks) + 1}"),
                    description=t.get("description", ""),
                    language=t.get("language", "c"),
                    sample_input=t.get("sample_input"),
                    expected_output=t.get("expected_output"),
                ))
            lab_manual.tasks = updated_tasks

        # Apply any analysis question edits
        if "analysis_questions" in payload and isinstance(payload["analysis_questions"], list):
            lab_manual.analysis_questions = [
                q if isinstance(q, str) else q.get("question", "")
                for q in payload["analysis_questions"]
            ]

        # Update session requirements
        reqs = []
        for t in lab_manual.tasks:
            reqs.append(Requirement(
                id=f"task_{t.task_id}",
                task_id=t.task_id,
                type=RequirementType.TASK,
                title=t.title or f"Task {t.task_id}",
                description=t.description or "",
                language=t.language or "c",
                status=RequirementStatus.PENDING,
                sample_input=t.sample_input,
                expected_output=t.expected_output,
            ))
        for idx, q in enumerate(getattr(lab_manual, "analysis_questions", []) or [], 1):
            reqs.append(Requirement(
                id=f"analysis_{idx}",
                task_id=idx,
                type=RequirementType.ANALYSIS_QUESTION,
                title=f"Analysis Question {idx}",
                description=q,
                status=RequirementStatus.PENDING,
            ))
        for idx, q in enumerate(getattr(lab_manual, "viva_questions", []) or [], 1):
            reqs.append(Requirement(
                id=f"viva_{idx}",
                task_id=idx,
                type=RequirementType.VIVA_QUESTION,
                title=f"Viva Question {idx}",
                description=q,
                status=RequirementStatus.PENDING,
            ))
        sess.requirements = reqs
        session_manager.save_session(sess)

        # Modules
        provider_mode = "Smart Offline (Deterministic Rules)"
        if cfg.ai.provider == "gemini" and (cfg.ai.api_key or os.environ.get("GEMINI_API_KEY")):
            provider_mode = f"Google Gemini ({cfg.ai.model or '2.5-pro'})"
        elif cfg.ai.provider == "groq" and (cfg.ai.api_key or os.environ.get("GROQ_API_KEY")):
            provider_mode = f"Groq Cloud ({cfg.ai.model or 'llama-3.3-70b'})"
        elif cfg.ai.provider in ["openai", "openrouter"] and (cfg.ai.api_key or os.environ.get("OPENAI_API_KEY")):
            provider_mode = f"OpenAI ({cfg.ai.model or 'gpt-4o-mini'})"
        elif cfg.ai.provider == "ollama":
            provider_mode = f"Ollama ({cfg.ai.ollama_model})"
        lab_manual._provider_used = provider_mode
        lab_manual._custom_instructions = instructions.strip() if instructions else ""

        orchestrator = TaskOrchestrator(cfg)
        solutions, exec_results, validation_report = orchestrator.process_session(
            session=sess,
            manual=lab_manual,
            custom_instructions=instructions or "",
        )

        studio = ScreenshotStudio(cfg)
        builder = DocumentBuilder(cfg)
        sanitizer = DocumentSanitizer(cfg)

        screenshots = []
        for sol, res in zip(solutions, exec_results):
            code_img, out_img = studio.capture_task_screenshots(sol, res)
            screenshots.append((code_img, out_img))

        if getattr(lab_manual, "observation_tables", None):
            solver_tmp = TaskSolver(cfg)
            lab_manual.observation_tables = solver_tmp.populate_observation_tables(
                lab_manual.observation_tables,
                exec_results=exec_results
            )

        clean_lab = f"LAB{lab_manual.lab_number}_completed" if lab_manual.lab_number else "Completed_Lab_Report"

        compiled_files = _recompile_all_formats(
            builder, sanitizer, lab_manual, solutions, exec_results, screenshots, clean_lab, formats=formats or "docx,pdf"
        )

        session_data = {
            "manual": lab_manual,
            "solutions": solutions,
            "exec_results": exec_results,
            "screenshots": screenshots,
            "cfg": cfg,
            "clean_lab": clean_lab,
            "instructions": instructions,
        }
        _set_session_data(sid, session_data)

        sess.artifacts = SessionArtifacts(
            docx_path=str(OUTPUT_DIR / compiled_files["docx"]) if compiled_files.get("docx") else None,
            pdf_path=str(OUTPUT_DIR / compiled_files["pdf"]) if compiled_files.get("pdf") else None,
        )
        session_manager.save_session(sess)

        tasks_response = _build_tasks_response(lab_manual.tasks, solutions, exec_results, screenshots)

        return _build_lab_result_payload(compiled_files, lab_manual, tasks_response, cfg, session_id=sid, validation_report=validation_report.model_dump() if validation_report else None)

    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"success": False, "error": str(e)}


@app.post("/api/refine")
async def refine_lab(
    instruction: str = Form(...),
    task_id: Optional[str] = Form(None),
    session_id: Optional[str] = Form(None),
):
    """Refines existing solutions using user natural language instructions."""
    try:
        session_data = _get_active_session_data(session_id)
        if not session_data or "manual" not in session_data:
            raise HTTPException(status_code=400, detail="No active lab to refine. Please solve a lab first.")

        cfg = session_data["cfg"]
        lab_manual = session_data["manual"]
        solutions = session_data["solutions"]
        exec_results = session_data["exec_results"]
        screenshots = session_data["screenshots"]
        clean_lab = session_data["clean_lab"]
        sid = session_id or session_manager.get_active_session_id()

        solver = TaskSolver(cfg)
        runner = CodeRunner(cfg)
        studio = ScreenshotStudio(cfg)
        builder = DocumentBuilder(cfg)
        sanitizer = DocumentSanitizer(cfg)

        target_id = None
        if task_id and task_id.lower() not in ["all", "none", ""]:
            try:
                target_id = int(task_id)
            except ValueError:
                pass

        # Refine specific task or all tasks
        for idx, task in enumerate(lab_manual.tasks):
            if target_id is not None and task.task_id != target_id:
                continue

            current_sol = solutions[idx]
            refined_sol = solver.refine_solution(task, current_sol, instruction)
            solutions[idx] = refined_sol

            res = runner.execute(refined_sol, sample_input=task.sample_input)
            exec_results[idx] = res

            code_img, out_img = studio.capture_task_screenshots(refined_sol, res)
            screenshots[idx] = (code_img, out_img)

        # Recompile all formats
        compiled_files = _recompile_all_formats(
            builder, sanitizer, lab_manual, solutions, exec_results, screenshots, clean_lab
        )

        tasks_response = _build_tasks_response(lab_manual.tasks, solutions, exec_results, screenshots)

        return _build_lab_result_payload(compiled_files, lab_manual, tasks_response, cfg, session_id=sid, message="Successfully updated and re-executed with instructions!")
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"success": False, "error": str(e)}


@app.post("/api/edit-task")
async def edit_task(
    task_id: int = Form(...),
    code: str = Form(...),
    explanation: Optional[str] = Form(None),
    session_id: Optional[str] = Form(None),
):
    """Directly updates task source code / explanation, re-executes locally, and regenerates all formats."""
    try:
        session_data = _get_active_session_data(session_id)
        if not session_data or "manual" not in session_data:
            raise HTTPException(status_code=400, detail="No active lab found. Please solve a lab first.")

        cfg = session_data["cfg"]
        lab_manual = session_data["manual"]
        solutions = session_data["solutions"]
        exec_results = session_data["exec_results"]
        screenshots = session_data["screenshots"]
        clean_lab = session_data["clean_lab"]
        sid = session_id or session_manager.get_active_session_id()

        runner = CodeRunner(cfg)
        studio = ScreenshotStudio(cfg)
        builder = DocumentBuilder(cfg)
        sanitizer = DocumentSanitizer(cfg)

        task_idx = None
        for idx, t in enumerate(lab_manual.tasks):
            if t.task_id == task_id:
                task_idx = idx
                break

        if task_idx is None:
            raise HTTPException(status_code=404, detail=f"Task {task_id} not found.")

        task = lab_manual.tasks[task_idx]
        sol = solutions[task_idx]
        sol.code = code
        if explanation is not None:
            sol.explanation = explanation

        # Re-execute on laptop
        res = runner.execute(sol, sample_input=task.sample_input)
        exec_results[task_idx] = res

        # Capture authentic screenshots
        code_img, out_img = studio.capture_task_screenshots(sol, res)
        screenshots[task_idx] = (code_img, out_img)

        # Recompile all formats
        compiled_files = _recompile_all_formats(
            builder, sanitizer, lab_manual, solutions, exec_results, screenshots, clean_lab
        )

        tasks_response = _build_tasks_response(lab_manual.tasks, solutions, exec_results, screenshots)
        return _build_lab_result_payload(compiled_files, lab_manual, tasks_response, cfg, session_id=sid)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"success": False, "error": str(e)}


@app.post("/api/edit-cover")
async def edit_cover(
    name: Optional[str] = Form(None),
    roll_number: Optional[str] = Form(None),
    section: Optional[str] = Form(None),
    department: Optional[str] = Form(None),
    subject: Optional[str] = Form(None),
    lab_title: Optional[str] = Form(None),
    include_instructor: Optional[str] = Form("false"),
    instructor: Optional[str] = Form(None),
    include_logo: Optional[str] = Form(None),
    logo_choice: Optional[str] = Form(None),
    custom_logo: Optional[UploadFile] = File(None),
    session_id: Optional[str] = Form(None),
):
    """Directly updates cover page details and regenerates all document formats."""
    try:
        session_data = _get_active_session_data(session_id)
        if not session_data or "manual" not in session_data:
            raise HTTPException(status_code=400, detail="No active lab found. Please solve a lab first.")

        cfg = session_data["cfg"]
        lab_manual = session_data["manual"]
        solutions = session_data["solutions"]
        exec_results = session_data["exec_results"]
        screenshots = session_data["screenshots"]
        clean_lab = session_data["clean_lab"]
        sid = session_id or session_manager.get_active_session_id()

        if name:
            cfg.student.name = name.strip()
        if roll_number:
            cfg.student.roll_number = roll_number.strip()
        if section:
            cfg.student.section = section.strip()
        if department:
            cfg.student.department = department.strip()
        if subject:
            lab_manual.course_name = subject.strip()
        if lab_title:
            cleaned_title = lab_title.strip()
            import re
            m = re.search(r"lab\s*#?\s*(\d+)", cleaned_title, re.IGNORECASE)
            if m:
                try:
                    lab_manual.lab_number = int(m.group(1))
                except ValueError:
                    pass
            lab_manual.title = cleaned_title

        if include_logo is not None:
            cfg.student.include_logo = bool(include_logo.lower() in ["true", "1", "yes", "on"])
        if logo_choice is not None:
            cfg.student.logo_choice = logo_choice
        if custom_logo and custom_logo.filename:
            logo_ext = Path(custom_logo.filename).suffix or ".png"
            logo_save_path = UPLOADS_DIR / f"custom_logo{logo_ext}"
            with open(logo_save_path, "wb") as buf:
                shutil.copyfileobj(custom_logo.file, buf)
            cfg.student.custom_logo_path = str(logo_save_path)
            cfg.student.logo_choice = "custom"

        is_inst_enabled = bool(include_instructor and include_instructor.lower() in ["true", "1", "yes", "on"])
        cfg.student.include_instructor = is_inst_enabled
        if is_inst_enabled and instructor:
            cfg.student.instructor = instructor.strip()
        else:
            cfg.student.instructor = ""

        builder = DocumentBuilder(cfg)
        sanitizer = DocumentSanitizer(cfg)

        compiled_files = _recompile_all_formats(
            builder, sanitizer, lab_manual, solutions, exec_results, screenshots, clean_lab
        )

        tasks_response = _build_tasks_response(lab_manual.tasks, solutions, exec_results, screenshots)
        return _build_lab_result_payload(compiled_files, lab_manual, tasks_response, cfg, session_id=sid, message="Cover page updated and report recompiled successfully!")
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"success": False, "error": str(e)}


@app.post("/api/upload-logo")
async def upload_logo_file(logo_file: UploadFile = File(...)):
    """Uploads custom university logo and returns preview URL."""
    try:
        UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
        ext = Path(logo_file.filename).suffix.lower() if logo_file.filename else ".png"
        if ext not in [".png", ".jpg", ".jpeg", ".webp"]:
            return {"success": False, "error": "Invalid file format. Allowed formats: PNG, JPG, JPEG, WEBP."}
        target_path = UPLOADS_DIR / f"custom_logo{ext}"
        with open(target_path, "wb") as buf:
            shutil.copyfileobj(logo_file.file, buf)
        ts = int(time.time() * 1000)
        return {
            "success": True,
            "url": f"/uploads/custom_logo{ext}?t={ts}",
            "filename": f"custom_logo{ext}",
            "path": str(target_path),
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.get("/api/preview/pdf/{filename}")
async def preview_pdf(filename: str):
    """Streams PDF inline with appropriate headers for browser embedding."""
    safe_name = Path(filename).name
    file_path = (OUTPUT_DIR / safe_name).resolve()
    if not file_path.exists() or not file_path.is_file() or not file_path.is_relative_to(OUTPUT_DIR.resolve()):
        raise HTTPException(status_code=404, detail="PDF not found")
    return FileResponse(
        path=str(file_path),
        filename=safe_name,
        media_type="application/pdf",
        headers={"Content-Disposition": f'inline; filename="{safe_name}"'}
    )


@app.get("/api/preview/html/{filename}")
async def preview_html(filename: str):
    """Renders full standalone HTML report document."""
    safe_name = Path(filename).name
    file_path = (OUTPUT_DIR / safe_name).resolve()
    if not file_path.exists() or not file_path.is_file() or not file_path.is_relative_to(OUTPUT_DIR.resolve()) or file_path.suffix.lower() not in [".html", ".htm"]:
        raise HTTPException(status_code=404, detail="HTML report not found")
    return HTMLResponse(content=file_path.read_text(encoding="utf-8"))


@app.get("/api/current-lab")
async def get_current_lab(session_id: Optional[str] = None):
    """Returns currently loaded or completed lab report data for instant UI session recovery."""
    res = _get_last_result(session_id)
    if res and res.get("success"):
        return res
    return {"success": False, "message": "No active lab report found."}


@app.post("/api/close-lab")
async def close_lab(session_id: Optional[str] = Form(None)):
    """Closes the current active lab session, clearing state so the student can upload/create a new lab."""
    target_id = session_id or session_manager.get_active_session_id()
    if target_id:
        session_manager.delete_session(target_id)
    return {"success": True, "message": "Active lab session closed. Ready for new lab manual."}


@app.get("/api/sessions")
async def list_sessions():
    """Lists all active and recent lab sessions."""
    sessions = session_manager.list_sessions()
    return {"success": True, "sessions": sessions, "active_session_id": session_manager.get_active_session_id()}


@app.get("/api/sessions/{session_id}")
async def get_session_details(session_id: str):
    """Retrieves full serialized state for a given session."""
    sess = session_manager.get_session(session_id)
    if not sess:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
    last_res = session_manager.get_live_data(session_id, "last_result")
    return {"success": True, "session": sess.model_dump(), "last_result": last_res}


@app.post("/api/sessions/{session_id}/activate")
async def activate_session(session_id: str):
    """Sets a specific session as active."""
    sess = session_manager.get_session(session_id)
    if not sess:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
    session_manager.set_active_session_id(session_id)
    last_res = session_manager.get_live_data(session_id, "last_result")
    return {"success": True, "session_id": session_id, "last_result": last_res}


@app.delete("/api/sessions/{session_id}")
async def delete_session_endpoint(session_id: str):
    """Deletes a session and removes its workspace directory."""
    success = session_manager.delete_session(session_id)
    return {"success": success}


@app.post("/api/save-document-canvas")
async def save_document_canvas(payload: dict = Body(...)):
    """Receives inline edits made on the document canvas (like a text editor) and recompiles all formats."""
    try:
        session_id = payload.get("session_id")
        session_data = _get_active_session_data(session_id)
        if not session_data or "manual" not in session_data:
            raise HTTPException(status_code=400, detail="No active lab to update. Please solve a lab first.")

        cfg = session_data["cfg"]
        lab_manual = session_data["manual"]
        solutions = session_data["solutions"]
        exec_results = session_data["exec_results"]
        screenshots = session_data["screenshots"]
        clean_lab = session_data["clean_lab"]
        sid = session_id or session_manager.get_active_session_id()

        # 1. Update Cover metadata if present
        cover = payload.get("cover", {})
        if cover:
            if cover.get("name"):
                cfg.student.name = cover["name"].strip()
            if cover.get("roll_number"):
                cfg.student.roll_number = cover["roll_number"].strip()
            if cover.get("section"):
                cfg.student.section = cover["section"].strip()
            if cover.get("department"):
                cfg.student.department = cover["department"].strip()
            if cover.get("subject"):
                lab_manual.course_name = cover["subject"].strip()
            elif cover.get("course_name"):
                lab_manual.course_name = cover["course_name"].strip()
            if cover.get("lab_title"):
                lab_manual.title = cover["lab_title"].strip()
            is_inst = bool(cover.get("include_instructor"))
            cfg.student.include_instructor = is_inst
            if is_inst and cover.get("instructor"):
                cfg.student.instructor = cover["instructor"].strip()
            else:
                cfg.student.instructor = ""
            if "include_logo" in cover:
                cfg.student.include_logo = bool(cover["include_logo"])
            if "logo_choice" in cover:
                cfg.student.logo_choice = str(cover["logo_choice"])
            if "custom_logo_path" in cover and cover["custom_logo_path"]:
                cfg.student.custom_logo_path = str(cover["custom_logo_path"])

        # 2. Update Tasks (titles, descriptions, code, explanation, answers)
        tasks_data = payload.get("tasks", [])
        reexecute = bool(payload.get("reexecute", False))

        runner = CodeRunner(cfg) if reexecute else None
        studio = ScreenshotStudio(cfg) if reexecute else None

        for t_update in tasks_data:
            tid = t_update.get("task_id")
            for idx, task in enumerate(lab_manual.tasks):
                if task.task_id == tid:
                    if "title" in t_update and t_update["title"]:
                        task.title = t_update["title"].strip()
                    if "description" in t_update:
                        task.description = t_update["description"].strip()
                    if idx < len(solutions):
                        sol = solutions[idx]
                        if "code" in t_update and t_update["code"] is not None:
                            sol.code = t_update["code"]
                        if "explanation" in t_update and t_update["explanation"] is not None:
                            sol.explanation = t_update["explanation"]
                        if "answers" in t_update and isinstance(t_update["answers"], dict):
                            sol.discussion_answers = t_update["answers"]

                        if reexecute and runner and studio:
                            res = runner.execute(sol, sample_input=task.sample_input)
                            exec_results[idx] = res
                            c_img, o_img = studio.capture_task_screenshots(sol, res)
                            screenshots[idx] = (c_img, o_img)
                    break

        # 3. Update Analysis Answers & Observation Tables if present
        analysis_payload = payload.get("analysis_answers", [])
        if analysis_payload and isinstance(analysis_payload, list):
            lab_manual.analysis_answers = [
                (v.get("question", "").strip(), AntiAIFilter.humanize_answer(v.get("answer", "").strip()))
                for v in analysis_payload
                if isinstance(v, dict) and v.get("question")
            ]

        obs_payload = payload.get("observation_tables", [])
        if obs_payload and isinstance(obs_payload, list):
            lab_manual.observation_tables = obs_payload

        # 4. Update Viva Answers if present
        viva_payload = payload.get("viva_answers", [])
        if viva_payload and isinstance(viva_payload, list):
            lab_manual.viva_answers = [
                (v.get("question", "").strip(), AntiAIFilter.humanize_answer(v.get("answer", "").strip()))
                for v in viva_payload
                if isinstance(v, dict) and v.get("question")
            ]

        builder = DocumentBuilder(cfg)
        sanitizer = DocumentSanitizer(cfg)

        compiled_files = _recompile_all_formats(
            builder, sanitizer, lab_manual, solutions, exec_results, screenshots, clean_lab
        )

        tasks_response = _build_tasks_response(lab_manual.tasks, solutions, exec_results, screenshots)
        return _build_lab_result_payload(compiled_files, lab_manual, tasks_response, cfg, session_id=sid, message="All document edits saved and recompiled across all formats!")
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"success": False, "error": str(e)}


@app.post("/api/execute-scratchpad")
async def execute_scratchpad(payload: dict = Body(...)):
    """Executes arbitrary C, Python, or SQL code live in the in-browser scratchpad runner."""
    try:
        language = (payload.get("language") or "python").lower().strip()
        code = payload.get("code") or ""
        stdin_input = payload.get("stdin") or ""

        session_id = payload.get("session_id") or session_manager.get_active_session_id()
        if session_id:
            scratch_dir = session_manager.get_session_dir(session_id) / "scratchpad"
        else:
            scratch_dir = WORKSPACE_DIR / "scratchpad"
        scratch_dir.mkdir(parents=True, exist_ok=True)

        session_data = _get_active_session_data(session_id)
        cfg = session_data["cfg"] if session_data and "cfg" in session_data else Config.load()
        import time, subprocess, sys

        start_time = time.time()
        stdout = ""
        stderr = ""
        exit_code = 0

        if language in ["c", "cpp"]:
            fname = "scratch.c" if language == "c" else "scratch.cpp"
            fpath = scratch_dir / fname
            fpath.write_text(code, encoding="utf-8")
            bin_path = scratch_dir / "scratch_bin"

            compiler = "gcc" if language == "c" else "g++"
            comp = subprocess.run(
                [compiler, "-O2", "-o", str(bin_path), str(fpath), "-lm"],
                cwd=str(scratch_dir),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=15,
            )
            if comp.returncode != 0:
                duration = time.time() - start_time
                return {
                    "success": False,
                    "stdout": comp.stdout.decode("utf-8", errors="replace"),
                    "stderr": comp.stderr.decode("utf-8", errors="replace"),
                    "exit_code": comp.returncode,
                    "execution_time": round(duration, 3),
                }

            run = subprocess.run(
                [str(bin_path)],
                cwd=str(scratch_dir),
                input=stdin_input.encode("utf-8") if stdin_input else None,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=15,
            )
            stdout = run.stdout.decode("utf-8", errors="replace")
            stderr = run.stderr.decode("utf-8", errors="replace")
            exit_code = run.returncode

        elif language == "sql":
            fpath = scratch_dir / "scratch.sql"
            fpath.write_text(code, encoding="utf-8")
            shared_db = (WORKSPACE_DIR / "dbms_lab.db").resolve()
            py_bin = sys.executable
            student_name_val = str(cfg.student.name) if (cfg and cfg.student and cfg.student.name) else "Student"
            student_roll_val = str(cfg.student.roll_number) if (cfg and cfg.student and cfg.student.roll_number) else "001"
            run = subprocess.run(
                [
                    py_bin,
                    "-m",
                    "labgenius.sql_runner",
                    str(fpath),
                    "--db",
                    str(shared_db),
                    "--name",
                    student_name_val,
                    "--roll",
                    student_roll_val,
                ],
                cwd=str(BASE_DIR),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=15,
            )
            stdout = run.stdout.decode("utf-8", errors="replace")
            stderr = run.stderr.decode("utf-8", errors="replace")
            exit_code = run.returncode

        else: # Python
            fpath = scratch_dir / "scratch.py"
            fpath.write_text(code, encoding="utf-8")
            py_bin = sys.executable
            env = os.environ.copy()
            env["PYTHONPATH"] = str(BASE_DIR)
            run = subprocess.run(
                [py_bin, str(fpath)],
                cwd=str(scratch_dir),
                env=env,
                input=stdin_input.encode("utf-8") if stdin_input else None,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=20,
            )
            stdout = run.stdout.decode("utf-8", errors="replace")
            stderr = run.stderr.decode("utf-8", errors="replace")
            exit_code = run.returncode

        duration = time.time() - start_time
        ms = int(duration * 1000)
        return {
            "success": (exit_code == 0),
            "stdout": stdout.strip(),
            "stderr": stderr.strip(),
            "exit_code": exit_code,
            "execution_time": round(duration, 3),
            "execution_time_ms": ms,
        }
    except subprocess.TimeoutExpired:
        return {"success": False, "stdout": "", "stderr": "Execution timed out (20s limit).", "exit_code": 124, "execution_time": 20.0, "execution_time_ms": 20000}
    except Exception as e:
        return {"success": False, "stdout": "", "stderr": str(e), "exit_code": 1, "execution_time": 0.0, "execution_time_ms": 0}


@app.get("/api/download-bundle")
async def download_submission_bundle(session_id: Optional[str] = None):
    """Packages reports, source code files, and authentic screenshots into a 1-click submission ZIP."""
    import zipfile, io
    session_data = _get_active_session_data(session_id)
    if not session_data or "clean_lab" not in session_data:
        raise HTTPException(status_code=400, detail="No active lab to bundle. Please solve a lab first.")

    clean_lab = session_data["clean_lab"]
    cfg = session_data["cfg"]
    lab_manual = session_data["manual"]
    solutions = session_data["solutions"]
    screenshots = session_data["screenshots"]

    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        # 1. Reports folder
        for ext in [".docx", ".pdf", ".html", ".md"]:
            doc_file = OUTPUT_DIR / f"{clean_lab}{ext}"
            if doc_file.exists():
                zip_file.write(doc_file, arcname=f"reports/{doc_file.name}")

        # 2. Source Code folder
        for sol in solutions:
            lang_ext = ".py" if sol.language == "python" else ".c" if sol.language == "c" else ".sql"
            fname = sol.file_name or f"task_{sol.task_id:02d}{lang_ext}"
            zip_file.writestr(f"src/{fname}", sol.code)

        # 3. Screenshots folder
        for (code_img, out_img) in screenshots:
            if code_img and code_img.exists():
                zip_file.write(code_img, arcname=f"screenshots/{code_img.name}")
            if out_img and out_img.exists():
                zip_file.write(out_img, arcname=f"screenshots/{out_img.name}")

        # 4. Submission Info text file
        info_txt = (
            f"====================================================\n"
            f"LAB SUBMISSION PACKAGE\n"
            f"Student Name:   {cfg.student.name}\n"
            f"Roll Number:    {cfg.student.roll_number}\n"
            f"Section:        {cfg.student.section}\n"
            f"Department:     {cfg.student.department}\n"
            f"Lab Title:      Lab #{lab_manual.lab_number}: {lab_manual.title}\n"
            f"Course:         {lab_manual.course_name}\n"
            f"Total Tasks:    {len(lab_manual.tasks)}\n"
            f"Submission Zip: {clean_lab}_Submission.zip\n"
            f"====================================================\n"
        )
        zip_file.writestr("SUBMISSION_INFO.txt", info_txt)

    zip_buffer.seek(0)
    zip_name = f"{clean_lab}_Submission_Package.zip"
    zip_dest = OUTPUT_DIR / zip_name
    zip_dest.write_bytes(zip_buffer.getvalue())

    return FileResponse(
        path=str(zip_dest),
        filename=zip_name,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{zip_name}"'}
    )


@app.get("/api/templates")
async def get_academic_templates():
    """Returns rich starter code templates for common C, Python, and DSA university labs."""
    templates = [
        {
            "id": "py-dsa-bst",
            "name": "Python: Binary Search Tree (BST)",
            "category": "DSA in Python",
            "language": "python",
            "code": "class Node:\n    def __init__(self, val):\n        self.val = val\n        self.left = None\n        self.right = None\n\nclass BST:\n    def __init__(self):\n        self.root = None\n\n    def insert(self, val):\n        if not self.root:\n            self.root = Node(val)\n        else:\n            self._insert(self.root, val)\n\n    def _insert(self, node, val):\n        if val < node.val:\n            if not node.left: node.left = Node(val)\n            else: self._insert(node.left, val)\n        elif val > node.val:\n            if not node.right: node.right = Node(val)\n            else: self._insert(node.right, val)\n\n    def inorder(self, node, res=None):\n        if res is None: res = []\n        if node:\n            self.inorder(node.left, res)\n            res.append(node.val)\n            self.inorder(node.right, res)\n        return res\n\nb = BST()\nfor x in [45, 12, 78, 34, 56, 89]: b.insert(x)\nprint('[+] BST Inorder Traversal:', b.inorder(b.root))\n"
        },
        {
            "id": "py-dsa-linkedlist",
            "name": "Python: Singly Linked List",
            "category": "DSA in Python",
            "language": "python",
            "code": "class Node:\n    def __init__(self, data):\n        self.data = data\n        self.next = None\n\nclass LinkedList:\n    def __init__(self):\n        self.head = None\n\n    def append(self, val):\n        if not self.head:\n            self.head = Node(val)\n            return\n        curr = self.head\n        while curr.next: curr = curr.next\n        curr.next = Node(val)\n\n    def display(self):\n        elems, curr = [], self.head\n        while curr:\n            elems.append(str(curr.data))\n            curr = curr.next\n        return ' -> '.join(elems) + ' -> None'\n\nll = LinkedList()\nfor v in [10, 20, 30, 40]: ll.append(v)\nprint('[+] Linked List:', ll.display())\n"
        },
        {
            "id": "py-dsa-quicksort",
            "name": "Python: QuickSort (Divide & Conquer)",
            "category": "DSA in Python",
            "language": "python",
            "code": "def quicksort(arr):\n    if len(arr) <= 1: return arr\n    pivot = arr[len(arr) // 2]\n    left = [x for x in arr if x < pivot]\n    mid = [x for x in arr if x == pivot]\n    right = [x for x in arr if x > pivot]\n    return quicksort(left) + mid + quicksort(right)\n\ndata = [48, 12, 89, 34, 23, 76, 5]\nprint('[+] Original Array: ', data)\nprint('[+] QuickSorted Array:', quicksort(data))\n"
        },
        {
            "id": "c-pointers-malloc",
            "name": "C: Dynamic Memory & Pointers",
            "category": "C Programming",
            "language": "c",
            "code": "#include <stdio.h>\n#include <stdlib.h>\n\nint main() {\n    int n = 5;\n    int *arr = (int*)malloc(n * sizeof(int));\n    if (!arr) return 1;\n    printf(\"[+] Allocated dynamic array at memory %p\\n\", (void*)arr);\n    for (int i = 0; i < n; i++) arr[i] = (i + 1) * 10;\n    printf(\"[+] Values: \");\n    for (int i = 0; i < n; i++) printf(\"%d \", *(arr + i));\n    printf(\"\\n\");\n    free(arr);\n    printf(\"[+] Memory successfully deallocated.\\n\");\n    return 0;\n}\n"
        },
        {
            "id": "c-prime-numbers",
            "name": "C: Prime Numbers Generator (1-300)",
            "category": "C Programming",
            "language": "c",
            "code": "#include <stdio.h>\n\nint main() {\n    printf(\"=== Prime Numbers Between 1 and 300 ===\\n\");\n    int count = 0;\n    for (int i = 2; i <= 300; i++) {\n        int isPrime = 1;\n        for (int j = 2; j * j <= i; j++) {\n            if (i % j == 0) { isPrime = 0; break; }\n        }\n        if (isPrime) {\n            printf(\"%4d\", i);\n            count++;\n            if (count % 10 == 0) printf(\"\\n\");\n        }\n    }\n    printf(\"\\n\\n[+] Total Primes Found: %d\\n\", count);\n    return 0;\n}\n"
        }
    ]
    return {"templates": templates}


@app.get("/api/download/{filename}")
async def download_file(filename: str):
    safe_name = Path(filename).name
    file_path = (OUTPUT_DIR / safe_name).resolve()
    if not file_path.exists() or not file_path.is_file() or not file_path.is_relative_to(OUTPUT_DIR.resolve()):
        raise HTTPException(status_code=404, detail="File not found")

    ext = file_path.suffix.lower()
    media_map = {
        ".pdf": "application/pdf",
        ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ".md": "text/markdown",
        ".html": "text/html",
        ".zip": "application/zip",
        ".py": "text/x-python",
        ".c": "text/x-c",
        ".sql": "application/sql",
    }
    media_type = media_map.get(ext, "application/octet-stream")
    return FileResponse(
        path=str(file_path),
        filename=safe_name,
        media_type=media_type,
    )

# ==============================================================================
# Doc Tools API Endpoints (Multi-Document Merger, Converter, Splitter, Inspector)
# ==============================================================================

@app.post("/api/doc-tools/merge")
async def api_merge_documents(
    files: List[UploadFile] = File(...),
    order: Optional[str] = Form(None),
    export_format: str = Form("pdf"),
    filename: Optional[str] = Form(None),
    page_break: bool = Form(True),
):
    if not files:
        raise HTTPException(status_code=400, detail="No files uploaded for merging.")

    temp_dir = Path(tempfile.mkdtemp(prefix="labgen_upload_merge_"))
    try:
        saved_files_list = []
        for idx, upload in enumerate(files):
            orig_name = Path(upload.filename or f"doc_{idx}").name
            dest_path = temp_dir / f"{idx}_{orig_name}"
            with open(dest_path, "wb") as buf:
                shutil.copyfileobj(upload.file, buf)
            saved_files_list.append((orig_name, dest_path))

        # Determine file order
        ordered_paths = []
        if order:
            try:
                order_list = json.loads(order)
                if isinstance(order_list, list):
                    # Consume from available files matching the names in order
                    available = list(saved_files_list)
                    for target_name in order_list:
                        for entry in list(available):
                            if entry[0] == target_name:
                                ordered_paths.append(entry[1])
                                available.remove(entry)
                                break
                    # Any remaining files not matched
                    for _, rem_path in available:
                        ordered_paths.append(rem_path)
            except Exception as e:
                print("[-] Could not parse custom order json:", e)

        if not ordered_paths:
            ordered_paths = [p for _, p in saved_files_list]

        if not ordered_paths:
            raise HTTPException(status_code=400, detail="No valid documents found to merge.")

        ext_clean = export_format.strip().lower().lstrip(".")
        if ext_clean not in ["pdf", "docx"]:
            ext_clean = "pdf"

        # Sanitize filename
        clean_name = re.sub(r'[^a-zA-Z0-9_\- ]', '', (filename or "Merged_Document").strip())[:60]
        if not clean_name:
            clean_name = f"Merged_Document_{int(time.time())}"
        out_filename = f"{clean_name}.{ext_clean}"
        out_path = OUTPUT_DIR / out_filename

        # Execute merge
        result = doc_tools.merge_documents(
            input_files=ordered_paths,
            output_format=ext_clean,
            output_path=out_path,
            insert_page_break=page_break,
        )

        return {
            "success": True,
            "filename": out_filename,
            "download_url": f"/api/download/{out_filename}",
            "preview_url": f"/api/preview/pdf/{out_filename}" if ext_clean == "pdf" else None,
            "format": ext_clean,
            "size_formatted": result.get("size_formatted"),
            "page_count": result.get("page_count"),
            "paragraph_count": result.get("paragraph_count"),
            "file_count": len(ordered_paths),
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


@app.post("/api/doc-tools/convert")
async def api_convert_document(
    file: UploadFile = File(...),
    target_format: str = Form("pdf"),
):
    temp_dir = Path(tempfile.mkdtemp(prefix="labgen_upload_conv_"))
    try:
        safe_name = Path(file.filename or "doc").name
        dest_path = temp_dir / safe_name
        with open(dest_path, "wb") as buf:
            shutil.copyfileobj(file.file, buf)

        target_clean = target_format.strip().lower().lstrip(".")
        if target_clean not in ["pdf", "docx"]:
            target_clean = "pdf"

        out_filename = f"{Path(safe_name).stem}_converted.{target_clean}"
        out_path = OUTPUT_DIR / out_filename

        result = doc_tools.convert_document(dest_path, target_clean, out_path)
        return {
            "success": True,
            "filename": out_filename,
            "download_url": f"/api/download/{out_filename}",
            "preview_url": f"/api/preview/pdf/{out_filename}" if target_clean == "pdf" else None,
            "format": target_clean,
            "size_formatted": result.get("size_formatted"),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


@app.post("/api/doc-tools/extract-pages")
async def api_extract_pdf_pages(
    file: UploadFile = File(...),
    page_ranges: str = Form(...),
):
    temp_dir = Path(tempfile.mkdtemp(prefix="labgen_upload_extract_"))
    try:
        safe_name = Path(file.filename or "doc.pdf").name
        dest_path = temp_dir / safe_name
        with open(dest_path, "wb") as buf:
            shutil.copyfileobj(file.file, buf)

        clean_ranges = re.sub(r'[^0-9,\-]', '', page_ranges)[:40]
        stem_safe = Path(safe_name).stem[:40]
        out_filename = f"{stem_safe}_pages_{clean_ranges.replace(',', '_')}.pdf"
        out_path = OUTPUT_DIR / out_filename

        result = doc_tools.extract_pdf_pages(dest_path, page_ranges, out_path)
        return {
            "success": True,
            "filename": out_filename,
            "download_url": f"/api/download/{out_filename}",
            "preview_url": f"/api/preview/pdf/{out_filename}",
            "format": "pdf",
            "extracted_pages_count": result.get("extracted_pages_count"),
            "total_source_pages": result.get("total_source_pages"),
            "size_formatted": result.get("size_formatted"),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


@app.post("/api/doc-tools/inspect")
async def api_inspect_document(file: UploadFile = File(...)):
    temp_dir = Path(tempfile.mkdtemp(prefix="labgen_upload_inspect_"))
    try:
        safe_name = Path(file.filename or "doc").name
        dest_path = temp_dir / safe_name
        with open(dest_path, "wb") as buf:
            shutil.copyfileobj(file.file, buf)

        result = doc_tools.inspect_document(dest_path)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


@app.get("/api/doc-tools/sample-files")
async def api_get_doc_tools_sample_files():
    """
    Creates and returns URLs to 3 ready-to-test sample documents (PDF, DOCX, TXT) matching reference UI.
    """
    import docx as pydocx
    import subprocess
    sample_pdf = OUTPUT_DIR / "Data_Structures_Lab1.pdf"
    sample_docx = OUTPUT_DIR / "Algorithms_Notes.docx"
    sample_txt = OUTPUT_DIR / "Example_Code.txt"

    if not sample_docx.exists():
        d = pydocx.Document()
        d.add_heading("Algorithms & Data Structures: Laboratory Notes", level=1)
        d.add_paragraph("This is the introductory algorithmic notes section formatted in Word (.docx). It includes problem specifications, asymptotic complexity benchmarks, and core logic.")
        p = d.add_paragraph()
        p.add_run("Student Name: ").bold = True
        p.add_run("Bheesham Kumar Sajnani\n")
        p.add_run("Topic: ").bold = True
        p.add_run("Divide-and-Conquer Recurrence Relations")
        d.save(str(sample_docx))

    if not sample_pdf.exists():
        temp_docx = OUTPUT_DIR / "_temp_ds_lab.docx"
        d2 = pydocx.Document()
        d2.add_heading("Data Structures Lab 01: Tree Traversal Analysis", level=1)
        d2.add_paragraph("This is the primary laboratory manual component formatted as a standalone PDF report.")
        d2.add_paragraph("Terminal Query Benchmarks: execution time 0.042s, buffer hits 98.4%.")
        d2.save(str(temp_docx))
        subprocess.run(["libreoffice", "--headless", "--convert-to", "pdf", str(temp_docx), "--outdir", str(OUTPUT_DIR)], check=True)
        if (OUTPUT_DIR / "_temp_ds_lab.pdf").exists():
            (OUTPUT_DIR / "_temp_ds_lab.pdf").rename(sample_pdf)
        if temp_docx.exists():
            temp_docx.unlink()

    if not sample_txt.exists():
        with open(sample_txt, "w") as f_txt:
            f_txt.write("// Example Code: Binary Search Tree Implementation\n// Time Complexity: O(log N) average, O(N) worst\n\nfunction searchBST(root, val) {\n    if (!root || root.val === val) return root;\n    if (val < root.val) return searchBST(root.left, val);\n    return searchBST(root.right, val);\n}\n")

    return {
        "samples": [
            {
                "name": sample_pdf.name,
                "url": f"/api/download/{sample_pdf.name}",
                "type": "pdf",
                "size_formatted": doc_tools._format_size(os.path.getsize(sample_pdf)),
            },
            {
                "name": sample_docx.name,
                "url": f"/api/download/{sample_docx.name}",
                "type": "docx",
                "size_formatted": doc_tools._format_size(os.path.getsize(sample_docx)),
            },
            {
                "name": sample_txt.name,
                "url": f"/api/download/{sample_txt.name}",
                "type": "txt",
                "size_formatted": doc_tools._format_size(os.path.getsize(sample_txt)),
            }
        ]
    }


def start():
    uvicorn.run("web_app:app", host="127.0.0.1", port=8000, reload=False)


if __name__ == "__main__":
    start()
