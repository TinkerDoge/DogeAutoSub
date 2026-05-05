import os
import pytest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


@pytest.mark.parametrize("name", ["styleSheetLight.css", "styleSheetDark.css"])
def test_css_can_be_applied(qtbot, name):
    from PySide6.QtWidgets import QWidget
    path = os.path.join(ROOT, "modules", name)
    with open(path, "r", encoding="utf-8") as f:
        css = f.read()
    w = QWidget()
    qtbot.addWidget(w)
    w.setStyleSheet(css)
    # Qt logs unknown-property warnings to stderr but does not raise; just
    # assert nothing crashed and the stylesheet round-trips.
    assert w.styleSheet() == css
