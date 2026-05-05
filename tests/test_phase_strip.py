import pytest
from PySide6.QtWidgets import QApplication

from modules.phase_strip import PhaseStrip


@pytest.fixture(scope="module")
def app():
    return QApplication.instance() or QApplication([])


def test_set_phases_creates_dots(app):
    strip = PhaseStrip()
    strip.set_phases(["A", "B", "C"])
    assert strip.dot_count() == 3


def test_set_active_marks_one_phase(app):
    strip = PhaseStrip()
    strip.set_phases(["A", "B", "C"])
    strip.set_active("B")
    assert strip.active_phase() == "B"


def test_mark_done_advances_state(app):
    strip = PhaseStrip()
    strip.set_phases(["A", "B"])
    strip.mark_done("A")
    assert strip.state_of("A") == "done"


def test_unknown_phase_is_ignored(app):
    strip = PhaseStrip()
    strip.set_phases(["A"])
    strip.set_active("Z")  # must not raise
    strip.mark_done("Z")   # must not raise
    assert strip.active_phase() is None


def test_set_accent_color_repaints(app):
    strip = PhaseStrip()
    strip.set_phases(["A"])
    strip.set_active("A")
    strip.set_accent_color("#b8823a")  # must not raise
