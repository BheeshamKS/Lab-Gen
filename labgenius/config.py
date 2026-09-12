"""
Configuration loader for LabGenius.
Handles student profiles, system settings, AI providers, and document metadata.
"""

import os
import getpass
import socket
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Dict, Any
import yaml


@dataclass
class StudentProfile:
    name: str = "Bheesham Kumar Sajnani"
    roll_number: str = "25F-DS-020"
    department: str = "Data Science"
    university: str = "Department of Data Science & Computing"
    semester: str = "Spring 2026"
    instructor: str = "Rohail Shaikh"


@dataclass
class SystemSettings:
    username: str = field(default_factory=lambda: getpass.getuser())
    hostname: str = field(default_factory=lambda: socket.gethostname().split(".")[0])
    workspace_dir: str = "workspace"
    default_lab_path: str = "~/Labs"


@dataclass
class AISettings:
    provider: str = "gemini"  # 'gemini', 'openai', 'anthropic', 'ollama', 'mock'
    model: str = "gemini-2.5-pro"  # Google's flagship model: 'gemini-2.5-pro', 'gemini-2.5-flash', 'gemini-1.5-pro'
    api_key_env: str = "GEMINI_API_KEY"
    api_key: Optional[str] = None
    ollama_url: str = "http://localhost:11434"
    ollama_model: str = "qwen2.5-coder:7b"
    persona: str = "undergraduate_student"
    scrub_buzzwords: bool = True


@dataclass
class TerminalCaptureSettings:
    theme: str = "pop-os-dark"
    font_family: str = "Fira Mono, DejaVu Sans Mono, monospace"
    font_size: int = 13
    window_width: int = 820
    show_titlebar: bool = True
    include_cursor: bool = True
    watermark_roll_number: bool = False


@dataclass
class DocumentSettings:
    font_family: str = "Calibri"
    heading_font: str = "Calibri Light"
    code_font: str = "Consolas"
    realistic_editing_minutes: int = 85
    realistic_revisions: int = 6
    application_tag: str = "Microsoft Office Word"


@dataclass
class Config:
    student: StudentProfile = field(default_factory=StudentProfile)
    system: SystemSettings = field(default_factory=SystemSettings)
    ai: AISettings = field(default_factory=AISettings)
    terminal: TerminalCaptureSettings = field(default_factory=TerminalCaptureSettings)
    document: DocumentSettings = field(default_factory=DocumentSettings)

    @classmethod
    def load(cls, config_path: Optional[str] = None) -> "Config":
        """Load configuration from YAML file or defaults."""
        search_paths = [
            config_path,
            "config.yaml",
            Path(__file__).parent.parent / "config.yaml",
        ]
        loaded_data: Dict[str, Any] = {}

        for p in search_paths:
            if p and Path(p).exists():
                try:
                    with open(p, "r", encoding="utf-8") as f:
                        loaded_data = yaml.safe_load(f) or {}
                    break
                except Exception:
                    pass

        student_data = loaded_data.get("student", {})
        system_data = loaded_data.get("system", {})
        ai_data = loaded_data.get("ai", {})
        term_data = loaded_data.get("terminal_capture", {})
        doc_data = loaded_data.get("document", {})

        # Check API key from env if available
        api_key_env = ai_data.get("api_key_env", "GEMINI_API_KEY")
        env_key = os.environ.get(api_key_env) or os.environ.get("GEMINI_API_KEY")

        # If user has no API key set, fallback gracefully to mock/auto
        ai_provider = ai_data.get("provider", "mock")
        if ai_provider == "gemini" and not env_key:
            # If no key is set yet, we will notify and allow mock mode or direct input
            pass

        return cls(
            student=StudentProfile(
                name=student_data.get("name", "Bheesham Kumar Sajnani"),
                roll_number=student_data.get("roll_number", "25F-DS-020"),
                department=student_data.get("department", "Data Science"),
                university=student_data.get("university", "Department of Data Science & Computing"),
                semester=student_data.get("semester", "Spring 2026"),
                instructor=student_data.get("instructor", "Rohail Shaikh"),
            ),
            system=SystemSettings(
                username=system_data.get("username", getpass.getuser()),
                hostname=system_data.get("hostname", socket.gethostname().split(".")[0]),
                workspace_dir=system_data.get("workspace_dir", "workspace"),
                default_lab_path=system_data.get("default_lab_path", "~/Labs"),
            ),
            ai=AISettings(
                provider=ai_provider,
                model=ai_data.get("model", "gemini-2.5-flash"),
                api_key_env=api_key_env,
                api_key=env_key,
                ollama_url=ai_data.get("ollama_url", "http://localhost:11434"),
                ollama_model=ai_data.get("ollama_model", "qwen2.5-coder:7b"),
                persona=ai_data.get("persona", "undergraduate_student"),
                scrub_buzzwords=ai_data.get("scrub_buzzwords", True),
            ),
            terminal=TerminalCaptureSettings(
                theme=term_data.get("theme", "pop-os-dark"),
                font_family=term_data.get("font_family", "Fira Mono, DejaVu Sans Mono, monospace"),
                font_size=term_data.get("font_size", 13),
                window_width=term_data.get("window_width", 820),
                show_titlebar=term_data.get("show_titlebar", True),
                include_cursor=term_data.get("include_cursor", True),
                watermark_roll_number=term_data.get("watermark_roll_number", False),
            ),
            document=DocumentSettings(
                font_family=doc_data.get("font_family", "Calibri"),
                heading_font=doc_data.get("heading_font", "Calibri Light"),
                code_font=doc_data.get("code_font", "Consolas"),
                realistic_editing_minutes=doc_data.get("realistic_editing_minutes", 85),
                realistic_revisions=doc_data.get("realistic_revisions", 6),
                application_tag=doc_data.get("application_tag", "Microsoft Office Word"),
            ),
        )
