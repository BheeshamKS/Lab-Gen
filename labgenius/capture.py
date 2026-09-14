"""
Authentic Screenshot Capture Studio for LabGenius.
Generates genuine light-theme IDE code screenshots and console output screenshots
matching university lab report submissions.
"""

import os
import html
import textwrap
import subprocess
from pathlib import Path
from typing import Tuple
from PIL import Image, ImageChops
import pygments
from pygments import highlight
from pygments.lexers import get_lexer_by_name, guess_lexer
from pygments.formatters import HtmlFormatter

from .config import Config
from .runner import ExecutionResult
from .solver import TaskSolution


class ScreenshotStudio:
    """Captures and synthesizes realistic code screenshots and console output screenshots."""

    def __init__(self, config: Config):
        self.config = config
        self.student = config.student
        self.system = config.system

    def capture_task_screenshots(self, solution: TaskSolution, exec_result: ExecutionResult) -> Tuple[Path, Path]:
        """Generates both the Code Screenshot and Output Screenshot for a task."""
        code_img_path = exec_result.work_dir / f"screenshot_code_task_{solution.task_id:02d}.png"
        out_img_path = exec_result.work_dir / f"screenshot_output_task_{solution.task_id:02d}.png"

        self.capture_code_screenshot(solution.code, solution.language, code_img_path)
        self.capture_output_screenshot(exec_result.stdout or exec_result.stderr, out_img_path)

        return code_img_path, out_img_path

    def capture_code_screenshot(self, code_str: str, language: str, dest_path: Path) -> Path:
        """Render an authentic light-mode VS Code snip with syntax highlighting instantly."""
        try:
            lexer = get_lexer_by_name(language.lower())
        except Exception:
            try:
                lexer = guess_lexer(code_str)
            except Exception:
                lexer = get_lexer_by_name("c")

        # Fast direct Pygments ImageFormatter (sub-50ms)
        try:
            from pygments.formatters import ImageFormatter
            formatter = ImageFormatter(
                font_name="DejaVu Sans Mono",
                font_size=13,
                line_numbers=False,
                style="vs",
                image_pad=16,
            )
            img_data = highlight(code_str.strip(), lexer, formatter)
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            with open(dest_path, "wb") as f:
                f.write(img_data)
            return dest_path
        except Exception:
            pass

        # Headless browser fallback if available
        formatter = HtmlFormatter(style="vs", noclasses=True)
        highlighted_code_html = highlight(code_str.strip(), lexer, formatter)

        html_template = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    background: #ffffff;
    padding: 14px 18px;
    font-family: 'Consolas', 'Cascadia Code', 'DejaVu Sans Mono', monospace;
    font-size: 14px;
    line-height: 1.45;
    color: #000000;
    display: inline-block;
  }}
  pre {{ font-family: inherit; font-size: inherit; line-height: inherit; margin: 0; }}
</style>
</head>
<body>
<div class="code-area">{highlighted_code_html}</div>
</body>
</html>"""

        html_file = dest_path.parent / f"_temp_code_{dest_path.stem}.html"
        with open(html_file, "w", encoding="utf-8") as f:
            f.write(html_template)

        raw_png = dest_path.parent / f"_raw_code_{dest_path.stem}.png"
        cmd = ["firefox", "--headless", "--screenshot", str(raw_png.resolve()), f"file://{html_file.resolve()}"]

        try:
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=8)
            if raw_png.exists():
                self._auto_crop_white(raw_png, dest_path)
                if raw_png.exists():
                    raw_png.unlink()
            else:
                self._fallback_code_pillow(code_str, dest_path)
        except Exception:
            self._fallback_code_pillow(code_str, dest_path)
        finally:
            if html_file.exists():
                html_file.unlink()

        return dest_path

    def capture_output_screenshot(self, output_text: str, dest_path: Path) -> Path:
        """Render a clean, white-background console output screenshot matching student submissions instantly."""
        if not output_text.strip():
            output_text = "Execution completed successfully."

        # Format long lines to wrap cleanly like standard terminal width
        lines = output_text.strip().splitlines()
        formatted = []
        for line in lines:
            if len(line) > 70 and not line.startswith("Name:") and not line.startswith("Roll No:"):
                formatted.append(textwrap.fill(line, width=68))
            else:
                formatted.append(line)
        wrapped_lines = ("\n".join(formatted)).splitlines()

        # Fast direct Pillow rendering (sub-30ms)
        try:
            from PIL import Image, ImageDraw, ImageFont
            font = None
            for font_candidate in [
                "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
                "/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf",
                "/usr/share/fonts/TTF/DejaVuSansMono.ttf",
            ]:
                if os.path.exists(font_candidate):
                    try:
                        font = ImageFont.truetype(font_candidate, 13)
                        break
                    except Exception:
                        pass
            if font is None:
                font = ImageFont.load_default()

            line_height = 20
            max_w = 0
            for line in wrapped_lines:
                bbox = font.getbbox(line) if hasattr(font, "getbbox") else (0, 0, len(line) * 8, 14)
                w = bbox[2] - bbox[0]
                if w > max_w:
                    max_w = w

            total_h = len(wrapped_lines) * line_height + 24
            total_w = max(max_w + 32, 280)

            img = Image.new("RGB", (total_w, total_h), (255, 255, 255))
            draw = ImageDraw.Draw(img)
            y = 12
            for line in wrapped_lines:
                draw.text((16, y), line, font=font, fill=(15, 15, 15))
                y += line_height

            dest_path.parent.mkdir(parents=True, exist_ok=True)
            img.save(dest_path, "PNG", optimize=True)
            return dest_path
        except Exception:
            pass

        # Fallback to headless browser if Pillow fails
        escaped_out = html.escape("\n".join(wrapped_lines))
        html_template = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    background: #ffffff;
    padding: 12px 16px;
    font-family: 'Consolas', 'Cascadia Code', 'DejaVu Sans Mono', monospace;
    font-size: 14px;
    line-height: 1.45;
    color: #000000;
    display: inline-block;
  }}
  pre {{ font-family: inherit; font-size: inherit; line-height: inherit; white-space: pre-wrap; margin: 0; }}
</style>
</head>
<body><pre>{escaped_out}</pre></body>
</html>"""

        html_file = dest_path.parent / f"_temp_out_{dest_path.stem}.html"
        with open(html_file, "w", encoding="utf-8") as f:
            f.write(html_template)

        raw_png = dest_path.parent / f"_raw_out_{dest_path.stem}.png"
        cmd = ["firefox", "--headless", "--screenshot", str(raw_png.resolve()), f"file://{html_file.resolve()}"]

        try:
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=8)
            if raw_png.exists():
                self._auto_crop_white(raw_png, dest_path)
                if raw_png.exists():
                    raw_png.unlink()
            else:
                self._fallback_output_pillow(output_text, dest_path)
        except Exception:
            self._fallback_output_pillow(output_text, dest_path)
        finally:
            if html_file.exists():
                html_file.unlink()

        return dest_path

    def _auto_crop_white(self, src: Path, dest: Path) -> None:
        """Crops excess white margins around text cleanly."""
        try:
            im = Image.open(src).convert("RGB")
            bg = Image.new("RGB", im.size, (255, 255, 255))
            diff = ImageChops.difference(im, bg)
            bbox = diff.getbbox()
            if bbox:
                # Add breathing room around text
                left = max(0, bbox[0] - 12)
                top = max(0, bbox[1] - 8)
                right = min(im.width, bbox[2] + 12)
                bottom = min(im.height, bbox[3] + 8)
                cropped = im.crop((left, top, right, bottom))
                cropped.save(dest, "PNG", optimize=True)
            else:
                im.save(dest, "PNG")
        except Exception:
            if src.exists():
                src.rename(dest)

    def _fallback_code_pillow(self, code_str: str, dest: Path) -> None:
        """Pillow fallback for code rendering."""
        from PIL import ImageDraw, ImageFont
        lines = code_str.splitlines()
        width = max(len(l) for l in lines) * 9 + 40
        height = len(lines) * 22 + 40
        img = Image.new("RGB", (max(width, 400), max(height, 200)), color=(255, 255, 255))
        draw = ImageDraw.Draw(img)
        y = 20
        for line in lines:
            color = (0, 0, 255) if line.startswith(("#include", "int ", "return", "for", "if")) else (0, 0, 0)
            draw.text((20, y), line, fill=color)
            y += 22
        img.save(dest, "PNG")

    def _fallback_output_pillow(self, output_text: str, dest: Path) -> None:
        """Pillow fallback for output rendering."""
        from PIL import ImageDraw
        lines = output_text.splitlines()
        width = max(len(l) for l in lines) * 9 + 40
        height = len(lines) * 22 + 40
        img = Image.new("RGB", (max(width, 400), max(height, 150)), color=(255, 255, 255))
        draw = ImageDraw.Draw(img)
        y = 20
        for line in lines:
            draw.text((20, y), line, fill=(10, 10, 10))
            y += 22
        img.save(dest, "PNG")
