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

    def dot_count(self) -> int:
        return len(self._dots)

    def active_phase(self) -> Optional[str]:
        return self._active

    def state_of(self, name: str) -> Optional[str]:
        d = self._dots.get(name)
        return d.state() if d else None
