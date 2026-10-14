"""
Multi-Language Code Runner for LabGenius.
Executes code directly in an isolated workspace, captures genuine stdout/stderr,
and prevents hangs by providing interactive stdin fallbacks and execution timeouts.
"""

import os
import sys
import time
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Tuple, Dict, List

from .config import Config
from .solver import TaskSolution


@dataclass
class ExecutionResult:
    task_id: int
    command_str: str
    stdout: str
    stderr: str
    exit_code: int
    execution_time: float
    output_files: Dict[str, Path]
    work_dir: Path
    success: bool


class CodeRunner:
    """Runs student code locally with interactive stdin simulation and crash protection."""

    # Default interactive inputs for prompts like "Enter number:", "Choice:", etc.
    DEFAULT_INTERACTIVE_INPUTS = "42\n10\n1\n0\n5\nyes\n\n"

    def __init__(self, config: Config):
        self.config = config
        self.base_workspace = Path(config.system.workspace_dir).resolve()
        self.base_workspace.mkdir(parents=True, exist_ok=True)

    def execute(self, solution: TaskSolution, sample_input: Optional[str] = None) -> ExecutionResult:
        """Execute a task solution in its isolated workspace directory."""
        task_dir = self.base_workspace / f"task_{solution.task_id:02d}"
        task_dir.mkdir(parents=True, exist_ok=True)

        code_path = task_dir / solution.file_name
        with open(code_path, "w", encoding="utf-8") as f:
            f.write(solution.code)

        # Determine command based on language
        cmd, run_cmd_display, compile_cmd = self._build_command(solution, code_path)

        start_time = time.time()
        env = os.environ.copy()
        repo_root = str(Path(__file__).resolve().parent.parent)
        existing_pp = env.get("PYTHONPATH", "")
        env["PYTHONPATH"] = f"{repo_root}:{existing_pp}" if existing_pp else repo_root
        env["PYTHONUNBUFFERED"] = "1"

        # Prepare stdin input: use provided sample_input or sensible interactive stream to prevent hangs
        stdin_data = sample_input if sample_input is not None else self.DEFAULT_INTERACTIVE_INPUTS

        try:
            if compile_cmd:
                comp_res = subprocess.run(
                    compile_cmd,
                    cwd=str(task_dir),
                    env=env,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    timeout=15,
                )
                if comp_res.returncode != 0:
                    duration = time.time() - start_time
                    return ExecutionResult(
                        task_id=solution.task_id,
                        command_str=run_cmd_display,
                        stdout=comp_res.stdout.decode("utf-8", errors="replace").strip(),
                        stderr=comp_res.stderr.decode("utf-8", errors="replace").strip(),
                        exit_code=comp_res.returncode,
                        execution_time=duration,
                        output_files={},
                        work_dir=task_dir,
                        success=False,
                    )

            res = subprocess.run(
                cmd,
                cwd=str(task_dir),
                env=env,
                input=stdin_data.encode("utf-8"),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=25,
            )
            duration = time.time() - start_time
            stdout = res.stdout.decode("utf-8", errors="replace")
            stderr = res.stderr.decode("utf-8", errors="replace")
            exit_code = res.returncode
        except subprocess.TimeoutExpired:
            duration = 25.0
            stdout = ""
            stderr = "Execution timed out after 25 seconds."
            exit_code = 124
        except Exception as e:
            duration = time.time() - start_time
            stdout = ""
            stderr = str(e)
            exit_code = 1

        # Check for output files (e.g. plot images, generated datasets)
        output_files = {}
        for item in task_dir.iterdir():
            if item.is_file() and item.suffix.lower() in [".png", ".jpg", ".jpeg", ".csv", ".txt"]:
                if item.name != solution.file_name:
                    output_files[item.name] = item

        return ExecutionResult(
            task_id=solution.task_id,
            command_str=run_cmd_display,
            stdout=stdout.strip(),
            stderr=stderr.strip(),
            exit_code=exit_code,
            execution_time=duration,
            output_files=output_files,
            work_dir=task_dir,
            success=(exit_code == 0),
        )

    def _build_command(self, solution: TaskSolution, code_path: Path) -> Tuple[List[str], str, Optional[List[str]]]:
        fname = code_path.name
        lang = solution.language.lower()

        if lang == "python":
            py_bin = sys.executable if "venv" in sys.executable else "python3"
            return [py_bin, fname], f"python3 {fname}", None

        elif lang == "c":
            bin_name = code_path.stem
            compile_cmd = ["gcc", "-O2", "-o", bin_name, fname, "-lm"]
            run_cmd = [f"./{bin_name}"]
            display_cmd = f"gcc -o {bin_name} {fname} -lm && ./{bin_name}"
            return run_cmd, display_cmd, compile_cmd

        elif lang in ["cpp", "c++"]:
            bin_name = code_path.stem
            compile_cmd = ["g++", "-O2", "-o", bin_name, fname, "-lm"]
            run_cmd = [f"./{bin_name}"]
            display_cmd = f"g++ -o {bin_name} {fname} && ./{bin_name}"
            return run_cmd, display_cmd, compile_cmd

        elif lang == "bash":
            return ["bash", fname], f"bash {fname}", None

        elif lang == "sql":
            py_bin = sys.executable
            shared_db = (self.base_workspace / "dbms_lab.db").resolve()
            student_name = str(self.config.student.name or "Student")
            student_roll = str(self.config.student.roll_number or "001")
            sql_cmd = [
                py_bin,
                "-m",
                "labgenius.sql_runner",
                fname,
                "--db",
                str(shared_db),
                "--name",
                student_name,
                "--roll",
                student_roll,
            ]
            display_cmd = f"sqlcmd -i {fname}"
            return sql_cmd, display_cmd, None

        else:
            return ["python3", fname], f"python3 {fname}", None
