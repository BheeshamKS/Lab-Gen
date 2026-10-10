"""
Session & State Isolation Module for LabGenius.
Provides strict Pydantic data models for Lab sessions, requirements, artifacts,
and a SessionManager backed by SQLite and per-session workspace directories.
"""

import json
import os
import shutil
import sqlite3
import threading
import time
import uuid
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from pydantic import BaseModel, Field


class RequirementType(str, Enum):
    TASK = "task"
    ANALYSIS_QUESTION = "analysis_question"
    VIVA_QUESTION = "viva_question"
    OBSERVATION_TABLE = "observation_table"
    THEORY = "theory"


class RequirementStatus(str, Enum):
    PENDING = "PENDING"
    EXTRACTED = "EXTRACTED"
    GENERATING = "GENERATING"
    GENERATED = "GENERATED"
    EXECUTING = "EXECUTING"
    VALIDATED = "VALIDATED"
    FAILED = "FAILED"


class Requirement(BaseModel):
    """Represents an atomic requirement extracted from the lab manual."""
    id: str = Field(description="Unique requirement ID (e.g., 'task_1', 'analysis_1')")
    task_id: Optional[int] = Field(default=None, description="Integer index if applicable")
    type: RequirementType = Field(default=RequirementType.TASK)
    title: str = Field(default="")
    description: str = Field(default="")
    language: str = Field(default="c")
    status: RequirementStatus = Field(default=RequirementStatus.PENDING)
    
    # Inputs & Expected
    instructions: str = Field(default="")
    sample_input: Optional[str] = None
    expected_output: Optional[str] = None
    requires_screenshot: bool = True
    requires_plot: bool = False
    
    # Generated code & explanation
    code: Optional[str] = None
    explanation: Optional[str] = None
    answers: Dict[str, str] = Field(default_factory=dict)
    
    # Execution outcomes
    stdout: Optional[str] = None
    stderr: Optional[str] = None
    exit_code: Optional[int] = None
    execution_time: Optional[float] = None
    
    # Visual assets
    code_screenshot_url: Optional[str] = None
    output_screenshot_url: Optional[str] = None
    
    # Validation
    validation_errors: List[str] = Field(default_factory=list)
    is_validated: bool = False


class StudentInfo(BaseModel):
    name: str = "Bheesham Kumar Sajnani"
    roll_number: str = "25F-DS-020"
    section: str = "25F-DS"
    department: str = "Data Science"
    university: str = "Dawood University of Engineering & Technology"
    semester: str = "Spring 2026"
    instructor: str = ""
    include_instructor: bool = False
    include_logo: bool = True
    logo_choice: str = "dawood"
    custom_logo_path: Optional[str] = None


class ManualInfo(BaseModel):
    file_path: Optional[str] = None
    file_name: Optional[str] = None
    title: str = ""
    course_name: str = ""
    lab_number: str = ""
    objectives: List[str] = Field(default_factory=list)
    raw_text: str = ""
    context: str = ""
    is_docx_template: bool = False
    viva_questions: List[str] = Field(default_factory=list)
    analysis_questions: List[str] = Field(default_factory=list)
    observation_tables: List[Dict[str, Any]] = Field(default_factory=list)


class SessionArtifacts(BaseModel):
    docx_path: Optional[str] = None
    docx_filename: Optional[str] = None
    docx_url: Optional[str] = None
    pdf_path: Optional[str] = None
    pdf_filename: Optional[str] = None
    pdf_url: Optional[str] = None
    md_filename: Optional[str] = None
    html_filename: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class LabSession(BaseModel):
    """Complete, self-contained state of a single lab generation session."""
    session_id: str = Field(default_factory=lambda: uuid.uuid4().hex[:12])
    created_at: float = Field(default_factory=time.time)
    updated_at: float = Field(default_factory=time.time)
    status: str = Field(default="created")  # created, parsing, extracted, generating, executed, completed, error
    
    student: StudentInfo = Field(default_factory=StudentInfo)
    manual: ManualInfo = Field(default_factory=ManualInfo)
    requirements: List[Requirement] = Field(default_factory=list)
    artifacts: SessionArtifacts = Field(default_factory=SessionArtifacts)
    
    provider_used: str = "offline"
    custom_instructions: str = ""
    error_message: Optional[str] = None
    extra_data: Dict[str, Any] = Field(default_factory=dict)

    def get_task_requirement(self, task_id: int) -> Optional[Requirement]:
        for req in self.requirements:
            if req.type == RequirementType.TASK and req.task_id == task_id:
                return req
        return None

    def update_timestamp(self) -> None:
        self.updated_at = time.time()


class SessionManager:
    """
    Thread-safe manager for LabSessions.
    Stores metadata in a lightweight SQLite index and maintains isolated
    directories under workspace/{session_id}/.
    """

    def __init__(self, workspace_root: Optional[Union[str, Path]] = None):
        if workspace_root is None:
            base_dir = Path(__file__).resolve().parent.parent
            self.workspace_root = (base_dir / "workspace").resolve()
        else:
            self.workspace_root = Path(workspace_root).resolve()

        self.workspace_root.mkdir(parents=True, exist_ok=True)
        self.db_path = self.workspace_root / "sessions.db"
        self._lock = threading.Lock()
        self._active_session_id: Optional[str] = None
        
        # Memory storage for runtime live objects (manual, solutions, runner instances, etc.)
        self._live_objects: Dict[str, Dict[str, Any]] = {}

        self._init_db()

    def _init_db(self) -> None:
        with self._lock:
            conn = sqlite3.connect(str(self.db_path))
            try:
                cursor = conn.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS sessions (
                        session_id TEXT PRIMARY KEY,
                        created_at REAL,
                        updated_at REAL,
                        status TEXT,
                        lab_title TEXT,
                        course_name TEXT,
                        student_name TEXT,
                        file_name TEXT,
                        provider TEXT,
                        json_path TEXT
                    )
                """)
                conn.commit()
            finally:
                conn.close()

    def get_session_dir(self, session_id: str) -> Path:
        """Returns the isolated workspace directory for the session."""
        session_dir = self.workspace_root / session_id
        session_dir.mkdir(parents=True, exist_ok=True)
        return session_dir

    def create_session(
        self,
        student_info: Optional[StudentInfo] = None,
        manual_info: Optional[ManualInfo] = None,
        session_id: Optional[str] = None,
    ) -> LabSession:
        sid = session_id or uuid.uuid4().hex[:12]
        session = LabSession(
            session_id=sid,
            student=student_info or StudentInfo(),
            manual=manual_info or ManualInfo(),
        )
        self.save_session(session)
        self.set_active_session_id(sid)
        return session

    def save_session(
        self,
        session: LabSession,
        live_data: Optional[Dict[str, Any]] = None,
    ) -> None:
        session.update_timestamp()
        s_dir = self.get_session_dir(session.session_id)
        json_file = s_dir / "session.json"

        # Write to JSON file
        with open(json_file, "w", encoding="utf-8") as f:
            f.write(session.model_dump_json(indent=2))

        # Store live runtime objects if provided
        with self._lock:
            if session.session_id not in self._live_objects:
                self._live_objects[session.session_id] = {}
            if live_data:
                self._live_objects[session.session_id].update(live_data)

            # Update SQLite index
            conn = sqlite3.connect(str(self.db_path))
            try:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO sessions (
                        session_id, created_at, updated_at, status,
                        lab_title, course_name, student_name, file_name, provider, json_path
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(session_id) DO UPDATE SET
                        updated_at = excluded.updated_at,
                        status = excluded.status,
                        lab_title = excluded.lab_title,
                        course_name = excluded.course_name,
                        student_name = excluded.student_name,
                        file_name = excluded.file_name,
                        provider = excluded.provider,
                        json_path = excluded.json_path
                """, (
                    session.session_id,
                    session.created_at,
                    session.updated_at,
                    session.status,
                    session.manual.title or "",
                    session.manual.course_name or "",
                    session.student.name or "",
                    session.manual.file_name or "",
                    session.provider_used or "offline",
                    str(json_file),
                ))
                conn.commit()
            finally:
                conn.close()

    def get_session(self, session_id: Optional[str] = None) -> Optional[LabSession]:
        target_id = session_id or self._active_session_id
        if not target_id:
            return None

        # Check file first
        s_dir = self.workspace_root / target_id
        json_file = s_dir / "session.json"
        if json_file.exists():
            try:
                with open(json_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                return LabSession.model_validate(data)
            except Exception:
                pass

        # Fallback to query SQLite
        with self._lock:
            conn = sqlite3.connect(str(self.db_path))
            try:
                cursor = conn.cursor()
                cursor.execute("SELECT json_path FROM sessions WHERE session_id = ?", (target_id,))
                row = cursor.fetchone()
                if row and row[0] and Path(row[0]).exists():
                    with open(row[0], "r", encoding="utf-8") as f:
                        data = json.load(f)
                    return LabSession.model_validate(data)
            finally:
                conn.close()

        return None

    def set_active_session_id(self, session_id: str) -> None:
        self._active_session_id = session_id

    def get_active_session_id(self) -> Optional[str]:
        return self._active_session_id

    def get_active_session(self) -> Optional[LabSession]:
        return self.get_session(self._active_session_id)

    def set_live_data(self, session_id: str, key: str, value: Any) -> None:
        with self._lock:
            if session_id not in self._live_objects:
                self._live_objects[session_id] = {}
            self._live_objects[session_id][key] = value

    def get_live_data(self, session_id: Optional[str], key: str, default: Any = None) -> Any:
        target_id = session_id or self._active_session_id
        if not target_id:
            return default
        with self._lock:
            return self._live_objects.get(target_id, {}).get(key, default)

    def list_sessions(self, limit: int = 50) -> List[Dict[str, Any]]:
        with self._lock:
            conn = sqlite3.connect(str(self.db_path))
            conn.row_factory = sqlite3.Row
            try:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT session_id, created_at, updated_at, status,
                           lab_title, course_name, student_name, file_name, provider
                    FROM sessions ORDER BY updated_at DESC LIMIT ?
                """, (limit,))
                rows = cursor.fetchall()
                return [dict(r) for r in rows]
            finally:
                conn.close()

    def delete_session(self, session_id: str) -> bool:
        with self._lock:
            if session_id in self._live_objects:
                del self._live_objects[session_id]
            if self._active_session_id == session_id:
                self._active_session_id = None

            s_dir = self.workspace_root / session_id
            if s_dir.exists():
                shutil.rmtree(s_dir, ignore_errors=True)

            conn = sqlite3.connect(str(self.db_path))
            try:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM sessions WHERE session_id = ?", (session_id,))
                conn.commit()
            finally:
                conn.close()

        return True


# Global default instance for convenience
default_session_manager = SessionManager()
