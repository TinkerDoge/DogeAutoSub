import pytest

from modules.eta_tracker import EtaTracker, WORKFLOW_PHASES


def test_subtitle_phase_weights_sum_to_one():
    weights = WORKFLOW_PHASES["subtitles"]
    assert abs(sum(p["weight"] for p in weights) - 1.0) < 1e-6


def test_notes_phase_weights_sum_to_one():
    weights = WORKFLOW_PHASES["notes"]
    assert abs(sum(p["weight"] for p in weights) - 1.0) < 1e-6


def test_translate_phase_weights_sum_to_one():
    weights = WORKFLOW_PHASES["translate"]
    assert abs(sum(p["weight"] for p in weights) - 1.0) < 1e-6


def test_initial_overall_fraction_is_zero():
    t = EtaTracker(workflow="subtitles")
    assert t.overall_fraction() == 0.0


def test_overall_fraction_advances_with_phases():
    t = EtaTracker(workflow="subtitles")
    t.start_phase("Preparing")
    t.complete_phase("Preparing")
    t.start_phase("Reading video")
    t.complete_phase("Reading video")
    # 5% + 5% = 10% completed before transcription begins.
    assert 0.09 <= t.overall_fraction() <= 0.11


def test_cold_start_returns_estimate_with_tilde():
    t = EtaTracker(workflow="subtitles")
    t.set_input_size(60.0)  # 60 audio-seconds
    t.start_phase("Transcribing")
    s = t.current_eta_string()
    assert s.startswith("~"), s


def test_ema_smoothing_rejects_spikes(monkeypatch):
    times = iter([1000.0, 1001.0, 1002.0, 1003.0, 1004.0, 1005.0])
    monkeypatch.setattr("modules.eta_tracker.time.monotonic", lambda: next(times))

    t = EtaTracker(workflow="subtitles")
    t.set_input_size(100.0)
    t.start_phase("Transcribing")          # t=1000
    t.update_position(10.0, 100.0)         # t=1001 — 10 a-s in 1 wall-s
    sample_a = t.current_phase_throughput()
    t.update_position(11.0, 100.0)         # t=1002 — almost-zero progress, would spike a non-EMA estimate
    sample_b = t.current_phase_throughput()
    # EMA must move less than 60% between consecutive samples even on adverse input.
    assert abs(sample_b - sample_a) / sample_a < 0.6


def test_complete_phase_marks_progress_full_for_that_share():
    t = EtaTracker(workflow="subtitles")
    t.start_phase("Preparing")
    t.complete_phase("Preparing")
    # After preparing, overall fraction = 0.05 (its weight).
    assert abs(t.overall_fraction() - 0.05) < 1e-6


def test_format_seconds_short():
    from modules.eta_tracker import format_remaining
    assert format_remaining(45) == "45s"
    assert format_remaining(70) == "1m 10s"
    assert format_remaining(3725) == "1h 2m"
    assert format_remaining(0) == "0s"
