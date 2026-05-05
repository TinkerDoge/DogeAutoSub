import pytest
from PySide6.QtWidgets import QApplication, QWidget


@pytest.fixture(scope="module")
def app():
    return QApplication.instance() or QApplication([])


def test_toast_constructs_and_shows(qtbot):
    from modules.toast import Toast
    from PySide6.QtWidgets import QWidget
    parent = QWidget(); qtbot.addWidget(parent); parent.resize(400, 300); parent.show()
    t = Toast(parent, "test message", kind="error", duration_ms=200)
    t.show_toast()
    assert t.text() == "test message"


from modules.toast import success_with_doge

def test_success_with_doge_returns_toast(app):
    parent = QWidget()
    parent.resize(400, 300)
    t = success_with_doge(parent, "Done", filename="output.srt")
    assert t.text().startswith("Done")
    assert "output.srt" in t.text()
