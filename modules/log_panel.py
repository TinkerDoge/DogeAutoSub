"""LogPanel widget: pipeline timeline + collapsible terminal console."""
from __future__ import annotations

import random
import time
from typing import Callable, Optional

from PySide6.QtCore import Qt, QSettings, Signal
from PySide6.QtGui import QColor, QTextCharFormat, QTextCursor
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QPlainTextEdit, QVBoxLayout, QWidget,
)


# ── Pipeline definitions ───────────────────────────────────────────────────
PIPELINE_SUBTITLES = ["Load model", "Extract audio", "Transcribe", "Translate", "Save SRT"]
PIPELINE_NOTES     = ["Read transcript", "Summarize", "Format"]
PIPELINE_TRANSLATE = ["Read file", "Detect language", "Translate", "Format output"]


# ── Colors ─────────────────────────────────────────────────────────────────
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
        m = int(seconds // 60)
        s = int(seconds % 60)
        return f"{m}m {s}s"
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    return f"{h}h {m}m"


# ── Doge narrator ──────────────────────────────────────────────────────────
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


# ── Timeline row ───────────────────────────────────────────────────────────
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
        self._phase_widget: Optional[QWidget] = None
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

    def set_active_widget(self, w: Optional[QWidget]) -> None:
        """Swap in a phase-specific animated indicator beside the dot."""
        self._clear_phase_widget()
        if w is None:
            return
        self._phase_widget = w
        self.dot.hide()
        self.layout().insertWidget(0, w)
        w.show()

    def reset_indicator(self) -> None:
        self._clear_phase_widget()
        self.dot.show()

    def _clear_phase_widget(self) -> None:
        if self._phase_widget is not None:
            self.layout().removeWidget(self._phase_widget)
            self._phase_widget.deleteLater()
            self._phase_widget = None

    def set_pending(self):
        self._state = "pending"
        self.reset_indicator()
        self._set_dot(self.DOT_PENDING)
        self.nameLabel.setStyleSheet("color: #b0b0b0;")
        self.detailLabel.setText("")
        self.tsLabel.setText("")
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
        self.reset_indicator()
        self._set_dot(self.DOT_DONE)
        self.nameLabel.setStyleSheet("color: #202020;")
        if self._start_ts:
            detail = detail or _format_duration(time.time() - self._start_ts)
        self.detailLabel.setText(detail)
        self.setStyleSheet("background: transparent;")

    def set_error(self, detail: str = ""):
        self._state = "error"
        self.reset_indicator()
        self._set_dot(self.DOT_ERROR)
        self.nameLabel.setStyleSheet("color: #e63946; font-weight: 600;")
        self.detailLabel.setText(detail or "error")
        self.setStyleSheet("background: transparent;")


# ── LogPanel ───────────────────────────────────────────────────────────────
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

    # ── Public API ─────────────────────────────────────────────────────────
    def set_pipeline(self, steps: list[str]) -> None:
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
            try:
                from modules.animations import make_phase_widget
                w = make_phase_widget(step, row)
                row.set_active_widget(w)
            except Exception:
                pass
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

    # ── Helpers ────────────────────────────────────────────────────────────
    def _emit(self, kind: str, **fields) -> None:
        evt = {"kind": kind}
        evt.update(fields)
        self.log_event.emit(evt)
