import pytest
from PySide6.QtWidgets import QApplication
from modules.mascot import MascotWidget


@pytest.fixture(scope="module")
def app():
    return QApplication.instance() or QApplication([])


def test_state_transitions(qtbot, tmp_path):
    from modules.mascot import MascotWidget
    w = MascotWidget(icons_root=str(tmp_path)); qtbot.addWidget(w)
    assert w.state == "idle"
    w.set_state("working"); assert w.state == "working"
    w.set_state("celebrate"); assert w.state == "celebrate"


def test_say_queues_messages(qtbot, tmp_path):
    from modules.mascot import MascotWidget
    from PySide6.QtWidgets import QLabel
    bubble = QLabel(); qtbot.addWidget(bubble)
    w = MascotWidget(icons_root=str(tmp_path), bubble_target=bubble)
    qtbot.addWidget(w); w.show()
    w.say("first", ms=50)
    w.say("second", ms=50)
    # No crash; second message queued
    assert len(w._say_queue) >= 1 or w._current_bubble is not None


def test_react_to_log_event_error(qtbot, tmp_path):
    from modules.mascot import MascotWidget
    w = MascotWidget(icons_root=str(tmp_path)); qtbot.addWidget(w)
    w.handle_log_event({"kind": "log", "level": "error", "text": "boom"})
    assert w.state == "confused"


def test_react_to_step_done_celebrates_briefly(qtbot, tmp_path):
    from modules.mascot import MascotWidget
    w = MascotWidget(icons_root=str(tmp_path)); qtbot.addWidget(w)
    w.set_state("working")
    w.handle_log_event({"kind": "step_done", "step": "Load model"})
    assert w.state in ("celebrate", "working")


def test_set_phase_known_phases(app, tmp_path):
    w = MascotWidget(icons_root=str(tmp_path))
    for phase in ("Preparing", "Reading video", "Transcribing", "Translating", "Saving"):
        w.set_phase(phase)  # must not raise
    assert w.state in {"working", "thinking"}


def test_set_phase_unknown_is_noop(app, tmp_path):
    w = MascotWidget(icons_root=str(tmp_path))
    before = w.state
    w.set_phase("Nonexistent Phase")
    assert w.state == before


def test_set_idle_workflow(app, tmp_path):
    w = MascotWidget(icons_root=str(tmp_path))
    w.set_idle("subtitles")
    assert w.state == "idle"


def test_png_fallback_when_gif_missing(app, tmp_path):
    mascot_dir = tmp_path / "mascot"
    mascot_dir.mkdir()
    (mascot_dir / "transcribing.png").write_bytes(b"\x89PNG\r\n\x1a\n")
    w = MascotWidget(icons_root=str(tmp_path))
    path = w._resolve_asset("transcribing")
    assert path is not None
    assert path.endswith(".png")
