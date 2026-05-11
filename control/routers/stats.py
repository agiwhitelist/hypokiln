"""Aggregate stats — success rate, per-stage durations, failure heatmap."""

from __future__ import annotations

from datetime import datetime
from statistics import mean, median

from fastapi import APIRouter

from hypokiln import pipeline as _pipeline
from hypokiln.pipeline import STAGES

router = APIRouter(prefix="/api/stats", tags=["stats"])


def _iso(s: str | None) -> datetime | None:
    if not s:
        return None
    try:
        return datetime.fromisoformat(s)
    except ValueError:
        return None


@router.get("")
def aggregate() -> dict:
    sdir = _pipeline.state_dir()
    runs = []
    if sdir.exists():
        for child in sorted(sdir.iterdir()):
            if not (child / "state.json").exists():
                continue
            state = _pipeline.load_state(child.name)
            if state is None:
                continue
            runs.append(state)

    total_runs = len(runs)
    completed_runs = sum(
        1 for r in runs if all(s.status == "completed" for s in r.stages)
    )
    failed_runs = sum(
        1 for r in runs if any(s.status == "failed" for s in r.stages)
    )

    # Per-stage stats
    stage_stats: list[dict] = []
    for sd in STAGES:
        durations: list[float] = []
        failures = 0
        for r in runs:
            stage = r.stages[sd.n - 1]
            if stage.status == "failed":
                failures += 1
            start = _iso(stage.started_at)
            end = _iso(stage.completed_at)
            if start and end:
                durations.append((end - start).total_seconds())
        stage_stats.append({
            "n": sd.n,
            "name": sd.name,
            "delegate": sd.delegate,
            "runs": len([
                r for r in runs
                if r.stages[sd.n - 1].status in {"completed", "failed"}
            ]),
            "failures": failures,
            "mean_seconds": round(mean(durations), 1) if durations else None,
            "median_seconds": round(median(durations), 1) if durations else None,
            "max_seconds": round(max(durations), 1) if durations else None,
        })

    return {
        "total_runs": total_runs,
        "completed_runs": completed_runs,
        "failed_runs": failed_runs,
        "success_rate": (completed_runs / total_runs) if total_runs else None,
        "per_stage": stage_stats,
    }
