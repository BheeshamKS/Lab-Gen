"""
Authentic Screenshot Capture Studio for LabGenius.
Generates genuine code and console output screenshots across multiple themes
(Modern Dark, Charcoal Slate, Cyber OLED, Editorial Parchment, and Bheesham Signature).
"""

import os
import io
import html
import textwrap
import subprocess
from pathlib import Path
from typing import Tuple, Optional
from PIL import Image, ImageDraw, ImageFont, ImageChops
import pygments
from pygments import highlight
from pygments.lexers import get_lexer_by_name, guess_lexer
from pygments.formatters import HtmlFormatter

from .config import Config
from .runner import ExecutionResult
from .solver import TaskSolution
from .themes import get_theme, ScreenshotTheme


class ScreenshotStudio:
    """Captures and synthesizes realistic code screenshots and console output screenshots."""

    def __init__(self, config: Config):
        self.config = config
        self.student = config.student
        self.system = config.system

    def _get_active_theme(self) -> ScreenshotTheme:
        theme_name = getattr(self.config.terminal, "theme", None)
        return get_theme(theme_name)

    @staticmethod
    def _get_font(size: int = 13):
        for candidate in [
            "/usr/share/fonts/truetype/custom/fonts/ttf/JetBrainsMono-Regular.ttf",
            "/usr/share/fonts/truetype/ibm-plex/IBMPlexMono-Regular.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf",
            "/usr/share/fonts/truetype/ubuntu/UbuntuMono-R.ttf",
        ]:
            if os.path.exists(candidate):
                try:
                    return ImageFont.truetype(candidate, size)
                except Exception:
                    pass
        return ImageFont.load_default()

    def capture_task_screenshots(self, solution: TaskSolution, exec_result: ExecutionResult) -> Tuple[Path, Path]:
        """Generates both the Code Screenshot and Output Screenshot for a task."""
        code_img_path = exec_result.work_dir / f"screenshot_code_task_{solution.task_id:02d}.png"
        out_img_path = exec_result.work_dir / f"screenshot_output_task_{solution.task_id:02d}.png"

        self.capture_code_screenshot(solution.code, solution.language, code_img_path, filename=solution.file_name)
        self.capture_output_screenshot(
            exec_result.stdout or exec_result.stderr,
            out_img_path,
            command_str=exec_result.command_str
        )

        return code_img_path, out_img_path

    def capture_code_screenshot(
        self,
        code_str: str,
        language: str,
        dest_path: Path,
        filename: Optional[str] = None
    ) -> Path:
        """Render an authentic code snip with theme syntax highlighting and optional macOS window header."""
        theme = self._get_active_theme()

        try:
            lexer = get_lexer_by_name(language.lower())
        except Exception:
            try:
                lexer = guess_lexer(code_str)
            except Exception:
                lexer = get_lexer_by_name("c")

        # Fast direct Pygments ImageFormatter
        try:
            from pygments.formatters import ImageFormatter
            formatter = ImageFormatter(
                font_name="DejaVu Sans Mono",
                font_size=theme.font_size,
                line_numbers=False,
                style=theme.syntax_style,
                image_pad=14,
            )
            raw_data = highlight(code_str.strip(), lexer, formatter)
            raw_im = Image.open(io.BytesIO(raw_data)).convert("RGB")

            if theme.window_style == "macos-dots":
                header_h = 32
                pad = 1
                total_w = max(raw_im.width + pad * 2, 380)
                total_h = raw_im.height + header_h + pad * 2

                canvas = Image.new("RGB", (total_w, total_h), theme.bg_color)
                draw = ImageDraw.Draw(canvas)

                # Header bar
                draw.rectangle([(0, 0), (total_w, header_h)], fill=theme.header_bg)
                # Traffic light dots
                draw.ellipse([(14, 11), (24, 21)], fill=(255, 95, 86))
                draw.ellipse([(30, 11), (40, 21)], fill=(255, 189, 46))
                draw.ellipse([(46, 11), (56, 21)], fill=(39, 201, 63))

                # Header title
                font_small = self._get_font(11)
                title_text = filename or f"solution.{language.lower()}"
                draw.text((66, 9), title_text, font=font_small, fill=(140, 145, 155))

                # Paste highlighted code
                canvas.paste(raw_im, (pad, header_h))
                # Border
                draw.rectangle([(0, 0), (total_w - 1, total_h - 1)], outline=theme.border_color, width=1)
                final_im = canvas
            else:
                # Frameless academic paper canvas (bheeshamks signature)
                draw = ImageDraw.Draw(raw_im)
                draw.rectangle([(0, 0), (raw_im.width - 1, raw_im.height - 1)], outline=theme.border_color, width=1)
                final_im = raw_im

            dest_path.parent.mkdir(parents=True, exist_ok=True)
            final_im.save(dest_path, "PNG", optimize=True)
            return dest_path
        except Exception:
            pass

        # Headless browser fallback if direct ImageFormatter fails
        formatter = HtmlFormatter(style=theme.syntax_style, noclasses=True)
        highlighted_code_html = highlight(code_str.strip(), lexer, formatter)

        html_template = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    background: {theme.bg_hex};
    padding: 14px 18px;
    font-family: 'DejaVu Sans Mono', 'Consolas', monospace;
    font-size: 14px;
    line-height: 1.45;
    color: {theme.text_hex};
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
                self._auto_crop(raw_png, dest_path, theme.bg_color)
                if raw_png.exists():
                    raw_png.unlink()
            else:
                self._fallback_code_pillow(code_str, dest_path, theme)
        except Exception:
            self._fallback_code_pillow(code_str, dest_path, theme)
        finally:
            if html_file.exists():
                html_file.unlink()

        return dest_path

    def capture_output_screenshot(
        self,
        output_text: str,
        dest_path: Path,
        command_str: Optional[str] = None
    ) -> Path:
        """Render a clean console output screenshot matching the active theme."""
        theme = self._get_active_theme()

        if not output_text.strip():
            output_text = "Commands completed successfully."

        # Format long lines to wrap cleanly
        lines = output_text.strip().splitlines()
        formatted = []
        for line in lines:
            if len(line) > 76 and not line.startswith("Name:") and not line.startswith("Roll No:"):
                formatted.append(textwrap.fill(line, width=74))
            else:
                formatted.append(line)
        wrapped_lines = ("\n".join(formatted)).splitlines()

        font = self._get_font(theme.font_size)
        font_small = self._get_font(11)
        line_h = theme.line_height

        # Calculate max line width
        max_w = 0
        for line in wrapped_lines:
            bbox = font.getbbox(line) if hasattr(font, "getbbox") else (0, 0, len(line) * 8, 14)
            w = bbox[2] - bbox[0]
            if w > max_w:
                max_w = w

        user = getattr(self.system, "username", "student")
        host = getattr(self.system, "hostname", "linux")
        prompt_line = f"{user}@{host}:~/workspace$ {command_str or 'run'}"
        prompt_bbox = font.getbbox(prompt_line) if hasattr(font, "getbbox") else (0, 0, len(prompt_line) * 8, 14)
        max_w = max(max_w, prompt_bbox[2] - prompt_bbox[0])

        if theme.window_style == "macos-dots":
            header_h = 32
            total_w = max(max_w + 36, 420)
            total_h = header_h + (len(wrapped_lines) + 2) * line_h + 20

            img = Image.new("RGB", (total_w, total_h), theme.bg_color)
            draw = ImageDraw.Draw(img)

            # Header bar
            draw.rectangle([(0, 0), (total_w, header_h)], fill=theme.header_bg)
            draw.ellipse([(14, 11), (24, 21)], fill=(255, 95, 86))
            draw.ellipse([(30, 11), (40, 21)], fill=(255, 189, 46))
            draw.ellipse([(46, 11), (56, 21)], fill=(39, 201, 63))
            draw.text((66, 9), f"terminal — {user}@{host}", font=font_small, fill=(140, 145, 155))

            # Prompt line
            curr_y = header_h + 12
            draw.text((18, curr_y), prompt_line, font=font, fill=theme.prompt_color)
            curr_y += line_h + 4

            # Console output lines
            for line in wrapped_lines:
                draw.text((18, curr_y), line, font=font, fill=theme.text_color)
                curr_y += line_h

            # Outer border
            draw.rectangle([(0, 0), (total_w - 1, total_h - 1)], outline=theme.border_color, width=1)
        else:
            # Frameless academic paper canvas (bheeshamks signature)
            total_w = max(max_w + 32, 340)
            total_h = len(wrapped_lines) * line_h + 24
            img = Image.new("RGB", (total_w, total_h), theme.bg_color)
            draw = ImageDraw.Draw(img)

            curr_y = 12
            for line in wrapped_lines:
                draw.text((16, curr_y), line, font=font, fill=theme.text_color)
                curr_y += line_h

            draw.rectangle([(0, 0), (total_w - 1, total_h - 1)], outline=theme.border_color, width=1)

        dest_path.parent.mkdir(parents=True, exist_ok=True)
        img.save(dest_path, "PNG", optimize=True)
        return dest_path

    def _auto_crop(self, src: Path, dest: Path, bg_color: Tuple[int, int, int]) -> None:
        """Crops excess background margins cleanly matching the active theme background."""
        try:
            im = Image.open(src).convert("RGB")
            bg = Image.new("RGB", im.size, bg_color)
            diff = ImageChops.difference(im, bg)
            bbox = diff.getbbox()
            if bbox:
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

    def _fallback_code_pillow(self, code_str: str, dest: Path, theme: ScreenshotTheme) -> None:
        """Pillow fallback for code rendering."""
        lines = code_str.splitlines()
        font = self._get_font(theme.font_size)
        width = max(len(l) for l in lines) * 9 + 40
        height = len(lines) * theme.line_height + 40
        img = Image.new("RGB", (max(width, 400), max(height, 200)), color=theme.bg_color)
        draw = ImageDraw.Draw(img)
        y = 20
        for line in lines:
            color = theme.accent_color if line.strip().startswith(("#include", "int ", "return", "for", "if", "SELECT", "CREATE")) else theme.text_color
            draw.text((20, y), line, font=font, fill=color)
            y += theme.line_height
        img.save(dest, "PNG")
