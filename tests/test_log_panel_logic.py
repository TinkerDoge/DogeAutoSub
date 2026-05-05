import pytest

from modules.log_panel import (
    PIPELINE_SUBTITLES, PIPELINE_NOTES, PIPELINE_TRANSLATE,
    DogeNarrator, _format_duration,
)


def test_pipelines_defined():
    assert PIPELINE_SUBTITLES == ["Load model", "Extract audio", "Transcribe", "Translate", "Save SRT"]
    assert PIPELINE_NOTES == ["Read transcript", "Summarize", "Format"]
    assert PIPELINE_TRANSLATE == ["Read file", "Detect language", "Translate", "Format output"]


def test_format_duration_seconds():
    assert _format_duration(0.4) == "0.4s"
    assert _format_duration(2.0) == "2.0s"
    assert _format_duration(75) == "1m 15s"
    assert _format_duration(3600) == "1h 0m"


def test_doge_narrator_speaks_every_n():
    n = DogeNarrator(every_n=3, seed=42)
    msgs = []
    n.on_event = lambda lvl, msg: msgs.append((lvl, msg))
    for _ in range(8):
        n.notify_step_done()
    # On steps 3 and 6 it should have spoken.
    assert len(msgs) == 2
    for lvl, msg in msgs:
        assert lvl == "doge"
        assert msg


def test_doge_narrator_disabled_emits_nothing():
    n = DogeNarrator(every_n=1, enabled=False)
    msgs = []
    n.on_event = lambda lvl, msg: msgs.append((lvl, msg))
    for _ in range(5):
        n.notify_step_done()
    assert msgs == []


def test_doge_narrator_completion_always_speaks():
    n = DogeNarrator(every_n=99, seed=1)
    msgs = []
    n.on_event = lambda lvl, msg: msgs.append((lvl, msg))
    n.notify_completion()
    assert len(msgs) == 1
    assert msgs[0][0] == "doge"


def test_log_panel_lifecycle(qtbot):
    from modules.log_panel import LogPanel, PIPELINE_SUBTITLES
    panel = LogPanel()
    qtbot.addWidget(panel)
    panel.set_pipeline(PIPELINE_SUBTITLES)
    panel.step_start("Load model")
    panel.log("info", "model loading...")
    panel.step_done("Load model", "1.2s")
    panel.step_start("Extract audio")
    panel.step_error("Extract audio", "ffmpeg missing")
    panel.notify_completion()
    assert "model loading" in panel.console.toPlainText()
