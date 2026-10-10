"""
Validation Gate Module for LabGenius.
Enforces strict quality checks on manual extraction, code execution,
and report content to eliminate blank sections, execution failures,
and AI-generated buzzwords.
"""

import re
from typing import Any, Dict, List, Optional, Tuple
from pydantic import BaseModel, Field

from .parser import LabManual, LabTask
from .solver import TaskSolution, AntiAIFilter
from .runner import ExecutionResult


class ValidationIssue(BaseModel):
    level: str = "error"  # "error", "warning"
    component: str  # "extraction", "execution", "solution", "report"
    message: str
    task_id: Optional[int] = None
    details: Optional[str] = None


class ValidationReport(BaseModel):
    is_valid: bool = True
    errors: List[ValidationIssue] = Field(default_factory=list)
    warnings: List[ValidationIssue] = Field(default_factory=list)

    def add_error(self, component: str, message: str, task_id: Optional[int] = None, details: Optional[str] = None) -> None:
        self.is_valid = False
        self.errors.append(ValidationIssue(
            level="error",
            component=component,
            message=message,
            task_id=task_id,
            details=details,
        ))

    def add_warning(self, component: str, message: str, task_id: Optional[int] = None, details: Optional[str] = None) -> None:
        self.warnings.append(ValidationIssue(
            level="warning",
            component=component,
            message=message,
            task_id=task_id,
            details=details,
        ))


class QualityValidator:
    """Rigorous gate checking extraction completeness, execution success, and report fidelity."""

    CRASH_INDICATORS = [
        "traceback (most recent call last):",
        "segmentation fault",
        "core dumped",
        "syntaxerror:",
        "nameerror:",
        "typeerror:",
        "indexerror:",
        "zerodivisionerror:",
        "fatal error:",
        "compilation terminated",
    ]

    AI_BUZZWORD_PATTERNS = [
        r"\bdelve(?:s|d|ing)?\b",
        r"\bpivotal\b",
        r"\bcrucial role\b",
        r"\btestament to\b",
        r"\bmeticulous(?:ly)?\b",
        r"\bcomprehensive understanding\b",
        r"\bit is important to note that\b",
        r"\bit is worth noting that\b",
    ]

    @classmethod
    def validate_extraction(cls, manual: LabManual) -> ValidationReport:
        """Validates that extracted lab manual has required structure and no missing analysis/tasks."""
        report = ValidationReport()

        if not manual.tasks:
            report.add_error("extraction", "No lab tasks were extracted from the manual.")
        else:
            for t in manual.tasks:
                if not t.description or len(t.description.strip()) < 10:
                    report.add_warning("extraction", f"Task {t.task_id} has a very short or empty description.", task_id=t.task_id)

        # Check if raw text mentions analysis questions, but none were extracted
        raw_lower = manual.raw_text.lower()
        has_analysis_mention = any(k in raw_lower for k in ["questions for analysis", "analysis question", "discussion question"])
        if has_analysis_mention and not manual.analysis_questions:
            report.add_warning("extraction", "The manual mentions Analysis / Discussion Questions, but none were extracted.")

        # Check if raw text mentions viva questions, but none were extracted
        has_viva_mention = any(k in raw_lower for k in ["viva question", "viva voce"])
        if has_viva_mention and not manual.viva_questions:
            report.add_warning("extraction", "The manual mentions Viva Questions, but none were extracted.")

        return report

    @classmethod
    def validate_execution(cls, solution: TaskSolution, result: ExecutionResult) -> ValidationReport:
        """Validates that local code execution finished cleanly with zero errors."""
        report = ValidationReport()

        # Check exit code
        if result.exit_code != 0:
            report.add_error(
                "execution",
                f"Task {solution.task_id} exited with non-zero exit code: {result.exit_code}",
                task_id=solution.task_id,
                details=result.stderr or result.stdout,
            )

        # Check for crash stack traces in stderr or stdout
        combined_output = f"{result.stdout}\n{result.stderr}".lower()
        for indicator in cls.CRASH_INDICATORS:
            if indicator in combined_output:
                report.add_error(
                    "execution",
                    f"Task {solution.task_id} output contains error crash trace: '{indicator}'",
                    task_id=solution.task_id,
                    details=combined_output[:300],
                )
                break

        # Check stdout is not empty
        if not result.stdout.strip() and not solution.is_gui_or_plot:
            report.add_warning(
                "execution",
                f"Task {solution.task_id} produced empty stdout.",
                task_id=solution.task_id,
            )

        return report

    @classmethod
    def validate_code_quality(cls, solution: TaskSolution) -> ValidationReport:
        """Validates generated student code for completeness and syntax hygiene."""
        report = ValidationReport()

        if not solution.code or len(solution.code.strip()) < 15:
            report.add_error("solution", f"Task {solution.task_id} has empty or trivial code.", task_id=solution.task_id)
            return report

        # Check for placeholder comments
        placeholders = ["// todo", "# todo", "// write code here", "# write code here", "pass # implement"]
        code_lower = solution.code.lower()
        for ph in placeholders:
            if ph in code_lower:
                report.add_warning(
                    "solution",
                    f"Task {solution.task_id} code contains unfilled placeholder '{ph}'",
                    task_id=solution.task_id,
                )

        return report

    @classmethod
    def validate_text_for_ai_buzzwords(cls, text: str, context_label: str = "text") -> ValidationReport:
        """Checks for stereotypical AI buzzwords."""
        report = ValidationReport()
        for pattern in cls.AI_BUZZWORD_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                report.add_warning(
                    "report",
                    f"{context_label} contains stereotypical AI buzzword: '{match.group(0)}'",
                    details=text[:200],
                )
        return report

    @classmethod
    def validate_full_pipeline(
        cls,
        manual: LabManual,
        solutions: List[TaskSolution],
        exec_results: List[ExecutionResult],
    ) -> ValidationReport:
        """Runs aggregate quality verification across the entire completed report."""
        report = cls.validate_extraction(manual)

        for sol in solutions:
            sol_rep = cls.validate_code_quality(sol)
            report.errors.extend(sol_rep.errors)
            report.warnings.extend(sol_rep.warnings)
            if not sol_rep.is_valid:
                report.is_valid = False

        for sol, res in zip(solutions, exec_results):
            exec_rep = cls.validate_execution(sol, res)
            report.errors.extend(exec_rep.errors)
            report.warnings.extend(exec_rep.warnings)
            if not exec_rep.is_valid:
                report.is_valid = False

        return report
