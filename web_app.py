"""
FastAPI Server & Web Application for LabGenius.
Provides a modern, interactive dashboard for lab completion, live screenshots, and report download.
"""

import os
import time
import shutil
import json
from pathlib import Path
from typing import Optional
import uvicorn
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Body
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

from labgenius.config import Config
from labgenius.parser import ManualParser
from labgenius.solver import TaskSolver
from labgenius.runner import CodeRunner
from labgenius.capture import ScreenshotStudio
from labgenius.builder import DocumentBuilder
from labgenius.sanitizer import DocumentSanitizer

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


@app.get("/", response_class=HTMLResponse)
async def serve_index():
    index_path = WEB_DIR / "index.html"
    if not index_path.exists():
        raise HTTPException(status_code=404, detail="Index file not found")
    content = index_path.read_text(encoding="utf-8")
    if LAST_RESULT and LAST_RESULT.get("success"):
        hydration_script = f"<script>window.__INITIAL_LAB__ = {json.dumps(LAST_RESULT)};</script>"
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


# Active lab state for fast interactive edits and refinements
CURRENT_LAB = {}
LAST_RESULT = {}

def _set_last_result(res: dict) -> dict:
    global LAST_RESULT
    if res and res.get("success"):
        LAST_RESULT = res
    return res


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
            "code_screenshot_url": code_url or out_url,
            "output_screenshot_url": out_url or code_url,
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

    # 1. Build DOCX & Sanitize
    builder.build_report(lab_manual, solutions, exec_results, screenshots, out_doc_path)
    sanitizer.sanitize_docx(out_doc_path)
    verification = sanitizer.verify_sanitization(out_doc_path)

    # 2. Build PDF via LibreOffice
    pdf_res = None
    if not formats or "pdf" in formats.lower():
        pdf_res = builder.build_pdf(out_doc_path, out_pdf_path)

    return {
        "docx": out_doc_path.name,
        "pdf": out_pdf_path.name if (pdf_res and pdf_res.exists()) else None,
        "md": None,
        "html": None,
        "verification": verification,
    }


@app.post("/api/run")
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
    include_logo: Optional[str] = Form("true"),
    logo_choice: Optional[str] = Form("dawood"),
    custom_logo: Optional[UploadFile] = File(None),
):
    global LAST_RESULT, CURRENT_LAB
    # Clear previous lab state so UI doesn't pull old data if user refreshes mid-generation
    LAST_RESULT.clear()
    CURRENT_LAB.clear()
    
    # Clean workspace directory to avoid leftover screenshots
    if WORKSPACE_DIR.exists():
        import shutil
        shutil.rmtree(WORKSPACE_DIR)
    WORKSPACE_DIR.mkdir(parents=True, exist_ok=True)

    try:
        # Load and configure
        cfg = Config.load()
        if name:
            cfg.student.name = name
        if roll_number:
            cfg.student.roll_number = roll_number
        if section:
            cfg.student.section = section
        if department:
            cfg.student.department = department
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
            cfg.terminal.theme = theme

        upload_target_dir = BASE_DIR / "uploads"
        upload_target_dir.mkdir(parents=True, exist_ok=True)

        if custom_logo and custom_logo.filename:
            logo_ext = Path(custom_logo.filename).suffix or ".png"
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
            target_manual_path = Path(sample_path) if sample_path else (EXAMPLES_DIR / "sample_lab_manual.docx")
        elif manual_file:
            target_manual_path = upload_target_dir / manual_file.filename
            with open(target_manual_path, "wb") as buffer:
                shutil.copyfileobj(manual_file.file, buffer)
        else:
            raise HTTPException(status_code=400, detail="No manual file uploaded or selected.")

        # 1. Parse Manual
        parser_obj = ManualParser(str(target_manual_path))
        lab_manual = parser_obj.parse()

        # 2. Modules
        solver = TaskSolver(cfg)
        runner = CodeRunner(cfg)
        studio = ScreenshotStudio(cfg)
        builder = DocumentBuilder(cfg)
        sanitizer = DocumentSanitizer(cfg)

        solutions = []
        exec_results = []
        screenshots = []

        # 3. Solve & Execute (respecting custom instructions if provided)
        for task in lab_manual.tasks:
            sol = solver.solve_task(task, custom_instructions=instructions)
            solutions.append(sol)

            res = runner.execute(sol, sample_input=task.sample_input)
            if not res.success and cfg.ai.provider != "mock":
                fixed = solver.auto_heal(task, sol.code, res.stderr)
                sol.code = fixed
                res = runner.execute(sol, sample_input=task.sample_input)

            exec_results.append(res)
            code_img, out_img = studio.capture_task_screenshots(sol, res)
            screenshots.append((code_img, out_img))

        clean_lab = f"LAB{lab_manual.lab_number}_completed" if lab_manual.lab_number else "Completed_Lab_Report"

        # 4. Compile all formats (.docx, .pdf, .md, .html)
        compiled_files = _recompile_all_formats(
            builder, sanitizer, lab_manual, solutions, exec_results, screenshots, clean_lab
        )

        # 5. Store in-memory session for post-generation refinements
        CURRENT_LAB["manual"] = lab_manual
        CURRENT_LAB["solutions"] = solutions
        CURRENT_LAB["exec_results"] = exec_results
        CURRENT_LAB["screenshots"] = screenshots
        CURRENT_LAB["cfg"] = cfg
        CURRENT_LAB["clean_lab"] = clean_lab
        CURRENT_LAB["instructions"] = instructions

        tasks_response = _build_tasks_response(lab_manual.tasks, solutions, exec_results, screenshots)

        lab_title_val = _format_lab_title(lab_manual)
        course_name_val = lab_manual.course_name or cfg.student.department or "Data Science"

        return _set_last_result({
            "success": True,
            "filename": compiled_files["docx"],
            "pdf_filename": compiled_files["pdf"],
            "md_filename": compiled_files["md"],
            "html_filename": compiled_files["html"],
            "lab_title": lab_title_val,
            "course_name": course_name_val,
            "tasks": tasks_response,
            "metadata": compiled_files["verification"],
            "has_pdf": bool(compiled_files["pdf"]),
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"success": False, "error": str(e)}


@app.post("/api/refine")
async def refine_lab(
    instruction: str = Form(...),
    task_id: Optional[str] = Form(None),
):
    """Refines existing solutions using user natural language instructions."""
    try:
        if not CURRENT_LAB or "manual" not in CURRENT_LAB:
            raise HTTPException(status_code=400, detail="No active lab to refine. Please solve a lab first.")

        cfg = CURRENT_LAB["cfg"]
        lab_manual = CURRENT_LAB["manual"]
        solutions = CURRENT_LAB["solutions"]
        exec_results = CURRENT_LAB["exec_results"]
        screenshots = CURRENT_LAB["screenshots"]
        clean_lab = CURRENT_LAB["clean_lab"]

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

        lab_title_val = _format_lab_title(lab_manual)
        course_name_val = lab_manual.course_name or cfg.student.department or "Data Science"

        return _set_last_result({
            "success": True,
            "filename": compiled_files["docx"],
            "pdf_filename": compiled_files["pdf"],
            "md_filename": compiled_files["md"],
            "html_filename": compiled_files["html"],
            "lab_title": lab_title_val,
            "course_name": course_name_val,
            "tasks": tasks_response,
            "metadata": compiled_files["verification"],
            "has_pdf": bool(compiled_files["pdf"]),
            "message": f"Successfully updated and re-executed with instructions!",
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"success": False, "error": str(e)}


@app.post("/api/edit-task")
async def edit_task(
    task_id: int = Form(...),
    code: str = Form(...),
    explanation: Optional[str] = Form(None),
):
    """Directly updates task source code / explanation, re-executes locally, and regenerates all formats."""
    try:
        if not CURRENT_LAB or "manual" not in CURRENT_LAB:
            raise HTTPException(status_code=400, detail="No active lab found. Please solve a lab first.")

        cfg = CURRENT_LAB["cfg"]
        lab_manual = CURRENT_LAB["manual"]
        solutions = CURRENT_LAB["solutions"]
        exec_results = CURRENT_LAB["exec_results"]
        screenshots = CURRENT_LAB["screenshots"]
        clean_lab = CURRENT_LAB["clean_lab"]

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

        lab_title_val = _format_lab_title(lab_manual)
        course_name_val = lab_manual.course_name or cfg.student.department or "Data Science"

        return _set_last_result({
            "success": True,
            "filename": compiled_files["docx"],
            "pdf_filename": compiled_files["pdf"],
            "md_filename": compiled_files["md"],
            "html_filename": compiled_files["html"],
            "lab_title": lab_title_val,
            "course_name": course_name_val,
            "tasks": tasks_response,
            "metadata": compiled_files["verification"],
            "has_pdf": bool(compiled_files["pdf"]),
        })
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
    lab_title: Optional[str] = Form(None),
    include_instructor: Optional[str] = Form("false"),
    instructor: Optional[str] = Form(None),
    include_logo: Optional[str] = Form(None),
    logo_choice: Optional[str] = Form(None),
    custom_logo: Optional[UploadFile] = File(None),
):
    """Directly updates cover page details and regenerates all document formats."""
    try:
        if not CURRENT_LAB or "manual" not in CURRENT_LAB:
            raise HTTPException(status_code=400, detail="No active lab found. Please solve a lab first.")

        cfg = CURRENT_LAB["cfg"]
        lab_manual = CURRENT_LAB["manual"]
        solutions = CURRENT_LAB["solutions"]
        exec_results = CURRENT_LAB["exec_results"]
        screenshots = CURRENT_LAB["screenshots"]
        clean_lab = CURRENT_LAB["clean_lab"]

        if name:
            cfg.student.name = name.strip()
        if roll_number:
            cfg.student.roll_number = roll_number.strip()
        if section:
            cfg.student.section = section.strip()
        if department:
            cfg.student.department = department.strip()
            lab_manual.course_name = department.strip()
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

        lab_title_val = _format_lab_title(lab_manual)
        course_name_val = lab_manual.course_name or cfg.student.department or "Data Science"

        return _set_last_result({
            "success": True,
            "filename": compiled_files["docx"],
            "pdf_filename": compiled_files["pdf"],
            "md_filename": compiled_files["md"],
            "html_filename": compiled_files["html"],
            "lab_title": lab_title_val,
            "course_name": course_name_val,
            "tasks": tasks_response,
            "metadata": compiled_files["verification"],
            "has_pdf": bool(compiled_files["pdf"]),
            "message": "Cover page updated and report recompiled successfully!",
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"success": False, "error": str(e)}


@app.post("/api/upload-logo")
async def upload_logo_file(logo_file: UploadFile = File(...)):
    """Uploads custom university logo and returns preview URL."""
    try:
        UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
        ext = Path(logo_file.filename).suffix or ".png"
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
    file_path = OUTPUT_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="PDF not found")
    return FileResponse(
        path=str(file_path),
        filename=filename,
        media_type="application/pdf",
        headers={"Content-Disposition": f'inline; filename="{filename}"'}
    )


@app.get("/api/preview/html/{filename}")
async def preview_html(filename: str):
    """Renders full standalone HTML report document."""
    file_path = OUTPUT_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="HTML report not found")
    return HTMLResponse(content=file_path.read_text(encoding="utf-8"))


@app.get("/api/current-lab")
async def get_current_lab():
    """Returns currently loaded or completed lab report data for instant UI session recovery."""
    if LAST_RESULT and LAST_RESULT.get("success"):
        return LAST_RESULT
    return {"success": False, "message": "No active lab report found."}


@app.post("/api/close-lab")
async def close_lab():
    """Closes the current active lab session, clearing state so the student can upload/create a new lab."""
    global CURRENT_LAB, LAST_RESULT
    CURRENT_LAB.clear()
    LAST_RESULT.clear()
    return {"success": True, "message": "Active lab session closed. Ready for new lab manual."}


@app.post("/api/save-document-canvas")
async def save_document_canvas(payload: dict = Body(...)):
    """Receives inline edits made on the document canvas (like a text editor) and recompiles all formats."""
    try:
        if not CURRENT_LAB or "manual" not in CURRENT_LAB:
            raise HTTPException(status_code=400, detail="No active lab to update. Please solve a lab first.")

        cfg = CURRENT_LAB["cfg"]
        lab_manual = CURRENT_LAB["manual"]
        solutions = CURRENT_LAB["solutions"]
        exec_results = CURRENT_LAB["exec_results"]
        screenshots = CURRENT_LAB["screenshots"]
        clean_lab = CURRENT_LAB["clean_lab"]

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
                lab_manual.course_name = cover["department"].strip()
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

        builder = DocumentBuilder(cfg)
        sanitizer = DocumentSanitizer(cfg)

        compiled_files = _recompile_all_formats(
            builder, sanitizer, lab_manual, solutions, exec_results, screenshots, clean_lab
        )

        tasks_response = _build_tasks_response(lab_manual.tasks, solutions, exec_results, screenshots)
        lab_title_val = _format_lab_title(lab_manual)
        course_name_val = lab_manual.course_name or cfg.student.department or "Data Science"

        return _set_last_result({
            "success": True,
            "filename": compiled_files["docx"],
            "pdf_filename": compiled_files["pdf"],
            "md_filename": compiled_files["md"],
            "html_filename": compiled_files["html"],
            "lab_title": lab_title_val,
            "course_name": course_name_val,
            "tasks": tasks_response,
            "metadata": compiled_files["verification"],
            "has_pdf": bool(compiled_files["pdf"]),
            "message": "All document edits saved and recompiled across all formats!",
        })
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

        scratch_dir = WORKSPACE_DIR / "scratchpad"
        scratch_dir.mkdir(parents=True, exist_ok=True)

        cfg = CURRENT_LAB.get("cfg") if CURRENT_LAB else Config.load()
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
                f'{compiler} -O2 -o "{bin_path}" "{fpath}" -lm',
                shell=True,
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
                f'"{bin_path}"',
                shell=True,
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
            run = subprocess.run(
                f'"{py_bin}" -m labgenius.sql_runner "{fpath}" --db "{shared_db}" --name "{cfg.student.name}" --roll "{cfg.student.roll_number}"',
                shell=True,
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
                f'"{py_bin}" "{fpath}"',
                shell=True,
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
async def download_submission_bundle():
    """Packages reports, source code files, and authentic screenshots into a 1-click submission ZIP."""
    import zipfile, io
    if not CURRENT_LAB or "clean_lab" not in CURRENT_LAB:
        raise HTTPException(status_code=400, detail="No active lab to bundle. Please solve a lab first.")

    clean_lab = CURRENT_LAB["clean_lab"]
    cfg = CURRENT_LAB["cfg"]
    lab_manual = CURRENT_LAB["manual"]
    solutions = CURRENT_LAB["solutions"]
    screenshots = CURRENT_LAB["screenshots"]

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
    file_path = OUTPUT_DIR / filename
    if not file_path.exists():
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
        filename=filename,
        media_type=media_type,
    )


def start():
    uvicorn.run("web_app:app", host="127.0.0.1", port=8000, reload=False)


if __name__ == "__main__":
    start()
