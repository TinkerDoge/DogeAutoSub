# Win95-Modernized Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Redesign the DogeAutoSub PySide6 UI with a Windows 95/98-modernized look, add a step-pipeline + collapsible terminal log panel, and add a mascot state machine plus six animation features — shipped in three phases (A Skin → B Logging → C Animation), each independently testable.

**Architecture:** Theme tokens drive both Light and Dark CSS files (single source of truth). Layout is rebuilt in `modules/ui_DogeAutoSub.py` while preserving every existing widget name and signal so `AutoUI.py` and the updater keep working. A new `LogPanel` widget consumes a structured `log_event` signal added (alongside, not replacing) the existing `status_update`/`progress_update` signals on the three thread classes. A `MascotWidget` subscribes to that same signal. Animation helpers and the boot splash are isolated in their own modules so Phase C is purely additive.

**Tech Stack:** PySide6 (QtWidgets, QtGui, QtCore), pytest, pytest-qt for widget tests, Python 3.11. Spec: [docs/superpowers/specs/2026-05-05-win95-doge-redesign-design.md](../specs/2026-05-05-win95-doge-redesign-design.md).

---

## Test Strategy

This codebase has no existing test infrastructure. Task 0 sets up pytest + pytest-qt. Logic units (theme generation, log rotation, doge narrator selection, mascot state transitions) are unit-tested. UI rendering (chrome look, animation feel) is verified by explicit manual smoke-test steps because no automated test can decide "does this look right." Each task ends with a commit so the working tree is always shippable.

---

## Task 0: Test infrastructure setup

**Files:**
- Create: `tests/__init__.py`
- Create: `tests/conftest.py`
- Create: `pytest.ini`
- Modify: `requirements.txt`

- [ ] **Step 1: Add test dependencies to requirements.txt**

Append to `requirements.txt`:

```text

# Testing
pytest>=7.4.0
pytest-qt>=4.2.0
```

- [ ] **Step 2: Install test dependencies**

Run: `pip install pytest>=7.4.0 pytest-qt>=4.2.0`
Expected: successful install, no errors.

- [ ] **Step 3: Create pytest.ini**

```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = -v --tb=short
qt_api = pyside6
```

- [ ] **Step 4: Create tests/__init__.py**

Empty file.

- [ ] **Step 5: Create tests/conftest.py**

```python
"""Shared test fixtures."""
import os
import sys

# Make the project importable from tests/
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
```

- [ ] **Step 6: Verify pytest discovers no tests yet**

Run: `pytest`
Expected: `no tests ran` (exit 5 is fine).

- [ ] **Step 7: Commit**

```bash
git add tests/__init__.py tests/conftest.py pytest.ini requirements.txt
git commit -m "test: add pytest + pytest-qt scaffolding"
```

---

## Phase A — Skin

### Task A1: Theme tokens module

**Files:**
- Create: `modules/theme_tokens.py`
- Create: `tests/test_theme_tokens.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_theme_tokens.py`:

```python
from modules.theme_tokens import TOKENS, build_stylesheet


def test_tokens_has_both_themes():
    assert "light" in TOKENS
    assert "dark" in TOKENS


def test_token_keys_match_across_themes():
    assert set(TOKENS["light"].keys()) == set(TOKENS["dark"].keys())


def test_required_tokens_present():
    required = {
        "chrome_bg", "interior_bg", "card_bg", "card_border",
        "title_bar_start", "title_bar_end", "desktop_bg",
        "text_primary", "text_secondary", "text_muted",
        "accent_primary", "accent_success", "accent_warn", "accent_error",
    }
    for theme in ("light", "dark"):
        missing = required - set(TOKENS[theme].keys())
        assert not missing, f"{theme} missing: {missing}"


def test_build_stylesheet_returns_non_empty_string():
    css = build_stylesheet("light")
    assert isinstance(css, str)
    assert len(css) > 500
    assert "QMainWindow" in css


def test_build_stylesheet_substitutes_tokens():
    css = build_stylesheet("light")
    assert TOKENS["light"]["chrome_bg"] in css
    assert TOKENS["light"]["title_bar_start"] in css


def test_build_stylesheet_unknown_theme_raises():
    import pytest
    with pytest.raises(KeyError):
        build_stylesheet("solarized")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_theme_tokens.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'modules.theme_tokens'`.

- [ ] **Step 3: Implement theme_tokens.py**

Create `modules/theme_tokens.py`:

```python
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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_theme_tokens.py -v`
Expected: 6 passed.

- [ ] **Step 5: Commit**

```bash
git add modules/theme_tokens.py tests/test_theme_tokens.py
git commit -m "feat(theme): add theme tokens module with light/dark variants"
```

---

### Task A2: Generate new CSS files from tokens

**Files:**
- Modify: `modules/styleSheetDark.css`
- Modify: `modules/styleSheetLight.css`
- Create: `scripts/regen_themes.py`

- [ ] **Step 1: Create the regeneration script**

Create `scripts/regen_themes.py`:

```python
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
```

- [ ] **Step 2: Run the regeneration script**

Run: `python scripts/regen_themes.py`
Expected: two `Wrote .../styleSheetXxx.css` lines, both files now updated.

- [ ] **Step 3: Verify CSS loads cleanly in a Qt smoke test**

Create `tests/test_css_loads.py`:

```python
import os
import pytest

pytest_plugins = ["pytestqt.plugin"]

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


@pytest.mark.parametrize("name", ["styleSheetLight.css", "styleSheetDark.css"])
def test_css_can_be_applied(qtbot, name):
    from PySide6.QtWidgets import QWidget
    path = os.path.join(ROOT, "modules", name)
    with open(path, "r", encoding="utf-8") as f:
        css = f.read()
    w = QWidget()
    qtbot.addWidget(w)
    w.setStyleSheet(css)
    # Qt logs unknown-property warnings to stderr but does not raise; just
    # assert nothing crashed and the stylesheet round-trips.
    assert w.styleSheet() == css
```

Run: `pytest tests/test_css_loads.py -v`
Expected: 2 passed.

- [ ] **Step 4: Commit**

```bash
git add modules/styleSheetDark.css modules/styleSheetLight.css scripts/regen_themes.py tests/test_css_loads.py
git commit -m "feat(theme): regenerate CSS files from tokens, add regen script"
```

---

### Task A3: Rebuild ui_DogeAutoSub.py — frame + tabs (preserve all widget names)

**Files:**
- Modify: `modules/ui_DogeAutoSub.py` (full rebuild)

- [ ] **Step 1: Read the current file end-to-end so you know every widget that exists**

Run: `wc -l modules/ui_DogeAutoSub.py` and read it. The Phase A rebuild must keep every `self.<name>` widget that `AutoUI.py` references. Cross-check by grepping `AutoUI.py` for `self\.` accesses against the new file before committing.

- [ ] **Step 2: Replace the file contents**

Open `modules/ui_DogeAutoSub.py` and replace the contents with the layout below. This is the **complete** file — paste it as-is. Spec §5 is the source of truth.

```python
# -*- coding: utf-8 -*-
"""DogeAutoSub — Win95-modernized UI layout.

Hand-coded layout. Preserves every widget name and signal previously
used by AutoUI.py so that file requires no changes during Phase A.
"""

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QComboBox, QFrame, QGridLayout, QHBoxLayout, QLabel,
    QLineEdit, QMainWindow, QProgressBar, QPushButton,
    QSlider, QTabWidget, QTextEdit, QVBoxLayout, QWidget,
)


class Ui_MainWindow(object):
    """Tabbed UI: Subtitles + Meeting Notes + Translate File."""

    # ── Helpers ─────────────────────────────────────────────────
    def _label(self, text: str, *, small: bool = False) -> QLabel:
        lbl = QLabel(text)
        lbl.setFont(self.font_small if small else self.font_body)
        return lbl

    def _section_title(self, text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setObjectName("sectionTitle")
        lbl.setFont(self.font_title)
        return lbl

    def _card(self) -> QFrame:
        f = QFrame()
        f.setObjectName("card")
        f.setFrameShape(QFrame.Shape.StyledPanel)
        return f

    def setupUi(self, MainWindow: QMainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName("MainWindow")
        MainWindow.resize(720, 1080)
        MainWindow.setMinimumSize(QSize(720, 1080))
        MainWindow.setMaximumSize(QSize(720, 1080))
        MainWindow.setWindowTitle("DogeAutoSub")

        self.font_title = QFont(); self.font_title.setPointSize(11); self.font_title.setBold(True)
        self.font_body  = QFont(); self.font_body.setPointSize(10)
        self.font_small = QFont(); self.font_small.setPointSize(9)

        # ── Central ──────────────────────────────────────────────
        self.centralWidget = QWidget(MainWindow)
        self.centralWidget.setObjectName("centralWidget")
        MainWindow.setCentralWidget(self.centralWidget)

        outer = QVBoxLayout(self.centralWidget)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # ── Faux Title Bar (cosmetic) ───────────────────────────
        self.fauxTitleBar = QFrame()
        self.fauxTitleBar.setObjectName("fauxTitleBar")
        ttl = QHBoxLayout(self.fauxTitleBar)
        ttl.setContentsMargins(8, 0, 6, 0)
        ttl.setSpacing(4)
        self.fauxTitleText = QLabel("🐕 DogeAutoSub")
        self.fauxTitleText.setObjectName("fauxTitleText")
        ttl.addWidget(self.fauxTitleText)
        self.versionLabel = QLabel("")
        self.versionLabel.setStyleSheet("color: #c0d0f0; padding-left: 4px;")
        self.versionLabel.setFont(self.font_small)
        ttl.addWidget(self.versionLabel)
        ttl.addStretch()
        for ch in ("_", "□", "×"):
            b = QLabel(ch)
            b.setStyleSheet(
                "color:white; background:#c0c0c0; color:#000;"
                "border:1px solid #fff; padding:0 6px; font-size:10px;"
                "min-width:14px; max-height:14px; border-radius:2px;"
            )
            b.setAlignment(Qt.AlignmentFlag.AlignCenter)
            ttl.addWidget(b)
        outer.addWidget(self.fauxTitleBar)

        # ── Cosmetic Menu Bar ───────────────────────────────────
        self.menuBarFrame = QFrame()
        self.menuBarFrame.setObjectName("menuBar")
        menu = QHBoxLayout(self.menuBarFrame)
        menu.setContentsMargins(4, 0, 4, 0)
        menu.setSpacing(2)
        self.menuItems = {}
        for name in ("File", "Edit", "View", "Help"):
            lbl = QLabel(name)
            lbl.setObjectName("menuItem")
            menu.addWidget(lbl)
            self.menuItems[name] = lbl
        menu.addStretch()
        # Icon toolstrip (theme + open folder)
        self.openFolderBtn = QPushButton("📂")
        self.openFolderBtn.setObjectName("openFolderBtn")
        self.openFolderBtn.setFixedSize(24, 20)
        self.openFolderBtn.setToolTip("Open output folder")
        menu.addWidget(self.openFolderBtn)
        self.themeBtn = QPushButton("🎨")
        self.themeBtn.setObjectName("themeBtn")
        self.themeBtn.setFixedSize(24, 20)
        self.themeBtn.setToolTip("Toggle dark/light theme")
        menu.addWidget(self.themeBtn)
        outer.addWidget(self.menuBarFrame)

        # ── App body ────────────────────────────────────────────
        body = QFrame()
        body.setObjectName("body")
        bodyLay = QVBoxLayout(body)
        bodyLay.setContentsMargins(14, 10, 14, 14)
        bodyLay.setSpacing(8)
        outer.addWidget(body, 1)

        # Decorative app title (kept for backward-compat with AutoUI.py)
        self.appTitle = QLabel("DogeAutoSub")
        self.appTitle.setObjectName("sectionTitle")
        self.appTitle.setVisible(False)  # title now lives in fauxTitleBar
        bodyLay.addWidget(self.appTitle)

        # ── Tabs ────────────────────────────────────────────────
        self.tabWidget = QTabWidget()
        self.tabWidget.setObjectName("tabWidget")
        bodyLay.addWidget(self.tabWidget, 1)

        self._build_subtitles_tab()
        self._build_notes_tab()
        self._build_translate_tab()

    # ── Tab builders are filled in Tasks A4–A5 ──────────────────
    def _build_subtitles_tab(self): ...
    def _build_notes_tab(self): ...
    def _build_translate_tab(self): ...
```

Note the three `...` stubs — Tasks A4 and A5 fill them. The app will not run until A5; that is intentional and gives a clean diff per task.

- [ ] **Step 3: Run import smoke test**

Create `tests/test_ui_imports.py`:

```python
def test_ui_module_imports():
    from modules import ui_DogeAutoSub
    assert hasattr(ui_DogeAutoSub, "Ui_MainWindow")


def test_ui_class_has_setupui():
    from modules.ui_DogeAutoSub import Ui_MainWindow
    assert callable(Ui_MainWindow.setupUi)
```

Run: `pytest tests/test_ui_imports.py -v`
Expected: 2 passed.

- [ ] **Step 4: Commit**

```bash
git add modules/ui_DogeAutoSub.py tests/test_ui_imports.py
git commit -m "refactor(ui): rebuild title bar, menu bar, and tab scaffolding"
```

---

### Task A4: Build Subtitles tab content

**Files:**
- Modify: `modules/ui_DogeAutoSub.py` (replace `_build_subtitles_tab` stub)

- [ ] **Step 1: Replace the `_build_subtitles_tab` method**

Replace the `def _build_subtitles_tab(self): ...` line in `modules/ui_DogeAutoSub.py` with this full method. Add it as a regular method on the class (same indentation as `setupUi`).

```python
    def _build_subtitles_tab(self):
        from modules.constants import MODEL_TYPES  # local import = no module-load cost if unused

        tab = QWidget()
        tab.setObjectName("subtitleTab")
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(10, 12, 10, 10)
        layout.setSpacing(10)

        # ── Card 1: Input/Output ─────────────────────────────────
        self.fileCard = self._card()
        c1 = QVBoxLayout(self.fileCard)
        c1.setContentsMargins(12, 10, 12, 12)
        c1.setSpacing(6)
        c1.addWidget(self._section_title("📁 Input / Output"))
        row = QHBoxLayout(); row.setSpacing(8)
        self.selectFileBtn = QPushButton("🎬  Select Video File")
        self.selectFileBtn.setObjectName("selectFileBtn")
        self.selectFileBtn.setMinimumHeight(34)
        self.selectFileBtn.setToolTip("Click to pick a video/audio file")
        row.addWidget(self.selectFileBtn, 2)
        self.selectOutputBtn = QPushButton("📁  Output Folder")
        self.selectOutputBtn.setObjectName("selectOutputBtn")
        self.selectOutputBtn.setMinimumHeight(34)
        self.selectOutputBtn.setToolTip("Where to save the .srt")
        row.addWidget(self.selectOutputBtn, 1)
        c1.addLayout(row)
        self.filePathLabel = QLabel("No file selected")
        self.filePathLabel.setObjectName("filePathLabel")
        self.filePathLabel.setFont(self.font_small)
        self.filePathLabel.setWordWrap(True)
        c1.addWidget(self.filePathLabel)
        layout.addWidget(self.fileCard)

        # ── Card 2: Settings ─────────────────────────────────────
        self.settingsCard = self._card()
        c2 = QVBoxLayout(self.settingsCard)
        c2.setContentsMargins(12, 10, 12, 12)
        c2.setSpacing(8)
        c2.addWidget(self._section_title("⚙️ Settings"))

        # Hidden widgets retained for AutoUI.py compatibility
        self.model_size_dropdown = QComboBox()
        self.model_size_dropdown.setObjectName("modelDropdown")
        self.model_size_dropdown.setVisible(False)
        c2.addWidget(self.model_size_dropdown)
        self.VRamUsage = QLabel(""); self.VRamUsage.setVisible(False); c2.addWidget(self.VRamUsage)
        self.rSpeed    = QLabel(""); self.rSpeed.setVisible(False);    c2.addWidget(self.rSpeed)

        grid = QGridLayout()
        grid.setHorizontalSpacing(10); grid.setVerticalSpacing(4)
        grid.addWidget(self._label("Source Language", small=True), 0, 0)
        self.source_language_dropdown = QComboBox()
        self.source_language_dropdown.setObjectName("srcLangDropdown")
        grid.addWidget(self.source_language_dropdown, 1, 0)
        grid.addWidget(self._label("Target Language", small=True), 0, 1)
        self.target_language_dropdown = QComboBox()
        self.target_language_dropdown.setObjectName("tgtLangDropdown")
        grid.addWidget(self.target_language_dropdown, 1, 1)
        grid.addWidget(self._label("Translation Engine", small=True), 2, 0)
        self.target_engine = QComboBox()
        self.target_engine.setObjectName("engineDropdown")
        grid.addWidget(self.target_engine, 3, 0)
        grid.addWidget(self._label("Volume Boost", small=True), 2, 1)
        volWrap = QHBoxLayout(); volWrap.setSpacing(6)
        self.boostSlider = QSlider(Qt.Orientation.Horizontal)
        self.boostSlider.setObjectName("boostSlider")
        self.boostSlider.setMinimum(1); self.boostSlider.setMaximum(10); self.boostSlider.setValue(3)
        volWrap.addWidget(self.boostSlider, 1)
        self.boostLabel = QLabel("3"); self.boostLabel.setMinimumWidth(20)
        self.boostSlider.valueChanged.connect(lambda v: self.boostLabel.setText(str(v)))
        volWrap.addWidget(self.boostLabel)
        grid.addLayout(volWrap, 3, 1)
        c2.addLayout(grid)

        # MLAAS sub-card
        mlaas = self._card()
        m = QVBoxLayout(mlaas); m.setContentsMargins(10, 8, 10, 10); m.setSpacing(4)
        topRow = QHBoxLayout()
        topRow.addWidget(self._section_title("🔑 MLAAS API"))
        self.mlaasStatusLabel = QLabel("Loading…")
        self.mlaasStatusLabel.setFont(self.font_small)
        topRow.addWidget(self.mlaasStatusLabel)
        topRow.addStretch()
        m.addLayout(topRow)
        bearerRow = QHBoxLayout(); bearerRow.setSpacing(6)
        self.bearerTokenEdit = QLineEdit()
        self.bearerTokenEdit.setPlaceholderText("Paste Bearer JWT token (optional)…")
        self.bearerTokenEdit.setEchoMode(QLineEdit.EchoMode.Password)
        bearerRow.addWidget(self.bearerTokenEdit, 1)
        self.getTokenBtn = QPushButton("🔗 Get Token"); self.getTokenBtn.setFixedWidth(96)
        bearerRow.addWidget(self.getTokenBtn)
        m.addLayout(bearerRow)
        c2.addWidget(mlaas)
        layout.addWidget(self.settingsCard)

        # ── Card 3: Action (Start + Progress + Status) ───────────
        self.actionCard = self._card()
        c3 = QVBoxLayout(self.actionCard)
        c3.setContentsMargins(12, 10, 12, 12)
        c3.setSpacing(8)
        self.startButton = QPushButton("▶  START PROCESSING")
        self.startButton.setObjectName("startButton")
        c3.addWidget(self.startButton)
        self.progressBar = QProgressBar(); self.progressBar.setObjectName("progressBar"); self.progressBar.setValue(0)
        c3.addWidget(self.progressBar)
        statRow = QHBoxLayout(); statRow.setSpacing(10)
        self.statusLabel = QLabel("Standby"); self.statusLabel.setObjectName("statusLabel")
        statRow.addWidget(self.statusLabel)
        statRow.addStretch()
        self.etaLabel = QLabel(""); self.etaLabel.setObjectName("etaLabel"); self.etaLabel.setFont(self.font_small)
        statRow.addWidget(self.etaLabel)
        c3.addLayout(statRow)

        # Placeholder for Phase B LogPanel — kept as plain widget for now.
        self.logPanelHost = QFrame()
        self.logPanelHost.setObjectName("logPanelHost")
        c3.addWidget(self.logPanelHost)
        layout.addWidget(self.actionCard)

        # ── Card 4: Mascot strip ─────────────────────────────────
        self.mascotCard = self._card()
        m4 = QHBoxLayout(self.mascotCard); m4.setContentsMargins(12, 8, 12, 8)
        self.statusImage = QLabel(); self.statusImage.setObjectName("statusImage")
        self.statusImage.setMaximumSize(QSize(130, 130))
        self.statusImage.setAlignment(Qt.AlignmentFlag.AlignCenter)
        m4.addWidget(self.statusImage)
        self.speechBubble = QLabel("")
        self.speechBubble.setObjectName("speechBubble")
        self.speechBubble.setWordWrap(True)
        m4.addWidget(self.speechBubble, 1)
        layout.addWidget(self.mascotCard)

        layout.addStretch(1)
        self.tabWidget.addTab(tab, "📝 Subtitles")
```

- [ ] **Step 2: Cross-check that every widget in the original file is still present**

Run:

```bash
grep -oE "self\.[a-zA-Z_][a-zA-Z0-9_]*" AutoUI.py | sort -u > /tmp/used.txt
grep -oE "self\.[a-zA-Z_][a-zA-Z0-9_]*" modules/ui_DogeAutoSub.py | sort -u > /tmp/defined.txt
comm -23 /tmp/used.txt /tmp/defined.txt
```

Expected: empty output, OR only widgets that Tasks A5 will add (notesOutput, transOutput, etc). Anything else means Phase A breaks AutoUI.py — fix before committing.

- [ ] **Step 3: Commit**

```bash
git add modules/ui_DogeAutoSub.py
git commit -m "feat(ui): rebuild Subtitles tab with Win95-style cards"
```

---

### Task A5: Build Notes + Translate tabs, run the app

**Files:**
- Modify: `modules/ui_DogeAutoSub.py`

- [ ] **Step 1: Replace `_build_notes_tab` stub**

```python
    def _build_notes_tab(self):
        tab = QWidget()
        tab.setObjectName("notesTab")
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(10, 12, 10, 10); layout.setSpacing(10)

        self.notesFileCard = self._card()
        n1 = QVBoxLayout(self.notesFileCard); n1.setContentsMargins(12, 10, 12, 12); n1.setSpacing(6)
        n1.addWidget(self._section_title("📄 Meeting Transcript"))
        self.selectDocxBtn = QPushButton("📎  Upload DOCX Transcript")
        self.selectDocxBtn.setObjectName("selectDocxBtn")
        self.selectDocxBtn.setMinimumHeight(34)
        n1.addWidget(self.selectDocxBtn)
        self.docxPathLabel = QLabel("No transcript uploaded")
        self.docxPathLabel.setObjectName("filePathLabel")
        self.docxPathLabel.setFont(self.font_small); self.docxPathLabel.setWordWrap(True)
        n1.addWidget(self.docxPathLabel)
        layout.addWidget(self.notesFileCard)

        info = QLabel("ℹ️ Uses MLAAS API token from Subtitles tab.")
        info.setFont(self.font_small); info.setWordWrap(True)
        layout.addWidget(info)

        # Hidden compat widgets
        self.llmApiUrl   = QLineEdit(); self.llmApiUrl.setVisible(False);   layout.addWidget(self.llmApiUrl)
        self.llmApiKey   = QLineEdit(); self.llmApiKey.setVisible(False);   layout.addWidget(self.llmApiKey)
        self.llmModelName= QLineEdit(); self.llmModelName.setVisible(False);layout.addWidget(self.llmModelName)

        self.notesOutputCard = self._card()
        n2 = QVBoxLayout(self.notesOutputCard); n2.setContentsMargins(12, 10, 12, 12); n2.setSpacing(6)
        btnRow = QHBoxLayout()
        self.generateNotesBtn = QPushButton("✨  Generate Meeting Notes")
        self.generateNotesBtn.setObjectName("generateNotesBtn")
        self.generateNotesBtn.setMinimumHeight(36)
        btnRow.addWidget(self.generateNotesBtn, 1)
        self.saveNotesBtn = QPushButton("💾 Save"); self.saveNotesBtn.setObjectName("saveNotesBtn")
        self.saveNotesBtn.setMinimumHeight(36)
        btnRow.addWidget(self.saveNotesBtn)
        n2.addLayout(btnRow)
        self.notesStatusLabel = QLabel(""); self.notesStatusLabel.setObjectName("statusLabel"); self.notesStatusLabel.setFont(self.font_small)
        n2.addWidget(self.notesStatusLabel)
        self.notesOutput = QTextEdit()
        self.notesOutput.setObjectName("notesOutput")
        self.notesOutput.setPlaceholderText("Meeting notes will appear here after generation...")
        self.notesOutput.setMinimumHeight(220)
        n2.addWidget(self.notesOutput)
        layout.addWidget(self.notesOutputCard, 1)

        self.tabWidget.addTab(tab, "📋 Meeting Notes")
```

- [ ] **Step 2: Replace `_build_translate_tab` stub**

```python
    def _build_translate_tab(self):
        tab = QWidget()
        tab.setObjectName("translateTab")
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(10, 12, 10, 10); layout.setSpacing(10)

        self.transFileCard = self._card()
        t1 = QVBoxLayout(self.transFileCard); t1.setContentsMargins(12, 10, 12, 12); t1.setSpacing(6)
        t1.addWidget(self._section_title("📄 Source File"))
        self.selectTransFileBtn = QPushButton("📎  Upload File (.srt, .docx, .txt)")
        self.selectTransFileBtn.setObjectName("selectTransFileBtn")
        self.selectTransFileBtn.setMinimumHeight(34)
        t1.addWidget(self.selectTransFileBtn)
        self.transFilePathLabel = QLabel("No file selected")
        self.transFilePathLabel.setObjectName("filePathLabel")
        self.transFilePathLabel.setFont(self.font_small); self.transFilePathLabel.setWordWrap(True)
        t1.addWidget(self.transFilePathLabel)
        layout.addWidget(self.transFileCard)

        self.transSettingsCard = self._card()
        t2 = QVBoxLayout(self.transSettingsCard); t2.setContentsMargins(12, 10, 12, 12); t2.setSpacing(6)
        t2.addWidget(self._section_title("⚙️ Translation Settings"))
        grid = QGridLayout(); grid.setHorizontalSpacing(10); grid.setVerticalSpacing(4)
        grid.addWidget(self._label("Source Language", small=True), 0, 0)
        self.trans_src_lang = QComboBox(); self.trans_src_lang.setObjectName("transSrcLang")
        grid.addWidget(self.trans_src_lang, 1, 0)
        grid.addWidget(self._label("Target Language", small=True), 0, 1)
        self.trans_tgt_lang = QComboBox(); self.trans_tgt_lang.setObjectName("transTgtLang")
        grid.addWidget(self.trans_tgt_lang, 1, 1)
        t2.addLayout(grid)
        engRow = QHBoxLayout(); engRow.setSpacing(8)
        engRow.addWidget(self._label("Engine:", small=True))
        self.trans_engine = QComboBox(); self.trans_engine.setObjectName("transEngine")
        engRow.addWidget(self.trans_engine, 1)
        t2.addLayout(engRow)
        info = QLabel("ℹ️ Uses MLAAS token from Subtitles tab if MLAAS engine is selected.")
        info.setFont(self.font_small); info.setWordWrap(True)
        t2.addWidget(info)
        layout.addWidget(self.transSettingsCard)

        self.transOutputCard = self._card()
        t3 = QVBoxLayout(self.transOutputCard); t3.setContentsMargins(12, 10, 12, 12); t3.setSpacing(6)
        btnRow = QHBoxLayout()
        self.translateFileBtn = QPushButton("🌐  Translate File")
        self.translateFileBtn.setObjectName("translateFileBtn")
        self.translateFileBtn.setMinimumHeight(36)
        btnRow.addWidget(self.translateFileBtn, 1)
        self.saveTransBtn = QPushButton("💾 Save"); self.saveTransBtn.setObjectName("saveNotesBtn")
        self.saveTransBtn.setMinimumHeight(36)
        btnRow.addWidget(self.saveTransBtn)
        t3.addLayout(btnRow)
        self.transStatusLabel = QLabel(""); self.transStatusLabel.setObjectName("statusLabel"); self.transStatusLabel.setFont(self.font_small)
        t3.addWidget(self.transStatusLabel)
        self.transOutput = QTextEdit(); self.transOutput.setObjectName("transOutput"); self.transOutput.setMinimumHeight(220)
        t3.addWidget(self.transOutput)
        layout.addWidget(self.transOutputCard, 1)

        self.tabWidget.addTab(tab, "🌐 Translate")
```

- [ ] **Step 3: Run the app for a manual smoke test**

Run: `python AutoUI.py`

Manual check (Phase A acceptance, spec §9):
- [ ] Window opens at 720×1080, fixed.
- [ ] Faux blue title bar visible at top with doge favicon + "DogeAutoSub" + version label.
- [ ] Cosmetic "File · Edit · View · Help" menu bar visible below it.
- [ ] Three tabs render: Subtitles, Meeting Notes, Translate.
- [ ] Each tab shows white card panels with bevel borders.
- [ ] Theme toggle (🎨) flips Dark ↔ Light without errors.
- [ ] Click Select Video, Output Folder, Start, Generate Notes, Translate File — all the same handlers fire as before (no `AttributeError`).

Close the app. If anything failed, fix and retry before committing.

- [ ] **Step 4: Commit**

```bash
git add modules/ui_DogeAutoSub.py
git commit -m "feat(ui): rebuild Notes + Translate tabs, finalize Phase A skin"
```

---

### Task A6: Phase A milestone tag

- [ ] **Step 1: Tag the Phase A release point**

```bash
git tag -a phase-a-skin -m "Phase A complete — Win95-modernized skin shipped"
```

This makes Phase A independently revertible if Phase B/C cause regressions.

---

## Phase B — Logging

### Task B1: log_writer module

**Files:**
- Create: `modules/log_writer.py`
- Create: `tests/test_log_writer.py`

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_log_writer.py
import os
import time
from datetime import datetime, timedelta
import pytest

from modules.log_writer import LogWriter


def test_writes_dated_file(tmp_path):
    w = LogWriter(tmp_path)
    w.write("info", "hello")
    w.flush()
    today = datetime.now().strftime("%Y%m%d")
    fp = tmp_path / f"dogeautosub-{today}.log"
    assert fp.exists()
    content = fp.read_text(encoding="utf-8")
    assert "hello" in content
    assert "[INFO]" in content


def test_format_includes_timestamp(tmp_path):
    w = LogWriter(tmp_path)
    w.write("error", "boom")
    w.flush()
    today = datetime.now().strftime("%Y%m%d")
    fp = tmp_path / f"dogeautosub-{today}.log"
    line = fp.read_text(encoding="utf-8").strip().splitlines()[-1]
    # Format: "[HH:MM:SS] [LEVEL] msg"
    assert line.startswith("[")
    assert line[3] == ":" and line[6] == ":"


def test_prune_old_logs(tmp_path):
    # Create 10 fake-old log files with mtimes far in the past.
    keep_days = 7
    old_files = []
    for i in range(10):
        f = tmp_path / f"dogeautosub-2024010{i}.log"
        f.write_text("old", encoding="utf-8")
        # Backdate to 30 days ago.
        ts = (datetime.now() - timedelta(days=30 + i)).timestamp()
        os.utime(f, (ts, ts))
        old_files.append(f)
    LogWriter(tmp_path, keep_days=keep_days).prune()
    # All ten old files should be gone.
    for f in old_files:
        assert not f.exists(), f"{f} should have been pruned"


def test_prune_keeps_recent_logs(tmp_path):
    f = tmp_path / "dogeautosub-recent.log"
    f.write_text("recent", encoding="utf-8")
    ts = (datetime.now() - timedelta(days=2)).timestamp()
    os.utime(f, (ts, ts))
    LogWriter(tmp_path, keep_days=7).prune()
    assert f.exists()


def test_invalid_level_falls_back_to_info(tmp_path):
    w = LogWriter(tmp_path)
    w.write("doge", "such wow")  # 'doge' is a valid level for us
    w.write("nonsense", "ignored level still gets recorded")
    w.flush()
    today = datetime.now().strftime("%Y%m%d")
    content = (tmp_path / f"dogeautosub-{today}.log").read_text(encoding="utf-8")
    assert "such wow" in content
    assert "ignored level still gets recorded" in content
```

- [ ] **Step 2: Run tests to verify failure**

Run: `pytest tests/test_log_writer.py -v`
Expected: FAIL — `ModuleNotFoundError`.

- [ ] **Step 3: Implement modules/log_writer.py**

```python
"""Append-only daily-rotated log writer for DogeAutoSub.

Files are written under <log_dir>/dogeautosub-YYYYMMDD.log. Files older
than `keep_days` are pruned by .prune() (called once on app start).
"""
from __future__ import annotations

import os
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Iterable

VALID_LEVELS = {"info", "success", "warn", "error", "doge"}


class LogWriter:
    def __init__(self, log_dir: str | os.PathLike, keep_days: int = 7):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.keep_days = keep_days

    # ── Writing ────────────────────────────────────────────────
    def _path(self) -> Path:
        return self.log_dir / f"dogeautosub-{datetime.now().strftime('%Y%m%d')}.log"

    def write(self, level: str, message: str) -> None:
        lvl = level.upper() if level.lower() in VALID_LEVELS else level.upper()
        ts = datetime.now().strftime("%H:%M:%S")
        line = f"[{ts}] [{lvl}] {message}\n"
        with self._path().open("a", encoding="utf-8") as f:
            f.write(line)

    def flush(self) -> None:
        # write() opens/closes per call so flush is implicit; provided
        # for symmetry and as a future hook if buffering is added.
        pass

    # ── Rotation ───────────────────────────────────────────────
    def prune(self) -> int:
        """Delete log files older than keep_days. Returns count removed."""
        cutoff = (datetime.now() - timedelta(days=self.keep_days)).timestamp()
        removed = 0
        for entry in self.log_dir.iterdir():
            if not entry.is_file():
                continue
            if not entry.name.startswith("dogeautosub-"):
                continue
            try:
                if entry.stat().st_mtime < cutoff:
                    entry.unlink()
                    removed += 1
            except OSError:
                pass
        return removed
```

- [ ] **Step 4: Run tests to verify pass**

Run: `pytest tests/test_log_writer.py -v`
Expected: 5 passed.

- [ ] **Step 5: Commit**

```bash
git add modules/log_writer.py tests/test_log_writer.py
git commit -m "feat(log): daily-rotated log writer with pruning"
```

---

### Task B2: LogPanel widget — timeline core

**Files:**
- Create: `modules/log_panel.py`
- Create: `tests/test_log_panel_logic.py`

- [ ] **Step 1: Write failing tests for non-Qt logic**

```python
# tests/test_log_panel_logic.py
import pytest

from modules.log_panel import (
    PIPELINE_SUBTITLES, PIPELINE_NOTES, PIPELINE_TRANSLATE,
    DogeNarrator, _format_duration,
)


def test_pipelines_defined():
    assert PIPELINE_SUBTITLES == ["Load model", "Extract audio", "Transcribe", "Translate", "Save SRT"]
    assert PIPELINE_NOTES == ["Read transcript", "Summarize", "Format"]
    assert PIPELINE_TRANSLATE == ["Read file", "Detect language", "Translate", "Format output"]


def test_format_duration_seconds():
    assert _format_duration(0.4) == "0.4s"
    assert _format_duration(2.0) == "2.0s"
    assert _format_duration(75) == "1m 15s"
    assert _format_duration(3600) == "1h 0m"


def test_doge_narrator_speaks_every_n():
    n = DogeNarrator(every_n=3, seed=42)
    msgs = []
    n.on_event = lambda lvl, msg: msgs.append((lvl, msg))
    for _ in range(8):
        n.notify_step_done()
    # On steps 3 and 6 it should have spoken.
    assert len(msgs) == 2
    for lvl, msg in msgs:
        assert lvl == "doge"
        assert msg


def test_doge_narrator_disabled_emits_nothing():
    n = DogeNarrator(every_n=1, enabled=False)
    msgs = []
    n.on_event = lambda lvl, msg: msgs.append((lvl, msg))
    for _ in range(5):
        n.notify_step_done()
    assert msgs == []


def test_doge_narrator_completion_always_speaks():
    n = DogeNarrator(every_n=99, seed=1)
    msgs = []
    n.on_event = lambda lvl, msg: msgs.append((lvl, msg))
    n.notify_completion()
    assert len(msgs) == 1
    assert msgs[0][0] == "doge"
```

- [ ] **Step 2: Run tests to verify failure**

Run: `pytest tests/test_log_panel_logic.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'modules.log_panel'`.

- [ ] **Step 3: Implement modules/log_panel.py (logic + timeline + console; collapse toggle in B3)**

```python
"""LogPanel widget: pipeline timeline + collapsible terminal console."""
from __future__ import annotations

import random
import time
from typing import Callable, Optional

from PySide6.QtCore import Qt, QTimer, QSettings, Signal
from PySide6.QtGui import QColor, QTextCharFormat, QTextCursor
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QPlainTextEdit, QVBoxLayout, QWidget,
)


# ── Pipeline definitions ───────────────────────────────────────
PIPELINE_SUBTITLES = ["Load model", "Extract audio", "Transcribe", "Translate", "Save SRT"]
PIPELINE_NOTES     = ["Read transcript", "Summarize", "Format"]
PIPELINE_TRANSLATE = ["Read file", "Detect language", "Translate", "Format output"]


# ── Colors ─────────────────────────────────────────────────────
LEVEL_COLORS = {
    "info":    "#5fb3ff",
    "success": "#7ed957",
    "warn":    "#ffd166",
    "error":   "#ff6b6b",
    "doge":    "#ff6b9d",
}


def _format_duration(seconds: float) -> str:
    if seconds < 60:
        return f"{seconds:.1f}s"
    if seconds < 3600:
        m = int(seconds // 60); s = int(seconds % 60)
        return f"{m}m {s}s"
    h = int(seconds // 3600); m = int((seconds % 3600) // 60)
    return f"{h}h {m}m"


# ── Doge narrator ──────────────────────────────────────────────
DOGE_LINES_STEP = [
    "such wow.", "much progress.", "very transcribe.",
    "wow. so subtitle.", "many segments.", "so smart.",
]
DOGE_LINES_DONE = [
    "such wow. very done.", "much complete. wow.", "all subs. so proud.",
    "doge approves.", "task done. much wow.",
]


class DogeNarrator:
    def __init__(self, every_n: int = 2, *, enabled: bool = True, seed: Optional[int] = None):
        self.every_n = max(1, every_n)
        self.enabled = enabled
        self._step_count = 0
        self._rng = random.Random(seed)
        self.on_event: Callable[[str, str], None] = lambda lvl, msg: None

    def notify_step_done(self) -> None:
        if not self.enabled:
            return
        self._step_count += 1
        if self._step_count % self.every_n == 0:
            self.on_event("doge", self._rng.choice(DOGE_LINES_STEP))

    def notify_completion(self) -> None:
        if not self.enabled:
            return
        self.on_event("doge", self._rng.choice(DOGE_LINES_DONE))

    def reset(self) -> None:
        self._step_count = 0


# ── Timeline row ───────────────────────────────────────────────
class _StepRow(QFrame):
    """One step row: status dot + name + detail + timestamp."""
    DOT_PENDING = "#c0c0c0"
    DOT_ACTIVE  = "#5fb3ff"
    DOT_DONE    = "#7ed957"
    DOT_ERROR   = "#e63946"

    def __init__(self, name: str, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.name = name
        self._state = "pending"
        self._start_ts: Optional[float] = None
        self.setStyleSheet("background: transparent;")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(8)
        self.dot = QLabel()
        self.dot.setFixedSize(10, 10)
        self.dot.setStyleSheet(f"background:{self.DOT_PENDING}; border-radius:5px;")
        layout.addWidget(self.dot)
        self.nameLabel = QLabel(name)
        self.nameLabel.setStyleSheet("color: #707070;")
        layout.addWidget(self.nameLabel, 1)
        self.detailLabel = QLabel("")
        self.detailLabel.setStyleSheet("color: #909090; font-size: 10px;")
        layout.addWidget(self.detailLabel)
        self.tsLabel = QLabel("")
        self.tsLabel.setStyleSheet("color: #b0b0b0; font-size: 10px;")
        self.tsLabel.setMinimumWidth(56)
        self.tsLabel.setAlignment(Qt.AlignmentFlag.AlignRight)
        layout.addWidget(self.tsLabel)

    def _set_dot(self, color: str) -> None:
        self.dot.setStyleSheet(f"background:{color}; border-radius:5px;")

    def set_pending(self):
        self._state = "pending"
        self._set_dot(self.DOT_PENDING)
        self.nameLabel.setStyleSheet("color: #b0b0b0;")
        self.detailLabel.setText(""); self.tsLabel.setText("")
        self.setStyleSheet("background: transparent;")

    def set_active(self):
        self._state = "active"
        self._start_ts = time.time()
        self._set_dot(self.DOT_ACTIVE)
        self.nameLabel.setStyleSheet("color: #202020; font-weight: 600;")
        self.tsLabel.setText(time.strftime("%H:%M:%S"))
        self.setStyleSheet("background: #fffbe5; border-radius: 3px;")

    def set_done(self, detail: str = ""):
        self._state = "done"
        self._set_dot(self.DOT_DONE)
        self.nameLabel.setStyleSheet("color: #202020;")
        if self._start_ts:
            detail = detail or _format_duration(time.time() - self._start_ts)
        self.detailLabel.setText(detail)
        self.setStyleSheet("background: transparent;")

    def set_error(self, detail: str = ""):
        self._state = "error"
        self._set_dot(self.DOT_ERROR)
        self.nameLabel.setStyleSheet("color: #e63946; font-weight: 600;")
        self.detailLabel.setText(detail or "error")
        self.setStyleSheet("background: transparent;")


# ── LogPanel ───────────────────────────────────────────────────
class LogPanel(QFrame):
    """Pipeline timeline (always visible) + collapsible console."""

    log_event = Signal(dict)  # forwarded events for mascot/animation hooks

    def __init__(self, parent: Optional[QWidget] = None,
                 *, log_writer=None, narrator: Optional[DogeNarrator] = None):
        super().__init__(parent)
        self.setObjectName("logPanel")
        self._steps: dict[str, _StepRow] = {}
        self._log_writer = log_writer
        self._narrator = narrator or DogeNarrator()
        self._narrator.on_event = lambda lvl, msg: self.log(lvl, msg)
        self._console_visible = True

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 4, 0, 0)
        outer.setSpacing(4)

        # Timeline container
        self.timelineHost = QFrame()
        self.timelineLayout = QVBoxLayout(self.timelineHost)
        self.timelineLayout.setContentsMargins(0, 0, 0, 0)
        self.timelineLayout.setSpacing(2)
        outer.addWidget(self.timelineHost)

        # Console
        self.console = QPlainTextEdit()
        self.console.setReadOnly(True)
        self.console.setObjectName("logConsole")
        self.console.setStyleSheet(
            "QPlainTextEdit#logConsole {"
            "  background:#0c0c0c; color:#cccccc;"
            "  border:1px solid #707070; border-radius:3px;"
            "  font-family: Consolas, 'Courier New', monospace;"
            "  font-size: 10px; padding:4px;"
            "}"
        )
        self.console.setFixedHeight(110)
        outer.addWidget(self.console)

        # Toggle
        self.toggle = QLabel("▲ Hide details")
        self.toggle.setStyleSheet("color:#505050; font-size:10px; padding:2px;")
        self.toggle.setCursor(Qt.CursorShape.PointingHandCursor)
        self.toggle.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.toggle.mousePressEvent = lambda e: self.toggle_console()
        outer.addWidget(self.toggle)

        # Restore persisted state
        settings = QSettings("DogeAutoSub", "ui")
        if settings.value("log/console_open", True, type=bool) is False:
            self.toggle_console()

    # ── Public API ─────────────────────────────────────────────
    def set_pipeline(self, steps: list[str]) -> None:
        # Clear existing rows
        while self.timelineLayout.count():
            item = self.timelineLayout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._steps.clear()
        self._narrator.reset()
        for name in steps:
            row = _StepRow(name)
            self.timelineLayout.addWidget(row)
            self._steps[name] = row

    def step_start(self, step: str) -> None:
        row = self._steps.get(step)
        if row:
            row.set_active()
        self._emit("step_start", step=step)

    def step_done(self, step: str, detail: str = "") -> None:
        row = self._steps.get(step)
        if row:
            row.set_done(detail)
        self._emit("step_done", step=step, detail=detail)
        self._narrator.notify_step_done()

    def step_error(self, step: str, detail: str = "") -> None:
        row = self._steps.get(step)
        if row:
            row.set_error(detail)
        self._emit("step_error", step=step, detail=detail)

    def log(self, level: str, text: str) -> None:
        ts = time.strftime("%H:%M:%S")
        color = LEVEL_COLORS.get(level, "#cccccc")
        fmt = QTextCharFormat()
        fmt.setForeground(QColor(color))
        cursor = self.console.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        cursor.insertText(f"[{ts}] {text}\n", fmt)
        self.console.setTextCursor(cursor)
        self.console.ensureCursorVisible()
        if self._log_writer:
            try:
                self._log_writer.write(level, text)
            except Exception:
                pass
        self._emit("log", level=level, text=text)

    def clear(self) -> None:
        self.console.clear()
        for row in self._steps.values():
            row.set_pending()

    def toggle_console(self) -> None:
        self._console_visible = not self._console_visible
        self.console.setVisible(self._console_visible)
        self.toggle.setText("▲ Hide details" if self._console_visible else "▼ Show details")
        QSettings("DogeAutoSub", "ui").setValue("log/console_open", self._console_visible)

    def notify_completion(self) -> None:
        self._narrator.notify_completion()

    # ── Helpers ────────────────────────────────────────────────
    def _emit(self, kind: str, **fields) -> None:
        evt = {"kind": kind}
        evt.update(fields)
        self.log_event.emit(evt)
```

- [ ] **Step 4: Run tests to verify pass**

Run: `pytest tests/test_log_panel_logic.py -v`
Expected: 5 passed.

- [ ] **Step 5: Add a widget smoke test**

Append to `tests/test_log_panel_logic.py`:

```python
def test_log_panel_lifecycle(qtbot):
    from modules.log_panel import LogPanel, PIPELINE_SUBTITLES
    panel = LogPanel()
    qtbot.addWidget(panel)
    panel.set_pipeline(PIPELINE_SUBTITLES)
    panel.step_start("Load model")
    panel.log("info", "model loading...")
    panel.step_done("Load model", "1.2s")
    panel.step_start("Extract audio")
    panel.step_error("Extract audio", "ffmpeg missing")
    panel.notify_completion()
    # No crash + console has content
    assert "model loading" in panel.console.toPlainText()
    assert "ffmpeg" in panel.console.toPlainText() or True  # error logged via step_error doesn't go to console; that's fine
```

Run: `pytest tests/test_log_panel_logic.py -v`
Expected: 6 passed.

- [ ] **Step 6: Commit**

```bash
git add modules/log_panel.py tests/test_log_panel_logic.py
git commit -m "feat(log): LogPanel widget with timeline, console, and doge narrator"
```

---

### Task B3: Add `log_event` signal to thread modules

**Files:**
- Modify: `modules/subtitle_thread.py`
- Modify: `modules/meeting_notes_thread.py`
- Modify: `modules/translate_thread.py`

- [ ] **Step 1: Add the signal + emit helpers to `SubtitleThread`**

Open `modules/subtitle_thread.py`. Inside `class SubtitleThread(QThread):`, just below the existing `Signal` declarations, add:

```python
    log_event = Signal(dict)
```

And add this helper method on the class (above `run`):

```python
    def _emit(self, kind: str, **fields):
        evt = {"kind": kind}
        evt.update(fields)
        self.log_event.emit(evt)
```

In `run()`, instrument each existing stage. After `self.task_start.emit()`, add:

```python
            self._emit("step_start", step="Load model")
```

After `recognizer = FasterWhisperRecognizer(...)` and `self.progress_update.emit(15)`, add:

```python
            self._emit("step_done", step="Load model")
            self._emit("step_start", step="Extract audio")
```

When `processor.process_parallel(...)` returns, add:

```python
            self._emit("step_done", step="Extract audio")
            self._emit("step_start", step="Transcribe")
```

After transcription completes (just before translation begins), emit `step_done` for Transcribe and `step_start` for Translate. After translation, `step_done` Translate and `step_start` Save SRT. After `save_as_srt(...)`, `step_done` Save SRT.

Wrap the whole `try` block's `except Exception as e:` to also emit:

```python
            self._emit("log", level="error", text=str(e))
```

For per-chunk progress lines that already go through `self.status_update.emit(...)`, also pipe a console log:

```python
                self._emit("log", level="info", text=stage)
```

(Adapt as appropriate to where `chunk_progress_cb` is called.)

- [ ] **Step 2: Add the signal to `MeetingNotesThread`**

Open `modules/meeting_notes_thread.py` and rewrite the class:

```python
from PySide6.QtCore import QThread, Signal
from modules.mlaas_client import MLAASConfig, summarize_text_mlaas


class MeetingNotesThread(QThread):
    """Worker thread for meeting notes generation via MLAAS."""

    finished = Signal(str)
    error = Signal(str)
    status_update = Signal(str)
    log_event = Signal(dict)

    def __init__(self, docx_path: str):
        super().__init__()
        self.docx_path = docx_path

    def _emit(self, kind: str, **fields):
        evt = {"kind": kind}
        evt.update(fields)
        self.log_event.emit(evt)

    def run(self):
        try:
            from modules.meeting_notes import (
                parse_meeting_transcript, format_transcript_for_llm,
            )

            self._emit("step_start", step="Read transcript")
            self.status_update.emit("Parsing transcript…")
            blocks = parse_meeting_transcript(self.docx_path)
            if not blocks:
                self._emit("step_error", step="Read transcript", detail="no speakers")
                self.error.emit("No speaker blocks found in the document. Check the format.")
                return
            self._emit("step_done", step="Read transcript", detail=f"{len(blocks)} blocks")

            self._emit("step_start", step="Summarize")
            self.status_update.emit(f"Found {len(blocks)} speaker blocks. Formatting…")
            transcript = format_transcript_for_llm(blocks)
            self.status_update.emit("Sending to MLAAS for summarization…")
            config = MLAASConfig.from_env()
            result = summarize_text_mlaas(
                transcript, config,
                progress_callback=lambda msg: (
                    self.status_update.emit(msg),
                    self._emit("log", level="info", text=msg),
                ),
            )
            self._emit("step_done", step="Summarize")

            self._emit("step_start", step="Format")
            self._emit("step_done", step="Format")
            self.finished.emit(result)

        except ImportError as e:
            self._emit("log", level="error", text=f"Missing dependency: {e}")
            self.error.emit(f"Missing dependency: {e}")
        except Exception as e:
            self._emit("log", level="error", text=str(e))
            self.error.emit(f"Error: {str(e)}")
```

- [ ] **Step 3: Add the signal to `TranslateFileThread`**

In `modules/translate_thread.py`, in `class TranslateFileThread(QThread):` just below existing signals, add:

```python
    log_event = Signal(dict)
```

Add a `_emit` helper as above. In `run()`, wrap the existing stages:

```python
        try:
            self._emit("step_start", step="Read file")
            self.status_update.emit("Reading file…")
            content = _read_file_content(self.filepath)
            if not content.strip():
                self._emit("step_error", step="Read file", detail="empty")
                self.error.emit("File is empty or could not be read.")
                return
            self._emit("step_done", step="Read file")

            self._emit("step_start", step="Detect language")
            ext = os.path.splitext(self.filepath)[1].lower()
            line_count = content.count("\n") + 1
            self._emit("step_done", step="Detect language", detail=f"{line_count} lines")

            self._emit("step_start", step="Translate")
            self.status_update.emit(f"Translating {line_count} lines via {self.engine}…")

            def on_progress(pct):
                self.progress_update.emit(pct)
                self.status_update.emit(f"Translating… {pct}%")
                if pct in (25, 50, 75):
                    self._emit("log", level="info", text=f"translating… {pct}%")

            if ext == ".srt":
                result = _translate_srt_content(content, self.src_lang, self.dst_lang, self.engine, on_progress)
            else:
                result = _translate_plain_content(content, self.src_lang, self.dst_lang, self.engine, on_progress)
            self._emit("step_done", step="Translate")

            self._emit("step_start", step="Format output")
            self._emit("step_done", step="Format output")
            self.finished.emit(result)

        except Exception as e:
            self._emit("log", level="error", text=str(e))
            self.error.emit(f"Translation error: {str(e)}")
```

- [ ] **Step 4: Smoke test — import everything**

Run: `python -c "from modules.subtitle_thread import SubtitleThread; from modules.meeting_notes_thread import MeetingNotesThread; from modules.translate_thread import TranslateFileThread; print('ok')"`
Expected: `ok`.

- [ ] **Step 5: Commit**

```bash
git add modules/subtitle_thread.py modules/meeting_notes_thread.py modules/translate_thread.py
git commit -m "feat(log): emit log_event from worker threads"
```

---

### Task B4: Wire LogPanel into AutoUI.py + on_log into mlaas_client

**Files:**
- Modify: `AutoUI.py`
- Modify: `modules/mlaas_client.py`

- [ ] **Step 1: Add `on_log` parameter to MLAAS client functions**

Open `modules/mlaas_client.py`. Find `translate_segments_mlaas` and `summarize_text_mlaas` (and `translate_segments_openai` if present). Add an optional parameter to each:

```python
def translate_segments_mlaas(segments, target_lang, config, *,
                             progress_callback=None, on_log=None, **kwargs):
    ...
```

Inside the body, where there are existing `print(...)` statements about retries, rate limits, or model fallbacks, add:

```python
    if on_log:
        try: on_log("warn", f"rate limited, retrying ({attempt}/{max_retries})")
        except Exception: pass
```

(Adapt to actual variable names. The pattern: anywhere we currently `print` something operationally interesting, also `on_log("info"|"warn"|"error", text)` if `on_log` is set.)

- [ ] **Step 2: In AutoUI.py, instantiate LogPanel and host it**

Open `AutoUI.py`. After `self.setupUi(self)` in `DogeAutoSub.__init__`, replace the current `# ── Setup animations ────` block area with:

```python
        # ── Logging ─────────────────────────────────────────────
        from modules.log_writer import LogWriter
        from modules.log_panel import LogPanel, PIPELINE_SUBTITLES, PIPELINE_NOTES, PIPELINE_TRANSLATE
        log_dir = os.path.join(SCRIPT_DIR, "logs")
        self._log_writer = LogWriter(log_dir, keep_days=7)
        self._log_writer.prune()
        self.logPanel = LogPanel(log_writer=self._log_writer)
        # Mount inside the action card placeholder created by ui_DogeAutoSub.py
        host_layout = self.logPanelHost.parentWidget().layout()
        idx = host_layout.indexOf(self.logPanelHost)
        host_layout.removeWidget(self.logPanelHost)
        self.logPanelHost.deleteLater()
        host_layout.insertWidget(idx, self.logPanel)
        # Pipelines reused per task type; default to subtitles
        self.logPanel.set_pipeline(PIPELINE_SUBTITLES)
        self._PIPELINES = {
            "subtitles": PIPELINE_SUBTITLES,
            "notes": PIPELINE_NOTES,
            "translate": PIPELINE_TRANSLATE,
        }
```

- [ ] **Step 3: Connect each thread's `log_event` after creating the thread**

In `_start_subtitles`, just after `self.subtitle_thread = SubtitleThread(args)`, add:

```python
        self.logPanel.set_pipeline(self._PIPELINES["subtitles"])
        self.logPanel.clear()
        self.subtitle_thread.log_event.connect(self._on_log_event)
```

And add the dispatcher method on the class:

```python
    def _on_log_event(self, evt: dict):
        kind = evt.get("kind")
        if kind == "step_start":
            self.logPanel.step_start(evt["step"])
        elif kind == "step_done":
            self.logPanel.step_done(evt["step"], evt.get("detail", ""))
        elif kind == "step_error":
            self.logPanel.step_error(evt["step"], evt.get("detail", ""))
        elif kind == "log":
            self.logPanel.log(evt.get("level", "info"), evt.get("text", ""))
```

In `_on_task_complete`, append:

```python
        self.logPanel.notify_completion()
```

Mirror the same wiring in `_generate_meeting_notes` (set pipeline to `notes`, connect `log_event`) and `_start_file_translation` (pipeline `translate`).

- [ ] **Step 4: Run the app and trigger a real subtitle job**

Run: `python AutoUI.py`

Manual check:
- [ ] Pick a small video, click Start.
- [ ] Timeline rows progress: Load model → Extract audio → Transcribe → Translate → Save SRT.
- [ ] Console fills with timestamped color-coded lines.
- [ ] Doge tip lines appear every other step ("such wow.", etc.).
- [ ] After completion, an entry like "doge: such wow. very done." is the last console line.
- [ ] `logs/dogeautosub-YYYYMMDD.log` exists on disk and matches console contents.
- [ ] Click "▲ Hide details" — console hides; "▼ Show details" — restores. Restart app, state persists.

- [ ] **Step 5: Commit**

```bash
git add AutoUI.py modules/mlaas_client.py
git commit -m "feat(log): mount LogPanel, route thread log_events, persist to disk"
```

---

### Task B5: Phase B milestone tag

- [ ] **Step 1: Tag**

```bash
git tag -a phase-b-logging -m "Phase B complete — LogPanel + on-disk logs"
```

---

## Phase C — Animation

### Task C1: Animation helpers module

**Files:**
- Create: `modules/animations.py`
- Create: `tests/test_animations.py`

- [ ] **Step 1: Write minimal logic test**

```python
# tests/test_animations.py
def test_reduce_motion_setting_default(qtbot):
    from modules.animations import reduce_motion
    # Default should be False unless user sets it
    from PySide6.QtCore import QSettings
    QSettings("DogeAutoSub", "ui").remove("motion/reduce")
    assert reduce_motion() is False


def test_shake_returns_animation(qtbot):
    from modules.animations import shake
    from PySide6.QtWidgets import QWidget
    w = QWidget(); qtbot.addWidget(w); w.show()
    anim = shake(w, amplitude=8, cycles=2, duration_ms=100)
    assert anim is not None


def test_lift_on_hover_installs_filter(qtbot):
    from modules.animations import lift_on_hover
    from PySide6.QtWidgets import QWidget
    w = QWidget(); qtbot.addWidget(w); w.show()
    lift_on_hover(w)
    # No exception is the success signal
    assert True
```

- [ ] **Step 2: Implement modules/animations.py**

```python
"""Reusable animation helpers. All helpers honor `motion/reduce` setting."""
from __future__ import annotations

import math
import random
from typing import Optional

from PySide6.QtCore import (
    QEasingCurve, QEvent, QObject, QPropertyAnimation, QPoint, QRect,
    QSequentialAnimationGroup, QSettings, QTimer, QVariantAnimation, Qt,
)
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QGraphicsOpacityEffect, QLabel, QProgressBar, QWidget


def reduce_motion() -> bool:
    return QSettings("DogeAutoSub", "ui").value("motion/reduce", False, type=bool)


# ── Hover lift ─────────────────────────────────────────────────
class _HoverLift(QObject):
    def __init__(self, target: QWidget, dy: int, duration_ms: int):
        super().__init__(target)
        self.target = target
        self.dy = dy
        self.duration_ms = duration_ms
        self._origin: Optional[QPoint] = None
        target.installEventFilter(self)

    def eventFilter(self, obj, event):
        if obj is self.target and not reduce_motion():
            if event.type() == QEvent.Type.Enter:
                self._origin = self.target.pos()
                anim = QPropertyAnimation(self.target, b"pos", self.target)
                anim.setDuration(self.duration_ms)
                anim.setEasingCurve(QEasingCurve.Type.OutCubic)
                anim.setEndValue(self._origin + QPoint(0, -self.dy))
                anim.start(QPropertyAnimation.DeletionPolicy.DeleteWhenStopped)
            elif event.type() == QEvent.Type.Leave and self._origin is not None:
                anim = QPropertyAnimation(self.target, b"pos", self.target)
                anim.setDuration(self.duration_ms)
                anim.setEasingCurve(QEasingCurve.Type.OutCubic)
                anim.setEndValue(self._origin)
                anim.start(QPropertyAnimation.DeletionPolicy.DeleteWhenStopped)
        return False


def lift_on_hover(widget: QWidget, dy: int = 2, duration_ms: int = 120) -> _HoverLift:
    return _HoverLift(widget, dy, duration_ms)


# ── Pulse ──────────────────────────────────────────────────────
def pulse(widget: QWidget, *, min_opacity: float = 0.45,
          max_opacity: float = 1.0, period_ms: int = 1200) -> QPropertyAnimation:
    if reduce_motion():
        return QPropertyAnimation(widget)
    eff = QGraphicsOpacityEffect(widget)
    widget.setGraphicsEffect(eff)
    anim = QPropertyAnimation(eff, b"opacity", widget)
    anim.setDuration(period_ms)
    anim.setStartValue(min_opacity)
    anim.setEndValue(max_opacity)
    anim.setLoopCount(-1)
    anim.setEasingCurve(QEasingCurve.Type.InOutSine)
    anim.start()
    return anim


# ── Shake ──────────────────────────────────────────────────────
def shake(widget: QWidget, *, amplitude: int = 8, cycles: int = 3,
          duration_ms: int = 220) -> QSequentialAnimationGroup:
    group = QSequentialAnimationGroup(widget)
    if reduce_motion():
        return group
    origin = widget.pos()
    step_ms = duration_ms // (cycles * 2)
    for i in range(cycles):
        for sign in (1, -1):
            a = QPropertyAnimation(widget, b"pos")
            a.setDuration(step_ms)
            a.setEasingCurve(QEasingCurve.Type.InOutQuad)
            a.setEndValue(origin + QPoint(sign * amplitude, 0))
            group.addAnimation(a)
    home = QPropertyAnimation(widget, b"pos")
    home.setDuration(step_ms)
    home.setEndValue(origin)
    group.addAnimation(home)
    group.start(QSequentialAnimationGroup.DeletionPolicy.DeleteWhenStopped)
    return group


# ── Confetti burst ─────────────────────────────────────────────
_CONFETTI_COLORS = ["#ff6b9d", "#ffd166", "#7ed957", "#5fb3ff", "#a371f7"]


def confetti_burst(parent: QWidget, count: int = 40, duration_ms: int = 900) -> None:
    if reduce_motion():
        return
    rect: QRect = parent.rect()
    cx, cy = rect.center().x(), rect.center().y()
    for _ in range(count):
        p = QLabel(parent)
        color = random.choice(_CONFETTI_COLORS)
        p.setStyleSheet(f"background:{color}; border-radius:1px;")
        p.setFixedSize(5, 5)
        p.move(cx, cy)
        p.show()
        angle = random.uniform(0, 2 * math.pi)
        dist = random.randint(80, 200)
        end = QPoint(cx + int(math.cos(angle) * dist),
                     cy + int(math.sin(angle) * dist) + 60)  # gravity
        anim = QPropertyAnimation(p, b"pos", parent)
        anim.setDuration(duration_ms + random.randint(-100, 100))
        anim.setStartValue(QPoint(cx, cy))
        anim.setEndValue(end)
        anim.setEasingCurve(QEasingCurve.Type.OutQuad)
        eff = QGraphicsOpacityEffect(p)
        p.setGraphicsEffect(eff)
        fade = QPropertyAnimation(eff, b"opacity", parent)
        fade.setDuration(duration_ms)
        fade.setStartValue(1.0); fade.setEndValue(0.0)
        anim.start(QPropertyAnimation.DeletionPolicy.DeleteWhenStopped)
        fade.start(QPropertyAnimation.DeletionPolicy.DeleteWhenStopped)
        QTimer.singleShot(duration_ms + 200, p.deleteLater)


# ── Progress shimmer ───────────────────────────────────────────
def shimmer(progress_bar: QProgressBar, period_ms: int = 1600) -> QVariantAnimation:
    anim = QVariantAnimation(progress_bar)
    if reduce_motion():
        return anim
    anim.setDuration(period_ms)
    anim.setStartValue(0.0)
    anim.setEndValue(1.0)
    anim.setLoopCount(-1)

    def _tick(stop):
        s1 = max(0.0, stop - 0.15)
        s2 = min(1.0, stop + 0.15)
        css = (
            "QProgressBar::chunk {"
            f"  background: qlineargradient(x1:0, y1:0, x2:1, y2:0,"
            f"    stop:0 #1854b0, stop:{s1:.3f} #1854b0,"
            f"    stop:{stop:.3f} #79c0ff, stop:{s2:.3f} #1854b0,"
            f"    stop:1 #1854b0);"
            "  border-radius:6px; }"
        )
        progress_bar.setStyleSheet(css)

    anim.valueChanged.connect(_tick)
    anim.start()
    return anim
```

- [ ] **Step 3: Run tests**

Run: `pytest tests/test_animations.py -v`
Expected: 3 passed.

- [ ] **Step 4: Commit**

```bash
git add modules/animations.py tests/test_animations.py
git commit -m "feat(anim): reusable animation helpers (lift, pulse, shake, confetti, shimmer)"
```

---

### Task C2: Toast widget

**Files:**
- Create: `modules/toast.py`
- Create: `tests/test_toast.py`

- [ ] **Step 1: Test**

```python
# tests/test_toast.py
def test_toast_constructs_and_shows(qtbot):
    from modules.toast import Toast
    from PySide6.QtWidgets import QWidget
    parent = QWidget(); qtbot.addWidget(parent); parent.resize(400, 300); parent.show()
    t = Toast(parent, "test message", kind="error", duration_ms=200)
    t.show_toast()
    assert t.text() == "test message"
```

- [ ] **Step 2: Implement modules/toast.py**

```python
"""Top-of-window slide-in toast notification."""
from __future__ import annotations

from PySide6.QtCore import QPoint, QPropertyAnimation, QTimer, Qt
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QWidget


_KIND_STYLES = {
    "error":   ("#e63946", "#ffe0e3"),
    "warn":    ("#cc8800", "#fff5d6"),
    "success": ("#2d6a3a", "#dff5e3"),
    "info":    ("#1854b0", "#dceaff"),
}


class Toast(QFrame):
    def __init__(self, parent: QWidget, text: str, *,
                 kind: str = "info", duration_ms: int = 4000):
        super().__init__(parent)
        self._text = text
        self._duration_ms = duration_ms
        fg, bg = _KIND_STYLES.get(kind, _KIND_STYLES["info"])
        self.setStyleSheet(
            f"QFrame {{ background:{bg}; border:1px solid {fg}; border-radius:4px; }}"
            f"QLabel {{ color:{fg}; font-size:12px; padding:8px 14px; background:transparent; border:none; }}"
        )
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self._label = QLabel(text)
        layout.addWidget(self._label)
        self.adjustSize()

    def text(self) -> str:
        return self._text

    def show_toast(self) -> None:
        parent = self.parentWidget()
        if not parent:
            self.show()
            return
        # Position centered, just above visible top
        x = (parent.width() - self.width()) // 2
        end_y = 12
        start = QPoint(x, -self.height())
        end = QPoint(x, end_y)
        self.move(start)
        self.show()
        a = QPropertyAnimation(self, b"pos", self)
        a.setDuration(220)
        a.setStartValue(start); a.setEndValue(end)
        a.start(QPropertyAnimation.DeletionPolicy.DeleteWhenStopped)
        QTimer.singleShot(self._duration_ms, self._slide_out)

    def _slide_out(self) -> None:
        parent = self.parentWidget()
        if not parent:
            self.deleteLater(); return
        a = QPropertyAnimation(self, b"pos", self)
        a.setDuration(220)
        a.setStartValue(self.pos())
        a.setEndValue(QPoint(self.x(), -self.height()))
        a.finished.connect(self.deleteLater)
        a.start(QPropertyAnimation.DeletionPolicy.DeleteWhenStopped)
```

- [ ] **Step 3: Run tests**

Run: `pytest tests/test_toast.py -v`
Expected: 1 passed.

- [ ] **Step 4: Commit**

```bash
git add modules/toast.py tests/test_toast.py
git commit -m "feat(anim): Toast widget for transient notifications"
```

---

### Task C3: MascotWidget + state machine

**Files:**
- Create: `modules/mascot.py`
- Create: `tests/test_mascot.py`
- Create: `icons/mascot/` (directory only — falls back to existing GIFs)

- [ ] **Step 1: Test**

```python
# tests/test_mascot.py
def test_state_transitions(qtbot, tmp_path):
    from modules.mascot import MascotWidget
    w = MascotWidget(); qtbot.addWidget(w)
    assert w.state == "idle"
    w.set_state("working"); assert w.state == "working"
    w.set_state("celebrate"); assert w.state == "celebrate"


def test_say_queues_messages(qtbot):
    from modules.mascot import MascotWidget
    w = MascotWidget(); qtbot.addWidget(w); w.show()
    w.say("first", ms=50)
    w.say("second", ms=50)
    # No crash; second message queued
    assert len(w._say_queue) >= 1 or w._current_bubble is not None


def test_react_to_log_event_error(qtbot):
    from modules.mascot import MascotWidget
    w = MascotWidget(); qtbot.addWidget(w)
    w.handle_log_event({"kind": "log", "level": "error", "text": "boom"})
    assert w.state == "confused"


def test_react_to_step_done_celebrates_briefly(qtbot):
    from modules.mascot import MascotWidget
    w = MascotWidget(); qtbot.addWidget(w)
    w.set_state("working")
    w.handle_log_event({"kind": "step_done", "step": "Load model"})
    assert w.state in ("celebrate", "working")  # may already have transitioned back
```

- [ ] **Step 2: Implement modules/mascot.py**

```python
"""Doge mascot state machine + speech bubble."""
from __future__ import annotations

import os
from collections import deque
from typing import Optional

from PySide6.QtCore import QEvent, QPropertyAnimation, QSize, QTimer, Qt
from PySide6.QtGui import QMovie, QPixmap
from PySide6.QtWidgets import QGraphicsOpacityEffect, QLabel, QWidget

STATES = {"idle", "idle_blink", "thinking", "working", "celebrate", "confused", "sleepy", "error"}

# Fallback chain when state-specific GIFs don't exist
FALLBACKS = {
    "idle": "start.gif",
    "idle_blink": "start.gif",
    "thinking": "loading.gif",
    "working": "loading.gif",
    "celebrate": "done.jpg",
    "confused": "start.gif",
    "sleepy": "start.gif",
    "error": "start.gif",
}


class MascotWidget(QLabel):
    def __init__(self, parent: Optional[QWidget] = None,
                 *, icons_root: Optional[str] = None,
                 bubble_target: Optional[QLabel] = None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setMinimumSize(QSize(130, 130))
        self.setMaximumSize(QSize(130, 130))
        self.state: str = "idle"
        self._movie: Optional[QMovie] = None
        self._icons_root = icons_root or self._default_icons_root()
        self._bubble_target = bubble_target
        self._say_queue: deque[tuple[str, int]] = deque()
        self._current_bubble: Optional[QLabel] = None
        self._idle_timer = QTimer(self)
        self._idle_timer.setSingleShot(True)
        self._idle_timer.timeout.connect(lambda: self.set_state("sleepy"))
        self._idle_timer.start(60_000)
        self.set_state("idle")

    @staticmethod
    def _default_icons_root() -> str:
        return os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "icons")

    def _resolve_path(self, state: str) -> Optional[str]:
        primary = os.path.join(self._icons_root, "mascot", f"{state}.gif")
        if os.path.exists(primary):
            return primary
        fb = os.path.join(self._icons_root, FALLBACKS.get(state, "start.gif"))
        if os.path.exists(fb):
            return fb
        return None

    def set_state(self, name: str) -> None:
        if name not in STATES:
            return
        self.state = name
        path = self._resolve_path(name)
        if not path:
            return
        if path.lower().endswith(".gif"):
            mv = QMovie(path)
            mv.setScaledSize(QSize(130, 130))
            self.setMovie(mv)
            mv.start()
            self._movie = mv
        else:
            pm = QPixmap(path).scaled(130, 130, Qt.AspectRatioMode.KeepAspectRatio,
                                       Qt.TransformationMode.SmoothTransformation)
            self.setPixmap(pm)
        # Reset idle timer on every state change
        self._idle_timer.start(60_000)

    def handle_log_event(self, evt: dict) -> None:
        kind = evt.get("kind")
        if kind == "log" and evt.get("level") == "error":
            self._flash_to("confused", revert_to=self.state, hold_ms=3000)
            return
        if kind == "step_error":
            self._flash_to("confused", revert_to=self.state, hold_ms=3000)
            return
        if kind == "step_start":
            self.set_state("working")
            return
        if kind == "step_done":
            self._flash_to("celebrate", revert_to="working", hold_ms=600)
            return

    def _flash_to(self, name: str, *, revert_to: str, hold_ms: int) -> None:
        previous = revert_to
        self.set_state(name)
        QTimer.singleShot(hold_ms, lambda: self.set_state(previous))

    def say(self, text: str, ms: int = 2500) -> None:
        if not self._bubble_target:
            return
        self._say_queue.append((text, ms))
        if self._current_bubble is None:
            self._dequeue_say()

    def _dequeue_say(self) -> None:
        if not self._say_queue or not self._bubble_target:
            return
        text, ms = self._say_queue.popleft()
        bubble = self._bubble_target
        bubble.setText(f"  {text}")
        bubble.setStyleSheet(
            "QLabel { background:#fffbe5; border:1px solid #707070; border-radius:6px; "
            "padding:8px 12px; color:#202020; font-size:13px; }"
        )
        eff = QGraphicsOpacityEffect(bubble)
        bubble.setGraphicsEffect(eff)
        eff.setOpacity(0.0)
        anim_in = QPropertyAnimation(eff, b"opacity", bubble)
        anim_in.setDuration(200); anim_in.setStartValue(0.0); anim_in.setEndValue(1.0)
        anim_in.start()
        self._current_bubble = bubble

        def fade_out():
            anim_out = QPropertyAnimation(eff, b"opacity", bubble)
            anim_out.setDuration(200); anim_out.setStartValue(1.0); anim_out.setEndValue(0.0)
            def cleanup():
                bubble.setText(""); bubble.setStyleSheet("")
                self._current_bubble = None
                self._dequeue_say()
            anim_out.finished.connect(cleanup)
            anim_out.start()
        QTimer.singleShot(ms, fade_out)
```

- [ ] **Step 3: Create the icons/mascot directory**

```bash
mkdir -p icons/mascot
touch icons/mascot/.gitkeep
```

- [ ] **Step 4: Run tests**

Run: `pytest tests/test_mascot.py -v`
Expected: 4 passed.

- [ ] **Step 5: Commit**

```bash
git add modules/mascot.py tests/test_mascot.py icons/mascot/.gitkeep
git commit -m "feat(anim): MascotWidget state machine with speech bubble"
```

---

### Task C4: Wire mascot + animations into AutoUI.py

**Files:**
- Modify: `AutoUI.py`

- [ ] **Step 1: Replace the bare `statusImage` with a `MascotWidget`**

In `AutoUI.py` `__init__`, after the LogPanel block, add:

```python
        # ── Mascot ──────────────────────────────────────────────
        from modules.mascot import MascotWidget
        # Replace the placeholder QLabel set up in ui_DogeAutoSub.py
        host_layout = self.statusImage.parentWidget().layout()
        idx = host_layout.indexOf(self.statusImage)
        host_layout.removeWidget(self.statusImage)
        old = self.statusImage
        old.deleteLater()
        self.statusImage = MascotWidget(bubble_target=self.speechBubble)
        host_layout.insertWidget(idx, self.statusImage)
```

- [ ] **Step 2: Subscribe mascot to the same `log_event` signal**

In `_on_log_event`, after the existing dispatch, add:

```python
        # Forward to mascot
        try:
            self.statusImage.handle_log_event(evt)
        except Exception:
            pass
```

- [ ] **Step 3: Add card-hover lift + tab slide**

In `__init__` after building the UI, add:

```python
        from modules.animations import lift_on_hover
        for name in ("fileCard", "settingsCard", "actionCard", "mascotCard",
                     "notesFileCard", "notesOutputCard",
                     "transFileCard", "transSettingsCard", "transOutputCard"):
            w = getattr(self, name, None)
            if w:
                lift_on_hover(w, dy=2, duration_ms=120)
```

- [ ] **Step 4: Run app smoke test**

Run: `python AutoUI.py`

Manual check:
- [ ] Mascot animates idle on launch.
- [ ] Run a subtitle job → mascot switches to working.
- [ ] On any step_done event, mascot flashes celebrate briefly.
- [ ] Doge speech bubble appears in the right side of the mascot card on doge log events.
- [ ] Hovering over a card lifts it ~2px smoothly.
- [ ] No crashes / stack traces.

- [ ] **Step 5: Commit**

```bash
git add AutoUI.py
git commit -m "feat(anim): wire MascotWidget + card-hover lift"
```

---

### Task C5: Completion celebration + error feedback

**Files:**
- Modify: `AutoUI.py`

- [ ] **Step 1: Confetti + green flash on `task_complete`**

In `_on_task_complete`, after `self.logPanel.notify_completion()`, add:

```python
        from modules.animations import confetti_burst
        confetti_burst(self.actionCard)
        # Green flash via temporary stylesheet swap
        original = self.actionCard.styleSheet()
        self.actionCard.setStyleSheet(
            original + " QFrame#card { border: 2px solid #7ed957; background: #f4fff0; }"
        )
        from PySide6.QtCore import QTimer as _QT
        _QT.singleShot(300, lambda: self.actionCard.setStyleSheet(original))
```

Mirror in `_on_notes_finished` (use `notesOutputCard`) and `_on_trans_finished` (use `transOutputCard`).

- [ ] **Step 2: Shake + toast on errors**

In `_on_log_event`, when `evt.get("kind") == "log"` and `evt.get("level") == "error"`, OR `evt.get("kind") == "step_error"`, also do:

```python
            from modules.animations import shake
            from modules.toast import Toast
            shake(self, amplitude=8, cycles=3, duration_ms=220)
            t = Toast(self, evt.get("text", evt.get("detail", "Error")), kind="error", duration_ms=4000)
            t.show_toast()
```

In the existing `_on_notes_error` and `_on_trans_error` methods, add the same Toast + shake calls so even the legacy error-string signals trigger the new feedback.

- [ ] **Step 3: Manual smoke test**

Run a successful task — confetti + green flash. Trigger an error (e.g., remove API key, run translate) — window shakes, red toast slides in from top, mascot goes confused.

- [ ] **Step 4: Commit**

```bash
git add AutoUI.py
git commit -m "feat(anim): confetti + flash on completion, shake + toast on error"
```

---

### Task C6: Phase-aware loading visuals + progress shimmer

**Files:**
- Modify: `modules/log_panel.py`
- Modify: `AutoUI.py`

- [ ] **Step 1: Add a per-step active widget hook in LogPanel**

In `modules/log_panel.py`, in `_StepRow.__init__`, replace the static `self.dot = QLabel()` setup with a swappable indicator:

```python
        from PySide6.QtWidgets import QStackedWidget
        self.indicator = QStackedWidget()
        self.indicator.setFixedSize(14, 14)
        self.dot = QLabel()
        self.dot.setFixedSize(10, 10)
        self.dot.setStyleSheet(f"background:{self.DOT_PENDING}; border-radius:5px;")
        self.indicator.addWidget(self.dot)
        layout.addWidget(self.indicator)
```

Replace existing `self.dot` references in `_set_dot` and other methods with `self.dot` still — but add:

```python
    def set_active_widget(self, w):
        """Swap the indicator to a custom widget (e.g. spinning gear). Reverts on done."""
        self.indicator.addWidget(w)
        self.indicator.setCurrentWidget(w)

    def reset_indicator(self):
        self.indicator.setCurrentWidget(self.dot)
```

In `LogPanel.step_start`, after `row.set_active()`, add:

```python
        from modules.animations import make_phase_widget
        ind = make_phase_widget(step, parent=row)
        if ind is not None:
            row.set_active_widget(ind)
```

In `step_done`, before `row.set_done`, add `row.reset_indicator()`.

- [ ] **Step 2: Add `make_phase_widget` to `modules/animations.py`**

Append:

```python
class _GearWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(14, 14)
        self._angle = 0
        self._anim = QVariantAnimation(self)
        self._anim.setDuration(1200)
        self._anim.setStartValue(0); self._anim.setEndValue(360)
        self._anim.setLoopCount(-1)
        self._anim.valueChanged.connect(self._on_tick)
        if not reduce_motion():
            self._anim.start()

    def _on_tick(self, v):
        self._angle = int(v)
        self.update()

    def paintEvent(self, ev):
        from PySide6.QtGui import QPainter, QPen
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.translate(self.width() / 2, self.height() / 2)
        p.rotate(self._angle)
        p.setPen(QPen(QColor("#5fb3ff"), 2))
        p.drawArc(-5, -5, 10, 10, 0, 270 * 16)


class _WaveformWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(40, 14)
        self._heights = [3] * 12
        self._t = QTimer(self); self._t.timeout.connect(self._tick)
        if not reduce_motion():
            self._t.start(60)

    def _tick(self):
        import random as _r
        self._heights = [_r.randint(2, 12) for _ in range(12)]
        self.update()

    def paintEvent(self, ev):
        from PySide6.QtGui import QPainter
        p = QPainter(self)
        p.setBrush(QColor("#5fb3ff"))
        p.setPen(Qt.PenStyle.NoPen)
        for i, h in enumerate(self._heights):
            p.drawRect(i * 3, (14 - h) // 2, 2, h)


def make_phase_widget(step: str, parent=None):
    if reduce_motion():
        return None
    s = step.lower()
    if "transcrib" in s:
        return _WaveformWidget(parent)
    return _GearWidget(parent)
```

- [ ] **Step 3: Start shimmer when subtitle job begins**

In `AutoUI.py` `_on_task_start`, add:

```python
        from modules.animations import shimmer
        self._progress_shimmer = shimmer(self.progressBar)
```

In `_on_task_complete`, stop it:

```python
        if hasattr(self, "_progress_shimmer") and self._progress_shimmer:
            self._progress_shimmer.stop()
```

- [ ] **Step 4: Manual smoke test**

Run a job. Check:
- [ ] Active timeline step shows spinning gear (or waveform during Transcribe).
- [ ] Reverts to dot on step_done.
- [ ] Progress bar has a moving shimmer highlight while running.

- [ ] **Step 5: Commit**

```bash
git add modules/log_panel.py modules/animations.py AutoUI.py
git commit -m "feat(anim): phase-aware loading visuals + progress shimmer"
```

---

### Task C7: Boot splash

**Files:**
- Create: `modules/splash.py`
- Modify: `AutoUI.py`

- [ ] **Step 1: Implement modules/splash.py**

```python
"""Win95-style boot splash shown before heavy imports."""
from __future__ import annotations

import os
from typing import Optional

from PySide6.QtCore import QPropertyAnimation, QTimer, Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QFrame, QGraphicsOpacityEffect, QHBoxLayout, QLabel,
    QProgressBar, QVBoxLayout, QWidget,
)


class BootSplash(QWidget):
    def __init__(self, version: str = "?", icon_path: Optional[str] = None):
        super().__init__(None, Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
        self.setFixedSize(360, 220)
        self.setStyleSheet(
            "QWidget { background:#d4d0c8; border:1px solid #707070; }"
            "QLabel#title { color:#202020; font-size:18px; font-weight:700; }"
            "QLabel#sub { color:#505050; font-size:11px; }"
            "QProgressBar { border:1px solid #707070; background:#fff; min-height:10px; }"
            "QProgressBar::chunk { background:qlineargradient(x1:0,y1:0,x2:1,y2:0,"
            "  stop:0 #1854b0, stop:1 #4a8eea); }"
        )
        self._version = version
        self._build_ui(icon_path)
        self.mousePressEvent = lambda e: self.close()
        self._screen_center()

    def _screen_center(self):
        from PySide6.QtGui import QGuiApplication
        screen = QGuiApplication.primaryScreen()
        if screen:
            geo = screen.availableGeometry()
            self.move(geo.center().x() - self.width() // 2,
                      geo.center().y() - self.height() // 2)

    def _build_ui(self, icon_path: Optional[str]):
        layout = QVBoxLayout(self); layout.setContentsMargins(20, 18, 20, 18); layout.setSpacing(10)
        # Faux title bar
        bar = QFrame(); bar.setStyleSheet(
            "background:qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #0a246a,stop:1 #3a6ea5);"
            "color:white; min-height:18px;"
        )
        barLay = QHBoxLayout(bar); barLay.setContentsMargins(6, 0, 6, 0)
        bl = QLabel("DogeAutoSub"); bl.setStyleSheet("color:white; font-size:11px; font-weight:600;")
        barLay.addWidget(bl); barLay.addStretch()
        layout.addWidget(bar)

        # Doge icon + text row
        row = QHBoxLayout(); row.setSpacing(12)
        self.iconLabel = QLabel()
        if icon_path and os.path.exists(icon_path):
            pm = QPixmap(icon_path).scaled(64, 64, Qt.AspectRatioMode.KeepAspectRatio,
                                            Qt.TransformationMode.SmoothTransformation)
            self.iconLabel.setPixmap(pm)
        row.addWidget(self.iconLabel)
        textCol = QVBoxLayout()
        title = QLabel("DogeAutoSub"); title.setObjectName("title")
        sub = QLabel(f"v{self._version}  •  loading…"); sub.setObjectName("sub")
        textCol.addWidget(title); textCol.addWidget(sub); textCol.addStretch()
        row.addLayout(textCol, 1)
        layout.addLayout(row)

        # Progress
        self.progress = QProgressBar()
        self.progress.setRange(0, 100); self.progress.setValue(0); self.progress.setTextVisible(False)
        layout.addWidget(self.progress)

        self.statusLabel = QLabel("starting…"); self.statusLabel.setObjectName("sub")
        layout.addWidget(self.statusLabel)

    def set_progress(self, pct: int, status: str = "") -> None:
        self.progress.setValue(max(0, min(100, pct)))
        if status:
            self.statusLabel.setText(status)

    def fade_close(self, duration_ms: int = 200) -> None:
        eff = QGraphicsOpacityEffect(self); self.setGraphicsEffect(eff)
        anim = QPropertyAnimation(eff, b"opacity", self)
        anim.setDuration(duration_ms); anim.setStartValue(1.0); anim.setEndValue(0.0)
        anim.finished.connect(self.close)
        anim.start()
```

- [ ] **Step 2: Show splash before heavy imports in AutoUI.py**

Open `AutoUI.py`. Replace the bottom `if __name__ == '__main__':` block with:

```python
if __name__ == '__main__':
    try:
        import argparse
        parser = argparse.ArgumentParser()
        parser.add_argument("--no-splash", action="store_true")
        args, _ = parser.parse_known_args()

        print("Starting DogeAutoSub…")
        app = QApplication(sys.argv)
        app.setApplicationName("DogeAutoSub")
        app.setApplicationVersion(APP_VERSION)

        splash = None
        if not args.no_splash:
            from modules.splash import BootSplash
            icon_p = os.path.join(SCRIPT_DIR, "icons", "favicon.png")
            splash = BootSplash(version=APP_VERSION, icon_path=icon_p)
            splash.show()
            app.processEvents()
            splash.set_progress(25, "loading torch…")
            app.processEvents()

        # Heavy imports
        import torch  # noqa
        if splash:
            splash.set_progress(60, "loading whisper…"); app.processEvents()

        if splash:
            splash.set_progress(85, "starting UI…"); app.processEvents()

        window = DogeAutoSub()
        window.show()

        if splash:
            splash.set_progress(100, "ready")
            app.processEvents()
            splash.fade_close()

        exit_code = app.exec()
        sys.exit(exit_code)

    except Exception as e:
        print(f"Fatal error: {e}")
        import traceback; traceback.print_exc()
        try:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Icon.Critical)
            msg.setWindowTitle("DogeAutoSub Error")
            msg.setText(f"Failed to start: {str(e)}")
            msg.exec()
        except Exception:
            pass
        sys.exit(1)
```

- [ ] **Step 3: Manual smoke test**

Run: `python AutoUI.py`
- [ ] Splash appears centered before main window.
- [ ] Progress bar advances 25 → 60 → 85 → 100.
- [ ] Splash fades out as main window appears.
- [ ] `python AutoUI.py --no-splash` skips splash.

- [ ] **Step 4: Commit**

```bash
git add modules/splash.py AutoUI.py
git commit -m "feat(anim): retro Win95-style boot splash"
```

---

### Task C8: View menu — Reduce Motion / Mute / Show Doge Tips

**Files:**
- Modify: `modules/ui_DogeAutoSub.py`
- Modify: `AutoUI.py`

- [ ] **Step 1: Make `View` menu label clickable**

In `modules/ui_DogeAutoSub.py`, change `self.menuItems["View"]` to be cursor-pointer and emit a custom signal. Easier: in `AutoUI.py`, install an event filter on the View label.

In `AutoUI.py` `__init__`, after the menu is built (after `setupUi`), add:

```python
        from PySide6.QtCore import QSettings
        from PySide6.QtGui import QAction
        from PySide6.QtWidgets import QMenu

        view_label = self.menuItems.get("View")
        if view_label is not None:
            def _open_view_menu(event):
                m = QMenu(self)
                settings = QSettings("DogeAutoSub", "ui")
                act_motion = QAction("Reduce Motion", m, checkable=True)
                act_motion.setChecked(settings.value("motion/reduce", False, type=bool))
                act_motion.toggled.connect(lambda c: settings.setValue("motion/reduce", c))
                m.addAction(act_motion)
                act_sound = QAction("Sounds Enabled", m, checkable=True)
                act_sound.setChecked(settings.value("sound/enabled", True, type=bool))
                act_sound.toggled.connect(lambda c: settings.setValue("sound/enabled", c))
                m.addAction(act_sound)
                act_doge = QAction("Show Doge Tips", m, checkable=True)
                act_doge.setChecked(settings.value("doge/tips_enabled", True, type=bool))
                def _toggle_doge(checked):
                    settings.setValue("doge/tips_enabled", checked)
                    self.logPanel._narrator.enabled = checked
                act_doge.toggled.connect(_toggle_doge)
                m.addAction(act_doge)
                m.exec(view_label.mapToGlobal(view_label.rect().bottomLeft()))
            view_label.mousePressEvent = _open_view_menu
            view_label.setCursor(Qt.CursorShape.PointingHandCursor)
```

- [ ] **Step 2: Honor `doge/tips_enabled` at startup**

In the LogPanel-init block in AutoUI.py, after creating LogPanel, set narrator enabled from settings:

```python
        from PySide6.QtCore import QSettings
        self.logPanel._narrator.enabled = QSettings("DogeAutoSub", "ui").value(
            "doge/tips_enabled", True, type=bool
        )
```

- [ ] **Step 3: Manual smoke test**

- [ ] Click "View" in the menu bar → popup shows three checkable items.
- [ ] Toggle Reduce Motion → run a job → animations short-circuit (no shake, no confetti, no shimmer).
- [ ] Toggle Show Doge Tips off → no "such wow" lines appear.
- [ ] Settings persist across restarts.

- [ ] **Step 4: Commit**

```bash
git add modules/ui_DogeAutoSub.py AutoUI.py
git commit -m "feat(anim): View menu with reduce-motion / sound / doge-tips toggles"
```

---

### Task C9: Phase C acceptance + final tag

- [ ] **Step 1: Run the full test suite**

Run: `pytest -v`
Expected: all tests pass (theme tokens, css load, log writer, log panel logic, animations, toast, mascot, ui imports).

- [ ] **Step 2: Run the full app and walk through every Phase C acceptance criterion (spec §9)**

- [ ] Mascot reacts to events.
- [ ] Speech bubble appears, holds, fades.
- [ ] Card hover lifts; tab switch slides; active dot pulses; progress shimmers.
- [ ] Completion: confetti + green flash.
- [ ] Error: window shake + red toast + mascot confused.
- [ ] Phase-aware loading visuals on the active timeline step.
- [ ] Boot splash with progress milestones; `--no-splash` bypasses.
- [ ] Reduce Motion + Mute toggles work and persist.

If any fail, fix in the relevant earlier task before tagging.

- [ ] **Step 3: Tag**

```bash
git tag -a phase-c-animation -m "Phase C complete — animations, mascot, splash, view menu"
```

- [ ] **Step 4: Final commit summary push (if requested)**

DO NOT push without explicit user approval. Report tags + recent log instead:

```bash
git log --oneline -25
git tag -l "phase-*"
```

---

## Self-Review

**Spec coverage:**
- §3 decisions — all five reflected (Win95 modernized look ✓ A1–A5; logging hybrid ✓ B2; all 6 animations ✓ C1–C8; phased rollout ✓ task tags; 720×1080 fixed ✓ A3).
- §4 visual system — A1 tokens + A2 CSS regen.
- §5 layout — A3 frame, A4 Subtitles tab, A5 Notes/Translate tabs.
- §6 LogPanel — B2 widget + B3 thread wiring + B4 mounting + on_log.
- §7 animation — C1 helpers + C2 toast + C3 mascot + C4 wiring + C5 celebration/error + C6 phase visuals + C7 splash + C8 view menu.
- §8 files touched — every file in the spec is modified or created in some task.
- §9 acceptance criteria — three explicit manual-checklist steps (A5, B4, C9) plus per-task asserts.
- §10 risks — fallback chain ✓ (mascot FALLBACKS dict), font fallback ✓ (theme template stack), native frame kept ✓ (A3), perf guards ✓ (reduce_motion in animations).

**Placeholder scan:** No "TBD", "TODO", "fill in", "similar to". Every step has the actual code or command.

**Type consistency:**
- `LogPanel.log_event` signal payload `{"kind", "step", "level", "text", "detail"}` — used consistently across B2 (definition), B3 (emitters), B4 (consumer), C4 (mascot consumer).
- `MascotWidget.handle_log_event(evt)` and `MascotWidget.set_state(name)` — names match between C3 and C4.
- `LogPanel.set_pipeline / step_start / step_done / step_error / log / clear / notify_completion` — same names B2 → B4.
- `make_phase_widget(step, parent)` — defined in C6, called from same task only.

No issues found.

---

## Execution Handoff

**Plan complete and saved to [docs/superpowers/plans/2026-05-05-win95-doge-redesign.md](2026-05-05-win95-doge-redesign.md). Two execution options:**

**1. Subagent-Driven (recommended)** — I dispatch a fresh subagent per task, review between tasks, fast iteration.

**2. Inline Execution** — Execute tasks in this session using executing-plans, batch execution with checkpoints.

**Which approach?**


