"""
Modular Task Orchestrator for LabGenius.
Coordinates requirement tracking, AI provider dispatching, local execution,
and validation gating for student lab reports.
"""

from typing import Any, Dict, List, Optional, Tuple

from .config import Config
from .parser import LabManual, LabTask
from .solver import TaskSolution, AntiAIFilter
from .runner import CodeRunner, ExecutionResult
from .validator import QualityValidator, ValidationReport
from .state import LabSession, Requirement, RequirementType, RequirementStatus
from .providers.base import BaseAIProvider
from .providers.gemini import GeminiProvider


class TaskOrchestrator:
    """Orchestrates requirement lifecycle through AI generation, execution, and validation."""

    def __init__(self, config: Optional[Config] = None, provider: Optional[BaseAIProvider] = None):
        self.config = config or Config.load()
        self.validator = QualityValidator()
        self.runner = CodeRunner(self.config)

        if provider:
            self.provider = provider
        else:
            self.provider = self._init_provider()

    def _init_provider(self) -> BaseAIProvider:
        prov_name = getattr(self.config.ai, "provider", "offline").lower()
        if prov_name == "gemini":
            try:
                return GeminiProvider(self.config)
            except Exception:
                pass
        
        # Fallback to TaskSolver wrapper as default provider
        from .solver import TaskSolver
        return TaskSolver(self.config)

    def process_session(
        self,
        session: LabSession,
        manual: LabManual,
        custom_instructions: str = "",
    ) -> Tuple[List[TaskSolution], List[ExecutionResult], ValidationReport]:
        """
        Executes complete pipeline across session requirements:
        1. AI Code & explanation generation
        2. Local sandboxed execution
        3. Quality validation gate
        4. Session requirement state updates
        """
        session.status = "generating"
        solutions: List[TaskSolution] = []
        exec_results: List[ExecutionResult] = []

        # 1. Generate Solutions for all tasks
        for task in manual.tasks:
            req = session.get_task_requirement(task.task_id)
            if req:
                req.status = RequirementStatus.GENERATING

            combined_context = f"{manual.title}\n{manual.course_name or ''}\n{manual.context or ''}".strip()
            sol = self.provider.solve_task(task, custom_instructions=custom_instructions, lab_context=combined_context)
            solutions.append(sol)

            if req:
                req.code = sol.code
                req.explanation = sol.explanation
                req.status = RequirementStatus.GENERATED

        # 2. Execute each task locally
        session.status = "executing"
        for task, sol in zip(manual.tasks, solutions):
            req = session.get_task_requirement(task.task_id)
            if req:
                req.status = RequirementStatus.EXECUTING

            res = self.runner.execute(sol, sample_input=task.sample_input)

            # Auto-healing if execution failed and AI provider is active
            if not res.success and getattr(self.config.ai, "provider", "") != "offline":
                try:
                    healed_sol = self.provider.refine_solution(
                        task,
                        sol,
                        instruction=f"Fix execution error: {res.stderr or 'Non-zero exit code'}",
                    )
                    healed_res = self.runner.execute(healed_sol, sample_input=task.sample_input)
                    if healed_res.success:
                        sol = healed_sol
                        res = healed_res
                except Exception:
                    pass

            exec_results.append(res)

            if req:
                req.stdout = res.stdout
                req.stderr = res.stderr
                req.exit_code = res.exit_code
                req.execution_time = res.execution_time
                req.status = RequirementStatus.VALIDATED if res.success else RequirementStatus.FAILED

        # 3. Answer Viva and Analysis Questions
        if manual.analysis_questions:
            manual.analysis_answers = self.provider.solve_analysis_questions(
                manual.analysis_questions,
                course_name=manual.course_name,
                custom_instructions=custom_instructions,
            )
            for idx, (q, a) in enumerate(manual.analysis_answers, 1):
                for r in session.requirements:
                    if r.type == RequirementType.ANALYSIS_QUESTION and r.task_id == idx:
                        r.explanation = a
                        r.status = RequirementStatus.VALIDATED

        if manual.viva_questions:
            manual.viva_answers = self.provider.solve_viva_questions(
                manual.viva_questions,
                course_name=manual.course_name,
                custom_instructions=custom_instructions,
            )
            for idx, (q, a) in enumerate(manual.viva_answers, 1):
                for r in session.requirements:
                    if r.type == RequirementType.VIVA_QUESTION and r.task_id == idx:
                        r.explanation = a
                        r.status = RequirementStatus.VALIDATED

        # 4. Aggregate Quality Validation
        report = self.validator.validate_full_pipeline(manual, solutions, exec_results)
        session.status = "completed" if report.is_valid else "warning"

        return solutions, exec_results, report
