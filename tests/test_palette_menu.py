import pytest
from PySide6.QtWidgets import QApplication, QWidget

from modules.palette_menu import PaletteMenuButton


@pytest.fixture(scope="module")
def app():
    return QApplication.instance() or QApplication([])


def test_default_selection_is_atari(app):
    parent = QWidget()
    btn = PaletteMenuButton(parent)
    assert btn.current_palette() == "atari"


def test_select_palette_emits_signal(app):
    parent = QWidget()
    btn = PaletteMenuButton(parent)
    received = []
    btn.palette_selected.connect(received.append)
    btn.select("crt")
    assert btn.current_palette() == "crt"
    assert received == ["crt"]


def test_select_unknown_palette_ignored(app):
    parent = QWidget()
    btn = PaletteMenuButton(parent)
    btn.select("solarized")
    assert btn.current_palette() == "atari"


def test_button_label_reflects_palette(app):
    parent = QWidget()
    btn = PaletteMenuButton(parent)
    btn.select("famicom")
    assert "Famicom" in btn.text()
