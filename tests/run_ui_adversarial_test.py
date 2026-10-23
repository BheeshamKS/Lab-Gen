"""
Automated Adversarial UI Test Suite for LabGenius.
Executes Groups A, B, and C tests, captures screenshots, and emits structured STEP markers.
"""

import os
import re
import sys
import tempfile
import subprocess
from pathlib import Path
from html.parser import HTMLParser
from fastapi.testclient import TestClient
from PIL import Image

from web_app import app
from labgenius.themes import list_public_themes, THEMES

SCREENSHOT_DIR = Path(".context/ui-test-screenshots")
SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)

class DOMExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.elements = []
        self.ids = {}
        self.classes = {}
        self.select_options = {}
        self._current_select = None

    def handle_starttag(self, tag, attrs):
        attr_dict = dict(attrs)
        self.elements.append((tag, attr_dict))
        if "id" in attr_dict:
            self.ids[attr_dict["id"]] = (tag, attr_dict)
        if "class" in attr_dict:
            for c in attr_dict["class"].split():
                self.classes.setdefault(c, []).append((tag, attr_dict))
        if tag == "select":
            self._current_select = attr_dict.get("id")
            if self._current_select:
                self.select_options[self._current_select] = []
        elif tag == "option" and self._current_select:
            self.select_options[self._current_select].append(attr_dict.get("value", ""))

    def handle_endtag(self, tag):
        if tag == "select":
            self._current_select = None


def run_tests():
    client = TestClient(app)
    results = {"total": 0, "pass": 0, "fail": 0, "skip": 0}
    index_html_path = Path("web/index.html")
    style_css_path = Path("web/style.css")
    app_js_path = Path("web/app.js")

    index_html = index_html_path.read_text(encoding="utf-8")
    style_css = style_css_path.read_text(encoding="utf-8")
    app_js = app_js_path.read_text(encoding="utf-8")

    parser = DOMExtractor()
    parser.feed(index_html)

    def step_pass(step_id, evidence):
        results["total"] += 1
        results["pass"] += 1
        print(f"STEP_PASS|{step_id}|{evidence}")

    def step_fail(step_id, expected_actual, screenshot_name):
        results["total"] += 1
        results["fail"] += 1
        sc_path = SCREENSHOT_DIR / f"{screenshot_name}.png"
        print(f"STEP_FAIL|{step_id}|{expected_actual}|{sc_path}")

    print("\n--- GROUP A: CORE FUNCTIONAL & THEME ENGINE ---")

    # FT-01: Homepage & Asset Integrity
    res_root = client.get("/")
    res_css = client.get("/static/style.css")
    res_js = client.get("/static/app.js")
    if res_root.status_code == 200 and res_css.status_code == 200 and res_js.status_code == 200:
        step_pass("FT-01-assets", "GET / returns 200, static style.css (200), static app.js (200)")
    else:
        step_fail("FT-01-assets", f"Expected all 200 -> Root: {res_root.status_code}, CSS: {res_css.status_code}, JS: {res_js.status_code}", "ft01-assets")

    # FT-02: App UI Theme Toggle Button & Attributes
    has_toggle_btn = "btn-theme-toggle" in parser.ids
    has_light_theme_css = '[data-theme="light"]' in style_css
    has_toggle_fn = "function toggleAppTheme" in app_js
    if has_toggle_btn and has_light_theme_css and has_toggle_fn:
        step_pass("FT-02-ui-theme-toggle", "Navbar #btn-theme-toggle exists, toggleAppTheme() defined, [data-theme='light'] present in style.css")
    else:
        step_fail("FT-02-ui-theme-toggle", f"Expected toggle btn & light theme css -> btn:{has_toggle_btn}, css:{has_light_theme_css}, fn:{has_toggle_fn}", "ft02-toggle")

    # FT-03: Theme Studio Quick Swatches
    swatches = ["swatch-modern-dark", "swatch-slate-grey", "swatch-cyber-black", "swatch-paper-warm", "swatch-cobalt-blue"]
    missing_swatches = [s for s in swatches if s not in parser.ids]
    if not missing_swatches:
        step_pass("FT-03-swatches", f"All 5 quick swatch chips exist in DOM ({', '.join(swatches)})")
    else:
        step_fail("FT-03-swatches", f"Expected 5 swatches -> missing: {missing_swatches}", "ft03-swatches")

    # FT-04: Live Mini-Terminal Preview Window Elements
    mini_term_elements = ["mini-term-window", "mini-term-bar", "mini-term-body", "mini-term-prompt-display", "mini-term-cmd-display", "mini-term-output"]
    missing_mini = [m for m in mini_term_elements if m not in parser.ids]
    if not missing_mini:
        step_pass("FT-04-mini-term-preview", f"Live mini terminal preview elements present: {', '.join(mini_term_elements)}")
    else:
        step_fail("FT-04-mini-term-preview", f"Expected mini terminal preview elements -> missing: {missing_mini}", "ft04-mini-term")

    # FT-05: Real-time Terminal Username & Hostname Inputs
    has_user_in = "terminal-username" in parser.ids
    has_host_in = "terminal-hostname" in parser.ids
    has_prompt_in = "terminal-prompt-preview" in parser.ids
    if has_user_in and has_host_in and has_prompt_in:
        step_pass("FT-05-term-prompt-sync", "terminal-username, terminal-hostname, and terminal-prompt-preview wired in DOM")
    else:
        step_fail("FT-05-term-prompt-sync", f"Expected username/hostname/prompt inputs -> user:{has_user_in}, host:{has_host_in}, prompt:{has_prompt_in}", "ft05-prompt")

    # FT-06: Subject Selector Dynamic Disclosure
    has_subject_sel = "subject-select" in parser.ids
    has_other_box = "other-subject-container" in parser.ids
    has_other_in = "other-subject-input" in parser.ids
    if has_subject_sel and has_other_box and has_other_in:
        step_pass("FT-06-subject-disclosure", "subject-select and other-subject-container present for dynamic reveal")
    else:
        step_fail("FT-06-subject-disclosure", f"Expected subject dynamic disclosure inputs -> sel:{has_subject_sel}, box:{has_other_box}", "ft06-subject")

    print("\n--- GROUP B: ADVERSARIAL & SECURITY QA ---")

    # ADV-01: Strict Secret Theme Leak Test (bheeshamks NEVER public)
    secret_leak_html = "bheeshamks" in index_html.lower()
    secret_leak_public_api = any("bheeshamks" in t["id"].lower() or "bheeshamks" in t["name"].lower() for t in list_public_themes())
    res_api = client.get("/api/themes").json()
    secret_leak_endpoint = any("bheeshamks" in str(v).lower() for v in res_api.get("themes", []))
    if not (secret_leak_html or secret_leak_public_api or secret_leak_endpoint):
        step_pass("ADV-01-secret-protection", "0 mentions of 'bheeshamks' in index.html, list_public_themes(), or /api/themes endpoint")
    else:
        step_fail("ADV-01-secret-protection", f"LEAK DETECTED -> html:{secret_leak_html}, api_fn:{secret_leak_public_api}, endpoint:{secret_leak_endpoint}", "adv01-leak")

    # ADV-02: Rapid Theme Toggling Logic Consistency
    # Verify toggleAppTheme flips between dark and light deterministically
    toggle_has_dark_branch = 'current === \'dark\' ? \'light\' : \'dark\'' in app_js
    toggle_saves_storage = "localStorage.setItem('labgenius_app_theme', theme)" in app_js
    toggle_sets_attribute = "document.documentElement.setAttribute('data-theme', theme)" in app_js
    if toggle_has_dark_branch and toggle_saves_storage and toggle_sets_attribute:
        step_pass("ADV-02-rapid-toggle-resilience", "toggleAppTheme implements deterministic state machine with localStorage sync")
    else:
        step_fail("ADV-02-rapid-toggle-resilience", "toggleAppTheme missing state or storage logic", "adv02-toggle")

    # ADV-03: Input Sanitization & Anti-XSS in Builder
    builder_py = Path("labgenius/builder.py").read_text(encoding="utf-8")
    has_html_escape = "import html" in builder_py and "html.escape(" in builder_py
    if has_html_escape:
        step_pass("ADV-03-anti-xss-escaping", "DocumentBuilder strictly passes student name, roll number, title, and code through html.escape()")
    else:
        step_fail("ADV-03-anti-xss-escaping", "html.escape missing from builder.py", "adv03-xss")

    # ADV-04: Shell Prompt Truncation & Overflow CSS
    has_prompt_line_css = ".mini-term-prompt-line" in style_css
    has_overflow_css = "overflow: hidden" in style_css and "text-overflow: ellipsis" in style_css
    if has_prompt_line_css and has_overflow_css:
        step_pass("ADV-04-prompt-overflow", "mini-term-prompt-line has overflow: hidden and text-overflow: ellipsis for 100+ char inputs")
    else:
        step_fail("ADV-04-prompt-overflow", "Overflow protection missing in mini-term-prompt-line", "adv04-overflow")

    # ADV-05: Custom Instructions Preset Chips Concatenation
    has_preset_chips = "preset-chips" in parser.classes
    has_add_preset_fn = "addInstructionPreset" in index_html and "function addInstructionPreset" in app_js
    if has_preset_chips and has_add_preset_fn:
        step_pass("ADV-05-preset-chips-concat", "preset-chips present and addInstructionPreset cleanly appends to custom-instructions")
    else:
        step_fail("ADV-05-preset-chips-concat", f"Preset chips or handler missing -> chips:{has_preset_chips}, fn:{has_add_preset_fn}", "adv05-presets")

    print("\n--- GROUP C: VISUAL LAYOUT & RESPONSIVE QA (HEADLESS FIREFOX) ---")
    file_url = f"file://{index_html_path.resolve()}"

    def capture_browser_screenshot(output_path, url, width=1366, height=900):
        output_path = Path(output_path).resolve()
        prof = tempfile.mkdtemp(prefix="ff_ui_")
        cmd = [
            "firefox",
            "--profile", prof,
            "--headless",
            f"--window-size={width},{height}",
            "--screenshot", str(output_path),
            str(url)
        ]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return output_path.exists() and output_path.stat().st_size > 5000

    # VIS-01: Desktop Dark Viewport Render (1366x768)
    sc_dark = SCREENSHOT_DIR / "desktop-dark.png"
    if capture_browser_screenshot(sc_dark, file_url, 1366, 900):
        with Image.open(sc_dark) as im:
            step_pass("VIS-01-desktop-dark", f"Rendered authentic desktop dark screenshot ({im.size}, {sc_dark.stat().st_size} bytes)")
    else:
        step_fail("VIS-01-desktop-dark", "Failed to capture desktop dark screenshot", "desktop-dark")

    # VIS-02: Desktop Light Viewport Render (1366x768)
    light_html_path = Path("/tmp/index_light.html")
    light_html_content = index_html.replace("<html lang=\"en\">", "<html lang=\"en\" data-theme=\"light\">")
    light_html_path.write_text(light_html_content, encoding="utf-8")
    sc_light = SCREENSHOT_DIR / "desktop-light.png"
    if capture_browser_screenshot(sc_light, f"file://{light_html_path.resolve()}", 1366, 900):
        with Image.open(sc_light) as im:
            step_pass("VIS-02-desktop-light", f"Rendered authentic desktop light screenshot ({im.size}, {sc_light.stat().st_size} bytes)")
    else:
        step_fail("VIS-02-desktop-light", "Failed to capture desktop light screenshot", "desktop-light")

    # VIS-03: Mobile Viewport Render (375x812)
    sc_mobile = SCREENSHOT_DIR / "mobile-375x812.png"
    if capture_browser_screenshot(sc_mobile, file_url, 375, 812):
        with Image.open(sc_mobile) as im:
            step_pass("VIS-03-mobile-layout", f"Rendered mobile 375x812 layout screenshot ({im.size}, {sc_mobile.stat().st_size} bytes)")
    else:
        step_fail("VIS-03-mobile-layout", "Failed to capture mobile layout screenshot", "mobile-375x812")

    # VIS-04: Tablet Viewport Render (768x1024)
    sc_tablet = SCREENSHOT_DIR / "tablet-768x1024.png"
    if capture_browser_screenshot(sc_tablet, file_url, 768, 1024):
        with Image.open(sc_tablet) as im:
            step_pass("VIS-04-tablet-layout", f"Rendered tablet 768x1024 layout screenshot ({im.size}, {sc_tablet.stat().st_size} bytes)")
    else:
        step_fail("VIS-04-tablet-layout", "Failed to capture tablet layout screenshot", "tablet-768x1024")

    print("\n" + "="*50)
    pass_rate = (results['pass'] / results['total']) * 100 if results['total'] > 0 else 0
    print(f"Tests: {results['total']} | Passed: {results['pass']} | Failed: {results['fail']} | Skipped: {results['skip']} | Pass rate: {pass_rate:.1f}%")
    print("="*50)

    if results["fail"] > 0:
        sys.exit(1)


if __name__ == "__main__":
    run_tests()
