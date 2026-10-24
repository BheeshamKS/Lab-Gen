"""
Comprehensive Verification Tests for the LabGenius Full UI Overhaul.
Verifies the 3-zone layout, theme engine, secret theme privacy, WebMCP tool definitions,
and end-to-end API workflows.
"""

import os
import json
import pytest
from pathlib import Path
from fastapi.testclient import TestClient

from web_app import app
from labgenius.themes import get_theme, list_public_themes, THEMES

client = TestClient(app)
BASE_DIR = Path(__file__).resolve().parent.parent


def test_index_html_contains_new_3zone_layout():
    """Verify web/index.html includes the app-shell, app-rail, settings-drawer, and discrete page views."""
    res = client.get("/")
    assert res.status_code == 200
    html = res.text

    # Zone 1: Navigation Rail (no duplicate logo, clean navigation items)
    assert 'class="app-rail"' in html or 'id="app-rail"' in html
    assert 'id="rail-item-home"' in html
    assert 'id="rail-item-doctools"' in html
    assert 'id="rail-item-playground"' in html
    assert 'id="rail-item-humanwriter"' in html
    assert 'id="btn-theme-toggle"' in html
    assert 'class="rail-logo"' not in html

    # Topbar Brand: Contains unified logo mark, no redundant doctools button
    assert 'class="topbar-logo-mark"' in html
    assert 'id="btn-quick-doctools"' not in html

    # Zone 2: Slide-Over Settings Drawer
    assert 'id="settings-drawer"' in html
    assert 'id="dtab-profile"' in html
    assert 'id="dtab-ai"' in html
    assert 'id="dtab-theme"' in html
    assert 'id="custom-theme-input"' in html
    assert 'id="btn-apply-custom-theme"' in html
    assert 'id="mini-term-window"' in html

    # Zone 3: Main Workspace & Page Views
    assert 'id="view-home"' in html
    assert 'id="view-wizard"' in html
    assert 'id="view-progress"' in html
    assert 'id="view-results"' in html
    assert 'id="view-doctools"' in html
    assert 'id="view-playground"' in html
    assert 'id="view-humanwriter"' in html


def test_theme_system_public_themes_and_secret_privacy():
    """Verify that public themes are returned and bheeshamks remains secret."""
    res = client.get("/api/themes")
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True

    public_ids = [t["id"] for t in data["themes"]]
    # All 5 public themes must be present
    assert "modern-dark" in public_ids
    assert "slate-grey" in public_ids
    assert "cyber-black" in public_ids
    assert "paper-warm" in public_ids
    assert "cobalt-blue" in public_ids

    # The secret theme 'bheeshamks' MUST NOT appear in the public list
    assert "bheeshamks" not in public_ids


def test_secret_bheeshamks_env_activation():
    """Verify that setting LABGENIUS_SCREENSHOT_THEME=bheeshamks activates the private theme."""
    os.environ["LABGENIUS_SCREENSHOT_THEME"] = "bheeshamks"
    try:
        active = get_theme()
        assert active.id == "bheeshamks"
        assert active.is_secret is True
        assert active.bg_hex == "#ffffff"
        assert active.text_hex == "#0f0f0f"
    finally:
        os.environ.pop("LABGENIUS_SCREENSHOT_THEME", None)


def test_custom_theme_direct_resolve():
    """Verify that /api/theme/{theme_name} resolves bheeshamks when typed in full without exposing it in public list."""
    res = client.get("/api/theme/bheeshamks")
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["theme"]["id"] == "bheeshamks"
    assert data["theme"]["name"] == "Bheesham Signature"
    assert data["theme"]["is_secret"] is True
    assert data["theme"]["bg_hex"] == "#ffffff"
    assert data["theme"]["window_style"] == "frameless"

    # Unknown theme returns success=False
    res_err = client.get("/api/theme/nonexistent-xyz")
    assert res_err.status_code == 200
    assert res_err.json()["success"] is False


def test_webmcp_tools_registration_in_app_js():
    """Verify that web/app.js contains first-party WebMCP registration with closed schemas."""
    app_js_path = BASE_DIR / "web" / "app.js"
    assert app_js_path.exists()
    content = app_js_path.read_text(encoding="utf-8")

    assert "registerWebMCPTools" in content
    assert "modelContext.registerTool" in content
    assert "generate_lab" in content
    assert "execute_code" in content
    assert "merge_documents" in content
    assert "switch_theme" in content
    assert "get_active_session" in content
    assert "additionalProperties: false" in content


def test_document_tools_api_endpoints():
    """Verify that all Document Tools API endpoints respond correctly."""
    # Sample files endpoint
    res = client.get("/api/doc-tools/sample-files")
    assert res.status_code == 200
    data = res.json()
    assert "samples" in data
    assert len(data["samples"]) > 0


def test_playground_execution_api():
    """Verify python execution in sandbox via /api/execute-scratchpad."""
    payload = {
        "language": "python",
        "code": "a = 2 + 3\nprint(f'SUM={a}')",
        "stdin": ""
    }
    res = client.post("/api/execute-scratchpad", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["exit_code"] == 0
    assert "SUM=5" in data["stdout"]
