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
        x = (parent.width() - self.width()) // 2
        end_y = 12
        start = QPoint(x, -self.height())
        end = QPoint(x, end_y)
        self.move(start)
        self.show()
        a = QPropertyAnimation(self, b"pos", self)
        a.setDuration(220)
        a.setStartValue(start)
        a.setEndValue(end)
        a.start(QPropertyAnimation.DeletionPolicy.DeleteWhenStopped)
        QTimer.singleShot(self._duration_ms, self._slide_out)

    def _slide_out(self) -> None:
        parent = self.parentWidget()
        if not parent:
            self.deleteLater()
            return
        a = QPropertyAnimation(self, b"pos", self)
        a.setDuration(220)
        a.setStartValue(self.pos())
        a.setEndValue(QPoint(self.x(), -self.height()))
        a.finished.connect(self.deleteLater)
        a.start(QPropertyAnimation.DeletionPolicy.DeleteWhenStopped)
