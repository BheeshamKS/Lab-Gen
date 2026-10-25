"""
Groq Cloud AI Provider for LabGenius.
Leverages Groq LPU inference (llama-3.3-70b-versatile, llama-3.1-8b-instant)
for ultra-fast lab generation, adversarial AI detection, and humanization.
"""

import json
import os
import re
from typing import Any, Dict, List, Optional, Tuple

import httpx

from ..config import Config
from ..parser import LabTask
from ..solver import TaskSolution
from .base import BaseAIProvider


class GroqProvider(BaseAIProvider):
    """Integrates Groq's high-speed LPU inference engine."""

    GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

    def __init__(self, config: Config):
        self.config = config
        self.api_key = (
            config.ai.api_key
            or os.environ.get("GROQ_API_KEY", "")
            or os.environ.get(config.ai.api_key_env, "")
        )
        self.model_name = getattr(config.ai, "groq_model", None) or "llama-3.3-70b-versatile"
        self._groq_client = None

    def _get_client(self):
        if self._groq_client is None:
            if not self.api_key:
                raise ValueError("GROQ_API_KEY is not set or provided.")
            try:
                from groq import Groq
                self._groq_client = Groq(api_key=self.api_key)
            except ImportError:
                self._groq_client = None
        return self._groq_client

    def generate_text(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> str:
        """Generates completion using Groq SDK or direct httpx REST call."""
        if not self.api_key:
            raise ValueError("GROQ_API_KEY is required for GroqProvider.")

        target_model = model or self.model_name or "llama-3.3-70b-versatile"
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        # Try official SDK first
        try:
            client = self._get_client()
            if client:
                res = client.chat.completions.create(
                    model=target_model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
                return res.choices[0].message.content or ""
        except Exception:
            pass

        # Fallback to direct HTTPX call
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": target_model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        with httpx.Client(timeout=30.0) as http_client:
            resp = http_client.post(self.GROQ_API_URL, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"] or ""

    def evaluate_ai_authenticity(self, text: str) -> Dict[str, Any]:
        """
        Adversarial AI detection judge: inspects text for chatbot syntax,
        uniformity, corporate fluff, and predictable structures.
        Returns {'ai_score': float (0.0-1.0), 'reasons': List[str]}.
        """
        system = (
            "You are an adversarial academic AI detector (comparable to Turnitin, GPTZero, CopyLeaks). "
            "Analyze the text rigorously for machine-generation patterns: uniform sentence cadence, "
            "corporate/academic filler, formulaic transition adverbs, sterile symmetry, lack of contractions, "
            "and absence of idiosyncratic human phrasing.\n"
            "Respond ONLY with a valid JSON object in this exact schema:\n"
            "{\n"
            '  "ai_score": 0.85,\n'
            '  "reasons": ["Uniform 18-word sentence cadence", "Formulaic transition starter", "Sterile uncontracted syntax"]\n'
            "}\n"
            "ai_score must be a float between 0.0 (100% human student writing) and 1.0 (100% AI generated)."
        )
        prompt = f"Analyze this text:\n\n\"\"\"\n{text}\n\"\"\""

        try:
            raw = self.generate_text(
                prompt=prompt,
                system_prompt=system,
                model="llama-3.3-70b-versatile",
                temperature=0.1,
                max_tokens=300,
            )
            # Parse JSON
            cleaned = raw.strip()
            if "```json" in cleaned:
                cleaned = cleaned.split("```json")[1].split("```")[0].strip()
            elif "```" in cleaned:
                cleaned = cleaned.split("```")[1].split("```")[0].strip()
            parsed = json.loads(cleaned)
            score = float(parsed.get("ai_score", 0.5))
            reasons = list(parsed.get("reasons", []))
            return {"ai_score": max(0.0, min(1.0, score)), "reasons": reasons}
        except Exception as e:
            return {"ai_score": None, "error": str(e), "reasons": [f"LLM detector evaluation unavailable ({e})"]}

    def humanize_text(
        self,
        text: str,
        profile: str = "academic_student",
        custom_instructions: str = "",
        feedback: str = "",
    ) -> str:
        """
        Rewrites AI text into genuine, high-burstiness human prose.
        Strictly obeys profile and user's custom guidance prompt.
        """
        system = (
            "You are an expert human academic writer and de-roboticizer. "
            "Your mission is to rewrite robotic AI-generated text into authentic, organic student writing "
            "that passes commercial AI detectors (GPTZero, Turnitin) with an AI score under 20%.\n\n"
            "MANDATORY HUMANIZATION RULES:\n"
            "1. HIGH BURSTINESS: Radically vary sentence length. Pair a punchy 4-word sentence with a longer descriptive sentence.\n"
            "2. NATURAL CONTRACTIONS: Use contractions naturally (it's, didn't, we're, don't, wasn't) instead of formal uncontracted forms.\n"
            "3. ZERO AI TELLS: Strictly ban words like 'delve', 'pivotal', 'crucial', 'testament', 'intricate tapestry', 'fosters', 'notably', 'in conclusion'.\n"
            "4. STRIP CODE CITATIONS IN PROSE: Replace internal variable names or code signatures (e.g. `df_task_sol_v1`) with descriptive plain English ('the data', 'the output array').\n"
            "5. NO CONVERSATIONAL FILLER: Output ONLY the rewritten text. Never say 'Here is the humanized version:' or 'Sure!'.\n"
        )
        if custom_instructions:
            system += f"\nUSER GUIDANCE (TOP PRIORITY - FOLLOW STRICTLY):\n{custom_instructions}\n"

        prompt = f"Profile: {profile}\n"
        if feedback:
            prompt += (
                f"\nCRITICAL CORRECTION FROM PREVIOUS PASS:\n"
                f"The previous attempt was flagged by the AI detector with the following issues:\n"
                f"{feedback}\n"
                f"You MUST fix these issues aggressively and ensure the text passes AI detection with <30% AI probability.\n"
            )

        prompt += f"\nText to rewrite:\n{text}"

        res = self.generate_text(
            prompt=prompt,
            system_prompt=system,
            model="llama-3.3-70b-versatile",
            temperature=0.85,
            max_tokens=2048,
        )
        return res.strip()

    def solve_task(
        self,
        task: LabTask,
        custom_instructions: str = "",
        lab_context: str = "",
    ) -> TaskSolution:
        lang = task.language or "python"
        ext = ".py" if lang == "python" else ".c" if lang == "c" else ".cpp" if lang == "cpp" else ".sql" if lang == "sql" else ".sh"
        fname = f"task_{task.task_id:02d}{ext}"
        student_name = getattr(getattr(self.config, 'student', None), 'name', 'Student')

        prompt = (
            f"Solve the following university lab task in {lang.upper()}.\n"
            f"Task Title: {task.title}\n"
            f"Task Description: {task.description}\n"
            f"Student Name: {student_name}\n\n"
            f"Respond ONLY with a JSON object in this format:\n"
            "{\n"
            f'  "code": "<executable {lang} code>",\n'
            '  "explanation": "<natural student explanation of approach>",\n'
            '  "expected_output": "<realistic console output>"\n'
            "}"
        )
        if custom_instructions:
            prompt += f"\nCustom Instructions: {custom_instructions}"

        raw = self.generate_text(prompt, temperature=0.3)
        cleaned = raw.strip()
        if "```json" in cleaned:
            cleaned = cleaned.split("```json")[1].split("```")[0].strip()
        elif "```" in cleaned:
            cleaned = cleaned.split("```")[1].split("```")[0].strip()
        data = json.loads(cleaned)

        return TaskSolution(
            task_id=task.task_id,
            filename=fname,
            language=lang,
            code=data.get("code", "").strip(),
            explanation=data.get("explanation", "").strip(),
            expected_output=data.get("expected_output", "").strip(),
        )

    def solve_analysis_questions(
        self,
        questions: List[str],
        course_name: str,
        custom_instructions: str = "",
    ) -> List[Tuple[str, str]]:
        if not questions:
            return []
        prompt = (
            f"Answer these {course_name} lab analysis questions as a knowledgeable student.\n"
            f"Questions:\n" + "\n".join(f"{i+1}. {q}" for i, q in enumerate(questions)) +
            "\n\nRespond with a JSON array of objects: [{\"question\": \"...\", \"answer\": \"...\"}]"
        )
        raw = self.generate_text(prompt, temperature=0.4)
        cleaned = raw.strip()
        if "```json" in cleaned:
            cleaned = cleaned.split("```json")[1].split("```")[0].strip()
        elif "```" in cleaned:
            cleaned = cleaned.split("```")[1].split("```")[0].strip()
        arr = json.loads(cleaned)
        return [(item["question"], item["answer"]) for item in arr]

    def solve_viva_questions(
        self,
        questions: List[str],
        course_name: str,
        custom_instructions: str = "",
    ) -> List[Tuple[str, str]]:
        if not questions:
            return []
        prompt = (
            f"Provide concise, direct viva-voce answers for these {course_name} questions.\n"
            f"Questions:\n" + "\n".join(f"{i+1}. {q}" for i, q in enumerate(questions)) +
            "\n\nRespond with a JSON array: [{\"question\": \"...\", \"answer\": \"...\"}]"
        )
        raw = self.generate_text(prompt, temperature=0.4)
        cleaned = raw.strip()
        if "```json" in cleaned:
            cleaned = cleaned.split("```json")[1].split("```")[0].strip()
        elif "```" in cleaned:
            cleaned = cleaned.split("```")[1].split("```")[0].strip()
        arr = json.loads(cleaned)
        return [(item["question"], item["answer"]) for item in arr]

    def refine_solution(
        self,
        task: LabTask,
        current_solution: TaskSolution,
        instruction: str,
    ) -> TaskSolution:
        prompt = (
            f"Refine this {current_solution.language} solution for task '{task.title}'.\n"
            f"Feedback: {instruction}\n"
            f"Current Code:\n{current_solution.code}\n\n"
            "Return JSON: {\"code\": \"...\", \"explanation\": \"...\", \"expected_output\": \"...\"}"
        )
        raw = self.generate_text(prompt, temperature=0.3)
        cleaned = raw.strip()
        if "```json" in cleaned:
            cleaned = cleaned.split("```json")[1].split("```")[0].strip()
        elif "```" in cleaned:
            cleaned = cleaned.split("```")[1].split("```")[0].strip()
        data = json.loads(cleaned)
        return TaskSolution(
            task_id=current_solution.task_id,
            filename=current_solution.filename,
            language=current_solution.language,
            code=data.get("code", current_solution.code),
            explanation=data.get("explanation", current_solution.explanation),
            expected_output=data.get("expected_output", current_solution.expected_output),
        )
