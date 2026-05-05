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


# ── Hover lift ─────────────────────────────────────────────────────────────
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


# ── Pulse ──────────────────────────────────────────────────────────────────
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


# ── Shake ──────────────────────────────────────────────────────────────────
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


# ── Confetti burst ─────────────────────────────────────────────────────────
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
        fade.setStartValue(1.0)
        fade.setEndValue(0.0)
        anim.start(QPropertyAnimation.DeletionPolicy.DeleteWhenStopped)
        fade.start(QPropertyAnimation.DeletionPolicy.DeleteWhenStopped)
        QTimer.singleShot(duration_ms + 200, p.deleteLater)


# ── Progress shimmer ───────────────────────────────────────────────────────
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


# ── Phase-aware indicator widgets ──────────────────────────────────────────
class _GearWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(14, 14)
        self._angle = 0
        self._anim = QVariantAnimation(self)
        self._anim.setDuration(1200)
        self._anim.setStartValue(0)
        self._anim.setEndValue(360)
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
        self._t = QTimer(self)
        self._t.timeout.connect(self._tick)
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
