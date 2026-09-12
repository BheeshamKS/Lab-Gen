"""
Lab Manual Parser for LabGenius.
Isolates assigned lab tasks from theory notes, extracts table patterns, and detects lab metadata.
"""

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Dict, Any

try:
    import docx
except ImportError:
    docx = None

try:
    import pypdf
except ImportError:
    pypdf = None


@dataclass
class LabTask:
    task_id: int
    title: str
    description: str
    language: str = "c"  # 'c', 'cpp', 'python', 'bash', 'sql'
    instructions: str = ""
    sample_input: Optional[str] = None
    expected_output: Optional[str] = None
    requires_screenshot: bool = True
    requires_plot: bool = False
    discussion_questions: List[str] = field(default_factory=list)


@dataclass
class LabManual:
    file_path: Path
    title: str
    course_name: str
    lab_number: str
    objectives: List[str] = field(default_factory=list)
    tasks: List[LabTask] = field(default_factory=list)
    raw_text: str = ""
    is_docx_template: bool = False


class ManualParser:
    """Parses DOCX and PDF lab manuals, strictly isolating assigned lab tasks from theory."""

    TASK_SECTION_MARKERS = [
        r"^(?:lab\s+)?tasks?[\s:]*$",
        r"lab\s+tasks?:",
        r"^(?:lab\s+)?exercises?[\s:]*$",
        r"^(?:lab\s+)?assignments?[\s:]*$",
        r"^(?:lab\s+)?activities?[\s:]*$",
        r"^(?:practice\s+)?problems?[\s:]*$",
        r"programs\s+to\s+implement[\s:]*$",
    ]

    END_SECTION_MARKERS = [
        r"^learning\s+outcomes?[\s:]*$",
        r"^conclusion[\s:]*$",
        r"^references?[\s:]*$",
        r"^marking\s+rubric[\s:]*$",
        r"^viva\s+questions?[\s:]*$",
    ]

    LANGUAGE_KEYWORDS = {
        "c": ["in c language", "dev c++", "dev-c++", "c program", "gcc", "#include <stdio.h>", "printf", ".c "],
        "cpp": ["c++", "cpp", "g++", "#include <iostream>", "std::cout", ".cpp"],
        "python": ["python", "python3", "def ", "import numpy", "import pandas", ".py"],
        "bash": ["bash", "shell script", "linux command", "grep", "awk", "#!/bin/bash"],
        "sql": ["sql", "select ", "insert into", "database", "sqlite", "table"],
    }

    def __init__(self, file_path: str):
        self.path = Path(file_path)
        if not self.path.exists():
            raise FileNotFoundError(f"Manual file not found: {self.path}")

    def parse(self) -> LabManual:
        """Parse the lab manual based on file extension."""
        suffix = self.path.suffix.lower()
        if suffix == ".docx":
            return self._parse_docx()
        elif suffix == ".pdf":
            return self._parse_pdf()
        elif suffix in [".txt", ".md"]:
            return self._parse_text()
        else:
            raise ValueError(f"Unsupported file format: {suffix}. Supported: .docx, .pdf, .txt, .md")

    def _detect_overall_language(self, text: str) -> str:
        text_lower = text.lower()
        if any(k in text_lower for k in [
            "sql", "sql server", "database", "create table", "alter table",
            "drop table", "select ", "insert into", "primary key", "foreign key",
            "truncate table", "dbms", "queries", "table_name"
        ]):
            return "sql"
        if any(k in text_lower for k in ["in c language", "dev c++", "dev-c++", "#include <stdio.h>", "stdio.h"]):
            return "c"
        if any(k in text_lower for k in ["c++", "cpp", "iostream"]):
            return "cpp"
        if any(k in text_lower for k in ["python", "pandas", "numpy"]):
            return "python"
        if any(k in text_lower for k in ["bash", "shell script", "linux command"]):
            return "bash"
        return "c"  # Default for programming fundamentals labs

    def _parse_docx(self) -> LabManual:
        if not docx:
            raise ImportError("python-docx is required to parse .docx files")

        doc = docx.Document(self.path)
        paragraphs_text = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
        full_text = "\n".join(paragraphs_text)
        overall_lang = self._detect_overall_language(full_text)

        # 1. Detect Lab Number and Title
        lab_number = "01"
        title = "LAB REPORT"

        # Check filename first
        m_fn = re.search(r"(?:lab|experiment)\s*#?\s*([0-9]+)", self.path.stem, re.IGNORECASE)
        if m_fn:
            lab_number = m_fn.group(1).zfill(2)

        # Check first 15 paragraphs for Lab/Experiment number and title
        for i, p in enumerate(paragraphs_text[:15]):
            m = re.search(r"(?:lab|experiment)\s*#?\s*([0-9]+)", p, re.IGNORECASE)
            if m:
                lab_number = m.group(1).zfill(2)
                after = re.sub(r"(?:lab|experiment)\s*#?\s*[0-9]+[\s:\.-]*", "", p, flags=re.IGNORECASE).strip()
                if len(after) > 3:
                    title = after
                elif i + 1 < len(paragraphs_text):
                    next_p = paragraphs_text[i + 1].strip()
                    if not any(next_p.lower().startswith(x) for x in ["objective", "theory", "date", "roll", "name"]):
                        title = next_p
                break

        # Clean title boilerplate
        title = re.sub(r"\s+in\s+c\s+language.*", "", title, flags=re.IGNORECASE).strip()
        title = re.sub(r"\s+in\s+c\+\+.*", "", title, flags=re.IGNORECASE).strip()
        title = re.sub(r"\s+in\s+python.*", "", title, flags=re.IGNORECASE).strip()
        title = title.rstrip(".:, -").upper()

        # Course name detection
        if overall_lang == "sql" or "dbms" in self.path.stem.lower() or "database" in full_text.lower()[:300]:
            course_name = "Database Management Systems (DBMS)"
        else:
            course_name = "Programming / Data Science"
            for p in paragraphs_text[:15]:
                if any(k in p.lower() for k in ["course", "subject", "data science", "computer science"]):
                    course_name = p.replace("Course:", "").strip()
                    break

        # 2. Find and Extract ONLY the Task Section
        tasks = self._extract_tasks_from_docx_body(doc, overall_lang)

        return LabManual(
            file_path=self.path,
            title=title,
            course_name=course_name,
            lab_number=lab_number,
            objectives=[],
            tasks=tasks,
            raw_text=full_text,
            is_docx_template=False,
        )

    def _extract_tasks_from_docx_body(self, doc: docx.Document, default_lang: str) -> List[LabTask]:
        """Traverses document body in order to extract tasks and attach any trailing tables."""
        tasks: List[LabTask] = []
        in_task_section = False
        current_task_num = 0
        current_task_lines: List[str] = []

        imperatives = [
            "create", "display", "add", "delete", "change", "drop", "write", "implement",
            "query", "find", "calculate", "design", "update", "select", "insert", "execute",
            "verify", "show", "truncate", "enforce", "alter", "modify"
        ]
        intro_starters = [
            "perform the following", "follow the instructions", "note:", "instructions:", "guidelines:"
        ]

        def save_current_task():
            nonlocal current_task_num, current_task_lines
            if current_task_num > 0 and current_task_lines:
                desc = "\n".join(current_task_lines).strip()
                first_line = current_task_lines[0].strip()
                title = f"Task {current_task_num}: {first_line[:60]}" if len(first_line) > 60 else f"Task {current_task_num}: {first_line}"
                tasks.append(
                    LabTask(
                        task_id=current_task_num,
                        title=title,
                        description=desc,
                        language=default_lang,
                    )
                )
            current_task_lines = []

        for el in doc.element.body:
            tag = el.tag.split("}")[-1]

            if tag == "p":
                p = docx.text.paragraph.Paragraph(el, doc)
                p_text = p.text.strip()
                if not p_text:
                    continue

                # Check for Task Section Start
                if not in_task_section:
                    for marker in self.TASK_SECTION_MARKERS:
                        if re.search(marker, p_text, re.IGNORECASE):
                            in_task_section = True
                            after_colon = re.sub(marker, "", p_text, flags=re.IGNORECASE).strip()
                            p_text = after_colon
                            break
                    if not in_task_section or not p_text:
                        continue

                # Check for End Section Marker
                for end_marker in self.END_SECTION_MARKERS:
                    if re.search(end_marker, p_text, re.IGNORECASE):
                        save_current_task()
                        return tasks

                # Skip section intro sentences (e.g. "Perform the following tasks in SQL Server:")
                if any(p_text.lower().startswith(intro) for intro in intro_starters):
                    continue

                # Case A: Explicit Numbered task (e.g. "1-", "1.", "Task 1:", "2-")
                task_match = re.match(r"^(?:task|exercise|program|query|question)?\s*#?\s*([0-9]+)\s*[-:\.]\s*(.*)", p_text, re.IGNORECASE)
                if task_match:
                    save_current_task()
                    current_task_num = int(task_match.group(1))
                    rest = task_match.group(2).strip()
                    current_task_lines = [rest] if rest else []
                    continue

                # Case B: Bullet items (e.g. •, -, *)
                m_bullet = re.match(r"^[\u2022\-\*]\s*(.*)", p_text)
                if m_bullet:
                    save_current_task()
                    current_task_num += 1
                    current_task_lines = [m_bullet.group(1).strip()]
                    continue

                # Case C: Unnumbered action items starting with an imperative verb
                first_word = p_text.split()[0].lower().rstrip(":,.-") if p_text.split() else ""
                if first_word in imperatives:
                    save_current_task()
                    current_task_num += 1
                    current_task_lines = [p_text]
                elif current_task_num > 0:
                    current_task_lines.append(p_text)

            elif tag == "tbl" and in_task_section and current_task_num > 0:
                # If a table appears immediately in a task (e.g. Pascal triangle, matrix, pattern)
                tbl = docx.table.Table(el, doc)
                table_lines = []
                for row in tbl.rows:
                    row_cells = [cell.text.strip() for cell in row.cells]
                    row_str = "  ".join(c for c in row_cells if c)
                    if row_str:
                        table_lines.append(row_str)
                if table_lines:
                    current_task_lines.append("\nOutput Pattern Table / Expected Output:")
                    current_task_lines.extend(table_lines)

        save_current_task()

        # Fallback if no task section was found with markers
        if not tasks:
            tasks = self._fallback_extract_tasks(doc, default_lang)

        return tasks

    def _fallback_extract_tasks(self, doc: docx.Document, default_lang: str) -> List[LabTask]:
        """Fallback if no explicit 'LAB TASKS:' heading exists."""
        tasks = []
        paragraphs = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
        for p in paragraphs:
            m = re.match(r"^(?:task|exercise|program|question)\s*#?\s*([0-9]+)[\s:\.-]+(.*)", p, re.IGNORECASE)
            if m:
                t_num = int(m.group(1))
                desc = m.group(2).strip()
                tasks.append(LabTask(task_id=t_num, title=f"Task {t_num}", description=desc, language=default_lang))

        if not tasks and paragraphs:
            tasks = [LabTask(task_id=1, title="Task 1", description="\n".join(paragraphs[-5:]), language=default_lang)]
        return tasks

    def _parse_pdf(self) -> LabManual:
        if not pypdf:
            raise ImportError("pypdf is required to parse .pdf files")

        reader = pypdf.PdfReader(self.path)
        full_text = "\n".join(page.extract_text() or "" for page in reader.pages)
        overall_lang = self._detect_overall_language(full_text)

        # Detect Title & Number
        lab_number = "01"
        title = "LAB REPORT"
        m = re.search(r"lab\s*#?\s*([0-9]+)\s*:\s*([^.\n\r]+)", full_text, re.IGNORECASE)
        if m:
            lab_number = m.group(1).zfill(2)
            raw_t = m.group(2).strip()
            raw_t = re.sub(r"\s+in\s+c\s+language.*", "", raw_t, flags=re.IGNORECASE).strip()
            title = raw_t.upper()

        tasks = []
        lines = full_text.splitlines()
        in_tasks = False
        current_task_num = 0
        current_lines: List[str] = []

        for line in lines:
            line_str = line.strip()
            if not in_tasks:
                for marker in self.TASK_SECTION_MARKERS:
                    if re.search(marker, line_str, re.IGNORECASE):
                        in_tasks = True
                        break
                continue

            for end_marker in self.END_SECTION_MARKERS:
                if re.search(end_marker, line_str, re.IGNORECASE):
                    if current_task_num > 0:
                        tasks.append(LabTask(task_id=current_task_num, title=f"Task {current_task_num}", description="\n".join(current_lines), language=overall_lang))
                    return LabManual(self.path, title, "Programming Lab", lab_number, [], tasks, full_text)

            tm = re.match(r"^([0-9]+)\s*[-:\.]\s*(.*)", line_str)
            if tm:
                if current_task_num > 0:
                    tasks.append(LabTask(task_id=current_task_num, title=f"Task {current_task_num}", description="\n".join(current_lines), language=overall_lang))
                current_task_num = int(tm.group(1))
                current_lines = [tm.group(2).strip()]
            elif current_task_num > 0:
                current_lines.append(line_str)

        if current_task_num > 0:
            tasks.append(LabTask(task_id=current_task_num, title=f"Task {current_task_num}", description="\n".join(current_lines), language=overall_lang))

        return LabManual(self.path, title, "Programming Lab", lab_number, [], tasks, full_text)

    def _parse_text(self) -> LabManual:
        with open(self.path, "r", encoding="utf-8") as f:
            text = f.read()
        return self._parse_pdf()
