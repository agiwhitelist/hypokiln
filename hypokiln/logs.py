"""Per-stage log files for the HypoKiln pipeline.

The CLI runner spawns one subprocess per stage. Each subprocess streams its
combined stdout+stderr into `.hypokiln/state/<slug>/logs/stage-NN.log` line by
line so the web UI can tail it live via SSE while the stage is still running.

The runner-side write path is in `hypokiln/runners/cli_runner.py`
(`_run_subprocess`). Read-side helpers live here.
"""

from __future__ import annotations

from collections import deque
from pathlib import Path

from . import pipeline as _pipeline


def log_dir(slug: str) -> Path:
    """Directory holding per-stage log files for one product."""
    return _pipeline.state_dir() / slug / "logs"


def log_path(slug: str, stage_n: int) -> Path:
    """File path for one stage's combined stdout+stderr."""
    return log_dir(slug) / f"stage-{stage_n:02d}.log"


def ensure_log_dir(slug: str) -> Path:
    d = log_dir(slug)
    d.mkdir(parents=True, exist_ok=True)
    return d


def tail_log(slug: str, stage_n: int, n_lines: int = 200) -> list[str]:
    """Return the last `n_lines` lines of a stage log, or [] if it doesn't exist."""
    p = log_path(slug, stage_n)
    if not p.exists():
        return []
    with p.open("r", encoding="utf-8", errors="replace") as fh:
        return list(deque(fh, maxlen=n_lines))


def read_log(slug: str, stage_n: int) -> str:
    p = log_path(slug, stage_n)
    if not p.exists():
        return ""
    return p.read_text(encoding="utf-8", errors="replace")


__all__ = ["ensure_log_dir", "log_dir", "log_path", "read_log", "tail_log"]
