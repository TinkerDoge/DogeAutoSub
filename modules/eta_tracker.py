"""Phase-weighted, EMA-smoothed time-remaining estimator.

Replaces the old ad-hoc ThroughputTracker. Always returns a value — the
cold-start fallback uses the calibrated default for the current phase
prefixed with '~' so the live status line never shows '--:--:--'.
"""
from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Optional


WORKFLOW_PHASES = {
    "subtitles": [
        {"name": "Preparing",     "weight": 0.05, "default_per_unit": 0.05},
        {"name": "Reading video", "weight": 0.05, "default_per_unit": 0.02},
        {"name": "Transcribing",  "weight": 0.70, "default_per_unit": 0.30},
        {"name": "Translating",   "weight": 0.18, "default_per_unit": 0.05},
        {"name": "Saving",        "weight": 0.02, "default_per_unit": 0.01},
    ],
    "notes": [
        {"name": "Reading transcript", "weight": 0.05, "default_per_unit": 0.0001},
        {"name": "Summarizing",        "weight": 0.90, "default_per_unit": 0.002},
        {"name": "Formatting",         "weight": 0.05, "default_per_unit": 0.0001},
    ],
    "translate": [
        {"name": "Reading file",       "weight": 0.05, "default_per_unit": 0.0001},
        {"name": "Detecting language", "weight": 0.05, "default_per_unit": 0.0001},
        {"name": "Translating",        "weight": 0.85, "default_per_unit": 0.0015},
        {"name": "Formatting output",  "weight": 0.05, "default_per_unit": 0.0001},
    ],
}


def format_remaining(seconds: float) -> str:
    seconds = max(0, int(seconds))
    if seconds < 60:
        return f"{seconds}s"
    if seconds < 3600:
        return f"{seconds // 60}m {seconds % 60}s"
    h = seconds // 3600
    m = (seconds % 3600) // 60
    return f"{h}h {m}m"


@dataclass
class _PhaseRun:
    name: str
    weight: float
    default_per_unit: float
    started_at: float
    position: float = 0.0
    total: float = 0.0
    throughput_ema: Optional[float] = None  # units of work per wall second
    completed: bool = False


class EtaTracker:
    """Track progress and time-remaining across a workflow's phases."""

    EMA_ALPHA = 0.3

    def __init__(self, workflow: str):
        if workflow not in WORKFLOW_PHASES:
            raise KeyError(f"Unknown workflow: {workflow!r}")
        self.workflow = workflow
        self._phases = {p["name"]: dict(p) for p in WORKFLOW_PHASES[workflow]}
        self._order = [p["name"] for p in WORKFLOW_PHASES[workflow]]
        self._runs: dict[str, _PhaseRun] = {}
        self._active: Optional[str] = None
        self._input_size: float = 0.0

    # ── input ────────────────────────────────────────────────────────────
    def set_input_size(self, size: float) -> None:
        """Size unit depends on workflow — audio seconds (subtitles), char count (notes/translate)."""
        self._input_size = max(0.0, size)

    def start_phase(self, name: str) -> None:
        spec = self._phases.get(name)
        if not spec:
            return
        self._active = name
        self._runs[name] = _PhaseRun(
            name=name,
            weight=spec["weight"],
            default_per_unit=spec["default_per_unit"],
            started_at=time.monotonic(),
        )

    def update_position(self, position: float, total: float) -> None:
        run = self._runs.get(self._active or "")
        if not run or total <= 0:
            return
        elapsed = max(1e-6, time.monotonic() - run.started_at)
        run.position = position
        run.total = total
        sample = position / elapsed  # units per wall second
        if run.throughput_ema is None:
            run.throughput_ema = sample
        else:
            run.throughput_ema = (
                self.EMA_ALPHA * sample + (1 - self.EMA_ALPHA) * run.throughput_ema
            )

    def complete_phase(self, name: str) -> None:
        run = self._runs.get(name)
        if run:
            run.completed = True
            run.position = run.total or run.position
        if self._active == name:
            self._active = None

    # ── outputs ──────────────────────────────────────────────────────────
    def current_phase_throughput(self) -> float:
        run = self._runs.get(self._active or "")
        return run.throughput_ema if run and run.throughput_ema else 0.0

    def overall_fraction(self) -> float:
        total = 0.0
        for name in self._order:
            spec = self._phases[name]
            run = self._runs.get(name)
            if not run:
                continue
            if run.completed:
                total += spec["weight"]
            elif run.total > 0:
                total += spec["weight"] * (run.position / run.total)
        return min(1.0, total)

    def current_eta_string(self) -> str:
        active = self._active
        if not active:
            return "—"
        run = self._runs[active]
        cold_start = (
            not run.throughput_ema
            or run.total <= 0
            or (time.monotonic() - run.started_at) < 2.0
        )
        if cold_start:
            est = self._default_total_seconds_from(active)
            return f"~{format_remaining(est)} left"
        # Measured: time left in active phase + sum of remaining-phase defaults.
        remaining_in_phase_units = max(0.0, run.total - run.position)
        phase_eta = remaining_in_phase_units / max(1e-6, run.throughput_ema)
        rest = self._default_total_seconds_from_after(active)
        return f"{format_remaining(phase_eta + rest)} left"

    # ── helpers ──────────────────────────────────────────────────────────
    def _default_total_seconds_from(self, from_phase: str) -> float:
        """Calibrated estimate for from_phase plus all later phases, scaled by input size."""
        scale = max(1.0, self._input_size)
        idx = self._order.index(from_phase)
        return sum(self._phases[n]["default_per_unit"] * scale for n in self._order[idx:])

    def _default_total_seconds_from_after(self, after_phase: str) -> float:
        scale = max(1.0, self._input_size)
        idx = self._order.index(after_phase) + 1
        return sum(self._phases[n]["default_per_unit"] * scale for n in self._order[idx:])
