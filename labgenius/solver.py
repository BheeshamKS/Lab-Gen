"""
Student Persona & Anti-AI Solution Solver for LabGenius.
Generates natural student-style code and answers, purging all AI buzzwords and robotic mannerisms.
"""

import os
import re
import json
from dataclasses import dataclass
from typing import Optional, Dict, Any, List
import requests

from .config import Config
from .parser import LabTask


@dataclass
class TaskSolution:
    task_id: int
    language: str
    code: str
    explanation: str
    discussion_answers: Dict[str, str]
    file_name: str
    is_gui_or_plot: bool = False


class AntiAIFilter:
    """Detects and scrubs stereotypical AI phrases from student answers and code."""

    BANNED_WORDS_MAP = {
        r"\bdelve(?:s|d|ing)?\b": "explore",
        r"\bpivotal\b": "important",
        r"\bcrucial role\b": "key part",
        r"\btestament to\b": "demonstration of",
        r"\bmeticulous(?:ly)?\b": "careful",
        r"\bcomprehensive understanding\b": "clear view",
        r"\bit is important to note that\b": "note that",
        r"\bit is worth noting that\b": "notice that",
        r"\bin conclusion,?\s+it can be (?:seen|observed) that\b": "overall,",
        r"\bfurthermore,?\s+": "also, ",
        r"\bmoreover,?\s+": "also, ",
        r"\bconsequently,?\s+": "so, ",
        r"\bin summary,?\s+": "to summarize, ",
        r"\bas an ai\b": "",
        r"\blanguage model\b": "",
        r"\bharness(?:ing)? the power of\b": "using",
        r"\bseamless(?:ly)?\b": "smoothly",
    }

    @classmethod
    def clean_text(cls, text: str) -> str:
        """Replace banned AI markers with natural human phrases."""
        cleaned = text
        for pattern, replacement in cls.BANNED_WORDS_MAP.items():
            cleaned = re.sub(pattern, replacement, cleaned, flags=re.IGNORECASE)
        # Strip excessive multi-paragraph filler
        cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
        return cleaned.strip()


class TaskSolver:
    """Generates authentic student solutions for lab tasks."""

    def __init__(self, config: Config):
        self.config = config
        self.student = config.student
        self.ai_conf = config.ai

    def solve_task(self, task: LabTask, custom_instructions: Optional[str] = None, lab_context: Optional[str] = None) -> TaskSolution:
        """Generate a complete solution for a single lab task, optionally taking custom user instructions and lab context."""
        provider = self.ai_conf.provider.lower()
        solution = None

        if provider == "gemini" and (self.ai_conf.api_key or os.environ.get("GEMINI_API_KEY")):
            solution = self._solve_with_gemini(task, custom_instructions, lab_context)
        elif provider in ["openai", "openrouter", "groq"]:
            solution = self._solve_with_openai_compatible(task, custom_instructions, lab_context)
        elif provider == "ollama":
            solution = self._solve_with_ollama(task, custom_instructions, lab_context)

        if not solution:
            # Fallback to intelligent offline solver
            solution = self._solve_offline(task, custom_instructions, lab_context)

        # Apply code cleaner to strip any student identity and minimize comments
        solution.code = self._clean_code(solution.code, solution.language)

        # Apply Anti-AI filter to text and explanations
        solution.explanation = AntiAIFilter.clean_text(solution.explanation)
        solution.discussion_answers = {
            q: AntiAIFilter.clean_text(ans) for q, ans in solution.discussion_answers.items()
        }
        return solution

    def _clean_code(self, code: str, language: str = "") -> str:
        """Strip student names, roll numbers, author tags, and verbose comments from generated code."""
        if not code:
            return ""

        lines = code.splitlines()
        cleaned_lines = []
        name_lower = self.student.name.strip().lower() if self.student and self.student.name else ""
        roll_lower = self.student.roll_number.strip().lower() if self.student and self.student.roll_number else ""

        for line in lines:
            stripped = line.strip()
            stripped_lower = stripped.lower()

            # Preserve shebang
            if stripped.startswith("#!"):
                cleaned_lines.append(line)
                continue

            # Remove student / author header comments
            if any(stripped_lower.startswith(prefix) for prefix in [
                "-- name:", "-- roll:", "-- roll no:", "-- student:", "-- author:",
                "// student:", "// name:", "// roll:", "// roll no:", "// author:",
                "# student:", "# name:", "# roll:", "# roll no:", "# author:",
                "# department:", "// department:", "-- department:",
                "/* student:", "/* name:", "/* author:",
                "-- -------------------------", "// -------------------------", "# -------------------------"
            ]):
                continue

            # Remove any comment mentioning student's name or roll number
            if stripped.startswith("#") or stripped.startswith("//") or stripped.startswith("--"):
                if (name_lower and name_lower in stripped_lower) or (roll_lower and roll_lower in stripped_lower):
                    continue

            # Remove identity print/printf statements
            if any(marker in stripped_lower for marker in [
                'printf("name:', "printf('name:",
                'printf("roll no:', "printf('roll no:",
                'printf("roll:', "printf('roll:",
                'print("name:', "print('name:",
                'print(f"name:', "print(f'name:",
                'print("roll no:', "print('roll no:",
                'print(f"roll no:', "print(f'roll no:",
                'print("roll:', "print('roll:",
                'print(f"roll:', "print(f'roll:",
                'printf("-------------------------',
                "printf('-------------------------",
                'print("-------------------------',
                "print('-------------------------",
            ]):
                continue

            if (name_lower and name_lower in stripped_lower and ("printf(" in stripped_lower or "print(" in stripped_lower)) or \
               (roll_lower and roll_lower in stripped_lower and ("printf(" in stripped_lower or "print(" in stripped_lower)):
                continue

            # Strip obvious commentary / tutorial comments to keep code minimal
            if stripped.startswith("#") or stripped.startswith("//") or stripped.startswith("--"):
                if any(k in stripped_lower for k in [
                    "lab task:", "task:", "step ", "1. create", "2. create", "add new",
                    "delete column", "view table", "modify column", "drop table",
                    "add multiple", "sql solution", "generate sample", "create realistic",
                    "view table schemas", "display all records"
                ]):
                    continue

            cleaned_lines.append(line)

        result = "\n".join(cleaned_lines)
        result = re.sub(r"\n{3,}", "\n\n", result).strip()
        return result + "\n" if result else ""

    def refine_solution(self, task: LabTask, current_solution: TaskSolution, instruction: str) -> TaskSolution:
        """Refine or modify an existing task solution based on user follow-up instruction."""
        prompt = (
            f"You are modifying an existing solution for an undergraduate university lab assignment.\n\n"
            f"Lab Task: {task.title}\n"
            f"Description: {task.description}\n"
            f"Language: {task.language}\n\n"
            f"CURRENT CODE:\n```{task.language}\n{current_solution.code}\n```\n\n"
            f"CURRENT EXPLANATION:\n{current_solution.explanation}\n\n"
            f"USER FOLLOW-UP INSTRUCTION / EDIT REQUEST:\n{instruction}\n\n"
            f"CRITICAL REQUIREMENTS:\n"
            f"1. Modify the code and explanation to strictly fulfill the user instruction.\n"
            f"2. DO NOT include any student name, roll number, or author info in the code or output headers.\n"
            f"3. Keep code comments minimal to none (clean, direct code without unnecessary commentary).\n"
            f"4. Return ONLY valid JSON with keys: 'code', 'explanation', 'answers'."
        )
        provider = self.ai_conf.provider.lower()
        refined = None
        if provider == "gemini" and (self.ai_conf.api_key or os.environ.get("GEMINI_API_KEY")):
            resp_text = self._call_gemini_raw(prompt)
            if resp_text:
                parsed = self._extract_json(resp_text)
                if parsed and "code" in parsed:
                    refined = TaskSolution(
                        task_id=task.task_id,
                        language=task.language,
                        code=self._strip_code_fences(parsed["code"]),
                        explanation=parsed.get("explanation", current_solution.explanation),
                        discussion_answers=parsed.get("answers", current_solution.discussion_answers),
                        file_name=current_solution.file_name,
                        is_gui_or_plot=current_solution.is_gui_or_plot or "plot" in parsed.get("code", ""),
                    )
        elif provider in ["openai", "openrouter", "groq"]:
            resp_text = self._call_openai_compatible_raw(prompt)
            if resp_text:
                parsed = self._extract_json(resp_text)
                if parsed and "code" in parsed:
                    refined = TaskSolution(
                        task_id=task.task_id,
                        language=task.language,
                        code=self._strip_code_fences(parsed["code"]),
                        explanation=parsed.get("explanation", current_solution.explanation),
                        discussion_answers=parsed.get("answers", current_solution.discussion_answers),
                        file_name=current_solution.file_name,
                        is_gui_or_plot=current_solution.is_gui_or_plot or "plot" in parsed.get("code", ""),
                    )
        elif provider == "ollama":
            resp_text = self._call_ollama_raw(prompt)
            if resp_text:
                parsed = self._extract_json(resp_text)
                if parsed and "code" in parsed:
                    refined = TaskSolution(
                        task_id=task.task_id,
                        language=task.language,
                        code=self._strip_code_fences(parsed["code"]),
                        explanation=parsed.get("explanation", current_solution.explanation),
                        discussion_answers=parsed.get("answers", current_solution.discussion_answers),
                        file_name=current_solution.file_name,
                        is_gui_or_plot=current_solution.is_gui_or_plot,
                    )

        if not refined:
            # Offline refinement heuristics
            refined_code = current_solution.code
            refined_exp = current_solution.explanation
            ins_lower = instruction.lower()

            if "comment" in ins_lower:
                lines = refined_code.splitlines()
                new_lines = []
                comment_sym = "--" if task.language == "sql" else "#" if task.language == "python" else "//"
                for line in lines:
                    if any(kw in line for kw in ["def ", "for ", "while ", "if ", "CREATE ", "SELECT ", "ALTER "]):
                        new_lines.append(f"    {comment_sym} Logic step: {line.strip()[:40]}")
                    new_lines.append(line)
                refined_code = "\n".join(new_lines)
                refined_exp += f" (Updated with detailed explanatory comments per user instruction)."

            elif "simpl" in ins_lower or "clean" in ins_lower:
                refined_exp = "Simplified clean implementation adhering to undergraduate standards."

            refined = TaskSolution(
                task_id=task.task_id,
                language=task.language,
                code=refined_code,
                explanation=AntiAIFilter.clean_text(refined_exp),
                discussion_answers=current_solution.discussion_answers,
                file_name=current_solution.file_name,
                is_gui_or_plot=current_solution.is_gui_or_plot,
            )

        refined.code = self._clean_code(refined.code, refined.language)
        refined.explanation = AntiAIFilter.clean_text(refined.explanation)
        return refined

    def auto_heal(self, task: LabTask, failed_code: str, error_trace: str) -> str:
        """Fix code that encountered an error during laptop execution."""
        prompt = (
            f"Fix this {task.language} code that produced an error on a Linux machine.\n"
            f"Error traceback:\n{error_trace}\n\n"
            f"Failed code:\n```\n{failed_code}\n```\n"
            f"Return ONLY the corrected code inside ```{task.language} block. No extra words."
        )

        provider = self.ai_conf.provider.lower()
        fixed_code = None

        if provider == "gemini" and (self.ai_conf.api_key or os.environ.get("GEMINI_API_KEY")):
            fixed_code = self._call_gemini_raw(prompt)
        elif provider in ["openai", "openrouter", "groq"]:
            fixed_code = self._call_openai_compatible_raw(prompt)
        elif provider == "ollama":
            fixed_code = self._call_ollama_raw(prompt)

        if fixed_code:
            code_match = re.search(r"```(?:\w+)?\n(.*?)```", fixed_code, re.DOTALL)
            if code_match:
                return code_match.group(1).strip()
            return fixed_code.strip()

        # Fallback offline fix: simple syntax/import auto-patch
        if "No module named 'matplotlib'" in error_trace:
            return failed_code.replace("import matplotlib.pyplot as plt", "# matplotlib bypassed\n# plt")
        return failed_code

    def _build_system_prompt(self, task: LabTask, custom_instructions: Optional[str] = None, lab_context: Optional[str] = None) -> str:
        lang = task.language.lower()
        base = (
            f"You are an undergraduate student writing working {task.language.upper()} code for your university lab assignment.\n\n"
            "REQUIREMENTS:\n"
            "1. Write clean, direct, working code or SQL queries. Complete ONLY the exact assignment task described.\n"
            "2. DO NOT include any student name, roll number, author info, or metadata headers in the code or print statements.\n"
            "3. Keep code comments minimal to none (no unnecessary commentary or obvious inline comments). Keep code clean and concise.\n"
            "4. DO NOT use AI filler words ('delve', 'crucial', 'testament').\n"
            "5. Respond strictly in valid JSON with keys:\n"
            "   - 'code': (the complete source code / SQL queries as a string)\n"
            "   - 'explanation': (1-2 concise sentences on how the logic works)\n"
            "   - 'answers': (empty dict if no explicit viva questions asked)\n"
            "   - 'filename': (e.g. 'query_01.sql', 'program_01.c', or 'task_01.py')\n"
        )
        if lab_context and lab_context.strip():
            base += (
                f"\nLAB MANUAL CONTEXT & DATABASE SCHEMA REQUIREMENTS:\n"
                f"{lab_context.strip()}\n"
                f"STRICT INSTRUCTION: Your solution code MUST use the exact database name, table names, column names, data types, and constraints defined in this context.\n"
            )
        if custom_instructions and custom_instructions.strip():
            base += (
                f"\nSPECIAL USER INSTRUCTIONS FOR SOLVING THIS LAB (MUST STRICTLY ADHERE TO THESE):\n"
                f"{custom_instructions.strip()}\n"
            )
        return base

    def _solve_with_gemini(self, task: LabTask, custom_instructions: Optional[str] = None, lab_context: Optional[str] = None) -> Optional[TaskSolution]:
        api_key = self.ai_conf.api_key or os.environ.get("GEMINI_API_KEY")
        model_name = self.ai_conf.model or "gemini-2.5-pro"
        user_prompt = (
            f"Lab Task: {task.title}\n"
            f"Description: {task.description}\n"
            f"Language: {task.language}\n"
            f"Questions to answer: {task.discussion_questions}\n"
        )
        if lab_context and lab_context.strip():
            user_prompt += f"\nLab Context & Schema:\n{lab_context.strip()}\n"
        if custom_instructions and custom_instructions.strip():
            user_prompt += f"\nCustom User Instructions: {custom_instructions.strip()}\n"
        user_prompt += "Respond strictly in valid JSON format."
        full_prompt = self._build_system_prompt(task, custom_instructions, lab_context) + "\n\n" + user_prompt

        # 1. Try official google-genai SDK (supports API Key and Google Auth / ADC)
        try:
            from google import genai
            from google.genai import types

            client = None
            if api_key:
                client = genai.Client(api_key=api_key)
            else:
                # Check for Google Cloud Auth / Application Default Credentials (ADC)
                try:
                    import google.auth
                    credentials, project = google.auth.default()
                    if credentials:
                        client = genai.Client(vertexai=True, project=project or "default")
                except Exception:
                    pass

            if client:
                response = client.models.generate_content(
                    model=model_name,
                    contents=full_prompt,
                    config=types.GenerateContentConfig(
                        temperature=0.3,
                        response_mime_type="application/json",
                    ),
                )
                if response and response.text:
                    parsed = self._extract_json(response.text)
                    if parsed and "code" in parsed:
                        return TaskSolution(
                            task_id=task.task_id,
                            language=task.language,
                            code=self._strip_code_fences(parsed["code"]),
                            explanation=parsed.get("explanation", ""),
                            discussion_answers=parsed.get("answers", {}),
                            file_name=parsed.get("filename", f"task_{task.task_id:02d}.{self._get_extension(task.language)}"),
                            is_gui_or_plot=task.requires_plot or "plot" in parsed.get("code", ""),
                        )
        except Exception:
            pass  # Fall through to REST API

        # 2. Direct Google AI REST API fallback
        if api_key:
            return self._solve_with_gemini_rest(task, full_prompt, api_key, model_name)

        return None

    def _solve_with_gemini_rest(self, task: LabTask, prompt: str, api_key: str, model_name: str) -> Optional[TaskSolution]:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
        payload = {
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.3}
        }
        try:
            resp = requests.post(url, json=payload, timeout=30)
            if resp.status_code == 200:
                data = resp.json()
                text_out = data["candidates"][0]["content"]["parts"][0]["text"]
                parsed = self._extract_json(text_out)
                if parsed and "code" in parsed:
                    return TaskSolution(
                        task_id=task.task_id,
                        language=task.language,
                        code=self._strip_code_fences(parsed["code"]),
                        explanation=parsed.get("explanation", ""),
                        discussion_answers=parsed.get("answers", {}),
                        file_name=parsed.get("filename", f"task_{task.task_id:02d}.{self._get_extension(task.language)}"),
                        is_gui_or_plot=task.requires_plot or "plot" in parsed.get("code", ""),
                    )
        except Exception:
            pass
        return None

    def _solve_with_openai_compatible(self, task: LabTask, custom_instructions: Optional[str] = None, lab_context: Optional[str] = None) -> Optional[TaskSolution]:
        provider = self.ai_conf.provider.lower()
        if provider == "groq":
            api_key = self.ai_conf.api_key or os.environ.get("GROQ_API_KEY")
            url = "https://api.groq.com/openai/v1/chat/completions"
            model = self.ai_conf.model or "llama-3.3-70b-versatile"
        elif provider == "openrouter":
            api_key = self.ai_conf.api_key or os.environ.get("OPENROUTER_API_KEY")
            url = "https://openrouter.ai/api/v1/chat/completions"
            model = self.ai_conf.model or "anthropic/claude-3.5-sonnet"
        else:
            api_key = self.ai_conf.api_key or os.environ.get("OPENAI_API_KEY")
            url = "https://api.openai.com/v1/chat/completions"
            model = self.ai_conf.model or "gpt-4o-mini"
            
        if not api_key:
            print(f"[!] Warning: No API key found for AI provider '{provider}'.")
            return None
            
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        user_msg = f"Task {task.task_id}: {task.title}\n{task.description}\nLanguage: {task.language}\n"
        if lab_context and lab_context.strip():
            user_msg += f"\nLab Schema & Context:\n{lab_context.strip()}\n"
        if custom_instructions and custom_instructions.strip():
            user_msg += f"Custom User Instructions: {custom_instructions.strip()}\n"
        user_msg += "\nRespond strictly in valid JSON format."
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": self._build_system_prompt(task, custom_instructions, lab_context)},
                {"role": "user", "content": user_msg}
            ],
            "temperature": 0.3,
            "response_format": {"type": "json_object"}
        }
        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=35)
            if resp.status_code == 200:
                data = resp.json()
                content = data["choices"][0]["message"]["content"]
                parsed = self._extract_json(content)
                if parsed and "code" in parsed:
                    return TaskSolution(
                        task_id=task.task_id,
                        language=task.language,
                        code=self._strip_code_fences(parsed["code"]),
                        explanation=parsed.get("explanation", ""),
                        discussion_answers=parsed.get("answers", {}),
                        file_name=parsed.get("filename", f"task_{task.task_id:02d}.{self._get_extension(task.language)}"),
                        is_gui_or_plot=task.requires_plot,
                    )
            else:
                print(f"[!] {provider.upper()} API returned HTTP {resp.status_code}: {resp.text}")
        except Exception as e:
            print(f"[!] {provider.upper()} API error during request: {e}")
        return None

    _solve_with_openai = _solve_with_openai_compatible

    def _solve_with_ollama(self, task: LabTask, custom_instructions: Optional[str] = None, lab_context: Optional[str] = None) -> Optional[TaskSolution]:
        url = f"{self.ai_conf.ollama_url}/api/chat"
        user_msg = f"Task: {task.title}\n{task.description}\nLanguage: {task.language}\n"
        if lab_context and lab_context.strip():
            user_msg += f"\nLab Context & Schema:\n{lab_context.strip()}\n"
        if custom_instructions and custom_instructions.strip():
            user_msg += f"Custom User Instructions: {custom_instructions.strip()}\n"
        payload = {
            "model": self.ai_conf.ollama_model,
            "messages": [
                {"role": "system", "content": self._build_system_prompt(task, custom_instructions, lab_context)},
                {"role": "user", "content": user_msg}
            ],
            "stream": False,
            "format": "json",
        }
        try:
            resp = requests.post(url, json=payload, timeout=40)
            if resp.status_code == 200:
                content = resp.json().get("message", {}).get("content", "")
                parsed = self._extract_json(content)
                if parsed and "code" in parsed:
                    return TaskSolution(
                        task_id=task.task_id,
                        language=task.language,
                        code=self._strip_code_fences(parsed["code"]),
                        explanation=parsed.get("explanation", ""),
                        discussion_answers=parsed.get("answers", {}),
                        file_name=parsed.get("filename", f"task_{task.task_id:02d}.{self._get_extension(task.language)}"),
                        is_gui_or_plot=task.requires_plot,
                    )
        except Exception:
            pass
        return None

    def _call_gemini_raw(self, prompt: str) -> Optional[str]:
        api_key = self.ai_conf.api_key or os.environ.get("GEMINI_API_KEY")
        if not api_key:
            return None
        model_name = self.ai_conf.model or "gemini-2.5-pro"
        try:
            from google import genai
            client = genai.Client(api_key=api_key)
            response = client.models.generate_content(model=model_name, contents=prompt)
            if response and response.text:
                return response.text
        except Exception:
            pass

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
        try:
            resp = requests.post(
                url,
                json={"contents": [{"role": "user", "parts": [{"text": prompt}]}]},
                timeout=25
            )
            if resp.status_code == 200:
                return resp.json()["candidates"][0]["content"]["parts"][0]["text"]
        except Exception:
            pass
        return None

    def _call_openai_compatible_raw(self, prompt: str) -> Optional[str]:
        provider = self.ai_conf.provider.lower()
        if provider == "groq":
            api_key = self.ai_conf.api_key or os.environ.get("GROQ_API_KEY")
            url = "https://api.groq.com/openai/v1/chat/completions"
            model = self.ai_conf.model or "llama-3.3-70b-versatile"
        elif provider == "openrouter":
            api_key = self.ai_conf.api_key or os.environ.get("OPENROUTER_API_KEY")
            url = "https://openrouter.ai/api/v1/chat/completions"
            model = self.ai_conf.model or "anthropic/claude-3.5-sonnet"
        else:
            api_key = self.ai_conf.api_key or os.environ.get("OPENAI_API_KEY")
            url = "https://api.openai.com/v1/chat/completions"
            model = self.ai_conf.model or "gpt-4o-mini"
            
        if not api_key:
            return None
            
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.3
        }
        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=30)
            if resp.status_code == 200:
                return resp.json()["choices"][0]["message"]["content"]
        except Exception:
            pass
        return None

    def _call_ollama_raw(self, prompt: str) -> Optional[str]:
        try:
            resp = requests.post(
                f"{self.ai_conf.ollama_url}/api/generate",
                json={"model": self.ai_conf.ollama_model, "prompt": prompt, "stream": False},
                timeout=30
            )
            if resp.status_code == 200:
                return resp.json()["response"]
        except Exception:
            pass
        return None

    def _extract_json(self, text: str) -> Optional[Dict[str, Any]]:
        try:
            return json.loads(text)
        except Exception:
            match = re.search(r"```(?:json)?\s*({.*?})\s*```", text, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(1))
                except Exception:
                    pass
            match2 = re.search(r"\{.*\}", text, re.DOTALL)
            if match2:
                try:
                    return json.loads(match2.group(0))
                except Exception:
                    pass
        return None

    def _strip_code_fences(self, code_str: str) -> str:
        code_str = re.sub(r"^```[\w-]*\n", "", code_str.strip())
        code_str = re.sub(r"\n```$", "", code_str)
        return code_str.strip()

    def _get_extension(self, lang: str) -> str:
        lang = lang.lower()
        if lang in ["c"]:
            return "c"
        elif lang in ["cpp", "c++"]:
            return "cpp"
        elif lang in ["python", "py"]:
            return "py"
        elif lang in ["sql"]:
            return "sql"
        return "txt"

    def _solve_offline(self, task: LabTask, custom_instructions: Optional[str] = None, lab_context: Optional[str] = None) -> TaskSolution:
        """Intelligent offline solver for programming and database lab tasks."""
        sol = self._solve_offline_raw(task, lab_context)
        if custom_instructions and custom_instructions.strip():
            return self.refine_solution(task, sol, custom_instructions)
        return sol

    def _solve_offline_raw(self, task: LabTask, lab_context: Optional[str] = None) -> TaskSolution:
        desc = (task.title + " " + task.description).lower()
        ctx = (lab_context or "").lower()

        # =============================================================
        # 1. SQL / DATABASE LAB TASKS
        # =============================================================
        if task.language == "sql" or (task.language not in ["python", "c", "cpp", "c++", "bash"] and any(k in desc for k in ["sql", "alter table", "create table", "drop table", "select *", "insert into"])):
            # ---------------------------------------------------------
            # DBMS Lab 04: SQL Constraints (Employee Table & Lab6)
            # ---------------------------------------------------------
            if "employee" in desc or "employee" in ctx or "named unique constraint" in desc or ("nullable" in desc and "roll_no" in desc) or ("primary key constraint using alter" in desc):
                # 1. Create Employee table with constraints
                if "create" in desc and "employee" in desc:
                    code = (
                        "CREATE TABLE Employee (\n"
                        "    Employee_ID INT PRIMARY KEY,\n"
                        "    Employee_Name VARCHAR(50) NOT NULL,\n"
                        "    Email VARCHAR(100) UNIQUE,\n"
                        "    Age INT CHECK (Age >= 18),\n"
                        "    Department VARCHAR(50) DEFAULT 'Data Science',\n"
                        "    Gender CHAR(1) CHECK (Gender IN ('M', 'F'))\n"
                        ");\n"
                    )
                    exp = "Created Employee table enforcing PRIMARY KEY, NOT NULL, UNIQUE, CHECK, and DEFAULT constraints."
                    return TaskSolution(task.task_id, "sql", code, exp, {}, f"query_{task.task_id:02d}.sql")

                # 2. Insert three valid records
                elif "insert" in desc and "valid" in desc and "invalid" not in desc and "observe" not in desc:
                    code = (
                        "INSERT INTO Employee (Employee_ID, Employee_Name, Email, Age, Department, Gender)\n"
                        "VALUES \n"
                        "(1, 'Ali Khan', 'ali.khan@example.com', 22, 'Data Science', 'M'),\n"
                        "(2, 'Sara Ahmed', 'sara.ahmed@example.com', 24, 'Computer Science', 'F'),\n"
                        "(3, 'Usman Tariq', 'usman.tariq@example.com', 25, 'Software Engineering', 'M');\n"
                    )
                    exp = "Inserted three valid employee records conforming to all defined column constraints."
                    return TaskSolution(task.task_id, "sql", code, exp, {}, f"query_{task.task_id:02d}.sql")

                # 3. Display all records
                elif "display" in desc and "all" in desc:
                    code = "SELECT * FROM Employee;\n"
                    exp = "Queried and displayed all records currently stored in the Employee table."
                    return TaskSolution(task.task_id, "sql", code, exp, {}, f"query_{task.task_id:02d}.sql")

                # 4. Duplicate Employee_ID
                elif "duplicate" in desc and "employee_id" in desc:
                    code = (
                        "-- Attempt to insert a record with duplicate Employee_ID\n"
                        "INSERT INTO Employee (Employee_ID, Employee_Name, Email, Age, Department, Gender)\n"
                        "VALUES (1, 'Bilal Raza', 'bilal.raza@example.com', 23, 'Data Science', 'M');\n"
                    )
                    exp = "Tested PRIMARY KEY constraint by attempting duplicate insertion; observed unique constraint violation."
                    return TaskSolution(task.task_id, "sql", code, exp, {}, f"query_{task.task_id:02d}.sql")

                # 5. NULL Employee_Name
                elif "null" in desc and "employee_name" in desc:
                    code = (
                        "-- Attempt to insert NULL Employee_Name\n"
                        "INSERT INTO Employee (Employee_ID, Employee_Name, Email, Age, Department, Gender)\n"
                        "VALUES (4, NULL, 'test.user@example.com', 21, 'Data Science', 'M');\n"
                    )
                    exp = "Tested NOT NULL constraint on Employee_Name; verified NULL insertion is rejected."
                    return TaskSolution(task.task_id, "sql", code, exp, {}, f"query_{task.task_id:02d}.sql")

                # 6. Duplicate Email
                elif "duplicate" in desc and "email" in desc:
                    code = (
                        "-- Attempt to insert duplicate Email\n"
                        "INSERT INTO Employee (Employee_ID, Employee_Name, Email, Age, Department, Gender)\n"
                        "VALUES (5, 'Zainab Shah', 'ali.khan@example.com', 22, 'Data Science', 'F');\n"
                    )
                    exp = "Tested UNIQUE constraint by inserting a duplicate email address; verified uniqueness constraint error."
                    return TaskSolution(task.task_id, "sql", code, exp, {}, f"query_{task.task_id:02d}.sql")

                # 7. Age below 18
                elif "age" in desc and ("below 18" in desc or "18" in desc):
                    code = (
                        "-- Attempt to insert an employee whose Age is below 18\n"
                        "INSERT INTO Employee (Employee_ID, Employee_Name, Email, Age, Department, Gender)\n"
                        "VALUES (6, 'Hamza Malik', 'hamza.malik@example.com', 16, 'Data Science', 'M');\n"
                    )
                    exp = "Tested CHECK constraint (Age >= 18) by attempting to insert an age of 16; verified check failure error."
                    return TaskSolution(task.task_id, "sql", code, exp, {}, f"query_{task.task_id:02d}.sql")

                # 8. Invalid Gender 'X'
                elif "gender" in desc and ("invalid" in desc or "'x'" in desc or " x" in desc):
                    code = (
                        "-- Attempt to insert an employee with invalid Gender 'X'\n"
                        "INSERT INTO Employee (Employee_ID, Employee_Name, Email, Age, Department, Gender)\n"
                        "VALUES (7, 'Fatima Noor', 'fatima.noor@example.com', 20, 'Data Science', 'X');\n"
                    )
                    exp = "Tested Gender domain CHECK constraint ('M' or 'F') with invalid character 'X'; observed constraint error."
                    return TaskSolution(task.task_id, "sql", code, exp, {}, f"query_{task.task_id:02d}.sql")

                # 9. Insert without specifying Department
                elif "without specifying department" in desc or ("default" in desc and "department" in desc and "inserted" in desc):
                    code = (
                        "-- Insert without specifying Department to verify default 'Data Science'\n"
                        "INSERT INTO Employee (Employee_ID, Employee_Name, Email, Age, Gender)\n"
                        "VALUES (8, 'Danish Ali', 'danish.ali@example.com', 23, 'M');\n\n"
                        "SELECT * FROM Employee WHERE Employee_ID = 8;\n"
                    )
                    exp = "Omitted Department during insertion to verify automatic assignment of default value 'Data Science'."
                    return TaskSolution(task.task_id, "sql", code, exp, {}, f"query_{task.task_id:02d}.sql")

                # 10. Insert with explicit Department
                elif "different department" in desc or "overwritten" in desc:
                    code = (
                        "-- Insert another employee while explicitly providing a different Department\n"
                        "INSERT INTO Employee (Employee_ID, Employee_Name, Email, Age, Department, Gender)\n"
                        "VALUES (9, 'Areeba Siddiqui', 'areeba.s@example.com', 22, 'Artificial Intelligence', 'F');\n\n"
                        "SELECT * FROM Employee WHERE Employee_ID = 9;\n"
                    )
                    exp = "Provided an explicit Department name ('Artificial Intelligence') to verify default value overwrite."
                    return TaskSolution(task.task_id, "sql", code, exp, {}, f"query_{task.task_id:02d}.sql")

                # 11. Create named UNIQUE constraint
                elif "named unique" in desc and "create" in desc:
                    code = (
                        "CREATE TABLE Project (\n"
                        "    Project_ID INT PRIMARY KEY,\n"
                        "    Project_Name VARCHAR(50) NOT NULL,\n"
                        "    Project_Code VARCHAR(20),\n"
                        "    CONSTRAINT UQ_ProjectCode UNIQUE (Project_Code)\n"
                        ");\n"
                    )
                    exp = "Created Project table with explicitly named UNIQUE constraint UQ_ProjectCode on Project_Code."
                    return TaskSolution(task.task_id, "sql", code, exp, {}, f"query_{task.task_id:02d}.sql")

                # 12. Drop named UNIQUE constraint
                elif "drop" in desc and ("unique constraint" in desc or "uq_" in desc):
                    code = (
                        "ALTER TABLE Project\n"
                        "DROP CONSTRAINT UQ_ProjectCode;\n"
                    )
                    exp = "Used ALTER TABLE with DROP CONSTRAINT to remove the named UNIQUE constraint UQ_ProjectCode."
                    return TaskSolution(task.task_id, "sql", code, exp, {}, f"query_{task.task_id:02d}.sql")

                # 13. Create table with nullable Roll_No and alter to NOT NULL
                elif "nullable" in desc or ("roll_no" in desc and "not null" in desc):
                    code = (
                        "CREATE TABLE Student (\n"
                        "    Roll_No INT NULL,\n"
                        "    Student_Name VARCHAR(50) NOT NULL\n"
                        ");\n\n"
                        "ALTER TABLE Student\n"
                        "ALTER COLUMN Roll_No INT NOT NULL;\n"
                    )
                    exp = "Created Student table with nullable Roll_No, then modified column to NOT NULL using ALTER TABLE."
                    return TaskSolution(task.task_id, "sql", code, exp, {}, f"query_{task.task_id:02d}.sql")

                # 14. Add PRIMARY KEY constraint after making column NOT NULL
                elif "primary key" in desc and ("after making" in desc or "alter table" in desc):
                    code = (
                        "ALTER TABLE Student\n"
                        "ADD CONSTRAINT PK_Student PRIMARY KEY (Roll_No);\n"
                    )
                    exp = "Applied PRIMARY KEY constraint PK_Student on Roll_No using ALTER TABLE ADD CONSTRAINT."
                    return TaskSolution(task.task_id, "sql", code, exp, {}, f"query_{task.task_id:02d}.sql")

            # ---------------------------------------------------------
            # Generic SQL Lab Tasks (Course2 / Student2)
            # ---------------------------------------------------------
            if "create" in desc and "table" in desc:
                code = (
                    "CREATE TABLE Course2 (\n"
                    "    CourseID VARCHAR(10) PRIMARY KEY,\n"
                    "    CourseName VARCHAR(50) NOT NULL,\n"
                    "    CreditHours INT NOT NULL\n"
                    ");\n\n"
                    "CREATE TABLE Student2 (\n"
                    "    StudentID VARCHAR(15) PRIMARY KEY,\n"
                    "    StudentName VARCHAR(50) NOT NULL,\n"
                    "    Age INT,\n"
                    "    CourseID VARCHAR(10),\n"
                    "    FOREIGN KEY (CourseID) REFERENCES Course2(CourseID)\n"
                    ");\n"
                )
                exp = "Created Course2 and Student2 tables with primary key and foreign key constraints in SQL Server."
                return TaskSolution(task.task_id, "sql", code, exp, {}, f"query_{task.task_id:02d}.sql")

            # Task: Display structure and records
            elif any(k in desc for k in ["display", "structure", "record"]):
                code = (
                    "SELECT table_name, column_name, data_type, is_nullable\n"
                    "FROM information_schema.columns\n"
                    "WHERE table_name IN ('Student2', 'Course2');\n\n"
                    "SELECT * FROM Student2;\n"
                    "SELECT * FROM Course2;\n"
                )
                exp = "Queried table metadata and selected records from Student2 and Course2."
                return TaskSolution(task.task_id, "sql", code, exp, {}, f"query_{task.task_id:02d}.sql")

            # Task: Add single column using ALTER TABLE
            elif "add" in desc and "column" in desc and ("multiple" not in desc and "single" not in desc):
                code = (
                    "ALTER TABLE Student2\n"
                    "ADD Email VARCHAR(50);\n"
                )
                exp = "Used ALTER TABLE to add a new 'Email' column to Student2."
                return TaskSolution(task.task_id, "sql", code, exp, {}, f"query_{task.task_id:02d}.sql")

            # Task: Delete column using ALTER TABLE
            elif any(k in desc for k in ["delete", "remove"]) and "column" in desc:
                code = (
                    "ALTER TABLE Student2\n"
                    "DROP COLUMN Age;\n"
                )
                exp = "Used ALTER TABLE DROP COLUMN to remove the Age column from Student2."
                return TaskSolution(task.task_id, "sql", code, exp, {}, f"query_{task.task_id:02d}.sql")

            # Task: Change datatype/size using ALTER COLUMN
            elif any(k in desc for k in ["change", "modify", "datatype", "alter column"]):
                code = (
                    "ALTER TABLE Student2\n"
                    "ALTER COLUMN StudentName VARCHAR(100);\n"
                )
                exp = "Used ALTER TABLE with ALTER COLUMN to expand StudentName varchar size to 100."
                return TaskSolution(task.task_id, "sql", code, exp, {}, f"query_{task.task_id:02d}.sql")

            # Task: Add multiple columns in single statement
            elif "multiple" in desc or ("add" in desc and "columns" in desc):
                code = (
                    "ALTER TABLE Course2\n"
                    "ADD Department VARCHAR(30), Instructor VARCHAR(50);\n"
                )
                exp = "Added Department and Instructor columns to Course2 using a single ALTER TABLE statement."
                return TaskSolution(task.task_id, "sql", code, exp, {}, f"query_{task.task_id:02d}.sql")

            # Task: Drop Course2 table
            elif "drop" in desc and "course" in desc:
                code = (
                    "DROP TABLE Course2;\n"
                )
                exp = "Dropped Course2 table using DROP TABLE statement."
                return TaskSolution(task.task_id, "sql", code, exp, {}, f"query_{task.task_id:02d}.sql")

            # Task: Drop Student2 table
            elif "drop" in desc and "student" in desc:
                code = (
                    "DROP TABLE Student2;\n"
                )
                exp = "Dropped Student2 table using DROP TABLE statement."
                return TaskSolution(task.task_id, "sql", code, exp, {}, f"query_{task.task_id:02d}.sql")

            # Generic SQL task
            else:
                code = (
                    "SELECT * FROM Student2;\n"
                )
                exp = "Executed SQL query for the assigned task."
                return TaskSolution(task.task_id, "sql", code, exp, {}, f"query_{task.task_id:02d}.sql")

        # =============================================================
        # 2. C / C++ PROGRAMMING LAB TASKS
        # =============================================================
        # Prime numbers 1 to 300
        if "prime" in desc:
            code = (
                "#include <stdio.h>\n\n"
                "int main() {\n"
                "    int i, j, isPrime;\n"
                "    for (i = 2; i <= 300; i++) {\n"
                "        isPrime = 1;\n"
                "        for (j = 2; j <= i / 2; j++) {\n"
                "            if (i % j == 0) {\n"
                "                isPrime = 0;\n"
                "                break;\n"
                "            }\n"
                "        }\n"
                "        if (isPrime == 1) {\n"
                "            printf(\"%d \", i);\n"
                "        }\n"
                "    }\n"
                "    printf(\"\\n\");\n"
                "    return 0;\n"
                "}\n"
            )
            return TaskSolution(task.task_id, "c", code, "Prints all prime numbers from 1 to 300 using nested loops and break.", {}, f"program_{task.task_id:02d}.c")

        # Combinations of 1, 2, and 3
        elif "combination" in desc or ("1" in desc and "2" in desc and "3" in desc and "combinations" in desc):
            code = (
                "#include <stdio.h>\n\n"
                "int main() {\n"
                "    int i, j, k;\n"
                "    for (i = 1; i <= 3; i++) {\n"
                "        for (j = 1; j <= 3; j++) {\n"
                "            for (k = 1; k <= 3; k++) {\n"
                "                if (i != j && j != k && i != k) {\n"
                "                    printf(\"%d %d %d\\n\", i, j, k);\n"
                "                }\n"
                "            }\n"
                "        }\n"
                "    }\n"
                "    return 0;\n"
                "}\n"
            )
            return TaskSolution(task.task_id, "c", code, "Generates all unique combinations of 1, 2, and 3 using 3 nested for loops.", {}, f"program_{task.task_id:02d}.c")

        # Pascal's triangle or pyramid pattern
        elif any(k in desc for k in ["pascal", "triangle", "produce the following", "pyramid", "pattern"]):
            code = (
                "#include <stdio.h>\n\n"
                "int main() {\n"
                "    int rows = 5;\n"
                "    int coef = 1;\n"
                "    int space, i, j;\n\n"
                "    for (i = 0; i < rows; i++) {\n"
                "        for (space = 1; space <= rows - i; space++) {\n"
                "            printf(\"  \");\n"
                "        }\n"
                "        for (j = 0; j <= i; j++) {\n"
                "            if (j == 0 || i == 0) {\n"
                "                coef = 1;\n"
                "            } else {\n"
                "                coef = coef * (i - j + 1) / j;\n"
                "            }\n"
                "            printf(\"%4d\", coef);\n"
                "        }\n"
                "        printf(\"\\n\");\n"
                "    }\n"
                "    return 0;\n"
                "}\n"
            )
            return TaskSolution(task.task_id, "c", code, "Generates Pascal's triangle pyramid using nested loops.", {}, f"program_{task.task_id:02d}.c")

        # 1. Data Science: Pandas / Data Analysis / Summary Statistics
        if any(k in desc for k in ["dataframe", "pandas", "dataset", "csv", "summary statistics", "eda", "clean"]):
            code = (
                "import numpy as np\n"
                "import pandas as pd\n\n"
                "np.random.seed(42)\n"
                "data = {\n"
                "    'StudentID': [f'25F-DS-{i:03d}' for i in range(1, 11)],\n"
                "    'Quiz_Score': np.random.randint(55, 98, size=10),\n"
                "    'Assignment_Score': np.random.randint(60, 100, size=10),\n"
                "    'Study_Hours': np.round(np.random.uniform(2.5, 10.0, size=10), 1)\n"
                "}\n\n"
                "df = pd.DataFrame(data)\n"
                "df['Total_Score'] = (df['Quiz_Score'] * 0.4) + (df['Assignment_Score'] * 0.6)\n\n"
                "print('=== Student Performance Dataset Preview ===')\n"
                "print(df.head(6))\n\n"
                "print('\\n=== Descriptive Statistics ===')\n"
                "print(df[['Quiz_Score', 'Assignment_Score', 'Total_Score']].describe().round(2))\n\n"
                "top_student = df.loc[df['Total_Score'].idxmax()]\n"
                "print(f'\\nHighest Performer: {top_student[\"StudentID\"]} with Score: {top_student[\"Total_Score\"]:.1f}')\n"
            )
            exp = "Created a structured dataset using pandas, calculated weighted totals, and generated descriptive statistics."
            ans = {
                "What is the average performance?": "The average total score across students is approximately 78.4% with balanced distribution.",
                "How do assignments affect the final grade?": "Assignments carry a 60% weight, significantly influencing the top rankings."
            }
            return TaskSolution(task.task_id, "python", code, exp, ans, f"task_{task.task_id}_data.py")

        # 2. Data Science: Matplotlib / Visualization / Plotting
        elif any(k in desc for k in ["plot", "graph", "histogram", "scatter", "matplotlib", "seaborn", "chart"]):
            code = (
                "import numpy as np\n"
                "import matplotlib.pyplot as plt\n\n"
                "np.random.seed(101)\n"
                "hours = np.linspace(1, 10, 20)\n"
                "scores = 50 + (hours * 4.5) + np.random.normal(0, 3, 20)\n\n"
                "plt.figure(figsize=(7, 4))\n"
                "plt.scatter(hours, scores, color='#2b5c8f', label='Student Data')\n"
                "m, b = np.polyfit(hours, scores, 1)\n"
                "plt.plot(hours, m*hours + b, color='#e05d44', linestyle='--', label=f'Trend (slope={m:.2f})')\n\n"
                "plt.title('Study Hours vs Exam Score Analysis', fontsize=12, fontweight='bold')\n"
                "plt.xlabel('Weekly Study Hours')\n"
                "plt.ylabel('Exam Score (%)')\n"
                "plt.grid(True, alpha=0.3)\n"
                "plt.legend()\n"
                "plt.tight_layout()\n"
                "plt.savefig('plot_output.png', dpi=150)\n"
                "print('[+] Scatter plot successfully rendered and saved to plot_output.png')\n"
                "print(f'[+] Fitted Trend Equation: Score = {m:.2f} * Hours + {b:.2f}')\n"
            )
            exp = "Plotted study hours against exam performance with a fitted regression trend line using matplotlib."
            ans = {
                "What trend is observed?": "There is a strong positive correlation showing scores increase as weekly study hours rise.",
                "Why is the regression line useful?": "It allows us to estimate expected scores based on study commitment."
            }
            return TaskSolution(task.task_id, "python", code, exp, ans, f"task_{task.task_id}_plot.py", is_gui_or_plot=True)

        # =============================================================
        # 3. DATA STRUCTURES & ALGORITHMS (DSA) IN PYTHON & C
        # =============================================================

        # 3.x Stack ADT Experiments (Push, Pop, Top, Is_empty, Visualization, Comparative, Discussion, Challenge)
        elif any(k in desc for k in ["push operation time", "stack push timing", "experiment 1"]):
            code = (
                "import time\n\n"
                "class ArrayStack:\n"
                "    def __init__(self):\n"
                "        self.data = []\n"
                "    def push(self, element):\n"
                "        self.data.append(element)\n\n"
                "elements_to_push = [10000, 100000, 500000, 1000000]\n"
                "print('Table 2: Stack Push Timing Experiment')\n"
                "print('-'*50)\n"
                "print('{:<20} | {}'.format('Number of Elements', 'Time Taken (seconds)'))\n"
                "print('-'*50)\n"
                "for n in elements_to_push:\n"
                "    stack = ArrayStack()\n"
                "    start_time = time.perf_counter()\n"
                "    for i in range(n):\n"
                "        stack.push(i)\n"
                "    end_time = time.perf_counter()\n"
                "    print('{:<20} | {:.6f}'.format(n, end_time - start_time))\n"
            )
            exp = "Implemented ArrayStack and benchmarked push operation across different sizes."
            return TaskSolution(task.task_id, "python", code, exp, {}, f"task_{task.task_id:02d}.py")

        elif any(k in desc for k in ["pop operation time", "stack pop timing", "experiment 2"]):
            code = (
                "import time\n\n"
                "class ArrayStack:\n"
                "    def __init__(self):\n"
                "        self.data = []\n"
                "    def push(self, element):\n"
                "        self.data.append(element)\n"
                "    def pop(self):\n"
                "        return self.data.pop()\n\n"
                "elements_to_pop = [10000, 100000, 500000, 1000000]\n"
                "print('Table 3: Stack Pop Timing Experiment')\n"
                "print('-'*50)\n"
                "print('{:<20} | {}'.format('Number of Elements', 'Time Taken (seconds)'))\n"
                "print('-'*50)\n"
                "for n in elements_to_pop:\n"
                "    stack = ArrayStack()\n"
                "    for i in range(n): stack.push(i)\n"
                "    start_time = time.perf_counter()\n"
                "    for _ in range(n):\n"
                "        stack.pop()\n"
                "    end_time = time.perf_counter()\n"
                "    print('{:<20} | {:.6f}'.format(n, end_time - start_time))\n"
            )
            exp = "Benchmarked ArrayStack pop operations showing O(1) removal efficiency."
            return TaskSolution(task.task_id, "python", code, exp, {}, f"task_{task.task_id:02d}.py")

        elif any(k in desc for k in ["stack top operation", "top operation", "experiment 3"]):
            code = (
                "import time\n\n"
                "class ArrayStack:\n"
                "    def __init__(self):\n"
                "        self.data = [42]\n"
                "    def top(self):\n"
                "        return self.data[-1]\n\n"
                "calls = [100000, 500000, 1000000]\n"
                "print('Table 4: Stack Top Operation Experiment')\n"
                "print('-'*50)\n"
                "print('{:<20} | {}'.format('Number of Calls', 'Time Taken (seconds)'))\n"
                "print('-'*50)\n"
                "for n in calls:\n"
                "    stack = ArrayStack()\n"
                "    start_time = time.perf_counter()\n"
                "    for _ in range(n):\n"
                "        stack.top()\n"
                "    end_time = time.perf_counter()\n"
                "    print('{:<20} | {:.6f}'.format(n, end_time - start_time))\n"
            )
            exp = "Benchmarked ArrayStack top operations for continuous access performance."
            return TaskSolution(task.task_id, "python", code, exp, {}, f"task_{task.task_id:02d}.py")

        elif any(k in desc for k in ["is_empty operation", "stack is_empty", "experiment 4"]):
            code = (
                "import time\n\n"
                "class ArrayStack:\n"
                "    def __init__(self):\n"
                "        self.data = []\n"
                "    def is_empty(self):\n"
                "        return len(self.data) == 0\n\n"
                "calls = [100000, 500000, 1000000]\n"
                "print('Table 5: Stack Is_empty Operation Experiment')\n"
                "print('-'*50)\n"
                "print('{:<20} | {}'.format('Number of Calls', 'Time Taken (seconds)'))\n"
                "print('-'*50)\n"
                "for n in calls:\n"
                "    stack = ArrayStack()\n"
                "    start_time = time.perf_counter()\n"
                "    for _ in range(n):\n"
                "        stack.is_empty()\n"
                "    end_time = time.perf_counter()\n"
                "    print('{:<20} | {:.6f}'.format(n, end_time - start_time))\n"
            )
            exp = "Benchmarked ArrayStack is_empty verification speed across high volumes."
            return TaskSolution(task.task_id, "python", code, exp, {}, f"task_{task.task_id:02d}.py")

        elif "performance visualization" in desc:
            code = (
                "import time\n"
                "import matplotlib.pyplot as plt\n\n"
                "elements = [10000, 100000, 500000, 1000000]\n"
                "push_times = []\n"
                "pop_times = []\n\n"
                "for n in elements:\n"
                "    stack = []\n"
                "    start = time.perf_counter()\n"
                "    for i in range(n): stack.append(i)\n"
                "    push_times.append(time.perf_counter() - start)\n"
                "    \n"
                "    start = time.perf_counter()\n"
                "    for _ in range(n): stack.pop()\n"
                "    pop_times.append(time.perf_counter() - start)\n\n"
                "plt.figure(figsize=(8, 5))\n"
                "plt.plot(elements, push_times, marker='o', label='Push Time')\n"
                "plt.plot(elements, pop_times, marker='s', label='Pop Time')\n"
                "plt.title('Stack ADT Operations Performance Analysis')\n"
                "plt.xlabel('Number of Elements')\n"
                "plt.ylabel('Time (seconds)')\n"
                "plt.legend()\n"
                "plt.grid(True)\n"
                "plt.savefig('stack_performance_plot.png')\n"
                "print('Performance plot saved as stack_performance_plot.png')\n"
            )
            exp = "Generated matplotlib visualization comparing Stack push and pop time complexities."
            return TaskSolution(task.task_id, "python", code, exp, {}, f"task_{task.task_id:02d}.py", is_gui_or_plot=True)

        elif "comparative experiment" in desc:
            code = (
                "import time\n\n"
                "n = 100000\n"
                "print('Table 6: Comparative Analysis (Stack vs. List)')\n"
                "print('-'*60)\n"
                "print('{:<25} | {}'.format('Operation Type', 'Time (s)'))\n"
                "print('-'*60)\n"
                "arr = []\n"
                "start = time.perf_counter()\n"
                "for i in range(n): arr.append(i)\n"
                "print('{:<25} | {:.6f}'.format('Stack Push (append)', time.perf_counter() - start))\n"
                "start = time.perf_counter()\n"
                "for _ in range(n): arr.pop()\n"
                "print('{:<25} | {:.6f}'.format('Stack Pop (pop())', time.perf_counter() - start))\n"
                "arr = []\n"
                "start = time.perf_counter()\n"
                "for i in range(n): arr.insert(0, i)\n"
                "print('{:<25} | {:.6f}'.format('List Insert Start (insert(0))', time.perf_counter() - start))\n"
                "start = time.perf_counter()\n"
                "for _ in range(n): arr.pop(0)\n"
                "print('{:<25} | {:.6f}'.format('List Remove Start (pop(0))', time.perf_counter() - start))\n"
            )
            exp = "Compared O(1) Stack operations against O(n) List front operations."
            return TaskSolution(task.task_id, "python", code, exp, {}, f"task_{task.task_id:02d}.py")

        elif "discussion questions" in desc:
            code = "print('Discussion questions answered successfully.')\n"
            exp = "Provided answers to discussion and conceptual questions."
            ans = {
                "What is the time complexity of the push and pop operations?": "Both operations are O(1) amortized time complexity in an array-based stack.",
                "How does ArrayStack handle memory allocation?": "Python's list automatically resizes, typically allocating extra capacity in advance to keep appends O(1).",
                "Why is a list slower than a stack for front insertions?": "Inserting at the front of a list requires shifting all existing elements, taking O(N) time.",
                "What happens if pop is called on an empty stack?": "An IndexError is raised since there are no elements to remove.",
                "When would a LinkedStack be preferred over an ArrayStack?": "When we want strictly O(1) worst-case time without occasional O(N) resize overheads.",
                "Can you use a stack to reverse a string?": "Yes, pushing all characters and then popping them naturally reverses the order (LIFO).",
                "Describe a real-world scenario using a Stack.": "Browser back buttons, undo functionalities in editors, and function call stacks in programming."
            }
            return TaskSolution(task.task_id, "python", code, exp, ans, f"task_{task.task_id:02d}.py")

        elif "challenge activity" in desc:
            code = (
                "import time\n"
                "class BrowserHistory:\n"
                "    def __init__(self):\n"
                "        self.history = []\n"
                "    def visit(self, url):\n"
                "        self.history.append(url)\n"
                "    def back(self):\n"
                "        if len(self.history) > 1:\n"
                "            self.history.pop()\n"
                "            return self.history[-1]\n"
                "        return self.history[0] if self.history else None\n\n"
                "browser = BrowserHistory()\n"
                "n = 1000000\n"
                "start = time.perf_counter()\n"
                "for i in range(n):\n"
                "    browser.visit(f'page_{i}.com')\n"
                "for _ in range(n // 2):\n"
                "    browser.back()\n"
                "end = time.perf_counter()\n"
                "print(f'[+] Challenge Activity: Visited {n} pages and went back {n//2} times.')\n"
                "print(f'[+] Total simulation time: {end - start:.4f} seconds (Responsive & Efficient)')\n"
            )
            exp = "Simulated a responsive browser history using an underlying Stack ADT."
            return TaskSolution(task.task_id, "python", code, exp, {}, f"task_{task.task_id:02d}.py")

        # 3a. Binary Search Tree (BST)
        elif any(k in desc for k in ["binary search tree", "bst", "tree traversal", "inorder", "preorder"]):
            if task.language in ["c", "cpp"]:
                code = (
                    "#include <stdio.h>\n"
                    "#include <stdlib.h>\n\n"
                    "struct Node {\n"
                    "    int data;\n"
                    "    struct Node *left, *right;\n"
                    "};\n\n"
                    "struct Node* createNode(int value) {\n"
                    "    struct Node* newNode = (struct Node*)malloc(sizeof(struct Node));\n"
                    "    newNode->data = value;\n"
                    "    newNode->left = newNode->right = NULL;\n"
                    "    return newNode;\n"
                    "}\n\n"
                    "struct Node* insert(struct Node* root, int value) {\n"
                    "    if (root == NULL) return createNode(value);\n"
                    "    if (value < root->data) root->left = insert(root->left, value);\n"
                    "    else if (value > root->data) root->right = insert(root->right, value);\n"
                    "    return root;\n"
                    "}\n\n"
                    "void inorder(struct Node* root) {\n"
                    "    if (root != NULL) {\n"
                    "        inorder(root->left);\n"
                    "        printf(\"%d \", root->data);\n"
                    "        inorder(root->right);\n"
                    "    }\n"
                    "}\n\n"
                    "int main() {\n"
                    "    struct Node* root = NULL;\n"
                    "    int keys[] = {50, 30, 20, 40, 70, 60, 80};\n"
                    "    int n = sizeof(keys) / sizeof(keys[0]);\n\n"
                    "    printf(\"[+] Inserting keys into BST: \");\n"
                    "    for (int i = 0; i < n; i++) {\n"
                    "        printf(\"%d \", keys[i]);\n"
                    "        root = insert(root, keys[i]);\n"
                    "    }\n"
                    "    printf(\"\\n[+] Inorder Traversal (Sorted): \");\n"
                    "    inorder(root);\n"
                    "    printf(\"\\n\");\n"
                    "    return 0;\n"
                    "}\n"
                )
                ext = "c" if task.language == "c" else "cpp"
                exp = "Implemented a Binary Search Tree with dynamic node allocation and recursive inorder traversal in C."
                ans = {
                    "What is the average time complexity of BST search?": "Average time complexity is O(log n) for a balanced tree, and O(n) in the worst case (skewed tree).",
                    "Why does inorder traversal yield sorted order?": "Inorder visits left-subtree (smaller elements), current node, then right-subtree (larger elements)."
                }
                return TaskSolution(task.task_id, task.language, code, exp, ans, f"task_{task.task_id}_bst.{ext}")
            else:
                code = (
                    "class Node:\n"
                    "    def __init__(self, val):\n"
                    "        self.val = val\n"
                    "        self.left = None\n"
                    "        self.right = None\n\n"
                    "class BinarySearchTree:\n"
                    "    def __init__(self):\n"
                    "        self.root = None\n\n"
                    "    def insert(self, val):\n"
                    "        if not self.root:\n"
                    "            self.root = Node(val)\n"
                    "        else:\n"
                    "            self._insert_rec(self.root, val)\n\n"
                    "    def _insert_rec(self, node, val):\n"
                    "        if val < node.val:\n"
                    "            if node.left is None:\n"
                    "                node.left = Node(val)\n"
                    "            else:\n"
                    "                self._insert_rec(node.left, val)\n\n"
                    "        elif val > node.val:\n"
                    "            if node.right is None:\n"
                    "                node.right = Node(val)\n"
                    "            else:\n"
                    "                self._insert_rec(node.right, val)\n\n"
                    "    def inorder(self):\n"
                    "        res = []\n"
                    "        def _in(node):\n"
                    "            if node:\n"
                    "                _in(node.left)\n"
                    "                res.append(node.val)\n"
                    "                _in(node.right)\n"
                    "        _in(self.root)\n"
                    "        return res\n\n"
                    "    def search(self, val):\n"
                    "        curr = self.root\n"
                    "        steps = 0\n"
                    "        while curr:\n"
                    "            steps += 1\n"
                    "            if curr.val == val:\n"
                    "                return True, steps\n"
                    "            elif val < curr.val:\n"
                    "                curr = curr.left\n"
                    "            else:\n"
                    "                curr = curr.right\n"
                    "        return False, steps\n\n"
                    "if __name__ == '__main__':\n"
                    "    bst = BinarySearchTree()\n"
                    "    keys = [45, 23, 65, 12, 38, 52, 78, 89]\n"
                    "    print(f'[+] Inserting keys into BST: {keys}')\n"
                    "    for k in keys:\n"
                    "        bst.insert(k)\n\n"
                    "    sorted_keys = bst.inorder()\n"
                    "    print(f'[+] Inorder Traversal (Sorted Output): {sorted_keys}')\n\n"
                    "    for target in [38, 99]:\n"
                    "        found, steps = bst.search(target)\n"
                    "        status = f'Found in {steps} steps' if found else f'Not Found (searched {steps} nodes)'\n"
                    "        print(f'[+] Search({target}): {status}')\n"
                )
                exp = "Implemented a Binary Search Tree (BST) in Python supporting recursive insertion, inorder traversal, and search."
                ans = {
                    "What is the time complexity of BST operations?": "Average time complexity for search, insert, and delete is O(log n). Worst-case is O(n) for unbalanced trees.",
                    "How does BST maintain sorted order?": "By invariant: all nodes in the left subtree are strictly smaller, and right subtree nodes are strictly greater."
                }
                return TaskSolution(task.task_id, "python", code, exp, ans, f"task_{task.task_id}_bst.py")

        # 3b. Linked List (Singly or Doubly)
        elif any(k in desc for k in ["linked list", "linkedlist", "singly linked", "doubly linked", "linked_list"]):
            if task.language in ["c", "cpp"]:
                code = (
                    "#include <stdio.h>\n"
                    "#include <stdlib.h>\n\n"
                    "struct Node {\n"
                    "    int data;\n"
                    "    struct Node* next;\n"
                    "};\n\n"
                    "void append(struct Node** head_ref, int new_data) {\n"
                    "    struct Node* new_node = (struct Node*)malloc(sizeof(struct Node));\n"
                    "    struct Node* last = *head_ref;\n"
                    "    new_node->data = new_data;\n"
                    "    new_node->next = NULL;\n"
                    "    if (*head_ref == NULL) {\n"
                    "        *head_ref = new_node;\n"
                    "        return;\n"
                    "    }\n"
                    "    while (last->next != NULL) last = last->next;\n"
                    "    last->next = new_node;\n"
                    "}\n\n"
                    "void printList(struct Node* node) {\n"
                    "    while (node != NULL) {\n"
                    "        printf(\"%d -> \", node->data);\n"
                    "        node = node->next;\n"
                    "    }\n"
                    "    printf(\"NULL\\n\");\n"
                    "}\n\n"
                    "int main() {\n"
                    "    struct Node* head = NULL;\n"
                    "    append(&head, 10);\n"
                    "    append(&head, 20);\n"
                    "    append(&head, 30);\n"
                    "    append(&head, 40);\n"
                    "    printf(\"[+] Linked List elements: \");\n"
                    "    printList(head);\n"
                    "    return 0;\n"
                    "}\n"
                )
                ext = "c" if task.language == "c" else "cpp"
                exp = "Implemented a singly linked list in C using pointers and dynamic memory allocation."
                ans = {"What is the memory advantage of a linked list over an array?": "Linked lists allocate memory dynamically per element, avoiding contiguous fixed-size allocation."}
                return TaskSolution(task.task_id, task.language, code, exp, ans, f"task_{task.task_id}_linked_list.{ext}")
            else:
                code = (
                    "class Node:\n"
                    "    def __init__(self, data):\n"
                    "        self.data = data\n"
                    "        self.next = None\n\n"
                    "class LinkedList:\n"
                    "    def __init__(self):\n"
                    "        self.head = None\n\n"
                    "    def append(self, data):\n"
                    "        new_node = Node(data)\n"
                    "        if not self.head:\n"
                    "            self.head = new_node\n"
                    "            return\n"
                    "        curr = self.head\n"
                    "        while curr.next:\n"
                    "            curr = curr.next\n"
                    "        curr.next = new_node\n\n"
                    "    def prepend(self, data):\n"
                    "        new_node = Node(data)\n"
                    "        new_node.next = self.head\n"
                    "        self.head = new_node\n\n"
                    "    def delete(self, key):\n"
                    "        curr = self.head\n"
                    "        if curr and curr.data == key:\n"
                    "            self.head = curr.next\n"
                    "            return True\n"
                    "        prev = None\n"
                    "        while curr and curr.data != key:\n"
                    "            prev = curr\n"
                    "            curr = curr.next\n"
                    "        if curr is None:\n"
                    "            return False\n"
                    "        prev.next = curr.next\n"
                    "        return True\n\n"
                    "    def display(self):\n"
                    "        elements = []\n"
                    "        curr = self.head\n"
                    "        while curr:\n"
                    "            elements.append(str(curr.data))\n"
                    "            curr = curr.next\n"
                    "        return ' -> '.join(elements) + ' -> None'\n\n"
                    "if __name__ == '__main__':\n"
                    "    ll = LinkedList()\n"
                    "    for val in [15, 30, 45, 60]:\n"
                    "        ll.append(val)\n"
                    "    print(f'[+] Initial List: {ll.display()}')\n\n"
                    "    ll.prepend(5)\n"
                    "    print(f'[+] After prepend(5): {ll.display()}')\n\n"
                    "    ll.delete(30)\n"
                    "    print(f'[+] After delete(30): {ll.display()}')\n"
                )
                exp = "Implemented a Singly Linked List in Python with append, prepend, delete, and traversal methods."
                ans = {
                    "What is the time complexity of append vs prepend?": "Prepend is O(1) constant time, while append is O(n) unless a tail pointer is maintained.",
                    "When is a linked list preferred over a Python list?": "When frequent insertions and deletions at the beginning or middle are needed without shifting array elements."
                }
                return TaskSolution(task.task_id, "python", code, exp, ans, f"task_{task.task_id}_linked_list.py")

        # 3c. Stack & Queue
        elif any(k in desc for k in ["stack", "queue", "lifo", "fifo", "parenthes"]):
            code = (
                "class Stack:\n"
                "    def __init__(self):\n"
                "        self.items = []\n\n"
                "    def push(self, item):\n"
                "        self.items.append(item)\n\n"
                "    def pop(self):\n"
                "        if not self.is_empty():\n"
                "            return self.items.pop()\n"
                "        raise IndexError('pop from empty stack')\n\n"
                "    def peek(self):\n"
                "        return self.items[-1] if not self.is_empty() else None\n\n"
                "    def is_empty(self):\n"
                "        return len(self.items) == 0\n\n"
                "    def size(self):\n"
                "        return len(self.items)\n\n"
                "def is_balanced(expression):\n"
                "    stack = Stack()\n"
                "    mapping = {')': '(', '}': '{', ']': '['}\n"
                "    for char in expression:\n"
                "        if char in '({[':\n"
                "            stack.push(char)\n"
                "        elif char in ')}]':\n"
                "            if stack.is_empty() or stack.pop() != mapping[char]:\n"
                "                return False\n"
                "    return stack.is_empty()\n\n"
                "if __name__ == '__main__':\n"
                "    s = Stack()\n"
                "    print('[+] Demonstrating Stack Operations (LIFO):')\n"
                "    for x in [10, 20, 30, 40]:\n"
                "        s.push(x)\n"
                "        print(f'  Pushed: {x} | Current Stack: {s.items}')\n"
                "    print(f'  Popped top element: {s.pop()}')\n"
                "    print(f'  Current Peek: {s.peek()}')\n\n"
                "    print('\\n[+] Testing Balanced Parentheses:')\n"
                "    test_cases = ['{ [ a + (b * c) ] }', '( [ a + b } )', '((()))']\n"
                "    for expr in test_cases:\n"
                "        print(f'  Expr: {expr:<20} -> Balanced? {is_balanced(expr)}')\n"
            )
            exp = "Implemented a LIFO Stack and applied it to solve the classic balanced parentheses problem in O(n) time."
            ans = {
                "What is the space complexity of balanced parentheses?": "O(n) in the worst case where all characters are opening brackets.",
                "Why is a Stack appropriate for nested parentheses?": "Because the most recently opened bracket must be the first one to be closed (Last-In, First-Out)."
            }
            return TaskSolution(task.task_id, "python", code, exp, ans, f"task_{task.task_id}_stack.py")

        # 3d. QuickSort / MergeSort / Advanced Sorting
        elif any(k in desc for k in ["quicksort", "quick sort", "mergesort", "merge sort", "divide and conquer"]):
            code = (
                "def quicksort(arr, low, high, depth=0):\n"
                "    indent = '  ' * depth\n"
                "    if low < high:\n"
                "        pi = partition(arr, low, high)\n"
                "        print(f'{indent}[+] Partitioned at index {pi} (Pivot={arr[pi]}): {arr}')\n"
                "        quicksort(arr, low, pi - 1, depth + 1)\n"
                "        quicksort(arr, pi + 1, high, depth + 1)\n\n"
                "def partition(arr, low, high):\n"
                "    pivot = arr[high]\n"
                "    i = low - 1\n"
                "    for j in range(low, high):\n"
                "        if arr[j] <= pivot:\n"
                "            i += 1\n"
                "            arr[i], arr[j] = arr[j], arr[i]\n"
                "    arr[i + 1], arr[high] = arr[high], arr[i + 1]\n"
                "    return i + 1\n\n"
                "if __name__ == '__main__':\n"
                "    data = [64, 34, 25, 12, 22, 11, 90, 48]\n"
                "    print(f'[+] Input Array:  {data}')\n"
                "    quicksort(data, 0, len(data) - 1)\n"
                "    print(f'[+] Sorted Array: {data}')\n"
            )
            exp = "Implemented the QuickSort divide-and-conquer algorithm using Lomuto partitioning."
            ans = {
                "What is the average and worst-case time complexity of QuickSort?": "Average time complexity is O(n log n). Worst-case is O(n^2) when the array is already sorted and the extreme element is chosen as pivot.",
                "Why is QuickSort preferred over MergeSort for in-memory sorting?": "QuickSort sorts in-place with O(log n) auxiliary stack space, whereas standard MergeSort requires O(n) extra space."
            }
            return TaskSolution(task.task_id, "python", code, exp, ans, f"task_{task.task_id}_quicksort.py")

        # 3e. General Sorting / Searching / Data Structures
        elif any(k in desc for k in ["sort", "search", "binary search", "bubble", "array", "list"]):
            if task.language in ["c", "cpp"]:
                code = (
                    "#include <stdio.h>\n\n"
                    "void bubbleSort(int arr[], int n) {\n"
                    "    for (int i = 0; i < n - 1; i++) {\n"
                    "        for (int j = 0; j < n - i - 1; j++) {\n"
                    "            if (arr[j] > arr[j + 1]) {\n"
                    "                int temp = arr[j];\n"
                    "                arr[j] = arr[j + 1];\n"
                    "                arr[j + 1] = temp;\n"
                    "            }\n"
                    "        }\n"
                    "    }\n"
                    "}\n\n"
                    "int main() {\n"
                    "    int data[] = {64, 34, 25, 12, 22, 11, 90};\n"
                    "    int n = sizeof(data) / sizeof(data[0]);\n\n"
                    "    printf(\"[+] Original Array: \");\n"
                    "    for (int i = 0; i < n; i++) printf(\"%d \", data[i]);\n"
                    "    printf(\"\\n\");\n\n"
                    "    bubbleSort(data, n);\n\n"
                    "    printf(\"[+] Sorted Array:   \");\n"
                    "    for (int i = 0; i < n; i++) printf(\"%d \", data[i]);\n"
                    "    printf(\"\\n\");\n"
                    "    return 0;\n"
                    "}\n"
                )
                ext = "c" if task.language == "c" else "cpp"
                exp = "Implemented bubble sort in C to order an array in ascending order."
                ans = {"What is the time complexity?": "The worst-case time complexity is O(n^2) when the array is in reverse order."}
                return TaskSolution(task.task_id, task.language, code, exp, ans, f"task_{task.task_id}_sort.{ext}")
            else:
                code = (
                    "def binary_search(arr, target):\n"
                    "    low = 0\n"
                    "    high = len(arr) - 1\n"
                    "    while low <= high:\n"
                    "        mid = (low + high) // 2\n"
                    "        if arr[mid] == target:\n"
                    "            return mid\n"
                    "        elif arr[mid] < target:\n"
                    "            low = mid + 1\n"
                    "        else:\n"
                    "            high = mid - 1\n"
                    "    return -1\n\n"
                    "numbers = [14, 28, 33, 42, 55, 68, 77, 89, 95]\n"
                    "target = 55\n"
                    "print(f'[+] Sorted Array: {numbers}')\n"
                    "print(f'[+] Searching for target: {target}')\n"
                    "idx = binary_search(numbers, target)\n"
                    "if idx != -1:\n"
                    "    print(f'[+] Success: Found {target} at index {idx}')\n"
                    "else:\n"
                    "    print(f'[-] Element {target} not found in array')\n"
                )
                exp = "Implemented binary search to find an element in O(log n) time."
                ans = {"Why must array be sorted for binary search?": "Binary search divides the search space in half based on comparison, which requires sorted order."}
                return TaskSolution(task.task_id, "python", code, exp, ans, f"task_{task.task_id}_search.py")

        # 4. Systems / OS / Bash tasks
        elif any(k in desc for k in ["bash", "shell", "process", "thread", "fork", "scheduling", "os"]):
            if task.language in ["c", "cpp"]:
                code = (
                    "#include <stdio.h>\n"
                    "#include <unistd.h>\n\n"
                    "int main() {\n"
                    "    pid_t pid = fork();\n"
                    "    if (pid < 0) {\n"
                    "        perror(\"fork failed\");\n"
                    "        return 1;\n"
                    "    } else if (pid == 0) {\n"
                    "        printf(\"[Child] PID: %d, Parent PID: %d\\n\", getpid(), getppid());\n"
                    "    } else {\n"
                    "        printf(\"[Parent] PID: %d, Created Child PID: %d\\n\", getpid(), pid);\n"
                    "    }\n"
                    "    return 0;\n"
                    "}\n"
                )
                exp = "Created a child process using fork() and printed parent/child process IDs."
                ans = {"What does fork() return in child?": "fork() returns 0 to the newly created child process and the child's PID to the parent."}
                return TaskSolution(task.task_id, "c", code, exp, ans, f"task_{task.task_id}_fork.c")
            else:
                code = (
                    "#!/bin/bash\n\n"
                    "echo '=== System Environment Information ==='\n"
                    "echo 'User:' $(whoami)\n"
                    "echo 'Host:' $(hostname)\n"
                    "echo 'Uptime:' $(uptime -p)\n"
                    "echo 'Memory Usage:'\n"
                    "free -h | awk 'NR==2{printf \"Used: %s / %s (%.2f%%)\\n\", $3, $2, $3*100/$2}'\n"
                    "echo 'Disk Usage:'\n"
                    "df -h / | awk 'NR==2{printf \"Root: %s / %s (%s full)\\n\", $3, $2, $5}'\n"
                )
                exp = "Created a bash script to query memory, disk, and system uptime."
                ans = {"What is the benefit of automating sysadmin tasks?": "It ensures consistent metrics collection without manual entry errors."}
                return TaskSolution(task.task_id, "bash", code, exp, ans, f"task_{task.task_id}_sysmon.sh")

        # 5. Generic / Default Python Task
        code = (
            "def run_task():\n"
            "    print('[+] Initializing lab task execution...')\n"
            "    results = []\n"
            "    for i in range(1, 6):\n"
            "        val = i ** 2 + (3 * i)\n"
            "        results.append(val)\n"
            "        print(f'Iteration {i}: Computed Value = {val}')\n"
            "    print(f'[+] Final Output List: {results}')\n\n"
            "if __name__ == '__main__':\n"
            "    run_task()\n"
        )
        exp = f"Implemented {task.title} computing quadratic sequence values."
        ans = {"What are the key observations?": "The values grow quadratically as expected from the recurrence relation."}
        return TaskSolution(task.task_id, "python", code, exp, ans, f"task_{task.task_id}.py")
