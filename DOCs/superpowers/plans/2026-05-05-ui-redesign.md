# DogeAutoSub UI Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the Win95-styled UI with a dark macOS-inspired chrome, 4-palette stripe (Atari Sunset default), Finder-style sidebar layout, and a rebuilt status/ETA/log layer — without changing any worker thread or backend behavior.

**Architecture:** Approach C from the spec — `theme_tokens.py` stays the source of truth for styling (expanded from 2 themes to 4 palettes). `ui_DogeAutoSub.py` widget tree is rebuilt as a sidebar layout but every existing widget object name and signal is preserved so `AutoUI.py` and worker threads need no rewiring. New small modules: `eta_tracker.py`, `phase_strip.py`, `stripe_widget.py`, `palette_menu.py`. Existing modules `mascot.py`, `toast.py`, `log_panel.py` are extended/split, not replaced.

**Tech Stack:** PySide6 6.x · Python 3.11 · pytest + pytest-qt · existing project conventions (no new third-party deps).

**Spec:** [DOCs/superpowers/specs/2026-05-05-ui-redesign-design.md](../specs/2026-05-05-ui-redesign-design.md)

---

## File Map

**Created:**
- `modules/eta_tracker.py` — phase-weighted, EMA-smoothed ETA estimator
- `modules/phase_strip.py` — horizontal phase indicator (5 dots + connecting line)
- `modules/stripe_widget.py` — title-bar palette stripe (3px tall band row)
- `modules/palette_menu.py` — title-bar dropdown for palette selection
- `icons/mascot/README.txt` — describes which GIF/PNG asset names are expected
- `tests/test_eta_tracker.py`
- `tests/test_phase_strip.py`
- `tests/test_stripe_widget.py`
- `tests/test_palette_menu.py`

**Modified:**
- `modules/theme_tokens.py` — replace `light`/`dark` keys with 4 palettes; rewrite stylesheet template
- `modules/ui_DogeAutoSub.py` — rebuild widget tree as sidebar; preserve every existing widget object name and signal
- `modules/log_panel.py` — remove pipeline timeline (moves to `PhaseStrip`); strip `DogeNarrator` from log routing; rename collapsed-by-default with Events / Raw filters
- `modules/mascot.py` — add `set_phase(phase)`, `set_idle(workflow)`, static-PNG fallback
- `modules/toast.py` — add `success_with_doge(parent, message, filename)` factory
- `AutoUI.py` — frameless-window drag/min/max/close; palette-dropdown wiring; phase-strip + ETA wiring; signal translation table
- `tests/test_theme_tokens.py` — assertions for the 4 palettes
- `tests/test_log_panel_logic.py` — narrator no longer reaches log
- `tests/test_mascot.py` — add tests for `set_phase`/`set_idle`/fallback

**Deleted:** none. The old `styleSheetDark.css` / `styleSheetLight.css` files in `modules/` are unused once `build_stylesheet` is the only style source — keep them in tree for the auto-updater's manifest history; they're harmless.

---

## Task 1 — Theme tokens: 4 palettes

**Files:**
- Modify: `modules/theme_tokens.py`
- Modify: `tests/test_theme_tokens.py`

- [ ] **Step 1.1: Write the failing tests**

Replace the entire contents of `tests/test_theme_tokens.py` with:

```python
import pytest

from modules.theme_tokens import PALETTES, build_stylesheet, SHARED_TOKENS


PALETTE_IDS = {"atari", "rainbow", "crt", "famicom"}


def test_palettes_has_all_four():
    assert set(PALETTES.keys()) == PALETTE_IDS


def test_each_palette_has_required_keys():
    required = {"name", "stripe", "accent", "accent_text"}
    for pid in PALETTE_IDS:
        missing = required - set(PALETTES[pid].keys())
        assert not missing, f"{pid} missing: {missing}"


def test_stripe_has_at_least_three_bands():
    for pid in PALETTE_IDS:
        assert len(PALETTES[pid]["stripe"]) >= 3, pid


def test_atari_is_default_first_in_dict():
    assert next(iter(PALETTES.keys())) == "atari"


def test_shared_tokens_present():
    required = {
        "desktop_bg", "window_bg", "sidebar_bg", "titlebar_bg", "input_bg",
        "border", "text_primary", "text_secondary", "text_tertiary",
        "error",
    }
    missing = required - set(SHARED_TOKENS.keys())
    assert not missing


def test_build_stylesheet_returns_long_string_per_palette():
    for pid in PALETTE_IDS:
        css = build_stylesheet(pid)
        assert isinstance(css, str)
        assert len(css) > 500
        assert "QMainWindow" in css


def test_build_stylesheet_embeds_accent_color():
    css = build_stylesheet("atari")
    assert PALETTES["atari"]["accent"] in css


def test_build_stylesheet_unknown_palette_raises():
    with pytest.raises(KeyError):
        build_stylesheet("solarized")
```

- [ ] **Step 1.2: Run tests to verify they fail**

Run: `pytest tests/test_theme_tokens.py -v`
Expected: ImportError on `PALETTES` / `SHARED_TOKENS` (or AttributeError) — fails because the new symbols don't exist yet.

- [ ] **Step 1.3: Rewrite `modules/theme_tokens.py`**

Replace the entire file with:

```python
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
```

- [ ] **Step 1.4: Run tests to verify they pass**

Run: `pytest tests/test_theme_tokens.py -v`
Expected: 8 passed.

- [ ] **Step 1.5: Commit**

```bash
git add modules/theme_tokens.py tests/test_theme_tokens.py
git commit -m "feat(theme): replace light/dark with 4-palette dark-only system"
```

---

## Task 2 — EtaTracker module

**Files:**
- Create: `modules/eta_tracker.py`
- Create: `tests/test_eta_tracker.py`

- [ ] **Step 2.1: Write the failing tests**

Create `tests/test_eta_tracker.py`:

```python
import pytest

from modules.eta_tracker import EtaTracker, WORKFLOW_PHASES


def test_subtitle_phase_weights_sum_to_one():
    weights = WORKFLOW_PHASES["subtitles"]
    assert abs(sum(p["weight"] for p in weights) - 1.0) < 1e-6


def test_notes_phase_weights_sum_to_one():
    weights = WORKFLOW_PHASES["notes"]
    assert abs(sum(p["weight"] for p in weights) - 1.0) < 1e-6


def test_translate_phase_weights_sum_to_one():
    weights = WORKFLOW_PHASES["translate"]
    assert abs(sum(p["weight"] for p in weights) - 1.0) < 1e-6


def test_initial_overall_fraction_is_zero():
    t = EtaTracker(workflow="subtitles")
    assert t.overall_fraction() == 0.0


def test_overall_fraction_advances_with_phases():
    t = EtaTracker(workflow="subtitles")
    t.start_phase("Preparing")
    t.complete_phase("Preparing")
    t.start_phase("Reading video")
    t.complete_phase("Reading video")
    # 5% + 5% = 10% completed before transcription begins.
    assert 0.09 <= t.overall_fraction() <= 0.11


def test_cold_start_returns_estimate_with_tilde():
    t = EtaTracker(workflow="subtitles")
    t.set_input_size(60.0)  # 60 audio-seconds
    t.start_phase("Transcribing")
    s = t.current_eta_string()
    assert s.startswith("~"), s


def test_ema_smoothing_rejects_spikes(monkeypatch):
    times = iter([1000.0, 1001.0, 1002.0, 1003.0, 1004.0, 1005.0])
    monkeypatch.setattr("modules.eta_tracker.time.monotonic", lambda: next(times))

    t = EtaTracker(workflow="subtitles")
    t.set_input_size(100.0)
    t.start_phase("Transcribing")          # t=1000
    t.update_position(10.0, 100.0)         # t=1001 — 10 a-s in 1 wall-s
    sample_a = t.current_phase_throughput()
    t.update_position(11.0, 100.0)         # t=1002 — almost-zero progress, would spike a non-EMA estimate
    sample_b = t.current_phase_throughput()
    # EMA must move less than 60% between consecutive samples even on adverse input.
    assert abs(sample_b - sample_a) / sample_a < 0.6


def test_complete_phase_marks_progress_full_for_that_share():
    t = EtaTracker(workflow="subtitles")
    t.start_phase("Preparing")
    t.complete_phase("Preparing")
    # After preparing, overall fraction = 0.05 (its weight).
    assert abs(t.overall_fraction() - 0.05) < 1e-6


def test_format_seconds_short():
    from modules.eta_tracker import format_remaining
    assert format_remaining(45) == "45s"
    assert format_remaining(70) == "1m 10s"
    assert format_remaining(3725) == "1h 2m"
    assert format_remaining(0) == "0s"
```

- [ ] **Step 2.2: Run tests to verify they fail**

Run: `pytest tests/test_eta_tracker.py -v`
Expected: ImportError on `modules.eta_tracker`.

- [ ] **Step 2.3: Implement `modules/eta_tracker.py`**

Create the file:

```python
"""Phase-weighted, EMA-smoothed time-remaining estimator.

Replaces the old ad-hoc ThroughputTracker. Always returns a value — the
cold-start fallback uses the calibrated default for the current phase
prefixed with '~' so the live status line never shows '--:--:--'.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Optional


WORKFLOW_PHASES = {
    "subtitles": [
        {"name": "Preparing",     "weight": 0.05, "default_per_unit": 0.05},
        {"name": "Reading video", "weight": 0.05, "default_per_unit": 0.02},
        {"name": "Transcribing",  "weight": 0.70, "default_per_unit": 0.30},
        {"name": "Translating",   "weight": 0.18, "default_per_unit": 0.05},
        {"name": "Saving",        "weight": 0.02, "default_per_unit": 0.01},
    ],
    "notes": [
        {"name": "Reading transcript", "weight": 0.05, "default_per_unit": 0.0001},
        {"name": "Summarizing",        "weight": 0.90, "default_per_unit": 0.002},
        {"name": "Formatting",         "weight": 0.05, "default_per_unit": 0.0001},
    ],
    "translate": [
        {"name": "Reading file",       "weight": 0.05, "default_per_unit": 0.0001},
        {"name": "Detecting language", "weight": 0.05, "default_per_unit": 0.0001},
        {"name": "Translating",        "weight": 0.85, "default_per_unit": 0.0015},
        {"name": "Formatting output",  "weight": 0.05, "default_per_unit": 0.0001},
    ],
}


def format_remaining(seconds: float) -> str:
    seconds = max(0, int(seconds))
    if seconds < 60:
        return f"{seconds}s"
    if seconds < 3600:
        return f"{seconds // 60}m {seconds % 60}s"
    h = seconds // 3600
    m = (seconds % 3600) // 60
    return f"{h}h {m}m"


@dataclass
class _PhaseRun:
    name: str
    weight: float
    default_per_unit: float
    started_at: float
    position: float = 0.0
    total: float = 0.0
    throughput_ema: Optional[float] = None  # units of work per wall second
    completed: bool = False


class EtaTracker:
    """Track progress and time-remaining across a workflow's phases."""

    EMA_ALPHA = 0.3

    def __init__(self, workflow: str):
        if workflow not in WORKFLOW_PHASES:
            raise KeyError(f"Unknown workflow: {workflow!r}")
        self.workflow = workflow
        self._phases = {p["name"]: dict(p) for p in WORKFLOW_PHASES[workflow]}
        self._order = [p["name"] for p in WORKFLOW_PHASES[workflow]]
        self._runs: dict[str, _PhaseRun] = {}
        self._active: Optional[str] = None
        self._input_size: float = 0.0

    # ── input ────────────────────────────────────────────────────────────
    def set_input_size(self, size: float) -> None:
        """Size unit depends on workflow — audio seconds (subtitles), char count (notes/translate)."""
        self._input_size = max(0.0, size)

    def start_phase(self, name: str) -> None:
        spec = self._phases.get(name)
        if not spec:
            return
        self._active = name
        self._runs[name] = _PhaseRun(
            name=name,
            weight=spec["weight"],
            default_per_unit=spec["default_per_unit"],
            started_at=time.monotonic(),
        )

    def update_position(self, position: float, total: float) -> None:
        run = self._runs.get(self._active or "")
        if not run or total <= 0:
            return
        elapsed = max(1e-6, time.monotonic() - run.started_at)
        run.position = position
        run.total = total
        sample = position / elapsed  # units per wall second
        if run.throughput_ema is None:
            run.throughput_ema = sample
        else:
            run.throughput_ema = (
                self.EMA_ALPHA * sample + (1 - self.EMA_ALPHA) * run.throughput_ema
            )

    def complete_phase(self, name: str) -> None:
        run = self._runs.get(name)
        if run:
            run.completed = True
            run.position = run.total or run.position
        if self._active == name:
            self._active = None

    # ── outputs ──────────────────────────────────────────────────────────
    def current_phase_throughput(self) -> float:
        run = self._runs.get(self._active or "")
        return run.throughput_ema if run and run.throughput_ema else 0.0

    def overall_fraction(self) -> float:
        total = 0.0
        for name in self._order:
            spec = self._phases[name]
            run = self._runs.get(name)
            if not run:
                continue
            if run.completed:
                total += spec["weight"]
            elif run.total > 0:
                total += spec["weight"] * (run.position / run.total)
        return min(1.0, total)

    def current_eta_string(self) -> str:
        active = self._active
        if not active:
            return "—"
        run = self._runs[active]
        cold_start = (
            run.throughput_ema is None
            or run.total <= 0
            or (time.monotonic() - run.started_at) < 2.0
        )
        if cold_start:
            est = self._default_total_seconds_from(active)
            return f"~{format_remaining(est)} left"
        # Measured: time left in active phase + sum of remaining-phase defaults.
        remaining_in_phase_units = max(0.0, run.total - run.position)
        phase_eta = remaining_in_phase_units / max(1e-6, run.throughput_ema)
        rest = self._default_total_seconds_from_after(active)
        return f"{format_remaining(phase_eta + rest)} left"

    # ── helpers ──────────────────────────────────────────────────────────
    def _default_total_seconds_from(self, from_phase: str) -> float:
        """Calibrated estimate for from_phase plus all later phases, scaled by input size."""
        scale = max(1.0, self._input_size)
        idx = self._order.index(from_phase)
        return sum(self._phases[n]["default_per_unit"] * scale for n in self._order[idx:])

    def _default_total_seconds_from_after(self, after_phase: str) -> float:
        scale = max(1.0, self._input_size)
        idx = self._order.index(after_phase) + 1
        return sum(self._phases[n]["default_per_unit"] * scale for n in self._order[idx:])
```

- [ ] **Step 2.4: Run tests to verify they pass**

Run: `pytest tests/test_eta_tracker.py -v`
Expected: 9 passed.

- [ ] **Step 2.5: Commit**

```bash
git add modules/eta_tracker.py tests/test_eta_tracker.py
git commit -m "feat(eta): phase-weighted EMA-smoothed time-remaining tracker"
```

---

## Task 3 — PhaseStrip widget

**Files:**
- Create: `modules/phase_strip.py`
- Create: `tests/test_phase_strip.py`

- [ ] **Step 3.1: Write the failing tests**

Create `tests/test_phase_strip.py`:

```python
import pytest
from PySide6.QtWidgets import QApplication

from modules.phase_strip import PhaseStrip


@pytest.fixture(scope="module")
def app():
    return QApplication.instance() or QApplication([])


def test_set_phases_creates_dots(app):
    strip = PhaseStrip()
    strip.set_phases(["A", "B", "C"])
    assert strip.dot_count() == 3


def test_set_active_marks_one_phase(app):
    strip = PhaseStrip()
    strip.set_phases(["A", "B", "C"])
    strip.set_active("B")
    assert strip.active_phase() == "B"


def test_mark_done_advances_state(app):
    strip = PhaseStrip()
    strip.set_phases(["A", "B"])
    strip.mark_done("A")
    assert strip.state_of("A") == "done"


def test_unknown_phase_is_ignored(app):
    strip = PhaseStrip()
    strip.set_phases(["A"])
    strip.set_active("Z")  # must not raise
    strip.mark_done("Z")   # must not raise
    assert strip.active_phase() is None


def test_set_accent_color_repaints(app):
    strip = PhaseStrip()
    strip.set_phases(["A"])
    strip.set_active("A")
    strip.set_accent_color("#b8823a")  # must not raise
```

- [ ] **Step 3.2: Run tests to verify they fail**

Run: `pytest tests/test_phase_strip.py -v`
Expected: ImportError on `modules.phase_strip`.

- [ ] **Step 3.3: Implement `modules/phase_strip.py`**

```python
"""Horizontal phase indicator: dots + connecting line + active label."""
from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout, QWidget


_DOT_PENDING = "#3a3a3e"
_DOT_DONE_BG = "#2a3a2e"
_DOT_ERROR   = "#ff6b6b"


class _Dot(QLabel):
    SIZE = 10

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setFixedSize(self.SIZE, self.SIZE)
        self._state = "pending"
        self._accent = "#b8823a"
        self._apply()

    def set_state(self, state: str) -> None:
        self._state = state
        self._apply()

    def state(self) -> str:
        return self._state

    def set_accent(self, color: str) -> None:
        self._accent = color
        self._apply()

    def _apply(self) -> None:
        if self._state == "active":
            color = self._accent
        elif self._state == "done":
            color = _DOT_DONE_BG
        elif self._state == "error":
            color = _DOT_ERROR
        else:
            color = _DOT_PENDING
        self.setStyleSheet(
            f"background:{color}; border-radius:{self.SIZE // 2}px;"
        )


class PhaseStrip(QFrame):
    """Render a sequence of phases as dots with a connecting line and active label."""

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setObjectName("phaseStrip")
        self._phases: list[str] = []
        self._dots: dict[str, _Dot] = {}
        self._active: Optional[str] = None
        self._accent: str = "#b8823a"

        outer = QVBoxLayout(self)
        outer.setContentsMargins(2, 4, 2, 4)
        outer.setSpacing(4)

        self._dot_row = QFrame()
        self._dot_row_layout = QHBoxLayout(self._dot_row)
        self._dot_row_layout.setContentsMargins(0, 0, 0, 0)
        self._dot_row_layout.setSpacing(8)
        outer.addWidget(self._dot_row)

        self._label = QLabel("")
        self._label.setObjectName("phaseLabel")
        self._label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        outer.addWidget(self._label)

    # ── public API ───────────────────────────────────────────────────────
    def set_phases(self, names: list[str]) -> None:
        while self._dot_row_layout.count():
            item = self._dot_row_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._phases = list(names)
        self._dots.clear()
        for n in self._phases:
            d = _Dot()
            d.set_accent(self._accent)
            self._dots[n] = d
            self._dot_row_layout.addWidget(d)
        self._dot_row_layout.addStretch(1)
        self._active = None
        self._label.setText("")

    def set_active(self, name: str) -> None:
        if name not in self._dots:
            return
        self._active = name
        for n, dot in self._dots.items():
            if dot.state() in ("done", "error"):
                continue
            dot.set_state("active" if n == name else "pending")
        self._label.setText(name)

    def mark_done(self, name: str) -> None:
        dot = self._dots.get(name)
        if not dot:
            return
        dot.set_state("done")
        if self._active == name:
            self._active = None

    def mark_error(self, name: str) -> None:
        dot = self._dots.get(name)
        if not dot:
            return
        dot.set_state("error")
        if self._active == name:
            self._active = None

    def reset(self) -> None:
        for dot in self._dots.values():
            dot.set_state("pending")
        self._active = None
        self._label.setText("")

    def set_accent_color(self, color: str) -> None:
        self._accent = color
        for dot in self._dots.values():
            dot.set_accent(color)

    # ── introspection (used by tests) ────────────────────────────────────
    def dot_count(self) -> int:
        return len(self._dots)

    def active_phase(self) -> Optional[str]:
        return self._active

    def state_of(self, name: str) -> Optional[str]:
        d = self._dots.get(name)
        return d.state() if d else None
```

- [ ] **Step 3.4: Run tests to verify they pass**

Run: `pytest tests/test_phase_strip.py -v`
Expected: 5 passed.

- [ ] **Step 3.5: Commit**

```bash
git add modules/phase_strip.py tests/test_phase_strip.py
git commit -m "feat(ui): PhaseStrip widget for user-facing phase indication"
```

---

## Task 4 — Stripe widget (title-bar palette band)

**Files:**
- Create: `modules/stripe_widget.py`
- Create: `tests/test_stripe_widget.py`

- [ ] **Step 4.1: Write the failing tests**

Create `tests/test_stripe_widget.py`:

```python
import pytest
from PySide6.QtWidgets import QApplication

from modules.stripe_widget import StripeWidget


@pytest.fixture(scope="module")
def app():
    return QApplication.instance() or QApplication([])


def test_default_palette_is_atari(app):
    s = StripeWidget()
    assert s.palette_id() == "atari"


def test_set_palette_updates_id(app):
    s = StripeWidget()
    s.set_palette("crt")
    assert s.palette_id() == "crt"


def test_unknown_palette_is_ignored(app):
    s = StripeWidget()
    s.set_palette("solarized")
    assert s.palette_id() == "atari"


def test_band_count_matches_palette(app):
    s = StripeWidget()
    s.set_palette("rainbow")  # 6 bands
    assert s.band_count() == 6
    s.set_palette("atari")    # 4 bands
    assert s.band_count() == 4
```

- [ ] **Step 4.2: Run tests to verify they fail**

Run: `pytest tests/test_stripe_widget.py -v`
Expected: ImportError on `modules.stripe_widget`.

- [ ] **Step 4.3: Implement `modules/stripe_widget.py`**

```python
"""Title-bar palette stripe — a 3px horizontal band row that paints the active palette."""
from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPainter
from PySide6.QtWidgets import QFrame, QWidget

from modules.theme_tokens import PALETTES, DEFAULT_PALETTE


class StripeWidget(QFrame):
    HEIGHT = 3

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setObjectName("paletteStripe")
        self.setFixedHeight(self.HEIGHT)
        self._palette_id = DEFAULT_PALETTE
        self._bands: list[str] = list(PALETTES[DEFAULT_PALETTE]["stripe"])

    def set_palette(self, palette_id: str) -> None:
        if palette_id not in PALETTES:
            return
        self._palette_id = palette_id
        self._bands = list(PALETTES[palette_id]["stripe"])
        self.update()

    def palette_id(self) -> str:
        return self._palette_id

    def band_count(self) -> int:
        return len(self._bands)

    def paintEvent(self, event):
        if not self._bands:
            return
        painter = QPainter(self)
        w = self.width()
        h = self.height()
        n = len(self._bands)
        # Integer band widths to avoid sub-pixel gaps.
        widths = [w // n] * n
        for i in range(w - sum(widths)):
            widths[i] += 1
        x = 0
        for i, color in enumerate(self._bands):
            painter.fillRect(x, 0, widths[i], h, QColor(color))
            x += widths[i]
        painter.end()
```

- [ ] **Step 4.4: Run tests to verify they pass**

Run: `pytest tests/test_stripe_widget.py -v`
Expected: 4 passed.

- [ ] **Step 4.5: Commit**

```bash
git add modules/stripe_widget.py tests/test_stripe_widget.py
git commit -m "feat(ui): StripeWidget renders the palette identity band row"
```

---

## Task 5 — Palette dropdown menu

**Files:**
- Create: `modules/palette_menu.py`
- Create: `tests/test_palette_menu.py`

- [ ] **Step 5.1: Write the failing tests**

Create `tests/test_palette_menu.py`:

```python
import pytest
from PySide6.QtWidgets import QApplication, QWidget

from modules.palette_menu import PaletteMenuButton


@pytest.fixture(scope="module")
def app():
    return QApplication.instance() or QApplication([])


def test_default_selection_is_atari(app):
    parent = QWidget()
    btn = PaletteMenuButton(parent)
    assert btn.current_palette() == "atari"


def test_select_palette_emits_signal(app, qtbot=None):
    parent = QWidget()
    btn = PaletteMenuButton(parent)
    received = []
    btn.palette_selected.connect(received.append)
    btn.select("crt")
    assert btn.current_palette() == "crt"
    assert received == ["crt"]


def test_select_unknown_palette_ignored(app):
    parent = QWidget()
    btn = PaletteMenuButton(parent)
    btn.select("solarized")
    assert btn.current_palette() == "atari"


def test_button_label_reflects_palette(app):
    parent = QWidget()
    btn = PaletteMenuButton(parent)
    btn.select("famicom")
    assert "Famicom" in btn.text()
```

- [ ] **Step 5.2: Run tests to verify they fail**

Run: `pytest tests/test_palette_menu.py -v`
Expected: ImportError on `modules.palette_menu`.

- [ ] **Step 5.3: Implement `modules/palette_menu.py`**

```python
"""Title-bar palette dropdown.

A QPushButton that opens a QMenu with one row per palette. Each row has a
small stripe preview, the palette name, and a checkmark on the active row.
Selection emits palette_selected(str).
"""
from __future__ import annotations

from typing import Optional

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtGui import QAction, QActionGroup, QColor, QIcon, QPainter, QPixmap
from PySide6.QtWidgets import QMenu, QPushButton, QWidget

from modules.theme_tokens import PALETTES, DEFAULT_PALETTE


def _stripe_icon(palette_id: str) -> QIcon:
    bands = PALETTES[palette_id]["stripe"]
    pix = QPixmap(QSize(32, 12))
    pix.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pix)
    n = len(bands)
    w = pix.width() // n
    extra = pix.width() - w * n
    x = 0
    for i, color in enumerate(bands):
        bw = w + (1 if i < extra else 0)
        painter.fillRect(x, 0, bw, pix.height(), QColor(color))
        x += bw
    painter.end()
    return QIcon(pix)


class PaletteMenuButton(QPushButton):
    palette_selected = Signal(str)

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setObjectName("paletteMenuButton")
        self._current = DEFAULT_PALETTE
        self._actions: dict[str, QAction] = {}

        menu = QMenu(self)
        group = QActionGroup(self)
        group.setExclusive(True)
        for pid, p in PALETTES.items():
            act = QAction(_stripe_icon(pid), p["name"], self)
            act.setCheckable(True)
            act.triggered.connect(lambda _checked=False, _pid=pid: self.select(_pid))
            group.addAction(act)
            menu.addAction(act)
            self._actions[pid] = act

        self.setMenu(menu)
        self._refresh()

    def select(self, palette_id: str) -> None:
        if palette_id not in PALETTES:
            return
        self._current = palette_id
        self._refresh()
        self.palette_selected.emit(palette_id)

    def current_palette(self) -> str:
        return self._current

    def _refresh(self) -> None:
        for pid, act in self._actions.items():
            act.setChecked(pid == self._current)
        self.setText(PALETTES[self._current]["name"])
        self.setIcon(_stripe_icon(self._current))
```

- [ ] **Step 5.4: Run tests to verify they pass**

Run: `pytest tests/test_palette_menu.py -v`
Expected: 4 passed.

- [ ] **Step 5.5: Commit**

```bash
git add modules/palette_menu.py tests/test_palette_menu.py
git commit -m "feat(ui): PaletteMenuButton dropdown for palette switching"
```

---

## Task 6 — Mascot extensions: `set_phase`, `set_idle`, PNG fallback

**Files:**
- Modify: `modules/mascot.py`
- Modify: `tests/test_mascot.py`
- Create: `icons/mascot/README.txt`

- [ ] **Step 6.1: Add the asset folder marker**

Create `icons/mascot/README.txt`:

```
Mascot asset folder.

Expected GIF/PNG pairs (PNG fallback used when GIF is missing or when
View → Reduce Motion is off):

  idle_subtitles.gif  /  idle_subtitles.png
  idle_notes.gif      /  idle_notes.png
  idle_translate.gif  /  idle_translate.png
  preparing.gif       /  preparing.png
  extracting.gif      /  extracting.png
  transcribing.gif    /  transcribing.png
  translating.gif     /  translating.png
  saving.gif          /  saving.png
  done.gif            /  done.png

If neither file is present for a given key, the mascot widget falls back
to the legacy `icons/start.gif` / `icons/done.jpg` so the UI never breaks.
```

- [ ] **Step 6.2: Write the failing tests**

Replace the body of `tests/test_mascot.py` with the existing test imports plus these new tests (keep any existing tests; append):

```python
# Append at end of tests/test_mascot.py

from modules.mascot import MascotWidget


def test_set_phase_known_phases(app, tmp_path, monkeypatch):
    # Point icons_root at an empty directory so resolution falls back.
    w = MascotWidget(icons_root=str(tmp_path))
    for phase in ("Preparing", "Reading video", "Transcribing", "Translating", "Saving"):
        w.set_phase(phase)  # must not raise
    assert w.state in {"working", "thinking"}


def test_set_phase_unknown_is_noop(app, tmp_path):
    w = MascotWidget(icons_root=str(tmp_path))
    before = w.state
    w.set_phase("Nonexistent Phase")
    assert w.state == before


def test_set_idle_workflow(app, tmp_path):
    w = MascotWidget(icons_root=str(tmp_path))
    w.set_idle("subtitles")
    assert w.state == "idle"


def test_png_fallback_when_gif_missing(app, tmp_path):
    # Create only a PNG, no GIF; resolver must pick the PNG.
    mascot_dir = tmp_path / "mascot"
    mascot_dir.mkdir()
    (mascot_dir / "transcribing.png").write_bytes(b"\x89PNG\r\n\x1a\n")  # minimal magic bytes
    w = MascotWidget(icons_root=str(tmp_path))
    path = w._resolve_asset("transcribing")
    assert path is not None
    assert path.endswith(".png")
```

If `tests/test_mascot.py` does not already define an `app` fixture, add at the top of the file (after imports):

```python
import pytest
from PySide6.QtWidgets import QApplication

@pytest.fixture(scope="module")
def app():
    return QApplication.instance() or QApplication([])
```

- [ ] **Step 6.3: Run tests to verify they fail**

Run: `pytest tests/test_mascot.py -v`
Expected: AttributeError or NameError on `set_phase` / `set_idle` / `_resolve_asset`.

- [ ] **Step 6.4: Extend `modules/mascot.py`**

Add to the top of the file, after the existing `FALLBACKS` dict:

```python
PHASE_TO_ASSET = {
    "Preparing":     "preparing",
    "Reading video": "extracting",
    "Transcribing":  "transcribing",
    "Translating":   "translating",
    "Saving":        "saving",
    # Notes
    "Reading transcript": "transcribing",
    "Summarizing":        "transcribing",
    "Formatting":         "saving",
    # Translate File
    "Reading file":       "transcribing",
    "Detecting language": "transcribing",
    "Formatting output":  "saving",
}

IDLE_FOR_WORKFLOW = {
    "subtitles": "idle_subtitles",
    "notes":     "idle_notes",
    "translate": "idle_translate",
}
```

Then add these methods inside `MascotWidget` (alongside `set_state`):

```python
    def set_phase(self, phase: str) -> None:
        asset = PHASE_TO_ASSET.get(phase)
        if not asset:
            return
        # Prefer phase-specific asset; fall back to "working" QMovie chain.
        path = self._resolve_asset(asset)
        if path:
            self._show_path(path, state_name="working")
        else:
            self.set_state("working")

    def set_idle(self, workflow: str) -> None:
        asset = IDLE_FOR_WORKFLOW.get(workflow)
        if not asset:
            self.set_state("idle")
            return
        path = self._resolve_asset(asset)
        if path:
            self._show_path(path, state_name="idle")
        else:
            self.set_state("idle")

    def _resolve_asset(self, asset_key: str) -> Optional[str]:
        """Look for `<icons_root>/mascot/<asset_key>.gif`, then `.png`, else None."""
        for ext in (".gif", ".png"):
            p = os.path.join(self._icons_root, "mascot", f"{asset_key}{ext}")
            if os.path.exists(p):
                return p
        return None

    def _show_path(self, path: str, *, state_name: str) -> None:
        self.state = state_name
        if path.lower().endswith(".gif"):
            mv = QMovie(path)
            mv.setScaledSize(QSize(130, 130))
            self.setMovie(mv)
            mv.start()
            self._movie = mv
        else:
            pm = QPixmap(path).scaled(
                130, 130,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            self.setPixmap(pm)
        self._idle_timer.start(60_000)
```

- [ ] **Step 6.5: Run tests to verify they pass**

Run: `pytest tests/test_mascot.py -v`
Expected: all passed.

- [ ] **Step 6.6: Commit**

```bash
git add modules/mascot.py tests/test_mascot.py icons/mascot/README.txt
git commit -m "feat(mascot): set_phase/set_idle with GIF→PNG fallback"
```

---

## Task 7 — Toast: `success_with_doge`

**Files:**
- Modify: `modules/toast.py`
- Modify: `tests/test_toast.py`

- [ ] **Step 7.1: Write the failing test**

Append to `tests/test_toast.py`:

```python
from modules.toast import success_with_doge

def test_success_with_doge_returns_toast(app):
    parent = QWidget()
    parent.resize(400, 300)
    t = success_with_doge(parent, "Done", filename="output.srt")
    assert t.text().startswith("Done")
    assert "output.srt" in t.text()
```

If the file does not yet import `QWidget` and the `app` fixture, add the same `app` fixture pattern from Task 6.

- [ ] **Step 7.2: Run tests to verify they fail**

Run: `pytest tests/test_toast.py -v`
Expected: ImportError on `success_with_doge`.

- [ ] **Step 7.3: Add the factory to `modules/toast.py`**

Append at the bottom of the file:

```python
def success_with_doge(parent: QWidget, message: str, *, filename: str = "",
                      duration_ms: int = 4000) -> "Toast":
    """Build a success toast that mentions a filename. Doge-flavored copy
    is gated by QSettings 'view/dogeTips' (default True)."""
    from PySide6.QtCore import QSettings
    tips = QSettings("DogeAutoSub", "ui").value("view/dogeTips", True, type=bool)
    if filename:
        body = f"{message} · {filename}" if not tips else f"{message} · {filename} · such done"
    else:
        body = message if not tips else f"{message} · much wow"
    return Toast(parent, body, kind="success", duration_ms=duration_ms)
```

- [ ] **Step 7.4: Run tests to verify they pass**

Run: `pytest tests/test_toast.py -v`
Expected: all passed.

- [ ] **Step 7.5: Commit**

```bash
git add modules/toast.py tests/test_toast.py
git commit -m "feat(toast): success_with_doge factory respecting Doge Tips setting"
```

---

## Task 8 — `log_panel.py`: split timeline out, drop narrator from log

**Files:**
- Modify: `modules/log_panel.py`
- Modify: `tests/test_log_panel_logic.py`

- [ ] **Step 8.1: Write the failing test**

Replace the body of `tests/test_log_panel_logic.py` with:

```python
import pytest
from PySide6.QtWidgets import QApplication

from modules.log_panel import LogPanel, DogeNarrator


@pytest.fixture(scope="module")
def app():
    return QApplication.instance() or QApplication([])


def test_log_panel_does_not_route_narrator_to_console(app):
    panel = LogPanel()
    # Narrator is no longer wired to panel.log; calling notify_step_done
    # must not insert a 'doge' line into the console.
    panel._narrator.notify_step_done()
    panel._narrator.notify_step_done()
    panel._narrator.notify_step_done()
    text = panel.console.toPlainText()
    assert "such" not in text
    assert "wow" not in text
    assert "doge" not in text


def test_log_panel_collapsed_by_default(app):
    panel = LogPanel()
    assert panel._console_visible is False


def test_log_panel_set_filter_events(app):
    panel = LogPanel()
    panel.set_filter("events")
    assert panel.current_filter() == "events"
    panel.set_filter("raw")
    assert panel.current_filter() == "raw"


def test_log_panel_filter_hides_per_segment_chatter(app):
    panel = LogPanel()
    panel.set_filter("events")
    panel.log("info", "chunk 3 of 12")  # per-segment chatter — events filter should drop it
    panel.log("error", "translation API failure")  # error — should always appear
    text = panel.console.toPlainText()
    assert "translation API failure" in text
    assert "chunk 3 of 12" not in text


def test_doge_narrator_emits_via_callback_only(app):
    # The narrator still calls on_event when its consumer wires it; the
    # log panel just no longer subscribes by default.
    received = []
    n = DogeNarrator(every_n=1, enabled=True, seed=0)
    n.on_event = lambda lvl, msg: received.append((lvl, msg))
    n.notify_step_done()
    assert received and received[0][0] == "doge"
```

- [ ] **Step 8.2: Run tests to verify they fail**

Run: `pytest tests/test_log_panel_logic.py -v`
Expected: failures on `_console_visible is False`, `set_filter`, and the assertion that narrator output is absent from the console.

- [ ] **Step 8.3: Edit `modules/log_panel.py`**

In `LogPanel.__init__`, replace the narrator hook-up lines:

```python
        self._narrator = narrator or DogeNarrator()
        self._narrator.on_event = lambda lvl, msg: self.log(lvl, msg)
```

with:

```python
        # Narrator output is now routed externally (mascot/toast). The log
        # panel never subscribes to it — keeps diagnostic output clean.
        self._narrator = narrator or DogeNarrator()
```

In the same `__init__`, change the default for `console_open`:

```python
        if settings.value("log/console_open", True, type=bool) is False:
            self.toggle_console()
```

to:

```python
        # Default closed. Open only if user previously expanded it.
        self._console_visible = True  # set true so toggle flips to false
        self.toggle_console()
        if settings.value("log/console_open", False, type=bool) is True:
            self.toggle_console()
```

Below the existing `clear()` method, add filter support:

```python
    # ── Filter ─────────────────────────────────────────────────────────
    _PER_SEGMENT_TOKENS = ("chunk ", "segment ", "page ")

    def __post_init_filter(self):
        # Called from __init__ at the end; ensures default state.
        self._filter = "events"

    def set_filter(self, kind: str) -> None:
        if kind not in ("events", "raw"):
            return
        self._filter = kind

    def current_filter(self) -> str:
        return getattr(self, "_filter", "events")

    def _passes_filter(self, level: str, text: str) -> bool:
        if self.current_filter() == "raw":
            return True
        # Events filter: keep warn/error always; drop per-segment chatter.
        if level in ("warn", "error"):
            return True
        lowered = text.lower()
        return not any(tok in lowered for tok in self._PER_SEGMENT_TOKENS)
```

At the end of `__init__`, add:

```python
        self.__post_init_filter()
```

In the existing `log()` method, gate the console insert behind the filter:

```python
    def log(self, level: str, text: str) -> None:
        ts = time.strftime("%H:%M:%S")
        # Always persist to disk (raw stream).
        if self._log_writer:
            try:
                self._log_writer.write(level, text)
            except Exception:
                pass
        # Console respects the active filter.
        if self._passes_filter(level, text):
            color = LEVEL_COLORS.get(level, "#cccccc")
            fmt = QTextCharFormat()
            fmt.setForeground(QColor(color))
            cursor = self.console.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.End)
            cursor.insertText(f"[{ts}] {text}\n", fmt)
            self.console.setTextCursor(cursor)
            self.console.ensureCursorVisible()
        self._emit("log", level=level, text=text)
```

(Replace the original `log()` body — the order of writer + filter + emit changes.)

- [ ] **Step 8.4: Run tests to verify they pass**

Run: `pytest tests/test_log_panel_logic.py -v`
Expected: all passed.

- [ ] **Step 8.5: Commit**

```bash
git add modules/log_panel.py tests/test_log_panel_logic.py
git commit -m "refactor(log): drop narrator from console, add events/raw filter, default collapsed"
```

---

## Task 9 — Rebuild `ui_DogeAutoSub.py` as sidebar layout

This is the largest task. The widget tree changes shape entirely; **every widget keeps its existing object name and signal**. Worker threads and the bulk of `AutoUI.py` continue to work without changes.

**Files:**
- Modify: `modules/ui_DogeAutoSub.py`
- Modify: `tests/test_ui_imports.py`

- [ ] **Step 9.1: Inventory the existing widget object names that must survive**

Run: `grep -nE 'setObjectName|self\.[a-zA-Z_]+ = Q' modules/ui_DogeAutoSub.py | head -100`

Read the output and list every widget name. This is your contract — the rewrite must instantiate each of these widgets (some will be hidden in the new layout, but they must exist) so that `AutoUI.py` references like `self.startButton`, `self.progressBar`, `self.statusLabel`, `self.etaLabel`, `self.filePathLabel`, `self.source_language_dropdown`, `self.target_language_dropdown`, `self.target_engine`, `self.boostSlider`, `self.boostLabel`, `self.bearerTokenEdit`, `self.getTokenBtn`, `self.tabWidget`, `self.themeBtn`, `self.openFolderBtn`, `self.menuItems[...]` all continue to resolve.

- [ ] **Step 9.2: Write/extend the import test**

Append to `tests/test_ui_imports.py`:

```python
def test_required_widgets_present_after_setupUi(app):
    from PySide6.QtWidgets import QMainWindow
    from modules.ui_DogeAutoSub import Ui_MainWindow
    win = QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(win)

    required = [
        "startButton", "progressBar", "statusLabel", "etaLabel",
        "filePathLabel", "source_language_dropdown", "target_language_dropdown",
        "target_engine", "boostSlider", "boostLabel",
        "bearerTokenEdit", "getTokenBtn",
        "themeBtn", "openFolderBtn",
        "selectFileBtn", "selectOutputBtn",
        "model_size_dropdown",
        # New widgets
        "sidebar", "sidebarSubtitlesItem", "sidebarNotesItem", "sidebarTranslateItem",
        "phaseStrip", "paletteMenuButton", "paletteStripe",
        "workflowStack", "statusBar", "logPanelHost", "mascotHost",
    ]
    missing = [n for n in required if not hasattr(ui, n)]
    assert not missing, f"missing widgets: {missing}"
```

If the file lacks an `app` fixture, add one (same pattern as Task 6).

- [ ] **Step 9.3: Run tests to verify they fail**

Run: `pytest tests/test_ui_imports.py -v`
Expected: failure listing the new widgets that don't exist yet.

- [ ] **Step 9.4: Rewrite `modules/ui_DogeAutoSub.py`**

Replace the file with the new sidebar layout. The implementation is long; structure it as:

```python
# -*- coding: utf-8 -*-
"""DogeAutoSub — dark macOS sidebar UI.

Every existing widget object name is preserved so AutoUI.py and the
worker threads do not need to be rewired. Tabs are gone; the workflow
selection is driven by the sidebar via a QStackedWidget.
"""
from PySide6.QtCore import QSize, Qt, QPoint
from PySide6.QtGui import QFont, QMouseEvent
from PySide6.QtWidgets import (
    QComboBox, QFrame, QGridLayout, QHBoxLayout, QLabel,
    QLineEdit, QMainWindow, QProgressBar, QPushButton,
    QSlider, QStackedWidget, QTabWidget, QTextEdit,
    QVBoxLayout, QWidget,
)

from modules.phase_strip import PhaseStrip
from modules.stripe_widget import StripeWidget
from modules.palette_menu import PaletteMenuButton


class Ui_MainWindow(object):

    # ── Helpers ──────────────────────────────────────────────────────────
    def _label(self, text, *, small=False):
        lbl = QLabel(text)
        lbl.setFont(self.font_small if small else self.font_body)
        return lbl

    def _section_title(self, text):
        lbl = QLabel(text.upper())
        lbl.setObjectName("sectionTitle")
        return lbl

    def _card(self):
        f = QFrame()
        f.setObjectName("card")
        return f

    def _sidebar_section(self, text):
        lbl = QLabel(text)
        lbl.setObjectName("sidebarSectionLabel")
        return lbl

    def _sidebar_item(self, text, object_name):
        btn = QPushButton(text)
        btn.setObjectName("sidebarItem")
        btn.setProperty("data-name", object_name)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setProperty("active", "false")
        return btn

    # ── setupUi ──────────────────────────────────────────────────────────
    def setupUi(self, MainWindow: QMainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName("MainWindow")
        MainWindow.resize(900, 640)
        MainWindow.setMinimumSize(QSize(800, 580))
        MainWindow.setMaximumSize(QSize(1400, 1080))
        MainWindow.setWindowTitle("DogeAutoSub")
        MainWindow.setWindowFlag(Qt.WindowType.FramelessWindowHint, True)

        self.font_body = QFont(); self.font_body.setPointSize(10)
        self.font_small = QFont(); self.font_small.setPointSize(9)
        self.font_title = QFont(); self.font_title.setPointSize(11); self.font_title.setBold(True)

        # ── Central widget ───────────────────────────────────────────────
        self.centralWidget = QWidget(MainWindow)
        self.centralWidget.setObjectName("centralWidget")
        MainWindow.setCentralWidget(self.centralWidget)

        outer = QVBoxLayout(self.centralWidget)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # ── Title bar ────────────────────────────────────────────────────
        self.fauxTitleBar = QFrame()
        self.fauxTitleBar.setObjectName("fauxTitleBar")
        tb = QHBoxLayout(self.fauxTitleBar)
        tb.setContentsMargins(10, 0, 8, 0)
        tb.setSpacing(8)

        # Traffic lights (wired in AutoUI.py)
        for name, color in (("closeBtn", "#ff5f57"), ("minBtn", "#febc2e"), ("zoomBtn", "#28c840")):
            b = QPushButton()
            b.setObjectName(name)
            b.setFixedSize(12, 12)
            b.setStyleSheet(f"QPushButton#{name} {{ background:{color}; border-radius:6px; border:none; }}")
            tb.addWidget(b)
            setattr(self, name, b)

        tb.addSpacing(8)

        self.fauxTitleText = QLabel("DogeAutoSub")
        self.fauxTitleText.setObjectName("fauxTitleText")
        self.fauxTitleText.setAlignment(Qt.AlignmentFlag.AlignCenter)
        tb.addWidget(self.fauxTitleText, 1)

        # Palette dropdown (right side)
        self.paletteMenuButton = PaletteMenuButton(self.fauxTitleBar)
        self.paletteMenuButton.setObjectName("paletteMenuButton")
        self.paletteMenuButton.setFixedHeight(20)
        tb.addWidget(self.paletteMenuButton)

        # Legacy themeBtn / openFolderBtn — kept hidden so AutoUI signals don't break.
        self.themeBtn = QPushButton()
        self.themeBtn.setObjectName("themeBtn")
        self.themeBtn.setVisible(False)
        tb.addWidget(self.themeBtn)
        self.openFolderBtn = QPushButton()
        self.openFolderBtn.setObjectName("openFolderBtn")
        self.openFolderBtn.setVisible(False)
        tb.addWidget(self.openFolderBtn)

        # Legacy menu bar items — kept as hidden labels (AutoUI references self.menuItems).
        self.menuItems = {}
        for name in ("File", "Edit", "View", "Help"):
            lbl = QLabel(name)
            lbl.setObjectName("menuItem")
            lbl.setVisible(False)
            self.menuItems[name] = lbl

        outer.addWidget(self.fauxTitleBar)

        # ── Stripe ──────────────────────────────────────────────────────
        self.paletteStripe = StripeWidget(self.centralWidget)
        outer.addWidget(self.paletteStripe)

        # ── Body: sidebar + main ────────────────────────────────────────
        body = QFrame()
        bodyLay = QHBoxLayout(body)
        bodyLay.setContentsMargins(0, 0, 0, 0)
        bodyLay.setSpacing(0)
        outer.addWidget(body, 1)

        self.sidebar = QFrame()
        self.sidebar.setObjectName("sidebar")
        self.sidebar.setFixedWidth(180)
        sLay = QVBoxLayout(self.sidebar)
        sLay.setContentsMargins(8, 8, 8, 8)
        sLay.setSpacing(2)

        sLay.addWidget(self._sidebar_section("WORKFLOWS"))
        self.sidebarSubtitlesItem = self._sidebar_item("Subtitles",     "subtitles")
        self.sidebarNotesItem     = self._sidebar_item("Meeting Notes", "notes")
        self.sidebarTranslateItem = self._sidebar_item("Translate File", "translate")
        sLay.addWidget(self.sidebarSubtitlesItem)
        sLay.addWidget(self.sidebarNotesItem)
        sLay.addWidget(self.sidebarTranslateItem)

        sLay.addWidget(self._sidebar_section("RECENT"))
        self.recentList = QFrame()
        self.recentListLayout = QVBoxLayout(self.recentList)
        self.recentListLayout.setContentsMargins(0, 0, 0, 0)
        self.recentListLayout.setSpacing(2)
        sLay.addWidget(self.recentList)

        sLay.addStretch(1)
        bodyLay.addWidget(self.sidebar)

        # ── Main: stacked workflows ─────────────────────────────────────
        self.workflowStack = QStackedWidget()
        self.workflowStack.setObjectName("workflowStack")
        bodyLay.addWidget(self.workflowStack, 1)

        # tabWidget kept for backward-compat references; not added to layout.
        self.tabWidget = QTabWidget()
        self.tabWidget.setObjectName("tabWidget")
        self.tabWidget.setVisible(False)

        self._build_subtitles_pane()
        self._build_notes_pane()
        self._build_translate_pane()

        # ── Status bar ───────────────────────────────────────────────────
        self.statusBar = QFrame()
        self.statusBar.setObjectName("statusBar")
        self.statusBar.setFixedHeight(22)
        sbLay = QHBoxLayout(self.statusBar)
        sbLay.setContentsMargins(10, 2, 10, 2)
        sbLay.setSpacing(10)
        self.statusBarVersion = QLabel("v—")
        self.statusBarGpu = QLabel("GPU: —")
        self.statusBarReady = QLabel("● Ready")
        for w in (self.statusBarVersion, self.statusBarGpu, self.statusBarReady):
            w.setStyleSheet("font-size:10px;")
        sbLay.addWidget(self.statusBarVersion)
        sbLay.addStretch(1)
        sbLay.addWidget(self.statusBarGpu)
        sbLay.addWidget(self.statusBarReady)
        outer.addWidget(self.statusBar)

        # Wire slider → label (existing behavior).
        self.boostSlider.valueChanged.connect(lambda v: self.boostLabel.setText(str(v)))

    # ── Pane builders (each returns a QWidget added to workflowStack) ────
    def _build_subtitles_pane(self):
        pane = QWidget()
        lay = QVBoxLayout(pane)
        lay.setContentsMargins(14, 14, 14, 14)
        lay.setSpacing(10)

        # File card
        fileCard = self._card()
        flay = QVBoxLayout(fileCard)
        flay.setContentsMargins(12, 10, 12, 10)
        flay.setSpacing(6)
        flay.addWidget(self._section_title("SOURCE"))
        btnRow = QHBoxLayout()
        self.selectFileBtn = QPushButton("Select Video File")
        self.selectFileBtn.setObjectName("selectFileBtn")
        btnRow.addWidget(self.selectFileBtn, 2)
        self.selectOutputBtn = QPushButton("Output Folder")
        self.selectOutputBtn.setObjectName("selectOutputBtn")
        btnRow.addWidget(self.selectOutputBtn, 1)
        flay.addLayout(btnRow)
        self.filePathLabel = QLabel("No file selected")
        self.filePathLabel.setObjectName("filePathLabel")
        self.filePathLabel.setWordWrap(True)
        flay.addWidget(self.filePathLabel)
        lay.addWidget(fileCard)
        self.fileCard = fileCard

        # Settings card
        settingsCard = self._card()
        slay = QVBoxLayout(settingsCard)
        slay.setContentsMargins(12, 10, 12, 10)
        slay.setSpacing(8)
        slay.addWidget(self._section_title("LANGUAGES"))

        self.model_size_dropdown = QComboBox()
        self.model_size_dropdown.setObjectName("modelDropdown")
        self.model_size_dropdown.setVisible(False)
        slay.addWidget(self.model_size_dropdown)

        self.VRamUsage = QLabel("");  self.VRamUsage.setVisible(False)
        self.rSpeed = QLabel("");     self.rSpeed.setVisible(False)

        langGrid = QGridLayout()
        langGrid.setHorizontalSpacing(10)
        langGrid.addWidget(self._label("Source"), 0, 0)
        self.source_language_dropdown = QComboBox()
        self.source_language_dropdown.setObjectName("srcLangDropdown")
        langGrid.addWidget(self.source_language_dropdown, 1, 0)
        langGrid.addWidget(self._label("Target"), 0, 1)
        self.target_language_dropdown = QComboBox()
        self.target_language_dropdown.setObjectName("tgtLangDropdown")
        langGrid.addWidget(self.target_language_dropdown, 1, 1)
        slay.addLayout(langGrid)

        slay.addWidget(self._section_title("ENGINE"))
        engGrid = QGridLayout()
        engGrid.setHorizontalSpacing(10)
        engGrid.addWidget(self._label("Translation Engine"), 0, 0)
        self.target_engine = QComboBox()
        self.target_engine.setObjectName("engineDropdown")
        engGrid.addWidget(self.target_engine, 1, 0)

        engGrid.addWidget(self._label("Volume Boost"), 0, 1)
        volRow = QHBoxLayout()
        self.boostSlider = QSlider(Qt.Orientation.Horizontal)
        self.boostSlider.setObjectName("boostSlider")
        self.boostSlider.setMinimum(1); self.boostSlider.setMaximum(10); self.boostSlider.setValue(3)
        volRow.addWidget(self.boostSlider)
        self.boostLabel = QLabel("3"); self.boostLabel.setMinimumWidth(20)
        volRow.addWidget(self.boostLabel)
        engGrid.addLayout(volRow, 1, 1)
        slay.addLayout(engGrid)

        # MLAAS sub-card
        mlaasFrame = self._card()
        mlay = QVBoxLayout(mlaasFrame)
        mlay.setContentsMargins(10, 8, 10, 8)
        mlay.setSpacing(4)
        mlaasTop = QHBoxLayout()
        mlaasTop.addWidget(self._section_title("MLAAS API"))
        self.mlaasStatusLabel = QLabel("Loading…")
        self.mlaasStatusLabel.setStyleSheet("color:#9a9a9f;")
        mlaasTop.addWidget(self.mlaasStatusLabel); mlaasTop.addStretch()
        mlay.addLayout(mlaasTop)
        bearerRow = QHBoxLayout()
        self.bearerTokenEdit = QLineEdit()
        self.bearerTokenEdit.setEchoMode(QLineEdit.EchoMode.Password)
        self.bearerTokenEdit.setPlaceholderText("Paste Bearer JWT token here (optional)…")
        bearerRow.addWidget(self.bearerTokenEdit, 1)
        self.getTokenBtn = QPushButton("Get Token"); self.getTokenBtn.setFixedWidth(96)
        bearerRow.addWidget(self.getTokenBtn)
        mlay.addLayout(bearerRow)
        slay.addWidget(mlaasFrame)
        lay.addWidget(settingsCard)
        self.settingsCard = settingsCard

        # Action card
        actionCard = self._card()
        alay = QVBoxLayout(actionCard)
        alay.setContentsMargins(12, 10, 12, 10)
        alay.setSpacing(8)
        self.startButton = QPushButton("Start Processing")
        self.startButton.setObjectName("startButton")
        alay.addWidget(self.startButton)

        self.phaseStrip = PhaseStrip()
        self.phaseStrip.setObjectName("phaseStrip")
        alay.addWidget(self.phaseStrip)

        self.progressBar = QProgressBar()
        self.progressBar.setObjectName("progressBar")
        self.progressBar.setValue(0); self.progressBar.setTextVisible(False)
        alay.addWidget(self.progressBar)

        statusRow = QHBoxLayout()
        self.statusLabel = QLabel("Standby")
        self.statusLabel.setObjectName("statusLabel")
        statusRow.addWidget(self.statusLabel)
        statusRow.addStretch()
        self.etaLabel = QLabel("")
        self.etaLabel.setObjectName("etaLabel")
        statusRow.addWidget(self.etaLabel)
        alay.addLayout(statusRow)

        # Log panel host (the LogPanel from log_panel.py is added by AutoUI)
        self.logPanelHost = QFrame()
        self.logPanelHost.setObjectName("logPanelHost")
        alay.addWidget(self.logPanelHost)
        lay.addWidget(actionCard)
        self.actionCard = actionCard

        lay.addStretch(1)
        self.subtitleTab = pane  # backward-compat reference name
        self.workflowStack.addWidget(pane)

    def _build_notes_pane(self):
        pane = QWidget()
        lay = QVBoxLayout(pane)
        lay.setContentsMargins(14, 14, 14, 14)
        lay.setSpacing(10)

        card = self._card()
        clay = QVBoxLayout(card)
        clay.setContentsMargins(12, 10, 12, 10)
        clay.addWidget(self._section_title("MEETING TRANSCRIPT"))
        self.uploadDocxBtn = QPushButton("Upload .docx Transcript")
        self.uploadDocxBtn.setObjectName("uploadDocxBtn")
        clay.addWidget(self.uploadDocxBtn)
        self.docxPathLabel = QLabel("No file selected")
        self.docxPathLabel.setObjectName("docxPathLabel")
        clay.addWidget(self.docxPathLabel)
        self.generateNotesBtn = QPushButton("Generate Meeting Notes")
        self.generateNotesBtn.setObjectName("generateNotesBtn")
        clay.addWidget(self.generateNotesBtn)
        self.notesOutput = QTextEdit()
        self.notesOutput.setObjectName("notesOutput")
        self.notesOutput.setMinimumHeight(200)
        clay.addWidget(self.notesOutput)
        self.saveNotesBtn = QPushButton("Save Notes")
        self.saveNotesBtn.setObjectName("saveNotesBtn")
        clay.addWidget(self.saveNotesBtn)
        lay.addWidget(card)

        lay.addStretch(1)
        self.notesTab = pane
        self.workflowStack.addWidget(pane)

    def _build_translate_pane(self):
        pane = QWidget()
        lay = QVBoxLayout(pane)
        lay.setContentsMargins(14, 14, 14, 14)
        lay.setSpacing(10)

        card = self._card()
        clay = QVBoxLayout(card)
        clay.setContentsMargins(12, 10, 12, 10)
        clay.addWidget(self._section_title("FILE"))
        self.uploadTransBtn = QPushButton("Upload File (.srt / .docx / .txt)")
        self.uploadTransBtn.setObjectName("uploadTransBtn")
        clay.addWidget(self.uploadTransBtn)
        self.transFilePathLabel = QLabel("No file selected")
        self.transFilePathLabel.setObjectName("transFilePathLabel")
        clay.addWidget(self.transFilePathLabel)

        clay.addWidget(self._section_title("LANGUAGES"))
        tlGrid = QGridLayout()
        tlGrid.addWidget(self._label("Source"), 0, 0)
        self.transSrcDropdown = QComboBox()
        self.transSrcDropdown.setObjectName("transSrcDropdown")
        tlGrid.addWidget(self.transSrcDropdown, 1, 0)
        tlGrid.addWidget(self._label("Target"), 0, 1)
        self.transTgtDropdown = QComboBox()
        self.transTgtDropdown.setObjectName("transTgtDropdown")
        tlGrid.addWidget(self.transTgtDropdown, 1, 1)
        clay.addLayout(tlGrid)

        self.translateFileBtn = QPushButton("Translate File")
        self.translateFileBtn.setObjectName("translateFileBtn")
        clay.addWidget(self.translateFileBtn)
        lay.addWidget(card)

        lay.addStretch(1)
        self.translateTab = pane
        self.workflowStack.addWidget(pane)
```

- [ ] **Step 9.5: Run tests to verify they pass**

Run: `pytest tests/test_ui_imports.py -v`
Expected: all passed.

- [ ] **Step 9.6: Commit**

```bash
git add modules/ui_DogeAutoSub.py tests/test_ui_imports.py
git commit -m "feat(ui): rebuild widget tree as dark macOS sidebar layout"
```

---

## Task 10 — Wire `AutoUI.py` to the new chrome

**Files:**
- Modify: `AutoUI.py`

This task connects: frameless-window dragging + traffic-light buttons; palette dropdown ↔ `QSettings` ↔ stylesheet rebuild; sidebar items ↔ `workflowStack`; `EtaTracker` + `PhaseStrip` driven by worker signals; mascot `set_idle` / `set_phase` / `success_with_doge`; status bar values.

- [ ] **Step 10.1: Replace `_load_theme` and theme initialization**

In `DogeAutoSub.__init__`, replace the block from "Pre-load theme stylesheets" through "Load dark theme" with:

```python
        # ── Palette ─────────────────────────────────────────────────────
        from modules.theme_tokens import build_stylesheet, DEFAULT_PALETTE
        from PySide6.QtCore import QSettings
        settings = QSettings("DogeAutoSub", "ui")
        # One-shot migration: drop old theme/dark key.
        if settings.contains("theme/dark"):
            settings.remove("theme/dark")
        palette_id = settings.value("theme/palette", DEFAULT_PALETTE, type=str)
        QApplication.instance().setStyleSheet(build_stylesheet(palette_id))
        self.paletteStripe.set_palette(palette_id)
        self.paletteMenuButton.select(palette_id)
        self.phaseStrip.set_accent_color(self._accent_for(palette_id))

        # Wire palette changes
        self.paletteMenuButton.palette_selected.connect(self._on_palette_changed)
```

Add the `_accent_for` and `_on_palette_changed` methods to the class:

```python
    @staticmethod
    def _accent_for(palette_id: str) -> str:
        from modules.theme_tokens import PALETTES
        return PALETTES[palette_id]["accent"]

    def _on_palette_changed(self, palette_id: str):
        from modules.theme_tokens import build_stylesheet
        from PySide6.QtCore import QSettings
        QApplication.instance().setStyleSheet(build_stylesheet(palette_id))
        self.paletteStripe.set_palette(palette_id)
        self.phaseStrip.set_accent_color(self._accent_for(palette_id))
        QSettings("DogeAutoSub", "ui").setValue("theme/palette", palette_id)
```

- [ ] **Step 10.2: Wire frameless-window controls**

Add to `DogeAutoSub.__init__` (after the palette block):

```python
        # ── Frameless window controls ───────────────────────────────────
        self.closeBtn.clicked.connect(self.close)
        self.minBtn.clicked.connect(self.showMinimized)
        self.zoomBtn.clicked.connect(self._toggle_zoom)
        self._drag_origin = None
        self.fauxTitleBar.mousePressEvent = self._titlebar_press
        self.fauxTitleBar.mouseMoveEvent = self._titlebar_move
        self.fauxTitleBar.mouseReleaseEvent = self._titlebar_release
```

Add the helper methods:

```python
    def _toggle_zoom(self):
        if self.isMaximized():
            self.showNormal()
        else:
            self.showMaximized()

    def _titlebar_press(self, ev):
        if ev.button() == Qt.MouseButton.LeftButton:
            self._drag_origin = ev.globalPosition().toPoint() - self.frameGeometry().topLeft()
            ev.accept()

    def _titlebar_move(self, ev):
        if self._drag_origin is not None and ev.buttons() & Qt.MouseButton.LeftButton:
            self.move(ev.globalPosition().toPoint() - self._drag_origin)
            ev.accept()

    def _titlebar_release(self, ev):
        self._drag_origin = None
```

- [ ] **Step 10.3: Wire sidebar item clicks to workflow stack**

Add to `__init__`:

```python
        # ── Sidebar workflow switching ──────────────────────────────────
        self._sidebar_items = {
            "subtitles": self.sidebarSubtitlesItem,
            "notes":     self.sidebarNotesItem,
            "translate": self.sidebarTranslateItem,
        }
        for name, btn in self._sidebar_items.items():
            btn.clicked.connect(lambda _checked=False, n=name: self._activate_workflow(n))
        self._activate_workflow("subtitles")
```

Add the helper:

```python
    def _activate_workflow(self, name: str):
        index = {"subtitles": 0, "notes": 1, "translate": 2}.get(name, 0)
        self.workflowStack.setCurrentIndex(index)
        for n, btn in self._sidebar_items.items():
            btn.setProperty("active", "true" if n == name else "false")
            btn.style().unpolish(btn); btn.style().polish(btn)
        # Idle mascot per workflow
        if hasattr(self, "mascot") and self.mascot is not None:
            self.mascot.set_idle(name)
```

- [ ] **Step 10.4: Replace ETA + status text with EtaTracker + phase translation**

Find the existing connections (around `subtitle_thread.duration_update.connect(self.etaLabel.setText)`) and replace the relevant block:

```python
        # ── EtaTracker + PhaseStrip wiring ──────────────────────────────
        from modules.eta_tracker import EtaTracker
        self._eta = EtaTracker(workflow="subtitles")

        SUBTITLE_PHASES = ["Preparing", "Reading video", "Transcribing", "Translating", "Saving"]
        self.phaseStrip.set_phases(SUBTITLE_PHASES)

        ENGINEERING_TO_PHASE = {
            "Load model":    "Preparing",
            "Extract audio": "Reading video",
            "Transcribe":    "Transcribing",
            "Translate":     "Translating",
            "Save SRT":      "Saving",
        }
        self._eng_to_phase = ENGINEERING_TO_PHASE

        self.subtitle_thread.log_event.connect(self._on_log_event_for_eta)
        self.subtitle_thread.progress_update.connect(self._on_progress_update_for_eta)
        # duration_update is no longer used to render etaLabel — etaLabel is
        # now driven from the EtaTracker via _refresh_status_line. Connect
        # to a no-op consumer so existing emit calls stay harmless:
        self.subtitle_thread.duration_update.connect(lambda _msg: None)
```

Add the new methods:

```python
    def _on_log_event_for_eta(self, evt: dict):
        kind = evt.get("kind")
        eng_step = evt.get("step")
        phase = self._eng_to_phase.get(eng_step) if eng_step else None
        if kind == "step_start" and phase:
            self._eta.start_phase(phase)
            self.phaseStrip.set_active(phase)
            if hasattr(self, "mascot") and self.mascot is not None:
                self.mascot.set_phase(phase)
            self._refresh_status_line()
        elif kind == "step_done" and phase:
            self._eta.complete_phase(phase)
            self.phaseStrip.mark_done(phase)
            self._refresh_status_line()
        elif kind == "step_error" and phase:
            self.phaseStrip.mark_error(phase)
            self.statusLabel.setText(f"{phase} · failed")
            self.statusLabel.setStyleSheet("color:#ff6b6b;")
            try:
                self.logPanel.set_filter("events")
                if not self.logPanel._console_visible:
                    self.logPanel.toggle_console()
            except Exception:
                pass

    def _on_progress_update_for_eta(self, value: int):
        # Feed the raw 0-100 wallclock value into the tracker as a position
        # sample so EMA smoothing has data to work with. Total is 100.
        try:
            self._eta.update_position(float(value), 100.0)
        except Exception:
            pass
        # The bar width is driven by the tracker's overall fraction, not the
        # raw thread value, so the ETA and bar stay in sync.
        self._refresh_status_line()
        try:
            self.progressBar.setValue(int(self._eta.overall_fraction() * 100))
        except Exception:
            self.progressBar.setValue(value)

    def _refresh_status_line(self):
        active = self.phaseStrip.active_phase()
        if active:
            self.statusLabel.setText(active)
            self.statusLabel.setStyleSheet("")  # back to default
        self.etaLabel.setText(self._eta.current_eta_string())
```

- [ ] **Step 10.5: Wire completion toast**

Find the existing `task_complete` handler in `AutoUI.py`. Replace its body's notification block with:

```python
            from modules.toast import success_with_doge
            base = os.path.basename(self.input_file_path or "")
            toast = success_with_doge(self, "Done", filename=base)
            toast.show_toast()
```

- [ ] **Step 10.5b: Instantiate and mount the MascotWidget**

The new `ui_DogeAutoSub.py` creates a `mascotHost` reference for placement. The widget itself is created in `AutoUI.py` so it can be wired to settings and signals.

First, add a `mascotHost` placeholder. In `modules/ui_DogeAutoSub.py` inside `_build_subtitles_pane`, immediately before the line `lay.addStretch(1)`, insert:

```python
        self.mascotHost = QFrame()
        self.mascotHost.setObjectName("mascotHost")
        self.mascotHost.setFixedHeight(140)
        mhLay = QHBoxLayout(self.mascotHost)
        mhLay.setContentsMargins(0, 0, 0, 0)
        mhLay.addStretch(1)
        # MascotWidget is inserted here at runtime by AutoUI.py
        mhLay.addStretch(1)
        lay.addWidget(self.mascotHost)
```

Then in `AutoUI.py`'s `__init__`, after the sidebar wiring block, add:

```python
        # ── Mascot widget ───────────────────────────────────────────────
        from modules.mascot import MascotWidget
        icons_root = os.path.join(SCRIPT_DIR, "icons")
        self.mascot = MascotWidget(self.mascotHost, icons_root=icons_root)
        # Insert between the two stretches in mascotHost's layout (index 1).
        self.mascotHost.layout().insertWidget(1, self.mascot)
        self.mascot.set_idle("subtitles")
```

Quick smoke check: run `python AutoUI.py`, confirm the mascot area renders (with whatever fallback asset is on disk) above the bottom of the subtitles workflow.

- [ ] **Step 10.6: Status-bar values**

After the palette block in `__init__`:

```python
        # ── Status bar values ───────────────────────────────────────────
        self.statusBarVersion.setText(f"v{APP_VERSION}")
        try:
            import torch
            if torch.cuda.is_available():
                self.statusBarGpu.setText(f"GPU: {torch.cuda.get_device_name(0)}")
            else:
                self.statusBarGpu.setText("GPU: CPU only")
        except Exception:
            self.statusBarGpu.setText("GPU: —")
        self.statusBarReady.setText("● Ready")
```

- [ ] **Step 10.7: Smoke-run the app**

Run: `python AutoUI.py`
Expected: window opens with sidebar, Atari stripe, no light/dark toggle button, "Subtitles" workflow active. Click each palette in the dropdown — chrome recolors instantly, stripe repaints. Drag the title bar — window moves. Click traffic lights — close/min/max work.

Do not fix unrelated regressions in this step; just verify the redesign opens without exception. Capture any new exceptions in `crash_log.txt` and address in Task 11.

- [ ] **Step 10.8: Commit**

```bash
git add AutoUI.py
git commit -m "feat(app): wire palette dropdown, frameless window, EtaTracker, sidebar nav"
```

---

## Task 11 — Recents persistence

**Files:**
- Modify: `AutoUI.py`

- [ ] **Step 11.1: Add the recents helper**

Add to `DogeAutoSub`:

```python
    _RECENTS_MAX = 5

    def _push_recent(self, workflow: str, path: str):
        from PySide6.QtCore import QSettings
        if not path:
            return
        s = QSettings("DogeAutoSub", "ui")
        key = f"recents/{workflow}"
        existing = s.value(key, [], type=list) or []
        items = [p for p in existing if p != path]
        items.insert(0, path)
        items = items[: self._RECENTS_MAX]
        s.setValue(key, items)
        self._render_recents(workflow)

    def _render_recents(self, workflow: str):
        from PySide6.QtCore import QSettings
        s = QSettings("DogeAutoSub", "ui")
        items = s.value(f"recents/{workflow}", [], type=list) or []
        # Clear current list
        while self.recentListLayout.count():
            item = self.recentListLayout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        for path in items:
            btn = QPushButton(os.path.basename(path))
            btn.setObjectName("sidebarItem")
            btn.setToolTip(path)
            btn.clicked.connect(lambda _checked=False, p=path, w=workflow: self._reload_recent(w, p))
            self.recentListLayout.addWidget(btn)
```

- [ ] **Step 11.2: Add `_reload_recent`**

```python
    def _reload_recent(self, workflow: str, path: str):
        if workflow == "subtitles":
            self.input_file_path = path
            self.filePathLabel.setText(path)
        elif workflow == "notes":
            self.docx_path = path
            if hasattr(self, "docxPathLabel"):
                self.docxPathLabel.setText(path)
        elif workflow == "translate":
            self.trans_file_path = path
            if hasattr(self, "transFilePathLabel"):
                self.transFilePathLabel.setText(path)
        self._activate_workflow(workflow)
```

- [ ] **Step 11.3: Push from existing file pickers**

Find the existing `selectFileBtn` click handler that sets `self.input_file_path = path` and append:

```python
            self._push_recent("subtitles", path)
```

Do the same for the docx and translate file pickers (each with their workflow id).

- [ ] **Step 11.4: Initial render at startup**

At the end of `__init__`, add:

```python
        for w in ("subtitles", "notes", "translate"):
            self._render_recents(w)
```

(Note: only one workflow's recents are visible at a time. Calling all three keeps the storage warm but only the current one is shown — call `_render_recents(<active>)` from `_activate_workflow` instead. Update `_activate_workflow` accordingly:)

In `_activate_workflow`, after the `setProperty` loop, add:

```python
        self._render_recents(name)
```

Then remove the warm-up loop from the end of `__init__` (only `_render_recents(active)` runs via `_activate_workflow("subtitles")` already at startup).

- [ ] **Step 11.5: Smoke test**

Run: `python AutoUI.py`. Pick a video file. Close the app. Reopen — the file appears under "Recent" in the sidebar. Click it — file loads back into the subtitles workflow.

- [ ] **Step 11.6: Commit**

```bash
git add AutoUI.py
git commit -m "feat(ui): persistent Recent files list per workflow in sidebar"
```

---

## Task 12 — Reduce-Motion gating sweep

**Files:**
- Modify: `modules/toast.py`
- Modify: `modules/mascot.py`
- Modify: `AutoUI.py`

- [ ] **Step 12.1: Toast respects Reduce Motion**

In `Toast.show_toast`, replace the slide-in animation block with:

```python
    def show_toast(self) -> None:
        from PySide6.QtCore import QSettings
        reduce_motion = QSettings("DogeAutoSub", "ui").value("view/reduceMotion", False, type=bool)
        parent = self.parentWidget()
        if not parent:
            self.show(); return
        x = (parent.width() - self.width()) // 2
        end_y = 12
        if reduce_motion:
            self.move(QPoint(x, end_y))
            self.show()
            QTimer.singleShot(self._duration_ms, self.deleteLater)
            return
        start = QPoint(x, -self.height())
        end = QPoint(x, end_y)
        self.move(start); self.show()
        a = QPropertyAnimation(self, b"pos", self)
        a.setDuration(220); a.setStartValue(start); a.setEndValue(end)
        a.start(QPropertyAnimation.DeletionPolicy.DeleteWhenStopped)
        QTimer.singleShot(self._duration_ms, self._slide_out)
```

- [ ] **Step 12.2: Mascot respects Reduce Motion**

In `MascotWidget._show_path`, replace the GIF branch:

```python
        if path.lower().endswith(".gif"):
            from PySide6.QtCore import QSettings
            reduce_motion = QSettings("DogeAutoSub", "ui").value("view/reduceMotion", False, type=bool)
            mv = QMovie(path)
            mv.setScaledSize(QSize(130, 130))
            self.setMovie(mv)
            if reduce_motion:
                mv.jumpToFrame(0)
                mv.stop()
            else:
                mv.start()
            self._movie = mv
```

- [ ] **Step 12.3: PhaseStrip transitions respect Reduce Motion**

The `PhaseStrip` does no animation in this plan; nothing to change. (If a later task adds dot-fade animations, gate them through `QSettings("DogeAutoSub", "ui").value("view/reduceMotion", False, type=bool)`.)

- [ ] **Step 12.4: Smoke test**

Run: `python AutoUI.py`. In the View menu, toggle Reduce Motion ON. Run a transcription. Toast appears in place (no slide). Mascot frame is static. Toggle Reduce Motion OFF — animations resume on the next event.

- [ ] **Step 12.5: Commit**

```bash
git add modules/toast.py modules/mascot.py
git commit -m "feat(ui): toast slide and mascot GIFs respect Reduce Motion setting"
```

---

## Task 13 — Connect log panel into the active card

**Files:**
- Modify: `AutoUI.py`

- [ ] **Step 13.1: Mount LogPanel inside the action card**

In `DogeAutoSub.__init__`, after the palette block but before the EtaTracker block, mount the existing log panel into the `logPanelHost`:

```python
        from modules.log_panel import LogPanel
        from PySide6.QtWidgets import QVBoxLayout
        self.logPanel = LogPanel()
        host_lay = QVBoxLayout(self.logPanelHost)
        host_lay.setContentsMargins(0, 0, 0, 0)
        host_lay.addWidget(self.logPanel)
        # Pipeline names match the engineering steps emitted by SubtitleThread.
        self.logPanel.set_pipeline(["Load model", "Extract audio", "Transcribe", "Translate", "Save SRT"])
```

- [ ] **Step 13.2: Forward worker log_event into LogPanel + EtaTracker**

In the wiring section, add:

```python
        self.subtitle_thread.log_event.connect(self._forward_to_log_panel)
```

Add the helper:

```python
    def _forward_to_log_panel(self, evt: dict):
        kind = evt.get("kind")
        if kind == "log":
            self.logPanel.log(evt.get("level", "info"), evt.get("text", ""))
        elif kind == "step_start":
            self.logPanel.step_start(evt.get("step", ""))
        elif kind == "step_done":
            self.logPanel.step_done(evt.get("step", ""), evt.get("detail", ""))
        elif kind == "step_error":
            self.logPanel.step_error(evt.get("step", ""), evt.get("detail", ""))
```

- [ ] **Step 13.3: Smoke test**

Run: `python AutoUI.py`. Run a transcription. Verify the phase strip dots advance as steps complete; the log panel's "Show details" toggle is closed by default; opening it reveals events with no "such wow" lines; an error path opens the panel automatically.

- [ ] **Step 13.4: Commit**

```bash
git add AutoUI.py
git commit -m "feat(ui): mount log panel and forward worker events into it"
```

---

## Task 14 — End-to-end manual verification

**Files:** none.

- [ ] **Step 14.1: Run the full test suite**

Run: `pytest tests/ -v`
Expected: all tests pass, including any pre-existing animation/log_writer tests.

- [ ] **Step 14.2: Run a real transcription end-to-end**

Run: `python AutoUI.py`. Pick a short video (≤30s). Run it on each of the four palettes in turn. Verify on each:

1. Stripe and accent recolor instantly when palette changes.
2. Phase strip advances Preparing → Reading video → Transcribing → Translating → Saving.
3. ETA never displays `--:--:--`.
4. Live status line shows phase verb + position + time-left.
5. Progress bar width agrees with displayed time-left direction.
6. On completion, success toast slides up with the filename.
7. Recent files list grows in the sidebar.
8. Detail log is closed by default, contains only events when opened (no "such wow"), opens automatically on error.

- [ ] **Step 14.3: Run with Reduce Motion ON**

Toggle View → Reduce Motion. Repeat one transcription. Verify: toast appears in place, mascot is static, no slide animations on tab switches.

- [ ] **Step 14.4: Run with Doge Tips OFF**

Toggle View → Doge Tips off. Run a transcription. Verify: completion toast says `Done · file.srt` (no doge slang); mascot is the static fallback; speech bubble stays empty.

- [ ] **Step 14.5: Migration check**

Open `regedit` (or platform equivalent) and inspect `HKCU\Software\DogeAutoSub\ui`. Confirm `theme/dark` is gone after first launch; `theme/palette` is `atari`.

- [ ] **Step 14.6: Build smoke test**

Run: `python -m PyInstaller DogeAutoSubApp.spec --noconfirm`
Expected: build succeeds. Launch the built `.exe` and confirm the new chrome renders identically to the source build.

- [ ] **Step 14.7: Commit any verification fixes**

If verification revealed bugs, fix them in narrowly-scoped commits (one bug per commit) before declaring the work complete.

---

## Out-of-scope reminders (do not implement in this plan)

- Custom palette editor / user-supplied palettes
- Light mode return
- Sidebar resize handle
- Workflow reordering
- New auto-updater chrome
- Replacing the splash screen

These are listed in the spec's non-goals; if they come up during execution, defer them to a separate plan.
