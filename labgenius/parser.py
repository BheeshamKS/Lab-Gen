"""
Lab Manual Parser for LabGenius.
Isolates assigned lab tasks from theory notes, extracts table patterns, and detects lab metadata.
"""

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Any, Tuple, Dict

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
    context: str = ""
    viva_questions: List[str] = field(default_factory=list)
    viva_answers: List[Tuple[str, str]] = field(default_factory=list)
    analysis_questions: List[str] = field(default_factory=list)
    analysis_answers: List[Tuple[str, str]] = field(default_factory=list)
    observation_tables: List[Dict[str, Any]] = field(default_factory=list)


class ManualParser:
    """Parses DOCX and PDF lab manuals, strictly isolating assigned lab tasks from theory."""

    TASK_SECTION_MARKERS = [
        r"^(?:\d+[\.\)]\s*)?(?:lab\s+)?tasks?[\s:]*$",
        r"lab\s+tasks?:",
        r"^(?:\d+[\.\)]\s*)?(?:lab\s+)?exercises?[\s:]*$",
        r"^(?:\d+[\.\)]\s*)?(?:lab\s+)?assignments?[\s:]*$",
        r"^(?:\d+[\.\)]\s*)?assignment\s*(?:/|and|&)?\s*(?:lab\s+)?tasks?[\s:]*$",
        r"^(?:\d+[\.\)]\s*)?(?:lab\s+)?activities?[\s:]*$",
        r"^(?:\d+[\.\)]\s*)?(?:practice\s+)?problems?[\s:]*$",
        r"programs\s+to\s+implement[\s:]*$",
        r"^(?:\d+[\.\)]\s*)?assignment\s+tasks?[\s:]*$",
        r"^(?:\d+[\.\)]\s*)?task\s+requirements?[\s:]*$",
        r"^(?:\d+[\.\)]\s*)?requirements?[\s:]*$",
        r"^(?:\d+[\.\)]\s*)?problem\s+statements?[\s:]*$",
    ]

    ROMAN_NUMERALS = {
        "i": 1, "ii": 2, "iii": 3, "iv": 4, "v": 5,
        "vi": 6, "vii": 7, "viii": 8, "ix": 9, "x": 10,
    }

    TASK_KEYWORD_PATTERN = (
        r"^(?:lab|task|assignment|experiment|exercise|activity|problem|program|part|query|question)"
        r"\s*#?\s*(?:0*([1-9][0-9]*)|([ivxldcm]+))\b(?:\s*[\u2013\u2014\-:\.]\s*(.*)|$)"
    )

    END_SECTION_MARKERS = [
        r"^(?:\d+[\.\)]\s*)?learning\s+outcomes?[\s:]*$",
        r"^(?:\d+[\.\)]\s*)?conclusion[\s:]*$",
        r"^(?:\d+[\.\)]\s*)?references?[\s:]*$",
        r"^(?:\d+[\.\)]\s*)?marking\s+rubric[\s:]*$",
        r"^(?:\d+[\.\)]\s*)?precautions?[\s:]*$",
        r"^(?:\d+[\.\)]\s*)?submission\s+requirements?[\s:]*$",
        r"^(?:\d+[\.\)]\s*)?expected\s+results?[\s:]*$",
    ]

    LANGUAGE_KEYWORDS = {
        "c": ["in c language", "dev c++", "dev-c++", "c program", "gcc", "#include <stdio.h>", "printf", ".c "],
        "cpp": ["c++", "cpp", "g++", "#include <iostream>", "std::cout", ".cpp"],
        "python": ["python", "python3", "def ", "import numpy", "import pandas", ".py"],
        "bash": ["bash", "shell script", "linux command", "grep", "awk", "#!/bin/bash"],
        "sql": ["sql", "select ", "insert into", "database", "sqlite", "table"],
    }

    def __init__(self, file_path: str, subject: Optional[str] = None, subject_name: Optional[str] = None):
        self.path = Path(file_path)
        if not self.path.exists():
            raise FileNotFoundError(f"Manual file not found: {self.path}")
        self.subject = (subject or "").strip().lower()
        self.subject_name = (subject_name or "").strip()

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
        if self.subject == "dbms":
            return "sql"
        if self.subject == "dsa":
            return "python"

        text_lower = text.lower()
        # Strict SQL detection to avoid false positives on Data Structure labs
        if any(k in text_lower for k in [
            "sql server", "create table", "alter table",
            "drop table", "select * from", "primary key", "foreign key",
            "truncate table", "dbms", "queries", "table_name"
        ]) and not "data structure" in text_lower[:500]:
            return "sql"
        if any(k in text_lower for k in [
            "in c language", "dev c++", "dev-c++", "#include <stdio.h>", "stdio.h",
            "systems programming in c", "programming in c", "c program", "c string", "gcc",
        ]):
            return "c"
        if any(k in text_lower for k in ["c++", "cpp", "iostream", "g++", "std::"]):
            return "cpp"
        if any(k in text_lower for k in ["python", "pandas", "numpy", "def ", "import "]):
            return "python"
        if any(k in text_lower for k in ["bash", "shell script", "linux command", "#!/bin/bash"]):
            return "bash"
        if any(k in text_lower for k in ["tree", "graph", "sort", "search", "stack", "queue", "linked list", "array"]):
            return "python"
        return "c"

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
        m_fn = re.search(r"(?:lab\s*(?:session|manual)?|experiment|session|assignment)\s*[:#-]?\s*([0-9]+)", self.path.stem, re.IGNORECASE)
        if m_fn:
            lab_number = m_fn.group(1).zfill(2)

        # Check first 15 paragraphs for explicit Topic / Title
        for p in paragraphs_text[:15]:
            p_clean = re.sub(r"^[#\s\*\-]+", "", p).strip()
            m_topic = re.match(r"^(?:title|topic)\s*[:\-]\s*(.+)", p_clean, re.IGNORECASE)
            if m_topic:
                cand_title = m_topic.group(1).strip()
                if len(cand_title) > 2:
                    title = cand_title
                    break

        # Check first 15 paragraphs for Lab/Experiment/Session/Assignment number and title
        for i, p in enumerate(paragraphs_text[:15]):
            m = re.search(r"(?:lab\s*(?:session|manual)?|experiment|session|assignment)\s*[:#-]?\s*([0-9]+)", p, re.IGNORECASE)
            if m:
                lab_number = m.group(1).zfill(2)
                if title == "LAB REPORT":
                    after = re.sub(r"(?:lab\s*(?:session|manual)?|experiment|session|assignment)\s*[:#-]?\s*[0-9]+[\s:\.-]*", "", p, flags=re.IGNORECASE).strip()
                    if len(after) > 3:
                        title = after
                    elif i + 1 < len(paragraphs_text):
                        next_p = paragraphs_text[i + 1].strip()
                        if not any(next_p.lower().startswith(x) for x in ["objective", "theory", "date", "roll", "name", "topic:", "title:"]):
                            title = next_p
                break

        # Clean title boilerplate
        title = re.sub(r"^[#\s\*\-]+", "", title).strip()
        title = re.sub(r"^(?:title|topic)\s*[:\-]\s*", "", title, flags=re.IGNORECASE).strip()
        title = re.sub(r"\s+in\s+c\s+language.*", "", title, flags=re.IGNORECASE).strip()
        title = re.sub(r"\s+in\s+c\+\+.*", "", title, flags=re.IGNORECASE).strip()
        title = re.sub(r"\s+in\s+python.*", "", title, flags=re.IGNORECASE).strip()
        title = title.rstrip(".:, -").upper()

        # Course name detection
        if self.subject == "dbms":
            course_name = "Database Management Systems (DBMS)"
        elif self.subject == "dsa":
            course_name = "Data Structures and Algorithms"
        elif self.subject_name:
            course_name = self.subject_name
        elif overall_lang == "sql" or "dbms" in self.path.stem.lower() or "database" in full_text.lower()[:300]:
            course_name = "Database Management Systems (DBMS)"
        else:
            course_name = "Programming / Data Science"
            for p in paragraphs_text[:15]:
                if any(k in p.lower() for k in ["course", "subject", "data science", "computer science"]):
                    course_name = p.replace("Course:", "").replace("Subject:", "").strip()
                    break

        # 2. Find and Extract ONLY the Task Section, Viva Questions, Analysis Questions, and Tables
        tasks, preamble_context, viva_questions, analysis_questions, observation_tables = self._extract_tasks_from_docx_body(doc, lab_number, overall_lang, title=title)

        return LabManual(
            file_path=self.path,
            title=title,
            course_name=course_name,
            lab_number=lab_number,
            objectives=[],
            tasks=tasks,
            raw_text=full_text,
            is_docx_template=False,
            context=preamble_context,
            viva_questions=viva_questions,
            analysis_questions=analysis_questions,
            observation_tables=observation_tables,
        )

    def _extract_tasks_from_docx_body(
        self, doc: Any, lab_number: str, default_lang: str, title: str = ""
    ) -> Tuple[List[LabTask], str, List[str], List[str], List[Dict[str, Any]]]:
        """Traverses document body to extract tasks, viva questions, analysis questions, and observation tables."""
        tasks: List[LabTask] = []
        viva_questions: List[str] = []
        analysis_questions: List[str] = []
        observation_tables: List[Dict[str, Any]] = []

        in_task_section = False
        in_viva_section = False
        in_analysis_section = False
        in_algos_section = False
        in_input_section = False
        in_proc_section = False
        in_algorithm_block = False

        algo_items: List[str] = []
        input_data_lines: List[str] = []
        procedure_lines: List[str] = []
        latest_tbl_title = ""

        current_task_num = 0
        current_task_title = ""
        current_task_lines: List[str] = []
        preamble_lines: List[str] = []

        task_kw_regex = re.compile(self.TASK_KEYWORD_PATTERN, re.IGNORECASE)

        imperatives = [
            "create", "display", "add", "delete", "change", "drop", "write", "implement",
            "query", "find", "calculate", "design", "update", "select", "insert", "execute",
            "verify", "show", "truncate", "enforce", "alter", "modify",
            "try", "use", "test", "check", "apply", "set", "demonstrate", "observe",
            "run", "make", "construct", "build", "retrieve", "list", "remove", "rename"
        ]
        intro_starters = [
            "perform the following", "follow the instructions", "note:", "instructions:", "guidelines:"
        ]

        paragraphs_text = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
        explicit_headings = []
        doc_lab_num = int(lab_number) if lab_number.isdigit() else 0

        for i, p in enumerate(paragraphs_text):
            if "lab manual" in p.lower():
                continue
            if i < 8 and any(k in p.lower() for k in ["course", "duration", "program", "department"]):
                continue
            m = task_kw_regex.match(p)
            if m:
                num = int(m.group(1))
                if i < 8 and re.match(r"^(?:lab|experiment|session)\b", p, re.IGNORECASE) and num == doc_lab_num:
                    continue
                explicit_headings.append(num)

        has_explicit_experiment_headings = len(explicit_headings) >= 2 or (len(explicit_headings) >= 1 and explicit_headings[0] == 1)

        def save_task():
            nonlocal current_task_num, current_task_title, current_task_lines, in_algorithm_block
            in_algorithm_block = False
            if current_task_num > 0 and (current_task_lines or current_task_title):
                desc = "\n".join(current_task_lines).strip()
                first_line = current_task_lines[0].strip() if current_task_lines else ""
                if not current_task_title:
                    first_line_clean = first_line.splitlines()[0].strip()
                    t_snippet = first_line_clean[:130].strip() if len(first_line_clean) > 130 else first_line_clean
                    current_task_title = f"Task {current_task_num}: {t_snippet}"

                clean_sub = re.sub(r"^task\s*\d+[\s:\-]*", "", current_task_title, flags=re.IGNORECASE).strip().rstrip(":")
                if clean_sub.lower().endswith("that") or clean_sub.lower() in ["create a python program", "write a python program", "implement a python program"]:
                    if title and len(title) > 5 and "lab" not in title.lower():
                        t_clean = title.title().strip()
                        if t_clean.lower().startswith("performance comparison"):
                            clean_sub = f"Implementation & {t_clean}"
                        elif t_clean.lower().startswith("implementation"):
                            clean_sub = t_clean
                        else:
                            clean_sub = f"Implementation & Performance Comparison of {t_clean}"
                    else:
                        clean_sub = re.sub(r"\s+that$", "", clean_sub, flags=re.IGNORECASE).strip()
                    current_task_title = f"Task {current_task_num}: {clean_sub}"

                tasks.append(
                    LabTask(
                        task_id=current_task_num,
                        title=current_task_title,
                        description=desc,
                        language=default_lang,
                    )
                )
            current_task_lines = []
            current_task_title = ""

        all_p_elements = [el for el in doc.element.body if el.tag.split("}")[-1] == "p"]

        for idx_el, el in enumerate(doc.element.body):
            tag = el.tag.split("}")[-1]

            if tag == "p":
                p = docx.text.paragraph.Paragraph(el, doc)
                p_text = p.text.strip()
                if not p_text:
                    continue

                # Section: Viva Questions
                if re.search(r"^(?:\d+[\.\)]\s*)?(?:viva(?:\s+voce)?(?:\s+questions?)?|interview\s*questions?)[\s:]*$", p_text, re.IGNORECASE):
                    save_task()
                    in_viva_section = True
                    in_analysis_section = False
                    in_task_section = False
                    in_algos_section = False
                    in_input_section = False
                    in_proc_section = False
                    continue

                # Section: Analysis Questions
                if re.search(r"^(?:\d+[\.\)]\s*)?(?:analysis\s*questions?|questions?\s+(?:for\s+)?analysis)[\s:]*$", p_text, re.IGNORECASE):
                    save_task()
                    in_analysis_section = True
                    in_viva_section = False
                    in_task_section = False
                    in_algos_section = False
                    in_input_section = False
                    in_proc_section = False
                    continue

                # Section: Algorithms / Programs to be Tested
                if re.search(r"^(?:(?:sorting\s+)?algorithms?|operations?|methods?|techniques?|programs?)\s+(?:to\s+be\s+tested|to\s+implement|tested|implemented)[\s:]*$", p_text, re.IGNORECASE):
                    save_task()
                    in_algos_section = True
                    in_input_section = False
                    in_proc_section = False
                    in_analysis_section = False
                    in_viva_section = False
                    continue

                # Section: Input Data
                if re.search(r"^input\s+data[\s:]*$", p_text, re.IGNORECASE):
                    in_input_section = True
                    in_algos_section = False
                    in_proc_section = False
                    continue

                # Section: Procedure
                if re.search(r"^procedure[\s:]*$", p_text, re.IGNORECASE):
                    in_proc_section = True
                    in_algos_section = False
                    in_input_section = False
                    continue

                # Track Table Titles
                if re.search(r"^(?:table\s+[0-9]+|observation\s+table)[\s:]*.*$", p_text, re.IGNORECASE):
                    latest_tbl_title = p_text

                if in_viva_section:
                    is_viva_end = any(re.search(end_m, p_text, re.IGNORECASE) for end_m in self.END_SECTION_MARKERS)
                    if is_viva_end:
                        in_viva_section = False
                        break
                    viva_questions.append(p_text)
                    continue

                m_exp = task_kw_regex.match(p_text)
                is_manual_header = "lab manual" in p_text.lower() or (idx_el < 8 and m_exp and re.match(r"^(?:lab|experiment|session)\b", p_text, re.IGNORECASE) and int(m_exp.group(1)) == doc_lab_num)

                m_named = re.match(
                    r"^(performance\s+visualization|comparative\s+experiment|discussion\s+questions|challenge\s+activity(?:\s*\([^)]*\))?)\b[\s:\.-]*(.*)",
                    p_text,
                    re.IGNORECASE
                )

                if in_analysis_section:
                    if (m_exp and not is_manual_header) or m_named:
                        in_analysis_section = False
                    else:
                        is_analysis_end = any(re.search(end_m, p_text, re.IGNORECASE) for end_m in self.END_SECTION_MARKERS) or \
                                          re.search(r"^viva\s*(?:questions?|voce)?[\s:]*$", p_text, re.IGNORECASE)
                        if is_analysis_end:
                            in_analysis_section = False
                            if re.search(r"^viva\s*(?:questions?|voce)?[\s:]*$", p_text, re.IGNORECASE):
                                in_viva_section = True
                                continue
                            break
                        analysis_questions.append(p_text)
                        continue

                if in_algos_section:
                    if any(p_text.lower().startswith(x) for x in ["input data", "procedure", "objective", "observation", "analysis", "viva"]):
                        in_algos_section = False
                    else:
                        algo_items.append(p_text)
                        continue

                if in_input_section:
                    if any(p_text.lower().startswith(x) for x in ["procedure", "objective", "observation", "analysis", "viva", "attach codes"]):
                        in_input_section = False
                    else:
                        input_data_lines.append(p_text)

                if in_proc_section:
                    if any(p_text.lower().startswith(x) for x in ["observation", "analysis", "viva", "attach codes", "table"]):
                        in_proc_section = False
                    else:
                        procedure_lines.append(p_text)

                if in_task_section:
                    is_end = any(re.search(end_m, p_text, re.IGNORECASE) for end_m in self.END_SECTION_MARKERS)
                    if is_end:
                        save_task()
                        return tasks, "\n".join(preamble_lines).strip(), viva_questions, analysis_questions, observation_tables

                m_plain_num = re.match(r"^0*([1-9][0-9]*)[\.\)]\s+(.*)", p_text)
                if m_exp and not is_manual_header:
                    save_task()
                    in_task_section = True
                    num_str = m_exp.group(1)
                    if num_str:
                        current_task_num = int(num_str)
                    elif m_exp.group(2):
                        current_task_num = self.ROMAN_NUMERALS.get(m_exp.group(2).lower(), 1)
                    rest = m_exp.group(3).strip() if m_exp.group(3) else ""

                    # If rest is empty, check next paragraph for task title
                    if not rest:
                        curr_p_idx = all_p_elements.index(el) if el in all_p_elements else -1
                        if curr_p_idx >= 0 and curr_p_idx + 1 < len(all_p_elements):
                            next_p_text = docx.text.paragraph.Paragraph(all_p_elements[curr_p_idx + 1], doc).text.strip()
                            if next_p_text and len(next_p_text) < 120 and not any(next_p_text.lower().startswith(x) for x in ["objective", "theory", "scenario", "dataset", "tasks", "pre-lab"]):
                                rest = next_p_text

                    current_task_title = f"Task {current_task_num}: {rest}" if rest else f"Task {current_task_num}"
                    current_task_lines = []
                    continue

                elif not has_explicit_experiment_headings and in_task_section and m_plain_num and not is_manual_header:
                    save_task()
                    current_task_num = int(m_plain_num.group(1))
                    rest = m_plain_num.group(2).strip()
                    current_task_title = f"Task {current_task_num}: {rest}" if rest else f"Task {current_task_num}"
                    current_task_lines = [rest] if rest else []
                    continue

                elif m_named and not is_manual_header:
                    save_task()
                    in_task_section = True
                    current_task_num += 1
                    named_title = m_named.group(1).strip()
                    rest = m_named.group(2).strip()
                    current_task_title = f"Task {current_task_num}: {named_title}"
                    if rest:
                        current_task_lines = [rest]
                    continue

                if not in_task_section:
                    for marker in self.TASK_SECTION_MARKERS:
                        if re.search(marker, p_text, re.IGNORECASE):
                            in_task_section = True
                            after_colon = re.sub(marker, "", p_text, flags=re.IGNORECASE).strip()
                            p_text = after_colon
                            break
                    if not in_task_section or not p_text:
                        continue

                if re.search(r"^(?:algorithm|pseudocode)[\s:]", p_text, re.IGNORECASE):
                    in_algorithm_block = True
                    if current_task_num > 0:
                        current_task_lines.append(p_text)
                    else:
                        preamble_lines.append(p_text)
                    continue

                if re.search(r"^code\s*(?:\([^)]*\))?[\s:]*$", p_text, re.IGNORECASE) or (p_text.lower().startswith("code") and "attach" in p_text.lower()):
                    save_task()
                    in_task_section = False
                    in_algorithm_block = False
                    continue

                if any(p_text.lower().startswith(intro) for intro in intro_starters):
                    if current_task_lines:
                        preamble_lines.extend(current_task_lines)
                        current_task_lines = []
                    if tasks:
                        for t in tasks:
                            preamble_lines.append(f"{t.title}\n{t.description}")
                        tasks.clear()
                    current_task_num = 0
                    current_task_title = ""
                    continue

                if not has_explicit_experiment_headings:
                    task_match = re.match(r"^([0-9]+)\s*[\u2013\u2014\-:\.]\s*(.*)", p_text)
                    if task_match:
                        save_task()
                        current_task_num = int(task_match.group(1))
                        rest = task_match.group(2).strip()
                        current_task_title = f"Task {current_task_num}: {rest[:130]}"
                        current_task_lines = [rest] if rest else []
                        continue

                    # Lettered list tasks: a), b), c) or (a), (b), (c)
                    m_letter = re.match(r"^(?:([a-zA-Z])|\(([a-zA-Z])\))[\.\)]\s*(.*)", p_text)
                    if m_letter:
                        save_task()
                        current_task_num += 1
                        letter_char = (m_letter.group(1) or m_letter.group(2)).lower()
                        rest = m_letter.group(3).strip()
                        current_task_title = f"Task {current_task_num} ({letter_char}): {rest[:130]}"
                        current_task_lines = [p_text]
                        continue

                    m_bullet = re.match(r"^[•\-\*]\s*(.*)", p_text)
                    if m_bullet:
                        save_task()
                        current_task_num += 1
                        b_text = m_bullet.group(1).strip()
                        current_task_title = f"Task {current_task_num}: {b_text[:130]}"
                        current_task_lines = [b_text]
                        continue

                    if not in_algorithm_block:
                        first_word = p_text.split()[0].lower().rstrip(":,.-") if p_text.split() else ""
                        if first_word in imperatives and len(p_text) > 10:
                            save_task()
                            current_task_num += 1
                            current_task_title = f"Task {current_task_num}: {p_text[:130]}"
                            current_task_lines = [p_text]
                            continue

                if in_task_section:
                    # Skip duplicate subtitle if already adopted into current_task_title
                    if current_task_title and p_text == current_task_title.split(": ", 1)[-1]:
                        continue
                    if current_task_num > 0:
                        current_task_lines.append(p_text)
                    else:
                        preamble_lines.append(p_text)

            elif tag == "tbl":
                tbl = docx.table.Table(el, doc)
                table_lines = []
                rows_data = []
                for row in tbl.rows:
                    row_cells = [cell.text.strip().replace('\n', ' ') for cell in row.cells]
                    rows_data.append(row_cells)
                    row_str = " | ".join(c for c in row_cells if c)
                    if row_str:
                        table_lines.append(row_str)

                # Check if it's the cover metadata table
                is_cover = any(
                    any(k in c.lower() for k in ["roll number", "student name", "enrollment", "section"])
                    for r in rows_data for c in r
                )
                if not is_cover and rows_data and len(rows_data) > 1:
                    headers = rows_data[0]
                    data_rows = rows_data[1:]
                    t_title = latest_tbl_title or f"Observation Table {len(observation_tables) + 1}"
                    observation_tables.append({
                        "title": t_title,
                        "headers": headers,
                        "rows": data_rows,
                    })
                    latest_tbl_title = ""

                if in_task_section and table_lines:
                    tbl_block = "\n[Observation / Data Table]:\n" + "\n".join(table_lines)
                    if current_task_num > 0:
                        current_task_lines.append(tbl_block)
                    else:
                        preamble_lines.append(tbl_block)

        save_task()

        # If no explicit tasks were found, but algorithms to test were listed, construct tasks from them
        if not tasks and algo_items:
            sizes_str = "sizes 500, 5000, and 10000"
            rev_str = "reverse ordered arrays"
            for idx_algo, algo_name in enumerate(algo_items, 1):
                clean_name = algo_name.strip()
                tasks.append(
                    LabTask(
                        task_id=idx_algo,
                        title=f"Task {idx_algo:02d}: {clean_name} Implementation & Reverse Array Analysis",
                        description=(
                            f"Implement {clean_name} in Python and execute on {rev_str} of {sizes_str} "
                            f"elements to analyze execution time in milliseconds under worst-case input scenario."
                        ),
                        language=default_lang,
                    )
                )
            bench_id = len(tasks) + 1
            tasks.append(
                LabTask(
                    task_id=bench_id,
                    title=f"Task {bench_id:02d}: Performance Benchmark & Observation Table Generation",
                    description=(
                        f"Execute comparative performance benchmark across all six sorting algorithms on "
                        f"{rev_str} of {sizes_str} elements, recording execution times and ranking algorithms "
                        f"from fastest to slowest."
                    ),
                    language=default_lang,
                )
            )

        if not tasks:
            tasks = self._fallback_extract_tasks(doc, default_lang)

        return tasks, "\n".join(preamble_lines).strip(), viva_questions, analysis_questions, observation_tables

    def _fallback_extract_tasks(self, doc: Any, default_lang: str) -> List[LabTask]:
        """Fallback if no explicit 'LAB TASKS:' heading exists."""
        tasks = []
        paragraphs = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
        
        filtered_paragraphs = []
        for p in paragraphs:
            if p.lower().startswith("references") or p.lower().startswith("bibliography"):
                break
            filtered_paragraphs.append(p)
            
        for p in filtered_paragraphs:
            m = re.match(r"^(?:task|exercise|program|question|experiment)\s*#?\s*([0-9]+)[\s:\.\u2013\u2014]+(.*)", p, re.IGNORECASE)
            if m:
                t_num = int(m.group(1))
                desc = m.group(2).strip()
                tasks.append(LabTask(task_id=t_num, title=f"Task {t_num}", description=desc, language=default_lang))

        if not tasks and filtered_paragraphs:
            tasks = [LabTask(task_id=1, title="Task 1", description="\n".join(filtered_paragraphs[-5:]), language=default_lang)]
        return tasks

    def _parse_pdf(self) -> LabManual:
        if not pypdf:
            raise ImportError("pypdf is required to parse .pdf files")

        reader = pypdf.PdfReader(self.path)
        full_text = "\n".join(page.extract_text() or "" for page in reader.pages)
        return self._parse_from_text(full_text)

    def _parse_text(self) -> LabManual:
        with open(self.path, "r", encoding="utf-8", errors="replace") as f:
            text = f.read()
        return self._parse_from_text(text)

    def _parse_from_text(self, full_text: str) -> LabManual:
        overall_lang = self._detect_overall_language(full_text)
        lines = [line.strip() for line in full_text.splitlines() if line.strip()]

        # 1. Detect Lab Number and Title
        lab_number = "01"
        title = "LAB REPORT"

        # Check filename first
        m_fn = re.search(r"(?:lab\s*(?:session|manual)?|experiment|session|assignment)\s*[:#-]?\s*([0-9]+)", self.path.stem, re.IGNORECASE)
        if m_fn:
            lab_number = m_fn.group(1).zfill(2)

        # Check first 25 lines for explicit Topic / Title
        for p in lines[:25]:
            p_clean = re.sub(r"^[#\s\*\-]+", "", p).strip()
            m_topic = re.match(r"^(?:title|topic)\s*[:\-]\s*(.+)", p_clean, re.IGNORECASE)
            if m_topic:
                cand_title = m_topic.group(1).strip()
                if len(cand_title) > 2:
                    title = cand_title
                    break

        # Check first 25 lines of text for Lab/Experiment/Session/Assignment number and title
        for i, p in enumerate(lines[:25]):
            m = re.search(r"(?:lab\s*(?:session|manual)?|experiment|session|assignment)\s*[:#-]?\s*([0-9]+)", p, re.IGNORECASE)
            if m:
                lab_number = m.group(1).zfill(2)
                if title == "LAB REPORT":
                    after = re.sub(r"(?:lab\s*(?:session|manual)?|experiment|session|assignment)\s*[:#-]?\s*[0-9]+[\s:\.-]*", "", p, flags=re.IGNORECASE).strip()
                    if len(after) > 3:
                        title = after
                    elif i + 1 < len(lines):
                        next_p = lines[i + 1].strip()
                        if not any(next_p.lower().startswith(x) for x in ["objective", "theory", "date", "roll", "name", "department", "university", "topic:", "title:"]):
                            title = next_p
                break

        # Also fallback regex if title wasn't found from above
        if title == "LAB REPORT":
            m_alt = re.search(r"(?:lab|session|assignment)\s*#?\s*([0-9]+)\s*[:\-]\s*([^.\n\r]+)", full_text, re.IGNORECASE)
            if m_alt:
                lab_number = m_alt.group(1).zfill(2)
                title = m_alt.group(2).strip()

        # Clean title boilerplate
        title = re.sub(r"^[#\s\*\-]+", "", title).strip()
        title = re.sub(r"^(?:title|topic)\s*[:\-]\s*", "", title, flags=re.IGNORECASE).strip()
        title = re.sub(r"\s+in\s+c\s+language.*", "", title, flags=re.IGNORECASE).strip()
        title = re.sub(r"\s+in\s+c\+\+.*", "", title, flags=re.IGNORECASE).strip()
        title = re.sub(r"\s+in\s+python.*", "", title, flags=re.IGNORECASE).strip()
        title = title.rstrip(".:, -").upper()

        # Course name detection
        if self.subject == "dbms":
            course_name_pdf = "Database Management Systems (DBMS)"
        elif self.subject == "dsa":
            course_name_pdf = "Data Structures and Algorithms"
        elif self.subject_name:
            course_name_pdf = self.subject_name
        elif overall_lang == "sql" or "dbms" in self.path.stem.lower() or "database" in full_text.lower()[:300]:
            course_name_pdf = "Database Management Systems (DBMS)"
        else:
            course_name_pdf = "Programming / Data Science"
            for p in lines[:20]:
                if any(k in p.lower() for k in ["course", "subject", "data science", "computer science"]):
                    course_name_pdf = p.replace("Course:", "").replace("Subject:", "").strip()
                    break

        course_name_pdf = re.sub(r"^[#\s\*\-]+", "", course_name_pdf).strip()

        tasks: List[LabTask] = []
        in_tasks = False
        in_viva = False
        in_analysis = False
        current_task_num = 0
        current_task_title = ""
        current_lines: List[str] = []
        preamble_lines: List[str] = []
        viva_questions: List[str] = []
        analysis_questions: List[str] = []
        observation_tables: List[Dict[str, Any]] = []
        table_lines: List[str] = []
        latest_tbl_title = ""

        doc_lab_num = int(lab_number) if lab_number.isdigit() else 0
        task_kw_regex = re.compile(self.TASK_KEYWORD_PATTERN, re.IGNORECASE)

        explicit_headings = []
        for i_l, l_raw in enumerate(lines):
            c_l = re.sub(r"^[#\s\*\-]+", "", l_raw).strip()
            c_no_f = re.sub(r"[\*\_]+", "", c_l).strip()
            m_h = task_kw_regex.match(c_no_f)
            if m_h:
                n_str = m_h.group(1)
                if n_str:
                    n_val = int(n_str)
                    if i_l < 15 and re.match(r"^(?:lab|experiment|session)\b", c_no_f, re.IGNORECASE) and n_val == doc_lab_num:
                        continue
                    explicit_headings.append(n_val)

        has_explicit_headings = len(explicit_headings) >= 2 or (len(explicit_headings) >= 1 and explicit_headings[0] == 1)

        def save_task():
            nonlocal current_task_num, current_task_title, current_lines
            if current_task_num > 0 and (current_lines or current_task_title):
                desc = "\n".join(current_lines).strip()
                first_line = current_lines[0].strip() if current_lines else ""
                if not current_task_title:
                    first_line_clean = first_line.splitlines()[0].strip()
                    t_snippet = first_line_clean[:130].strip() if len(first_line_clean) > 130 else first_line_clean
                    current_task_title = f"Task {current_task_num}: {t_snippet}"
                tasks.append(
                    LabTask(
                        task_id=current_task_num,
                        title=current_task_title,
                        description=desc,
                        language=overall_lang,
                    )
                )
            current_lines = []
            current_task_title = ""

        def flush_table():
            nonlocal table_lines, latest_tbl_title
            if len(table_lines) >= 2:
                h_line = [c.strip() for c in table_lines[0].strip("|").split("|")]
                data_rows = []
                for r_line in table_lines[1:]:
                    if re.match(r"^[\s\|:\-]+$", r_line):
                        continue
                    data_rows.append([c.strip() for c in r_line.strip("|").split("|")])
                if h_line and data_rows:
                    observation_tables.append({
                        "title": latest_tbl_title or f"Observation Table {len(observation_tables)+1}",
                        "headers": h_line,
                        "rows": data_rows,
                    })
            table_lines = []
            latest_tbl_title = ""

        for idx, line_str in enumerate(lines):
            # Skip page headers / footers that repeat across pages
            if len(line_str) < 55 and any(hdr in line_str.lower() for hdr in [
                "lab manual", "dawood university", "department of data science", "department of computer"
            ]):
                continue

            clean_line = re.sub(r"^[#\s\*\-]+", "", line_str).strip()
            clean_line_no_fmt = re.sub(r"[\*\_]+", "", clean_line).strip()

            # Track observation table titles
            if re.search(r"^(?:table\s+[0-9]+|observation\s+table)[\s:]*.*$", clean_line_no_fmt, re.IGNORECASE):
                latest_tbl_title = clean_line_no_fmt

            # Track Markdown table rows
            if line_str.startswith("|") and line_str.endswith("|"):
                table_lines.append(line_str)
                continue
            elif table_lines:
                flush_table()

            # Viva Voce section
            if re.search(r"^(?:\d+[\.\)]\s*)?(?:viva(?:\s+voce)?(?:\s+questions?)?|interview\s*questions?)[\s:]*$", clean_line_no_fmt, re.IGNORECASE):
                save_task()
                in_viva = True
                in_analysis = False
                in_tasks = False
                continue

            # Analysis Questions section
            if re.search(r"^(?:\d+[\.\)]\s*)?(?:analysis\s*questions?|questions?\s+(?:for\s+)?analysis)[\s:]*$", clean_line_no_fmt, re.IGNORECASE):
                save_task()
                in_analysis = True
                in_viva = False
                in_tasks = False
                continue

            if in_viva:
                if any(re.search(end_m, clean_line_no_fmt, re.IGNORECASE) for end_m in self.END_SECTION_MARKERS):
                    break
                if viva_questions and not re.match(r"^(?:\d+[\.\)]|[-*•]|Q\d+:?)\s+", clean_line_no_fmt, re.IGNORECASE):
                    viva_questions[-1] = f"{viva_questions[-1]} {clean_line_no_fmt}"
                else:
                    viva_questions.append(clean_line_no_fmt)
                continue

            if in_analysis:
                is_analysis_end = any(re.search(end_m, clean_line_no_fmt, re.IGNORECASE) for end_m in self.END_SECTION_MARKERS) or \
                                   re.search(r"^(?:\d+[\.\)]\s*)?(?:viva(?:\s+voce)?(?:\s+questions?)?|interview\s*questions?)[\s:]*$", clean_line_no_fmt, re.IGNORECASE)
                if is_analysis_end:
                    in_analysis = False
                    if re.search(r"^(?:\d+[\.\)]\s*)?(?:viva(?:\s+voce)?(?:\s+questions?)?|interview\s*questions?)[\s:]*$", clean_line_no_fmt, re.IGNORECASE):
                        in_viva = True
                    continue
                if analysis_questions and not re.match(r"^(?:\d+[\.\)]|[-*•]|Q\d+:?)\s+", clean_line_no_fmt, re.IGNORECASE):
                    analysis_questions[-1] = f"{analysis_questions[-1]} {clean_line_no_fmt}"
                else:
                    analysis_questions.append(clean_line_no_fmt)
                continue

            # Check for End Section Marker
            if in_tasks:
                if any(re.search(end_m, clean_line_no_fmt, re.IGNORECASE) for end_m in self.END_SECTION_MARKERS):
                    save_task()
                    break

            # Check explicit task pattern
            tm = task_kw_regex.match(clean_line_no_fmt)
            is_doc_heading = idx < 15 and tm and re.match(r"^(?:lab|experiment|session)\b", clean_line_no_fmt, re.IGNORECASE) and (
                (tm.group(1) and int(tm.group(1)) == doc_lab_num) or
                (tm.group(2) and self.ROMAN_NUMERALS.get(tm.group(2).lower(), -1) == doc_lab_num)
            )

            m_named = re.match(
                r"^(performance\s+visualization|comparative\s+experiment|discussion\s+questions|challenge\s+activity(?:\s*\([^)]*\))?)\b[\s:\.-]*(.*)",
                clean_line_no_fmt,
                re.IGNORECASE
            )

            # Check section marker (e.g. "2. LAB TASKS:", "9. Assignment:", "LAB TASKS:")
            is_section_marker = any(re.search(marker, clean_line_no_fmt, re.IGNORECASE) for marker in self.TASK_SECTION_MARKERS)
            if not in_tasks and is_section_marker:
                in_tasks = True
                continue
            elif in_tasks and is_section_marker:
                continue

            m_plain_num = re.match(r"^0*([1-9][0-9]*)[\.\)]\s+(.*)", clean_line_no_fmt)

            if tm and not is_doc_heading:
                save_task()
                in_tasks = True
                num_str = tm.group(1)
                if num_str:
                    current_task_num = int(num_str)
                elif tm.group(2):
                    current_task_num = self.ROMAN_NUMERALS.get(tm.group(2).lower(), 1)
                rest = tm.group(3).strip() if tm.group(3) else ""
                current_task_title = f"Task {current_task_num}: {rest}" if rest else f"Task {current_task_num}"
                current_lines = [rest] if rest else []
                continue

            elif not has_explicit_headings and in_tasks and m_plain_num and not is_doc_heading:
                save_task()
                current_task_num = int(m_plain_num.group(1))
                rest = m_plain_num.group(2).strip()
                current_task_title = f"Task {current_task_num}: {rest}" if rest else f"Task {current_task_num}"
                current_lines = [rest] if rest else []
                continue

            elif m_named and not is_doc_heading:
                save_task()
                in_tasks = True
                current_task_num += 1
                named_title = m_named.group(1).strip()
                rest = m_named.group(2).strip()
                current_task_title = f"Task {current_task_num}: {named_title}"
                current_lines = [rest] if rest else []
                continue

            if in_tasks:
                if current_task_num == 0:
                    # Context preamble before first task (e.g. database/table definitions)
                    preamble_lines.append(line_str)
                else:
                    current_lines.append(line_str)

        flush_table()
        save_task()

        # Fallback if no tasks were extracted
        if not tasks:
            for p in lines:
                p_clean = re.sub(r"^[#\s\*\-]+", "", p).strip()
                m_fb = re.match(r"^(?:task|exercise|program|question|query|problem)\s*#?\s*([0-9]+)[\s:\.-]+(.*)", p_clean, re.IGNORECASE)
                if m_fb:
                    t_num = int(m_fb.group(1))
                    desc = m_fb.group(2).strip()
                    tasks.append(LabTask(task_id=t_num, title=f"Task {t_num}", description=desc, language=overall_lang))

        if not tasks and lines:
            tasks = [LabTask(task_id=1, title="Task 1", description="\n".join(lines[-10:]), language=overall_lang)]

        preamble_context = "\n".join(preamble_lines).strip()
        return LabManual(
            file_path=self.path,
            title=title,
            course_name=course_name_pdf,
            lab_number=lab_number,
            objectives=[],
            tasks=tasks,
            raw_text=full_text,
            is_docx_template=False,
            context=preamble_context,
            viva_questions=viva_questions,
            analysis_questions=analysis_questions,
            observation_tables=observation_tables,
        )
