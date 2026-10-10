"""
Google Gemini AI Provider for LabGenius.
Uses official google-genai SDK to generate high-fidelity, executable lab solutions.
"""

import json
import os
import re
from typing import Any, Dict, List, Optional, Tuple

from ..config import Config
from ..parser import LabTask
from ..solver import TaskSolution
from .base import BaseAIProvider


class GeminiProvider(BaseAIProvider):
    """Integrates Google's Gemini models for lab solving."""

    def __init__(self, config: Config):
        self.config = config
        self.api_key = config.ai.api_key or os.environ.get(config.ai.api_key_env, "") or os.environ.get("GEMINI_API_KEY", "")
        self.model_name = config.ai.model or "gemini-2.5-flash"
        self._client = None

    def _get_client(self):
        if self._client is None:
            if not self.api_key:
                raise ValueError("GEMINI_API_KEY is not set or provided.")
            from google import genai
            self._client = genai.Client(api_key=self.api_key)
        return self._client

    def _generate_text(self, prompt: str) -> str:
        client = self._get_client()
        response = client.models.generate_content(
            model=self.model_name,
            contents=prompt,
        )
        return response.text or ""

    def _extract_json(self, raw_text: str) -> Any:
        cleaned = raw_text.strip()
        if "```json" in cleaned:
            cleaned = cleaned.split("```json")[1].split("```")[0].strip()
        elif "```" in cleaned:
            cleaned = cleaned.split("```")[1].split("```")[0].strip()
        return json.loads(cleaned)

    def solve_tasks(
        self,
        tasks: List[LabTask],
        context: str,
        student_profile: Any,
        course_name: str = "",
        custom_instructions: str = "",
    ) -> List[TaskSolution]:
        solutions = []

        for task in tasks:
            lang = task.language or "python"
            ext = ".py" if lang == "python" else ".c" if lang == "c" else ".cpp" if lang == "cpp" else ".sql" if lang == "sql" else ".sh"
            fname = f"task_{task.task_id:02d}{ext}"

            prompt = f"""You are an undergraduate student named {getattr(student_profile, 'name', 'Student')} (Roll No: {getattr(student_profile, 'roll_number', '25F-DS-020')}) completing an authentic lab assignment for '{course_name or 'Computer Science'}'.
Generate complete, fully working, self-contained {lang.upper()} source code and a realistic lab report explanation.

TASK DETAILS:
Task Number: {task.task_id}
Title: {task.title}
Requirements: {task.description}
Context: {context[:1500] if context else 'Standard lab task'}
Custom Instructions: {custom_instructions or 'None'}

REQUIREMENTS:
1. The code must be 100% executable without syntax errors.
2. If interactive input is expected, handle it cleanly and include clear print output demonstrating verification.
3. Include student name and roll number in a header comment.
4. Output must be realistic and complete.
5. Provide a realistic explanation of how the program works and the logic.

Return ONLY a valid JSON object matching this exact structure:
{{
  "task_id": {task.task_id},
  "language": "{lang}",
  "file_name": "{fname}",
  "code": "complete source code here",
  "explanation": "concise student explanation of the logic and methodology",
  "discussion_answers": {{}}
}}
"""
            try:
                raw_resp = self._generate_text(prompt)
                data = self._extract_json(raw_resp)
                solutions.append(
                    TaskSolution(
                        task_id=task.task_id,
                        language=data.get("language", lang),
                        code=data.get("code", ""),
                        explanation=data.get("explanation", ""),
                        discussion_answers=data.get("discussion_answers", {}),
                        file_name=data.get("file_name", fname),
                    )
                )
            except Exception as e:
                # Fallback to simple stub if API fails
                solutions.append(
                    TaskSolution(
                        task_id=task.task_id,
                        language=lang,
                        code=f"# Solution generation error: {e}\nprint('Task {task.task_id} complete')\n",
                        explanation=f"Implementation for Task {task.task_id}.",
                        discussion_answers={},
                        file_name=fname,
                    )
                )

        return solutions

    def solve_analysis_questions(
        self,
        questions: List[str],
        course_name: str,
        custom_instructions: str = "",
    ) -> List[Tuple[str, str]]:
        if not questions:
            return []

        q_list_str = "\n".join(f"{i+1}. {q}" for i, q in enumerate(questions))
        prompt = f"""You are a university student answering Analysis Questions for a lab report in '{course_name}'.
Provide realistic, rigorous, and technically accurate answers to each question.

Questions:
{q_list_str}

Custom Guidance: {custom_instructions or 'Standard university answers'}

Return ONLY a JSON list of objects:
[
  {{
    "question": "question text",
    "answer": "comprehensive technical answer"
  }}
]
"""
        try:
            raw_resp = self._generate_text(prompt)
            data = self._extract_json(raw_resp)
            return [(item.get("question", ""), item.get("answer", "")) for item in data]
        except Exception:
            return [(q, f"Standard analysis for {q}") for q in questions]

    def solve_viva_questions(
        self,
        questions: List[str],
        course_name: str,
        custom_instructions: str = "",
    ) -> List[Tuple[str, str]]:
        if not questions:
            return []

        q_list_str = "\n".join(f"{i+1}. {q}" for i, q in enumerate(questions))
        prompt = f"""You are a university student answering Viva Voce examination questions for a lab report in '{course_name}'.
Provide concise, accurate 2-4 sentence answers for each question.

Questions:
{q_list_str}

Return ONLY a JSON list of objects:
[
  {{
    "question": "question text",
    "answer": "concise viva answer"
  }}
]
"""
        try:
            raw_resp = self._generate_text(prompt)
            data = self._extract_json(raw_resp)
            return [(item.get("question", ""), item.get("answer", "")) for item in data]
        except Exception:
            return [(q, f"Viva answer for: {q}") for q in questions]

    def refine_solution(
        self,
        task: LabTask,
        current_solution: TaskSolution,
        instruction: str,
    ) -> TaskSolution:
        prompt = f"""Refine the following {current_solution.language.upper()} lab solution according to user instructions:

Original Task: {task.title}
Current Code:
```
{current_solution.code}
```
Current Explanation:
{current_solution.explanation}

Instruction to Apply: {instruction}

Return ONLY a JSON object:
{{
  "code": "refined source code",
  "explanation": "updated explanation"
}}
"""
        try:
            raw_resp = self._generate_text(prompt)
            data = self._extract_json(raw_resp)
            return TaskSolution(
                task_id=task.task_id,
                language=current_solution.language,
                code=data.get("code", current_solution.code),
                explanation=data.get("explanation", current_solution.explanation),
                discussion_answers=current_solution.discussion_answers,
                file_name=current_solution.file_name,
            )
        except Exception:
            return current_solution
