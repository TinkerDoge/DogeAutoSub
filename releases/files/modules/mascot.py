"""Doge mascot state machine + speech bubble."""
from __future__ import annotations

import os
from collections import deque
from typing import Optional

from PySide6.QtCore import QPropertyAnimation, QSize, QTimer, Qt
from PySide6.QtGui import QMovie, QPixmap
from PySide6.QtWidgets import QGraphicsOpacityEffect, QLabel, QWidget

STATES = {"idle", "idle_blink", "thinking", "working", "celebrate", "confused", "sleepy", "error"}

# Fallback chain when state-specific GIFs don't exist
FALLBACKS = {
    "idle":       "start.gif",
    "idle_blink": "start.gif",
    "thinking":   "loading.gif",
    "working":    "loading.gif",
    "celebrate":  "done.jpg",
    "confused":   "start.gif",
    "sleepy":     "start.gif",
    "error":      "start.gif",
}

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


class MascotWidget(QLabel):
    def __init__(self, parent: Optional[QWidget] = None,
                 *, icons_root: Optional[str] = None,
                 bubble_target: Optional[QLabel] = None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setMinimumSize(QSize(64, 64))
        self.setMaximumSize(QSize(64, 64))
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
            mv.setScaledSize(QSize(64, 64))
            self.setMovie(mv)
            mv.start()
            self._movie = mv
        else:
            pm = QPixmap(path).scaled(
                64, 64,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            self.setPixmap(pm)
        self._idle_timer.start(60_000)

    def set_phase(self, phase: str) -> None:
        asset = PHASE_TO_ASSET.get(phase)
        if not asset:
            return
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
        """Look for <icons_root>/mascot/<asset_key>.gif then .png, else None."""
        for ext in (".gif", ".png"):
            p = os.path.join(self._icons_root, "mascot", f"{asset_key}{ext}")
            if os.path.exists(p):
                return p
        return None

    def _show_path(self, path: str, *, state_name: str) -> None:
        self.state = state_name
        if path.lower().endswith(".gif"):
            mv = QMovie(path)
            mv.setScaledSize(QSize(64, 64))
            self.setMovie(mv)
            from PySide6.QtCore import QSettings
            reduce_motion = QSettings("DogeAutoSub", "ui").value(
                "motion/reduce", False, type=bool
            )
            mv.jumpToFrame(0)
            if not reduce_motion:
                mv.start()
            self._movie = mv
        else:
            pm = QPixmap(path).scaled(
                64, 64,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            self.setPixmap(pm)
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
        anim_in.setDuration(200)
        anim_in.setStartValue(0.0)
        anim_in.setEndValue(1.0)
        anim_in.start()
        self._current_bubble = bubble

        def fade_out():
            anim_out = QPropertyAnimation(eff, b"opacity", bubble)
            anim_out.setDuration(200)
            anim_out.setStartValue(1.0)
            anim_out.setEndValue(0.0)

            def cleanup():
                bubble.setText("")
                bubble.setStyleSheet("")
                self._current_bubble = None
                self._dequeue_say()

            anim_out.finished.connect(cleanup)
            anim_out.start()

        QTimer.singleShot(ms, fade_out)
