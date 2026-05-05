"""Single source of truth for DogeAutoSub theme colors.

Stylesheets for both Light and Dark themes are generated from these tokens.
Editing colors here updates both themes consistently.
"""

TOKENS = {
    "light": {
        "chrome_bg":         "#d4d0c8",
        "interior_bg":       "#ece9d8",
        "card_bg":           "#ffffff",
        "card_border":       "#a0a0a0",
        "title_bar_start":   "#0a246a",
        "title_bar_end":     "#3a6ea5",
        "desktop_bg":        "#2a8e8e",
        "text_primary":      "#202020",
        "text_secondary":    "#505050",
        "text_muted":        "#808080",
        "accent_primary":    "#1854b0",
        "accent_primary_hi": "#4a8eea",
        "accent_success":    "#7ed957",
        "accent_warn":       "#ffd166",
        "accent_error":      "#e63946",
        "bevel_light":       "#ffffff",
        "bevel_dark":        "#707070",
        "input_bg":          "#ffffff",
        "console_bg":        "#0c0c0c",
        "console_text":      "#cccccc",
    },
    "dark": {
        "chrome_bg":         "#3a3a3a",
        "interior_bg":       "#1e1e1e",
        "card_bg":           "#2a2a2a",
        "card_border":       "#505050",
        "title_bar_start":   "#000040",
        "title_bar_end":     "#1a3a6a",
        "desktop_bg":        "#1a4040",
        "text_primary":      "#e0e0e0",
        "text_secondary":    "#a0a0a0",
        "text_muted":        "#707070",
        "accent_primary":    "#4a8eea",
        "accent_primary_hi": "#79c0ff",
        "accent_success":    "#7ed957",
        "accent_warn":       "#ffd166",
        "accent_error":      "#ff6b6b",
        "bevel_light":       "#5a5a5a",
        "bevel_dark":        "#1a1a1a",
        "input_bg":          "#1a1a1a",
        "console_bg":        "#0c0c0c",
        "console_text":      "#cccccc",
    },
}


def build_stylesheet(theme: str) -> str:
    """Build a Qt stylesheet string from the named theme's tokens."""
    if theme not in TOKENS:
        raise KeyError(f"Unknown theme: {theme!r}. Choose from {list(TOKENS)}.")
    t = TOKENS[theme]
    return _TEMPLATE.format(**t)


_TEMPLATE = """
* {{
    font-family: "Pixelated MS Sans Serif", "MS Sans Serif", Tahoma, "Segoe UI", system-ui, sans-serif;
}}

QMainWindow {{
    background-color: {desktop_bg};
    color: {text_primary};
}}

QWidget#centralWidget {{
    background-color: {chrome_bg};
}}

QFrame#fauxTitleBar {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 {title_bar_start}, stop:1 {title_bar_end});
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
    min-height: 24px;
    max-height: 24px;
}}

QLabel#fauxTitleText {{
    color: white;
    font-weight: 700;
    font-size: 12px;
    padding-left: 8px;
}}

QFrame#menuBar {{
    background-color: {chrome_bg};
    border-bottom: 1px solid {bevel_dark};
    min-height: 22px;
    max-height: 22px;
}}

QLabel#menuItem {{
    color: {text_primary};
    font-size: 12px;
    padding: 2px 10px;
}}
QLabel#menuItem:hover {{
    background-color: {accent_primary};
    color: white;
}}

QTabWidget::pane {{
    border: 1px solid {bevel_dark};
    border-top: 1px solid {bevel_dark};
    background-color: {interior_bg};
    top: -1px;
}}

QTabBar::tab {{
    background-color: {chrome_bg};
    color: {text_secondary};
    border: 1px solid {bevel_dark};
    border-top-color: {bevel_light};
    border-left-color: {bevel_light};
    border-bottom: none;
    padding: 6px 18px;
    margin-right: 2px;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
    font-size: 12px;
    font-weight: 600;
}}

QTabBar::tab:selected {{
    background-color: {interior_bg};
    color: {text_primary};
    margin-bottom: -1px;
    padding-bottom: 7px;
}}

QFrame#card {{
    background-color: {card_bg};
    border: 1px solid {card_border};
    border-radius: 4px;
}}

QLabel#sectionTitle {{
    color: {text_secondary};
    font-size: 11px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 1px;
    padding: 0;
}}

QLabel#filePathLabel {{
    color: {accent_primary};
    font-size: 11px;
}}

QLabel#statusLabel {{
    color: {text_primary};
    font-size: 12px;
    font-weight: 500;
}}

QPushButton {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 {bevel_light}, stop:1 {chrome_bg});
    color: {text_primary};
    border: 1px solid {bevel_dark};
    border-top-color: {bevel_light};
    border-left-color: {bevel_light};
    border-radius: 3px;
    padding: 5px 14px;
    font-size: 12px;
    min-height: 22px;
}}
QPushButton:hover {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 {bevel_light}, stop:1 {accent_primary_hi});
    color: white;
}}
QPushButton:pressed {{
    background: {chrome_bg};
    border-top-color: {bevel_dark};
    border-left-color: {bevel_dark};
    border-bottom-color: {bevel_light};
    border-right-color: {bevel_light};
    padding-top: 6px;
    padding-left: 15px;
}}
QPushButton:disabled {{
    color: {text_muted};
    background: {chrome_bg};
}}

QPushButton#startButton, QPushButton#generateNotesBtn, QPushButton#translateFileBtn {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 {accent_primary_hi}, stop:1 {accent_primary});
    color: white;
    font-size: 13px;
    font-weight: 700;
    min-height: 32px;
    padding: 8px 24px;
}}
QPushButton#startButton:hover, QPushButton#generateNotesBtn:hover, QPushButton#translateFileBtn:hover {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 white, stop:1 {accent_primary_hi});
    color: {accent_primary};
}}

QComboBox, QLineEdit {{
    background-color: {input_bg};
    color: {text_primary};
    border: 1px solid {bevel_dark};
    border-top-color: {bevel_dark};
    border-left-color: {bevel_dark};
    border-bottom-color: {bevel_light};
    border-right-color: {bevel_light};
    border-radius: 2px;
    padding: 4px 8px;
    font-size: 12px;
    min-height: 20px;
}}
QComboBox:hover, QLineEdit:focus {{
    border-color: {accent_primary};
}}

QComboBox::drop-down {{
    width: 18px;
    border-left: 1px solid {bevel_dark};
    background-color: {chrome_bg};
}}

QComboBox QAbstractItemView {{
    background-color: {card_bg};
    color: {text_primary};
    border: 1px solid {bevel_dark};
    selection-background-color: {accent_primary};
    selection-color: white;
}}

QLabel {{
    color: {text_primary};
    font-size: 12px;
    background: transparent;
}}

QProgressBar {{
    background-color: {chrome_bg};
    border: 1px solid {bevel_dark};
    border-radius: 6px;
    text-align: center;
    font-size: 10px;
    color: {text_primary};
    min-height: 12px;
    max-height: 12px;
}}

QProgressBar::chunk {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 {accent_primary}, stop:1 {accent_primary_hi});
    border-radius: 6px;
}}

QSlider::groove:horizontal {{
    height: 6px;
    background: {chrome_bg};
    border: 1px solid {bevel_dark};
    border-radius: 3px;
}}
QSlider::handle:horizontal {{
    background: {accent_primary_hi};
    border: 1px solid {accent_primary};
    width: 14px;
    height: 14px;
    margin: -5px 0;
    border-radius: 8px;
}}
QSlider::sub-page:horizontal {{
    background: {accent_primary};
    border-radius: 3px;
}}

QTextEdit {{
    background-color: {card_bg};
    color: {text_primary};
    border: 1px solid {bevel_dark};
    border-top-color: {bevel_dark};
    border-left-color: {bevel_dark};
    border-bottom-color: {bevel_light};
    border-right-color: {bevel_light};
    border-radius: 3px;
    padding: 8px;
    font-size: 12px;
    selection-background-color: {accent_primary};
}}

QToolTip {{
    background-color: #ffffe1;
    color: #000;
    border: 1px solid {bevel_dark};
    padding: 4px 8px;
    font-size: 11px;
}}

QScrollBar:vertical {{
    background: {chrome_bg};
    width: 14px;
}}
QScrollBar::handle:vertical {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 {bevel_light}, stop:1 {chrome_bg});
    border: 1px solid {bevel_dark};
    min-height: 30px;
}}
"""
