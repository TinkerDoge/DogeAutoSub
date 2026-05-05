"""Append-only daily-rotated log writer for DogeAutoSub.

Files are written under <log_dir>/dogeautosub-YYYYMMDD.log. Files older
than `keep_days` are pruned by .prune() (called once on app start).
"""
from __future__ import annotations

import os
from datetime import datetime, timedelta
from pathlib import Path

VALID_LEVELS = {"info", "success", "warn", "error", "doge"}


class LogWriter:
    def __init__(self, log_dir: str | os.PathLike, keep_days: int = 7):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.keep_days = keep_days

    # ── Writing ────────────────────────────────────────────────────────────
    def _path(self) -> Path:
        return self.log_dir / f"dogeautosub-{datetime.now().strftime('%Y%m%d')}.log"

    def write(self, level: str, message: str) -> None:
        lvl = level.upper()
        ts = datetime.now().strftime("%H:%M:%S")
        line = f"[{ts}] [{lvl}] {message}\n"
        with self._path().open("a", encoding="utf-8") as f:
            f.write(line)

    def flush(self) -> None:
        # write() opens/closes per call so flush is implicit; provided
        # for symmetry and as a future hook if buffering is added.
        pass

    # ── Rotation ───────────────────────────────────────────────────────────
    def prune(self) -> int:
        """Delete log files older than keep_days. Returns count removed."""
        cutoff = (datetime.now() - timedelta(days=self.keep_days)).timestamp()
        removed = 0
        for entry in self.log_dir.iterdir():
            if not entry.is_file():
                continue
            if not entry.name.startswith("dogeautosub-"):
                continue
            try:
                if entry.stat().st_mtime < cutoff:
                    entry.unlink()
                    removed += 1
            except OSError:
                pass
        return removed
