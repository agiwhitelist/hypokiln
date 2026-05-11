"""Multi-run portfolio data — one row per slug on a shared timeline."""

from __future__ import annotations

from fastapi import APIRouter

from hypokiln import pipeline as _pipeline

router = APIRouter(prefix="/api/portfolio", tags=["portfolio"])


@router.get("")
def portfolio() -> dict:
    sdir = _pipeline.state_dir()
    rows = []
    if sdir.exists():
        for child in sorted(sdir.iterdir()):
            if not (child / "state.json").exists():
                continue
            state = _pipeline.load_state(child.name)
            if state is None:
                continue
            row_stages = [
                {
                    "n": s.stage,
                    "status": s.status,
                    "started_at": s.started_at,
                    "completed_at": s.completed_at,
                }
                for s in state.stages
            ]
            rows.append({
                "slug": state.slug,
                "prompt": state.prompt,
                "created_at": state.created_at,
                "updated_at": state.updated_at,
                "autonomous": state.autonomous,
                "stages": row_stages,
            })
    rows.sort(key=lambda r: r["created_at"])
    return {"rows": rows}
