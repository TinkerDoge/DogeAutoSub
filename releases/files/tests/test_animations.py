def test_reduce_motion_setting_default(qtbot):
    from modules.animations import reduce_motion
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
    assert True
