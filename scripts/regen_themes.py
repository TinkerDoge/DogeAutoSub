"""Regenerate the two CSS files from theme_tokens.

Run this whenever modules/theme_tokens.py changes:
    python scripts/regen_themes.py
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from modules.theme_tokens import build_stylesheet

OUTPUTS = {
    "light": os.path.join(ROOT, "modules", "styleSheetLight.css"),
    "dark":  os.path.join(ROOT, "modules", "styleSheetDark.css"),
}

HEADER = "/* AUTO-GENERATED from modules/theme_tokens.py — do not edit by hand. */\n/* Run: python scripts/regen_themes.py */\n\n"

for theme, path in OUTPUTS.items():
    css = HEADER + build_stylesheet(theme)
    with open(path, "w", encoding="utf-8") as f:
        f.write(css)
    print(f"Wrote {path} ({len(css)} bytes)")
