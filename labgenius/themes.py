"""
Modular Screenshot & Document Theme System for LabGenius.
Provides curated terminal themes (Slate Grey, Cyber Black, Editorial Parchment, Modern Dark, Cobalt Blue)
and supports custom signature themes configured via .env.
"""

import os
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, List, Optional, Tuple


def load_dotenv():
    """Parses .env file from project root if present and sets environment variables."""
    root_dir = Path(__file__).resolve().parent.parent
    env_paths = [
        root_dir / ".env",
        Path.cwd() / ".env",
    ]
    for env_path in env_paths:
        if env_path.exists():
            try:
                with open(env_path, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if not line or line.startswith("#") or "=" not in line:
                            continue
                        k, v = line.split("=", 1)
                        k = k.strip()
                        v = v.strip().strip("'\"")
                        if k and k not in os.environ:
                            os.environ[k] = v
            except Exception:
                pass


# Execute dotenv loading on module import
load_dotenv()


@dataclass
class ScreenshotTheme:
    id: str
    name: str
    is_secret: bool
    category: str  # 'grey', 'black', 'white', 'dark', 'secret'
    bg_color: Tuple[int, int, int]
    bg_hex: str
    text_color: Tuple[int, int, int]
    text_hex: str
    syntax_style: str  # Pygments syntax highlighting style
    window_style: str  # 'macos-dots', 'terminal-bar', 'frameless'
    border_color: Tuple[int, int, int]
    header_bg: Tuple[int, int, int]
    prompt_color: Tuple[int, int, int]
    accent_color: Tuple[int, int, int]
    font_name: str = "DejaVu Sans Mono"
    font_size: int = 13
    line_height: int = 22


THEMES: Dict[str, ScreenshotTheme] = {
    # -------------------------------------------------------------
    # 1. SECRET THEME: BHEESHAMKS (Signature Academic White)
    # Strictly for owner use via .env (SCREENSHOT_THEME=bheeshamks).
    # Never listed in public dropdowns, docs, or UI listings.
    # -------------------------------------------------------------
    "bheeshamks": ScreenshotTheme(
        id="bheeshamks",
        name="Bheesham Signature",
        is_secret=True,
        category="secret",
        bg_color=(255, 255, 255),
        bg_hex="#ffffff",
        text_color=(15, 15, 15),
        text_hex="#0f0f0f",
        syntax_style="vs",
        window_style="frameless",
        border_color=(226, 232, 240),
        header_bg=(255, 255, 255),
        prompt_color=(30, 41, 59),
        accent_color=(0, 0, 255),
    ),

    # -------------------------------------------------------------
    # 2. PUBLIC THEME: SLATE GREY (Charcoal Slate / Matte Grey)
    # -------------------------------------------------------------
    "slate-grey": ScreenshotTheme(
        id="slate-grey",
        name="Charcoal Slate (Grey)",
        is_secret=False,
        category="grey",
        bg_color=(40, 44, 52),
        bg_hex="#282c34",
        text_color=(171, 178, 191),
        text_hex="#abb2bf",
        syntax_style="one-dark",
        window_style="macos-dots",
        border_color=(60, 66, 78),
        header_bg=(33, 37, 43),
        prompt_color=(97, 175, 239),
        accent_color=(97, 175, 239),
    ),

    # -------------------------------------------------------------
    # 3. PUBLIC THEME: CYBER BLACK (Pitch Black OLED)
    # -------------------------------------------------------------
    "cyber-black": ScreenshotTheme(
        id="cyber-black",
        name="Cyber OLED (Pitch Black)",
        is_secret=False,
        category="black",
        bg_color=(10, 12, 16),
        bg_hex="#0a0c10",
        text_color=(230, 237, 243),
        text_hex="#e6edf3",
        syntax_style="github-dark",
        window_style="macos-dots",
        border_color=(48, 54, 61),
        header_bg=(16, 20, 26),
        prompt_color=(63, 185, 80),
        accent_color=(88, 166, 255),
    ),

    # -------------------------------------------------------------
    # 4. PUBLIC THEME: EDITORIAL PARCHMENT (Warm Vintage Light - NOT Pure White)
    # -------------------------------------------------------------
    "paper-warm": ScreenshotTheme(
        id="paper-warm",
        name="Editorial Parchment (Warm Light)",
        is_secret=False,
        category="white",
        bg_color=(245, 241, 233),
        bg_hex="#f5f1e9",
        text_color=(46, 52, 64),
        text_hex="#2e3440",
        syntax_style="solarized-light",
        window_style="macos-dots",
        border_color=(216, 207, 188),
        header_bg=(236, 230, 220),
        prompt_color=(133, 102, 33),
        accent_color=(181, 137, 0),
    ),

    # -------------------------------------------------------------
    # 5. PUBLIC THEME: MIDNIGHT MODERN (Deep Dark Indigo)
    # -------------------------------------------------------------
    "modern-dark": ScreenshotTheme(
        id="modern-dark",
        name="Midnight Modern (Dark)",
        is_secret=False,
        category="dark",
        bg_color=(22, 24, 33),
        bg_hex="#161821",
        text_color=(210, 215, 222),
        text_hex="#d2d7de",
        syntax_style="monokai",
        window_style="macos-dots",
        border_color=(45, 49, 66),
        header_bg=(29, 31, 42),
        prompt_color=(180, 142, 173),
        accent_color=(138, 178, 242),
    ),

    # -------------------------------------------------------------
    # 6. PUBLIC THEME: DEEP COBALT (Navy Blue)
    # -------------------------------------------------------------
    "cobalt-blue": ScreenshotTheme(
        id="cobalt-blue",
        name="Deep Cobalt (Navy)",
        is_secret=False,
        category="dark",
        bg_color=(15, 23, 42),
        bg_hex="#0f172a",
        text_color=(226, 232, 240),
        text_hex="#e2e8f0",
        syntax_style="nord",
        window_style="macos-dots",
        border_color=(51, 65, 85),
        header_bg=(30, 41, 59),
        prompt_color=(56, 189, 248),
        accent_color=(56, 189, 248),
    ),
}

# Legacy and convenient aliases
THEME_ALIASES = {
    "linux-dark": "modern-dark",
    "pop-os-dark": "modern-dark",
    "cosmic-dark": "slate-grey",
    "ubuntu-yaru": "slate-grey",
    "vscode-dark": "cyber-black",
    "dark": "modern-dark",
    "grey": "slate-grey",
    "gray": "slate-grey",
    "black": "cyber-black",
    "white": "paper-warm",
    "light": "paper-warm",
    "parchment": "paper-warm",
    "cobalt": "cobalt-blue",
}


def get_theme(theme_name: Optional[str] = None) -> ScreenshotTheme:
    """
    Resolves the active ScreenshotTheme.
    Order of precedence:
    1. Explicit theme_name passed
    2. SCREENSHOT_THEME / TERMINAL_THEME / LAB_THEME from environment or .env
    3. Default to modern-dark
    """
    raw_name = (
        theme_name
        or os.environ.get("SCREENSHOT_THEME")
        or os.environ.get("TERMINAL_THEME")
        or os.environ.get("LAB_THEME")
        or "modern-dark"
    )
    normalized = str(raw_name).strip().lower()

    # Secret owner theme resolution
    if normalized == "bheeshamks":
        return THEMES["bheeshamks"]

    # Alias mapping
    if normalized in THEME_ALIASES:
        normalized = THEME_ALIASES[normalized]

    # Public theme lookup
    if normalized in THEMES and not THEMES[normalized].is_secret:
        return THEMES[normalized]

    # Default fallback
    return THEMES["modern-dark"]


def list_public_themes() -> List[Dict]:
    """Returns only public themes suitable for client dropdowns and public listings."""
    public_list = []
    for t_id, theme in THEMES.items():
        if not theme.is_secret:
            public_list.append({
                "id": theme.id,
                "name": theme.name,
                "category": theme.category,
                "bg_hex": theme.bg_hex,
                "text_hex": theme.text_hex,
                "header_bg_hex": f"#{theme.header_bg[0]:02x}{theme.header_bg[1]:02x}{theme.header_bg[2]:02x}",
                "border_hex": f"#{theme.border_color[0]:02x}{theme.border_color[1]:02x}{theme.border_color[2]:02x}",
                "prompt_hex": f"#{theme.prompt_color[0]:02x}{theme.prompt_color[1]:02x}{theme.prompt_color[2]:02x}",
            })
    return public_list
