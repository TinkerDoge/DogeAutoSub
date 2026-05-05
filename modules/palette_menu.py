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
