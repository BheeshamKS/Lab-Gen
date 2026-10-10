"""
Document Ingestion & Structural Extraction Engine for LabGenius.
Bridges raw lab documents (DOCX, PDF) to strictly validated Pydantic requirements.
Supports both deterministic heuristic extraction and LLM-assisted structural parsing.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
from pydantic import BaseModel, Field

from .config import Config
from .parser import ManualParser, LabManual, LabTask
from .state import LabSession, Requirement, RequirementType, RequirementStatus, ManualInfo
from .validator import QualityValidator, ValidationReport


class StructuredTask(BaseModel):
    task_id: int
    title: str
    description: str
    language: str = "python"
    sample_input: Optional[str] = None
    expected_output: Optional[str] = None
    discussion_questions: List[str] = Field(default_factory=list)


class StructuredExtraction(BaseModel):
    title: str = ""
    course_name: str = ""
    lab_number: str = ""
    objectives: List[str] = Field(default_factory=list)
    tasks: List[StructuredTask] = Field(default_factory=list)
    analysis_questions: List[str] = Field(default_factory=list)
    viva_questions: List[str] = Field(default_factory=list)
    observation_tables: List[Dict[str, Any]] = Field(default_factory=list)


class IngestionEngine:
    """Ingests academic lab manuals and converts them to validated requirements."""

    def __init__(self, config: Optional[Config] = None):
        self.config = config or Config.load()
        self.validator = QualityValidator()

    def ingest_file(
        self,
        file_path: Union[str, Path],
        subject: Optional[str] = None,
        subject_name: Optional[str] = None,
        use_llm_refinement: bool = False,
    ) -> Tuple[LabManual, ValidationReport]:
        """
        Parses a lab manual file, validates extraction completeness,
        and optionally uses LLM structured outputs to refine tasks and questions.
        """
        path = Path(file_path).resolve()
        if not path.exists():
            raise FileNotFoundError(f"Lab manual not found at {path}")

        # 1. Deterministic baseline extraction
        parser = ManualParser(str(path), subject=subject, subject_name=subject_name)
        manual = parser.parse()

        # 2. Validation Gate Check
        report = self.validator.validate_extraction(manual)

        # 3. Optional LLM Refinement if extraction had warnings or explicit flag
        if use_llm_refinement and (not manual.tasks or report.warnings):
            manual = self._refine_extraction_with_llm(manual)
            report = self.validator.validate_extraction(manual)

        return manual, report

    def to_session_requirements(self, manual: LabManual) -> List[Requirement]:
        """Converts extracted LabManual tasks and questions to atomic Session Requirements."""
        requirements: List[Requirement] = []

        # 1. Convert Tasks
        for t in manual.tasks:
            requirements.append(
                Requirement(
                    id=f"task_{t.task_id}",
                    task_id=t.task_id,
                    type=RequirementType.TASK,
                    title=t.title,
                    description=t.description,
                    language=t.language,
                    status=RequirementStatus.EXTRACTED,
                    sample_input=t.sample_input,
                    expected_output=t.expected_output,
                    requires_screenshot=t.requires_screenshot,
                    requires_plot=t.requires_plot,
                )
            )

        # 2. Convert Analysis Questions
        for idx, q in enumerate(manual.analysis_questions, 1):
            requirements.append(
                Requirement(
                    id=f"analysis_{idx}",
                    task_id=idx,
                    type=RequirementType.ANALYSIS_QUESTION,
                    title=f"Analysis Question {idx}",
                    description=q,
                    status=RequirementStatus.EXTRACTED,
                )
            )

        # 3. Convert Viva Questions
        for idx, q in enumerate(manual.viva_questions, 1):
            requirements.append(
                Requirement(
                    id=f"viva_{idx}",
                    task_id=idx,
                    type=RequirementType.VIVA_QUESTION,
                    title=f"Viva Question {idx}",
                    description=q,
                    status=RequirementStatus.EXTRACTED,
                )
            )

        # 4. Convert Observation Tables
        for idx, tbl in enumerate(manual.observation_tables, 1):
            requirements.append(
                Requirement(
                    id=f"table_{idx}",
                    task_id=idx,
                    type=RequirementType.OBSERVATION_TABLE,
                    title=tbl.get("title") or f"Observation Table {idx}",
                    description=str(tbl),
                    status=RequirementStatus.EXTRACTED,
                )
            )

        return requirements

    def _refine_extraction_with_llm(self, manual: LabManual) -> LabManual:
        """
        Uses configured LLM provider to extract structured requirements if deterministic parser missed them.
        """
        # Truncate text if enormous to stay well within token windows
        raw_snippet = manual.raw_text[:8000] if manual.raw_text else ""
        if not raw_snippet:
            return manual

        prompt = f"""You are an expert document parser for academic university computer science lab manuals.
Extract the structural components from the following lab manual text:
1. Title
2. Course Name
3. Lab Number
4. Assigned Lab Tasks (isolate executable programming exercises from theory or objectives)
5. Analysis / Discussion Questions
6. Viva Voce Questions

Document Text:
\"\"\"
{raw_snippet}
\"\"\"

Return ONLY valid JSON matching this schema:
{{
  "title": "string",
  "course_name": "string",
  "lab_number": "string",
  "objectives": ["string"],
  "tasks": [
    {{
      "task_id": 1,
      "title": "string",
      "description": "string",
      "language": "python or c or cpp or sql"
    }}
  ],
  "analysis_questions": ["string"],
  "viva_questions": ["string"]
}}
"""
        # For offline / mock fallback, return the existing manual
        if getattr(self.config.ai, "provider", "") in ["offline", "mock"]:
            return manual

        try:
            # If Google Gemini is configured
            if self.config.ai.provider == "gemini":
                import os
                api_key = self.config.ai.api_key or os.environ.get("GEMINI_API_KEY")
                if api_key:
                    from google import genai
                    client = genai.Client(api_key=api_key)
                    response = client.models.generate_content(
                        model=self.config.ai.model or "gemini-2.5-flash",
                        contents=prompt,
                    )
                    text = response.text or ""
                    import json
                    json_str = text.strip()
                    if "```json" in json_str:
                        json_str = json_str.split("```json")[1].split("```")[0].strip()
                    elif "```" in json_str:
                        json_str = json_str.split("```")[1].split("```")[0].strip()
                    parsed_json = json.loads(json_str)

                    # Update manual fields if better
                    if not manual.analysis_questions and parsed_json.get("analysis_questions"):
                        manual.analysis_questions = parsed_json["analysis_questions"]
                    if not manual.tasks and parsed_json.get("tasks"):
                        new_tasks = []
                        for t in parsed_json["tasks"]:
                            new_tasks.append(
                                LabTask(
                                    task_id=t.get("task_id", 1),
                                    title=t.get("title", f"Task {t.get('task_id', 1)}"),
                                    description=t.get("description", ""),
                                    language=t.get("language", manual.tasks[0].language if manual.tasks else "python"),
                                )
                            )
                        manual.tasks = new_tasks
        except Exception:
            # Gracefully degrade to deterministic extraction
            pass

        return manual
