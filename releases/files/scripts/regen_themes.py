"""Regenerate CSS snapshots from theme_tokens palettes.

The old light/dark pair is superseded by the 4-palette system. This script
now writes one file per palette so the auto-updater manifest remains stable.

Run whenever modules/theme_tokens.py changes:
    python scripts/regen_themes.py
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from modules.theme_tokens import build_stylesheet, PALETTES

HEADER = "/* AUTO-GENERATED from modules/theme_tokens.py — do not edit by hand. */\n/* Run: python scripts/regen_themes.py */\n\n"

for palette_id in PALETTES:
    path = os.path.join(ROOT, "modules", f"styleSheet_{palette_id}.css")
    css = HEADER + build_stylesheet(palette_id)
    with open(path, "w", encoding="utf-8") as f:
        f.write(css)
    print(f"Wrote {path} ({len(css)} bytes)")
