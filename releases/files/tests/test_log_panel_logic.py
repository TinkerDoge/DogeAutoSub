import pytest
from PySide6.QtWidgets import QApplication

from modules.log_panel import LogPanel, DogeNarrator


@pytest.fixture(scope="module")
def app():
    return QApplication.instance() or QApplication([])


def test_log_panel_does_not_route_narrator_to_console(app):
    panel = LogPanel()
    panel._narrator.notify_step_done()
    panel._narrator.notify_step_done()
    panel._narrator.notify_step_done()
    text = panel.console.toPlainText()
    assert "such" not in text
    assert "wow" not in text
    assert "doge" not in text


def test_log_panel_collapsed_by_default(app):
    panel = LogPanel()
    assert panel._console_visible is False


def test_log_panel_set_filter_events(app):
    panel = LogPanel()
    panel.set_filter("events")
    assert panel.current_filter() == "events"
    panel.set_filter("raw")
    assert panel.current_filter() == "raw"


def test_log_panel_filter_hides_per_segment_chatter(app):
    panel = LogPanel()
    panel.set_filter("events")
    panel.log("info", "chunk 3 of 12")
    panel.log("error", "translation API failure")
    text = panel.console.toPlainText()
    assert "translation API failure" in text
    assert "chunk 3 of 12" not in text


def test_doge_narrator_emits_via_callback_only(app):
    received = []
    n = DogeNarrator(every_n=1, enabled=True, seed=0)
    n.on_event = lambda lvl, msg: received.append((lvl, msg))
    n.notify_step_done()
    assert received and received[0][0] == "doge"
