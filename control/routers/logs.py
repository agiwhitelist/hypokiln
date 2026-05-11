"""Per-stage log tail + SSE stream."""

from __future__ import annotations

import asyncio
import os

from fastapi import APIRouter, HTTPException
from sse_starlette.sse import EventSourceResponse

from hypokiln import logs as _logs
from hypokiln import pipeline as _pipeline

router = APIRouter(prefix="/api/runs", tags=["logs"])


@router.get("/{slug}/logs/{stage_n}")
def tail(slug: str, stage_n: int, n: int = 200) -> dict:
    try:
        slug = _pipeline.validate_slug(slug)
    except ValueError as exc:
        raise HTTPException(400, str(exc))
    lines = _logs.tail_log(slug, stage_n, n_lines=n)
    return {
        "slug": slug,
        "stage": stage_n,
        "lines": lines,
        "path": str(_logs.log_path(slug, stage_n).relative_to(_pipeline.REPO_ROOT))
            if _logs.log_path(slug, stage_n).exists() else None,
    }


@router.get("/{slug}/logs/{stage_n}/stream")
async def stream(slug: str, stage_n: int):
    """SSE stream of new log lines as they are written.

    Yields one event per appended line; closes when the stage completes
    (status moves to completed/failed) or after `HYPOKILN_SSE_IDLE_MAX_S`.
    """
    try:
        slug = _pipeline.validate_slug(slug)
    except ValueError as exc:
        raise HTTPException(400, str(exc))

    log_path = _logs.log_path(slug, stage_n)
    idle_max = int(os.environ.get("HYPOKILN_SSE_IDLE_MAX_S", "300"))

    async def gen():
        last_size = 0
        if log_path.exists():
            last_size = log_path.stat().st_size
            # Send the existing tail as initial state.
            with log_path.open("r", encoding="utf-8", errors="replace") as fh:
                tail_lines = fh.readlines()[-200:]
            yield {"event": "init", "data": "".join(tail_lines)}
        idle = 0
        while True:
            await asyncio.sleep(1.0)
            if log_path.exists():
                size = log_path.stat().st_size
                if size > last_size:
                    with log_path.open("r", encoding="utf-8", errors="replace") as fh:
                        fh.seek(last_size)
                        chunk = fh.read()
                    last_size = size
                    idle = 0
                    yield {"event": "append", "data": chunk}
                else:
                    idle += 1
            else:
                idle += 1
            if idle >= idle_max:
                yield {"event": "idle", "data": "no new log lines"}
                break

    return EventSourceResponse(gen())
