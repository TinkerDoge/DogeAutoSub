def test_toast_constructs_and_shows(qtbot):
    from modules.toast import Toast
    from PySide6.QtWidgets import QWidget
    parent = QWidget(); qtbot.addWidget(parent); parent.resize(400, 300); parent.show()
    t = Toast(parent, "test message", kind="error", duration_ms=200)
    t.show_toast()
    assert t.text() == "test message"
