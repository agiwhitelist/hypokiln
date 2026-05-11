"""GET / POST endpoints for ideas (slugs) in HypoKiln."""

from __future__ import annotations

import asyncio
import os
import shutil
import subprocess
import sys
from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from hypokiln import REPO_ROOT
from hypokiln import pipeline as _pipeline
from hypokiln.cli import _slugify

router = APIRouter(prefix="/api/runs", tags=["runs"])


# ──────────────── schemas ────────────────


class StageView(BaseModel):
    stage: int
    name: str
    status: str
    delegate: str
    started_at: str | None
    completed_at: str | None
    artifacts: list[str]
    notes: str


class RunView(BaseModel):
    slug: str
    prompt: str
    autonomous: bool
    created_at: str
    updated_at: str
    stages: list[StageView]
    gates: dict[str, dict]


class RunSummary(BaseModel):
    slug: str
    prompt: str
    autonomous: bool
    created_at: str
    updated_at: str
    done: int
    total: int
    current_stage: int | None
    blocked_on_gate: int | None


class NewRunRequest(BaseModel):
    prompt: str = Field(..., min_length=4)
    slug: str | None = None
    yolo: bool = False
    cli_bin: str | None = None


def _state_to_view(state) -> RunView:
    return RunView(
        slug=state.slug,
        prompt=state.prompt,
        autonomous=state.autonomous,
        created_at=state.created_at,
        updated_at=state.updated_at,
        stages=[StageView(**s.__dict__) for s in state.stages],
        gates=state.gates,
    )


def _state_to_summary(state) -> RunSummary:
    done = sum(1 for s in state.stages if s.status == "completed")
    current = next((s.stage for s in state.stages if s.status in {"pending", "in_progress", "failed"}), None)
    blocked_gate = None
    if current and current > 1:
        prev = state.stages[current - 2]
        if prev.status == "completed":
            from hypokiln.pipeline import STAGES
            prev_def = STAGES[prev.stage - 1]
            if prev_def.gate_after is not None and not state.gates.get(str(prev_def.gate_after), {}).get("signed"):
                blocked_gate = prev_def.gate_after
    return RunSummary(
        slug=state.slug,
        prompt=state.prompt,
        autonomous=state.autonomous,
        created_at=state.created_at,
        updated_at=state.updated_at,
        done=done,
        total=len(state.stages),
        current_stage=current,
        blocked_on_gate=blocked_gate,
    )


# ──────────────── endpoints ────────────────


@router.get("", response_model=list[RunSummary])
def list_runs() -> list[RunSummary]:
    sdir = _pipeline.state_dir()
    out: list[RunSummary] = []
    if not sdir.exists():
        return out
    for child in sorted(sdir.iterdir()):
        if not (child / "state.json").exists():
            continue
        state = _pipeline.load_state(child.name)
        if state is None:
            continue
        out.append(_state_to_summary(state))
    out.sort(key=lambda r: r.updated_at, reverse=True)
    return out


@router.get("/{slug}", response_model=RunView)
def get_run(slug: str) -> RunView:
    try:
        slug = _pipeline.validate_slug(slug)
    except ValueError as exc:
        raise HTTPException(400, str(exc))
    state = _pipeline.load_state(slug)
    if state is None:
        raise HTTPException(404, f"No run for slug {slug!r}")
    return _state_to_view(state)


@router.post("", status_code=202)
async def create_run(body: NewRunRequest) -> dict:
    """Spawn `kiln build` in the background. Returns the slug.

    The web UI polls /api/runs/<slug> for state and tails logs via
    /api/runs/<slug>/logs/<stage>/stream for live updates.
    """
    slug = _pipeline.validate_slug(body.slug or _slugify(body.prompt))
    if _pipeline.load_state(slug) is not None:
        raise HTTPException(409, f"slug {slug!r} already exists")

    kiln = shutil.which("kiln") or shutil.which("hypokiln")
    if kiln is None:
        # Fall back to invoking the module via the current python.
        kiln_argv = [sys.executable, "-m", "hypokiln.cli"]
    else:
        kiln_argv = [kiln]

    argv = [*kiln_argv, "build", body.prompt, "--slug", slug]
    if body.yolo:
        argv.append("--yolo")
    if body.cli_bin:
        argv += ["--cli-bin", body.cli_bin]

    # Detached: the parent FastAPI request must return immediately;
    # the build can take minutes. Use Popen with no stdin/stdout pipes
    # since the CLI writes its own per-stage log files.
    env = dict(os.environ)
    subprocess.Popen(
        argv,
        cwd=str(REPO_ROOT),
        env=env,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )
    return {"slug": slug, "argv": argv}


@router.post("/{slug}/retry")
async def retry_from(slug: str, body: dict) -> dict:
    """Reset stages N..end to pending and respawn `kiln resume <slug>`."""
    try:
        slug = _pipeline.validate_slug(slug)
    except ValueError as exc:
        raise HTTPException(400, str(exc))
    from_stage = int(body.get("from_stage", 1))
    state = _pipeline.load_state(slug)
    if state is None:
        raise HTTPException(404, f"No run for slug {slug!r}")
    for s in state.stages:
        if s.stage >= from_stage:
            s.status = "pending"
            s.started_at = None
            s.completed_at = None
            s.artifacts = []
            s.notes = ""
    _pipeline.save_state(state)

    kiln = shutil.which("kiln") or shutil.which("hypokiln") or sys.executable
    argv = [kiln, "resume", slug] if kiln in (shutil.which("kiln"), shutil.which("hypokiln")) else [sys.executable, "-m", "hypokiln.cli", "resume", slug]
    subprocess.Popen(
        argv,
        cwd=str(REPO_ROOT),
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )
    return {"slug": slug, "from_stage": from_stage}


@router.delete("/{slug}")
def archive_run(slug: str) -> dict:
    """Move state under `.hypokiln/state/_archive/<slug>/`."""
    try:
        slug = _pipeline.validate_slug(slug)
    except ValueError as exc:
        raise HTTPException(400, str(exc))
    src = _pipeline.state_dir() / slug
    if not src.exists():
        raise HTTPException(404, f"No run for slug {slug!r}")
    dst_root = _pipeline.state_dir() / "_archive"
    dst_root.mkdir(parents=True, exist_ok=True)
    dst = dst_root / slug
    if dst.exists():
        # Append timestamp to avoid clobbering a prior archive.
        from datetime import datetime, timezone
        suffix = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
        dst = dst_root / f"{slug}-{suffix}"
    shutil.move(str(src), str(dst))
    return {"slug": slug, "archived_to": str(dst.relative_to(REPO_ROOT))}
