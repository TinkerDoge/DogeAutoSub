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
        self.setMinimumHeight(self.HEIGHT)
        self.setMaximumHeight(self.HEIGHT)
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
        widths = [w // n] * n
        for i in range(w - sum(widths)):
            widths[i] += 1
        x = 0
        for i, color in enumerate(self._bands):
            painter.fillRect(x, 0, widths[i], h, QColor(color))
            x += widths[i]
        painter.end()
