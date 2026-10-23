"""
Unit and Integration Tests for Themes, Screenshot Studio, and UI System.
Verifies that:
1. Secret theme 'bheeshamks' is strictly protected, never leaked in public listings or API endpoints.
2. Distinct public themes (Slate Grey, Cyber Black, Editorial Parchment, Modern Dark, Cobalt Blue) exist and render correctly.
3. Warm Parchment ('paper-warm') is distinctly non-pure-white (#f5f1e9 != #ffffff).
4. ScreenshotStudio renders authentic images for all themes without error.
5. FastAPI endpoint /api/themes returns valid sanitized payload.
6. HTML report builder generates document theme switcher toolbar and dynamic CSS properties.
"""

import os
import unittest
import tempfile
from pathlib import Path
from PIL import Image
from fastapi.testclient import TestClient

from labgenius.config import Config
from labgenius.themes import (
    THEMES,
    ScreenshotTheme,
    get_theme,
    list_public_themes,
)
from labgenius.capture import ScreenshotStudio
from labgenius.builder import DocumentBuilder
from labgenius.parser import LabManual, LabTask
from labgenius.solver import TaskSolution
from labgenius.runner import ExecutionResult
from web_app import app


class TestThemesAndUI(unittest.TestCase):

    def setUp(self):
        self.cfg = Config.load()
        self.temp_dir = tempfile.TemporaryDirectory()
        self.workspace = Path(self.temp_dir.name)
        self.cfg.system.workspace_dir = str(self.workspace)
        self.client = TestClient(app)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_01_secret_theme_bheeshamks_protection(self):
        """Verifies that bheeshamks is marked secret and completely absent from public listings."""
        # 1. Direct registry check
        self.assertIn("bheeshamks", THEMES)
        theme = THEMES["bheeshamks"]
        self.assertTrue(theme.is_secret)
        self.assertEqual(theme.bg_hex, "#ffffff")
        self.assertEqual(theme.syntax_style, "vs")
        self.assertEqual(theme.window_style, "frameless")

        # 2. list_public_themes MUST NOT leak bheeshamks in id or name
        public_themes = list_public_themes()
        public_ids = [t["id"] for t in public_themes]
        public_names = [t["name"].lower() for t in public_themes]

        self.assertNotIn("bheeshamks", public_ids)
        for name in public_names:
            self.assertNotIn("bheesham", name)

    def test_02_public_themes_exist_and_distinct(self):
        """Verifies grey, black, warm white, modern dark, and cobalt blue themes are present and distinct."""
        public_themes = list_public_themes()
        public_dict = {t["id"]: t for t in public_themes}

        # Grey theme
        self.assertIn("slate-grey", public_dict)
        self.assertEqual(public_dict["slate-grey"]["bg_hex"], "#282c34")

        # Black theme
        self.assertIn("cyber-black", public_dict)
        self.assertEqual(public_dict["cyber-black"]["bg_hex"], "#0a0c10")

        # Warm light/white theme
        self.assertIn("paper-warm", public_dict)
        self.assertEqual(public_dict["paper-warm"]["bg_hex"], "#f5f1e9")
        # Ensure paper-warm is NOT pure white #ffffff
        self.assertNotEqual(public_dict["paper-warm"]["bg_hex"], "#ffffff")

        # Indigo modern dark and cobalt blue
        self.assertIn("modern-dark", public_dict)
        self.assertIn("cobalt-blue", public_dict)

    def test_03_theme_precedence_and_env_resolution(self):
        """Verifies get_theme respects .env override and explicit theme selection."""
        old_screenshot_env = os.environ.get("SCREENSHOT_THEME")
        old_terminal_env = os.environ.get("TERMINAL_THEME")

        try:
            # 1. Secret theme resolution via env
            os.environ["SCREENSHOT_THEME"] = "bheeshamks"
            theme = get_theme()
            self.assertEqual(theme.id, "bheeshamks")
            self.assertTrue(theme.is_secret)

            # 2. Explicit public selection overrides
            theme_explicit = get_theme("slate-grey")
            self.assertEqual(theme_explicit.id, "slate-grey")
            self.assertFalse(theme_explicit.is_secret)

            # 3. Fallback when env unset
            del os.environ["SCREENSHOT_THEME"]
            if "TERMINAL_THEME" in os.environ:
                del os.environ["TERMINAL_THEME"]
            theme_default = get_theme()
            self.assertEqual(theme_default.id, "modern-dark")

        finally:
            if old_screenshot_env is not None:
                os.environ["SCREENSHOT_THEME"] = old_screenshot_env
            elif "SCREENSHOT_THEME" in os.environ:
                del os.environ["SCREENSHOT_THEME"]

            if old_terminal_env is not None:
                os.environ["TERMINAL_THEME"] = old_terminal_env
            elif "TERMINAL_THEME" in os.environ:
                del os.environ["TERMINAL_THEME"]

    def test_04_screenshot_studio_capture_all_themes(self):
        """Verifies that ScreenshotStudio renders valid PNG files for all themes."""
        studio = ScreenshotStudio(self.cfg)
        test_code = 'print("Hello from LabGenius Theme Engine!")\nx = [i**2 for i in range(10)]\nprint(x)'
        test_output = 'Hello from LabGenius Theme Engine!\n[0, 1, 4, 9, 16, 25, 36, 49, 64, 81]\nProcess finished with exit code 0.'

        themes_to_test = ["slate-grey", "cyber-black", "paper-warm", "bheeshamks"]

        for t_id in themes_to_test:
            self.cfg.terminal.theme = t_id
            code_dest = self.workspace / f"code_{t_id}.png"
            out_dest = self.workspace / f"out_{t_id}.png"

            # Render code snip
            res_code = studio.capture_code_screenshot(test_code, "python", code_dest, filename="test.py")
            self.assertTrue(res_code.exists(), f"Code screenshot missing for {t_id}")
            self.assertGreater(res_code.stat().st_size, 500)

            # Open with PIL to verify it's a valid readable image
            with Image.open(res_code) as img:
                self.assertEqual(img.format, "PNG")
                self.assertGreater(img.width, 100)
                self.assertGreater(img.height, 50)

            # Render terminal output
            res_out = studio.capture_output_screenshot(test_output, out_dest, command_str="python3 test.py")
            self.assertTrue(res_out.exists(), f"Output screenshot missing for {t_id}")
            self.assertGreater(res_out.stat().st_size, 500)

            with Image.open(res_out) as img:
                self.assertEqual(img.format, "PNG")
                self.assertGreater(img.width, 100)
                self.assertGreater(img.height, 50)

    def test_05_api_themes_endpoint(self):
        """Verifies that /api/themes returns valid JSON with no secret theme leaks."""
        old_env = os.environ.get("SCREENSHOT_THEME")
        try:
            # Test when secret theme is in env
            os.environ["SCREENSHOT_THEME"] = "bheeshamks"
            resp = self.client.get("/api/themes")
            self.assertEqual(resp.status_code, 200)
            data = resp.json()

            self.assertTrue(data.get("success"))
            self.assertTrue(data.get("is_custom_env"))
            # Public active theme fallback
            self.assertEqual(data.get("active_theme"), "modern-dark")

            # Check that bheeshamks is nowhere in returned themes list
            theme_ids = [t["id"] for t in data["themes"]]
            self.assertNotIn("bheeshamks", theme_ids)

            # Test when public theme is in env
            os.environ["SCREENSHOT_THEME"] = "slate-grey"
            resp2 = self.client.get("/api/themes")
            data2 = resp2.json()
            self.assertFalse(data2.get("is_custom_env"))
            self.assertEqual(data2.get("active_theme"), "slate-grey")

        finally:
            if old_env is not None:
                os.environ["SCREENSHOT_THEME"] = old_env
            elif "SCREENSHOT_THEME" in os.environ:
                del os.environ["SCREENSHOT_THEME"]

    def test_06_builder_html_theme_switcher(self):
        """Verifies that the HTML document builder includes theme variables and switcher toolbar."""
        builder = DocumentBuilder(self.cfg)
        manual = LabManual(
            file_path=self.workspace / "dummy.docx",
            title="Database Systems Lab 06",
            course_name="Database Systems",
            lab_number="06",
            tasks=[
                LabTask(task_id="task_1", title="Task 1: Query Employees", description="Select all employees.")
            ]
        )
        solutions = [
            TaskSolution(
                task_id=1,
                language="sql",
                code="SELECT * FROM Employees;",
                explanation="Fetches employees.",
                discussion_answers={},
                file_name="task1.sql",
            )
        ]
        exec_results = [
            ExecutionResult(
                task_id=1,
                command_str="sqlite3 test.db < task1.sql",
                stdout="emp_id | name\n1 | Alice\n2 | Bob",
                stderr="",
                exit_code=0,
                execution_time=0.02,
                output_files={},
                work_dir=self.workspace,
                success=True,
            )
        ]
        code_img = self.workspace / "code_img.png"
        out_img = self.workspace / "out_img.png"
        code_img.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 50)
        out_img.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 50)

        html_out = self.workspace / "report.html"
        self.cfg.terminal.theme = "slate-grey"
        builder.build_html_report(manual, solutions, exec_results, [(code_img, out_img)], html_out)

        self.assertTrue(html_out.exists())
        content = html_out.read_text(encoding="utf-8")

        # Must include theme CSS variables
        self.assertIn("--doc-theme-bg", content)
        self.assertIn("--doc-theme-text", content)
        self.assertIn("--doc-theme-border", content)

        # Must include the interactive switcher toolbar
        self.assertIn("theme-toolbar", content)
        self.assertIn("setDocTheme", content)
        self.assertIn("Charcoal Slate", content)
        self.assertIn("Cyber OLED", content)
        self.assertIn("Editorial Parchment", content)

        # Must NOT include secret theme name in the switcher toolbar
        self.assertNotIn("bheeshamks", content)


if __name__ == "__main__":
    unittest.main()
