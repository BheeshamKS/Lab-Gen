"""
FastAPI Server & Web Application for LabGenius.
Provides a modern, interactive dashboard for lab completion, live screenshots, and report download.
"""

import os
import shutil
from pathlib import Path
from typing import Optional
import uvicorn
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
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

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
WORKSPACE_DIR.mkdir(parents=True, exist_ok=True)

# Mount static web files and workspace for live screenshot loading
app.mount("/static", StaticFiles(directory=str(WEB_DIR)), name="static")
app.mount("/workspace", StaticFiles(directory=str(WORKSPACE_DIR)), name="workspace")


@app.get("/", response_class=HTMLResponse)
async def serve_index():
    index_path = WEB_DIR / "index.html"
    if not index_path.exists():
        raise HTTPException(status_code=404, detail="Index file not found")
    with open(index_path, "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())


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


@app.post("/api/run")
async def run_lab(
    manual_file: Optional[UploadFile] = File(None),
    is_sample: Optional[str] = Form(None),
    sample_path: Optional[str] = Form(None),
    name: Optional[str] = Form(None),
    roll_number: Optional[str] = Form(None),
    department: Optional[str] = Form(None),
    instructor: Optional[str] = Form(None),
    provider: Optional[str] = Form(None),
    api_key: Optional[str] = Form(None),
    theme: Optional[str] = Form(None),
):
    try:
        # Load and configure
        cfg = Config.load()
        if name:
            cfg.student.name = name
        if roll_number:
            cfg.student.roll_number = roll_number
        if department:
            cfg.student.department = department
        if instructor:
            cfg.student.instructor = instructor
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
            else:
                cfg.ai.provider = provider
        if api_key:
            cfg.ai.api_key = api_key
        if theme:
            cfg.terminal.theme = theme

        # Save uploaded file or use sample
        upload_target_dir = BASE_DIR / "uploads"
        upload_target_dir.mkdir(parents=True, exist_ok=True)

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
        tasks_response = []

        # 3. Solve & Execute
        for task in lab_manual.tasks:
            sol = solver.solve_task(task)
            solutions.append(sol)

            res = runner.execute(sol, sample_input=task.sample_input)
            if not res.success and cfg.ai.provider != "mock":
                fixed = solver.auto_heal(task, sol.code, res.stderr)
                sol.code = fixed
                res = runner.execute(sol, sample_input=task.sample_input)

            exec_results.append(res)
            code_img, out_img = studio.capture_task_screenshots(sol, res)
            screenshots.append((code_img, out_img))

            # Web URLs for screenshots
            try:
                code_url = f"/{code_img.resolve().relative_to(BASE_DIR.resolve()).as_posix()}"
            except Exception:
                code_url = f"/workspace/task_{task.task_id:02d}/{code_img.name}"

            try:
                out_url = f"/{out_img.resolve().relative_to(BASE_DIR.resolve()).as_posix()}"
            except Exception:
                out_url = f"/workspace/task_{task.task_id:02d}/{out_img.name}"

            tasks_response.append({
                "task_id": task.task_id,
                "title": task.title,
                "description": task.description,
                "language": task.language,
                "code": sol.code,
                "explanation": sol.explanation,
                "answers": sol.discussion_answers,
                "code_screenshot_url": code_url,
                "output_screenshot_url": out_url,
                "screenshot_url": out_url,
                "success": res.success,
            })

        # 4. Build Document
        clean_lab = f"LAB{lab_manual.lab_number}_completed" if lab_manual.lab_number else "Completed_Lab_Report"
        out_doc_path = OUTPUT_DIR / f"{clean_lab}.docx"

        builder.build_report(lab_manual, solutions, exec_results, screenshots, out_doc_path)

        # 5. Sanitize
        sanitizer.sanitize_docx(out_doc_path)
        verification = sanitizer.verify_sanitization(out_doc_path)

        return {
            "success": True,
            "filename": out_doc_path.name,
            "tasks": tasks_response,
            "metadata": verification,
        }

    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"success": False, "error": str(e)}


@app.get("/api/download/{filename}")
async def download_file(filename: str):
    file_path = OUTPUT_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(
        path=str(file_path),
        filename=filename,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )


def start():
    uvicorn.run("web_app:app", host="127.0.0.1", port=8000, reload=False)


if __name__ == "__main__":
    start()
