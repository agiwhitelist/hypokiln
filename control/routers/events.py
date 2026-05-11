"""Global SSE stream — broadcasts state.json changes across all slugs.

The web UI subscribes to this once at app boot and receives a tiny event
whenever any state.json under .hypokiln/state/ is modified. The browser
then re-fetches the affected slug's full state for a fresh render.
"""

from __future__ import annotations

import asyncio

from fastapi import APIRouter

from hypokiln import pipeline as _pipeline

router = APIRouter(prefix="/api/events", tags=["events"])


@router.get("/stream")
async def stream():
    """Emit `state` events whenever a state.json mtime changes."""
    sdir = _pipeline.state_dir()

    async def gen():
        seen: dict[str, float] = {}
        # Initial snapshot of every state.json mtime so we don't fire on first scan.
        if sdir.exists():
            for child in sdir.iterdir():
                p = child / "state.json"
                if p.is_file():
                    seen[child.name] = p.stat().st_mtime
        yield {"event": "ready", "data": "subscribed"}

        while True:
            await asyncio.sleep(2.0)
            if not sdir.exists():
                continue
            for child in sdir.iterdir():
                p = child / "state.json"
                if not p.is_file():
                    continue
                m = p.stat().st_mtime
                prev = seen.get(child.name)
                if prev is None or m > prev:
                    seen[child.name] = m
                    yield {"event": "state", "data": child.name}
