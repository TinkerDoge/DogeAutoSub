"""Single source of truth for DogeAutoSub palette colors.

The dark macOS-inspired chrome is fixed; only the accent color and the
title-bar stripe bands change between palettes. Surface tones, borders,
and text grays are shared so contrast can never break when a user
switches palettes.
"""

SHARED_TOKENS = {
    "desktop_bg":     "#0e0e10",
    "window_bg":      "#1c1c1f",
    "sidebar_bg":     "#161618",
    "titlebar_bg":    "#232327",
    "card_bg":        "#1c1c1f",
    "input_bg":       "#0f0f11",
    "border":         "#2a2a2e",
    "border_strong":  "#3a3a3e",
    "text_primary":   "#cfcfd2",
    "text_secondary": "#9a9a9f",
    "text_tertiary":  "#6a6a70",
    "text_pixel":     "#8a8a90",
    "error":          "#ff6b6b",
    "warn":           "#ffd166",
    "success":        "#7ed957",
}

PALETTES = {
    "atari": {
        "name": "Atari Sunset",
        "stripe": ["#7a3b2e", "#9a5a36", "#b8823a", "#c9a558"],
        "accent": "#b8823a",
        "accent_text": "#1a1207",
    },
    "rainbow": {
        "name": "Apple Six-Stripe",
        "stripe": ["#6f8c52", "#c2a85a", "#c4884a", "#a85049", "#7a4a8a", "#4f7a9a"],
        "accent": "#6f8c52",
        "accent_text": "#0e0e10",
    },
    "crt": {
        "name": "CRT Dusk",
        "stripe": ["#3a6a8a", "#5a7a9a", "#8a5a8a", "#a85a6a"],
        "accent": "#5a7a9a",
        "accent_text": "#0e0e10",
    },
    "famicom": {
        "name": "Famicom",
        "stripe": ["#8a2a2a", "#b84a3a", "#d6c7b5", "#3a3a3a"],
        "accent": "#b84a3a",
        "accent_text": "#0e0e10",
    },
}

DEFAULT_PALETTE = "atari"


def build_stylesheet(palette_id: str) -> str:
    if palette_id not in PALETTES:
        raise KeyError(f"Unknown palette: {palette_id!r}. Choose from {list(PALETTES)}.")
    p = PALETTES[palette_id]
    tokens = {**SHARED_TOKENS, "accent": p["accent"], "accent_text": p["accent_text"]}
    return _TEMPLATE.format(**tokens)


_TEMPLATE = """
* {{
    font-family: -apple-system, "SF Pro Text", "Inter", "Segoe UI", system-ui, sans-serif;
    color: {text_primary};
}}

QMainWindow {{
    background: {desktop_bg};
}}

QWidget#centralWidget {{
    background: {window_bg};
    border-radius: 12px;
}}

QFrame#fauxTitleBar {{
    background: {titlebar_bg};
    border-top-left-radius: 12px;
    border-top-right-radius: 12px;
    min-height: 28px;
    max-height: 28px;
    border-bottom: 1px solid {border};
}}

QLabel#fauxTitleText {{
    color: {text_primary};
    font-size: 12px;
    font-weight: 600;
    background: transparent;
}}

QFrame#sidebar {{
    background: {sidebar_bg};
    border-right: 1px solid {border};
}}

QLabel#sidebarSectionLabel {{
    color: {text_tertiary};
    font-family: "Pixelated MS Sans Serif", "MS Sans Serif", monospace;
    font-size: 9px;
    letter-spacing: 1.4px;
    padding: 8px 10px 4px 10px;
    background: transparent;
}}

QPushButton#sidebarItem {{
    background: transparent;
    color: {text_secondary};
    border: none;
    border-radius: 6px;
    padding: 7px 10px;
    text-align: left;
    font-size: 12px;
}}
QPushButton#sidebarItem:hover {{
    background: {border};
    color: {text_primary};
}}
QPushButton#sidebarItem[active="true"] {{
    background: {accent};
    color: {accent_text};
    font-weight: 600;
}}

QFrame#card {{
    background: {card_bg};
    border: 1px solid {border};
    border-radius: 8px;
}}

QLabel#sectionTitle {{
    color: {text_tertiary};
    font-family: "Pixelated MS Sans Serif", "MS Sans Serif", monospace;
    font-size: 9px;
    letter-spacing: 1.4px;
    text-transform: uppercase;
    background: transparent;
}}

QLabel#statusLabel {{
    color: {text_primary};
    font-size: 12px;
    background: transparent;
}}

QLabel#etaLabel {{
    color: {text_secondary};
    font-family: "Pixelated MS Sans Serif", "MS Sans Serif", monospace;
    font-size: 10px;
    background: transparent;
}}

QPushButton {{
    background: {border};
    color: {text_primary};
    border: 1px solid {border_strong};
    border-radius: 6px;
    padding: 6px 12px;
    font-size: 12px;
    min-height: 22px;
}}
QPushButton:hover {{
    background: {border_strong};
}}
QPushButton:disabled {{
    color: {text_tertiary};
}}

QPushButton#closeBtn, QPushButton#minBtn, QPushButton#zoomBtn {{
    min-width: 12px; max-width: 12px;
    min-height: 12px; max-height: 12px;
    padding: 0;
    margin: 0 2px;
    border: none;
    border-radius: 6px;
}}
QPushButton#closeBtn  {{ background: #ff5f57; }}
QPushButton#minBtn    {{ background: #febc2e; }}
QPushButton#zoomBtn   {{ background: #28c840; }}
QPushButton#closeBtn:hover, QPushButton#minBtn:hover, QPushButton#zoomBtn:hover {{
    border: 1px solid rgba(0,0,0,0.3);
}}

QPushButton#startButton, QPushButton#generateNotesBtn, QPushButton#translateFileBtn {{
    background: {accent};
    color: {accent_text};
    border: 1px solid {accent};
    font-weight: 700;
    min-height: 30px;
    padding: 7px 18px;
}}
QPushButton#startButton:hover, QPushButton#generateNotesBtn:hover, QPushButton#translateFileBtn:hover {{
    background: {accent};
    border-color: {text_primary};
}}

QComboBox, QLineEdit, QTextEdit, QPlainTextEdit {{
    background: {input_bg};
    color: {text_primary};
    border: 1px solid {border};
    border-radius: 6px;
    padding: 5px 8px;
    font-size: 12px;
    min-height: 20px;
    selection-background-color: {accent};
    selection-color: {accent_text};
}}
QComboBox:hover, QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {{
    border-color: {accent};
}}

QComboBox QAbstractItemView {{
    background: {card_bg};
    color: {text_primary};
    border: 1px solid {border_strong};
    selection-background-color: {accent};
    selection-color: {accent_text};
}}

QLabel {{
    color: {text_primary};
    font-size: 12px;
    background: transparent;
}}

QProgressBar {{
    background: {input_bg};
    border: 1px solid {border};
    border-radius: 4px;
    text-align: center;
    font-size: 9px;
    color: {text_primary};
    min-height: 8px;
    max-height: 8px;
}}
QProgressBar::chunk {{
    background: {accent};
    border-radius: 4px;
}}

QSlider::groove:horizontal {{
    height: 4px;
    background: {border};
    border-radius: 2px;
}}
QSlider::handle:horizontal {{
    background: {accent};
    border: none;
    width: 14px;
    height: 14px;
    margin: -5px 0;
    border-radius: 7px;
}}
QSlider::sub-page:horizontal {{
    background: {accent};
    border-radius: 2px;
}}

QMenu {{
    background: {card_bg};
    border: 1px solid {border_strong};
    border-radius: 8px;
    padding: 6px;
    color: {text_primary};
}}
QMenu::item {{
    padding: 6px 10px;
    border-radius: 6px;
    font-size: 12px;
}}
QMenu::item:selected {{
    background: {border};
}}

QScrollBar:vertical {{
    background: transparent;
    width: 10px;
    margin: 4px 2px;
}}
QScrollBar::handle:vertical {{
    background: {border_strong};
    min-height: 24px;
    border-radius: 4px;
}}
QScrollBar::handle:vertical:hover {{
    background: {text_tertiary};
}}
QScrollBar::add-line, QScrollBar::sub-line {{
    height: 0;
}}

QToolTip {{
    background: {card_bg};
    color: {text_primary};
    border: 1px solid {border_strong};
    padding: 4px 8px;
    font-size: 11px;
    border-radius: 6px;
}}
"""
