"""Win95-styled boot splash shown while the app initialises."""
from __future__ import annotations

import os
from typing import Optional

from PySide6.QtCore import QPropertyAnimation, QSize, Qt, QTimer
from PySide6.QtGui import QColor, QLinearGradient, QPainter, QPixmap
from PySide6.QtWidgets import QApplication, QFrame, QLabel, QProgressBar, QVBoxLayout, QWidget


class BootSplash(QWidget):
    """Frameless splash: logo + title + progress bar.

    Usage::
        splash = BootSplash()
        splash.show()
        splash.set_progress(50, "Loading model…")
        splash.fade_close()   # when ready
    """

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent, Qt.WindowType.FramelessWindowHint | Qt.WindowType.SplashScreen)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(QSize(360, 220))
        self._center_on_screen()

        root = QFrame(self)
        root.setObjectName("splashRoot")
        root.setFixedSize(360, 220)
        root.setStyleSheet(
            "QFrame#splashRoot {"
            "  background: #c0c0c0;"
            "  border: 2px solid #000000;"
            "}"
        )

        layout = QVBoxLayout(root)
        layout.setContentsMargins(0, 0, 0, 12)
        layout.setSpacing(0)

        # Title bar
        title_bar = QFrame()
        title_bar.setFixedHeight(28)
        title_bar.setStyleSheet(
            "QFrame { background: qlineargradient(x1:0,y1:0,x2:1,y2:0,"
            " stop:0 #000080, stop:1 #1084d0); }"
        )
        tb_layout = QVBoxLayout(title_bar)
        tb_layout.setContentsMargins(8, 0, 0, 0)
        tb_layout.setSpacing(0)
        tb_label = QLabel("DogeAutoSub")
        tb_label.setStyleSheet("color: #ffffff; font-size: 12px; font-weight: bold; background: transparent;")
        tb_layout.addWidget(tb_label)
        layout.addWidget(title_bar)

        # Logo area
        logo_label = QLabel()
        logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        _icon = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "icons", "favicon.png")
        if os.path.exists(_icon):
            logo_label.setPixmap(
                QPixmap(_icon).scaled(64, 64, Qt.AspectRatioMode.KeepAspectRatio,
                                      Qt.TransformationMode.SmoothTransformation)
            )
        else:
            logo_label.setText("🐕")
            logo_label.setStyleSheet("font-size: 40px;")
        layout.addWidget(logo_label, 1)

        # App name
        name_label = QLabel("DogeAutoSub")
        name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        name_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #000080;")
        layout.addWidget(name_label)

        # Status label
        self._status = QLabel("Starting…")
        self._status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._status.setStyleSheet("font-size: 10px; color: #404040;")
        layout.addWidget(self._status)

        # Progress bar
        self._bar = QProgressBar()
        self._bar.setFixedHeight(14)
        self._bar.setRange(0, 100)
        self._bar.setValue(0)
        self._bar.setTextVisible(False)
        self._bar.setStyleSheet(
            "QProgressBar { background:#ffffff; border:1px inset #808080; margin:0 16px; }"
            "QProgressBar::chunk { background:#000080; }"
        )
        layout.addWidget(self._bar)

    def _center_on_screen(self) -> None:
        screen = QApplication.primaryScreen()
        if screen:
            sg = screen.availableGeometry()
            self.move(sg.center().x() - 180, sg.center().y() - 110)

    def set_progress(self, value: int, status: str = "") -> None:
        self._bar.setValue(max(0, min(100, value)))
        if status:
            self._status.setText(status)
        QApplication.processEvents()

    def fade_close(self) -> None:
        from PySide6.QtWidgets import QGraphicsOpacityEffect
        eff = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(eff)
        anim = QPropertyAnimation(eff, b"opacity", self)
        anim.setDuration(300)
        anim.setStartValue(1.0)
        anim.setEndValue(0.0)
        anim.finished.connect(self.close)
        anim.start()
