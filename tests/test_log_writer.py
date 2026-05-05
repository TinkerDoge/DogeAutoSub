import os
import time
from datetime import datetime, timedelta
import pytest

from modules.log_writer import LogWriter


def test_writes_dated_file(tmp_path):
    w = LogWriter(tmp_path)
    w.write("info", "hello")
    w.flush()
    today = datetime.now().strftime("%Y%m%d")
    fp = tmp_path / f"dogeautosub-{today}.log"
    assert fp.exists()
    content = fp.read_text(encoding="utf-8")
    assert "hello" in content
    assert "[INFO]" in content


def test_format_includes_timestamp(tmp_path):
    w = LogWriter(tmp_path)
    w.write("error", "boom")
    w.flush()
    today = datetime.now().strftime("%Y%m%d")
    fp = tmp_path / f"dogeautosub-{today}.log"
    line = fp.read_text(encoding="utf-8").strip().splitlines()[-1]
    # Format: "[HH:MM:SS] [LEVEL] msg"
    assert line.startswith("[")
    assert line[3] == ":" and line[6] == ":"


def test_prune_old_logs(tmp_path):
    keep_days = 7
    old_files = []
    for i in range(10):
        f = tmp_path / f"dogeautosub-2024010{i}.log"
        f.write_text("old", encoding="utf-8")
        ts = (datetime.now() - timedelta(days=30 + i)).timestamp()
        os.utime(f, (ts, ts))
        old_files.append(f)
    LogWriter(tmp_path, keep_days=keep_days).prune()
    for f in old_files:
        assert not f.exists(), f"{f} should have been pruned"


def test_prune_keeps_recent_logs(tmp_path):
    f = tmp_path / "dogeautosub-recent.log"
    f.write_text("recent", encoding="utf-8")
    ts = (datetime.now() - timedelta(days=2)).timestamp()
    os.utime(f, (ts, ts))
    LogWriter(tmp_path, keep_days=7).prune()
    assert f.exists()


def test_invalid_level_falls_back_to_info(tmp_path):
    w = LogWriter(tmp_path)
    w.write("doge", "such wow")
    w.write("nonsense", "ignored level still gets recorded")
    w.flush()
    today = datetime.now().strftime("%Y%m%d")
    content = (tmp_path / f"dogeautosub-{today}.log").read_text(encoding="utf-8")
    assert "such wow" in content
    assert "ignored level still gets recorded" in content
