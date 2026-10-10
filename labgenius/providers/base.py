"""
Base AI Provider Interface for LabGenius.
Standardizes LLM completions, structured task generation,
and answer synthesis across all supported models.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple

from ..parser import LabTask
from ..solver import TaskSolution


class BaseAIProvider(ABC):
    """Abstract base class for AI completion providers."""

    @abstractmethod
    def solve_tasks(
        self,
        tasks: List[LabTask],
        context: str,
        student_profile: Any,
        course_name: str = "",
        custom_instructions: str = "",
    ) -> List[TaskSolution]:
        """Generates authentic executable code and explanation for a list of lab tasks."""
        pass

    @abstractmethod
    def solve_analysis_questions(
        self,
        questions: List[str],
        course_name: str,
        custom_instructions: str = "",
    ) -> List[Tuple[str, str]]:
        """Generates realistic student answers for analysis / discussion questions."""
        pass

    @abstractmethod
    def solve_viva_questions(
        self,
        questions: List[str],
        course_name: str,
        custom_instructions: str = "",
    ) -> List[Tuple[str, str]]:
        """Generates realistic concise student answers for viva voce questions."""
        pass

    @abstractmethod
    def refine_solution(
        self,
        task: LabTask,
        current_solution: TaskSolution,
        instruction: str,
    ) -> TaskSolution:
        """Modifies and improves an existing task solution using natural language feedback."""
        pass
