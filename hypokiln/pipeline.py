"""HypoKiln pipeline state machine.

Walks the six-stage idea kiln, persists state, blocks on the G1 gate,
resumes from the last completed stage.

State file: <state_dir>/<slug>/state.json. Default state_dir is
`.hypokiln/state` (configurable via HYPOKILN_STATE_DIR).

The six stages:
  1. Trend Radar           — Trend Scout Agent
  2. Pain Extractor        — Trend Scout Agent
  3. Hypothesis Generator  — Product Strategist Agent
  4. Kill Filter           — Market Skeptic Agent
  5. Market Snapshot       — Market Skeptic Agent
  6. Selection Score       — Product Strategist Agent  → G1

The Market Skeptic critique loop (Stages 1/3/5) iterates author →
deterministic gate → critic-feedback → revise until the gate passes
or HYPOKILN_CRITIQUE_MAX_ITER (default 3) iterations exhaust.
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Literal

from . import REPO_ROOT
from .gates import GateId, is_autonomous, require_gate


StageStatus = Literal["pending", "in_progress", "completed", "failed", "skipped"]


@dataclass(frozen=True)
class StageDef:
    n: int
    name: str
    delegate: str
    gate_after: GateId | None = None


STAGES: tuple[StageDef, ...] = (
    StageDef(1, "Trend Radar", "Trend Scout Agent"),
    StageDef(2, "Pain Extractor", "Trend Scout Agent"),
    StageDef(3, "Hypothesis Generator", "Product Strategist Agent"),
    StageDef(4, "Kill Filter", "Market Skeptic Agent"),
    StageDef(5, "Market Snapshot", "Market Skeptic Agent"),
    StageDef(6, "Selection Score", "Product Strategist Agent", gate_after=1),
)


@dataclass
class StageRecord:
    stage: int
    name: str
    status: StageStatus
    delegate: str
    started_at: str | None = None
    completed_at: str | None = None
    artifacts: list[str] = field(default_factory=list)
    notes: str = ""


@dataclass
class PipelineState:
    slug: str
    prompt: str
    autonomous: bool
    created_at: str
    updated_at: str
    stages: list[StageRecord] = field(default_factory=list)
    gates: dict[str, dict] = field(default_factory=dict)


# ──────────────── helpers ────────────────


_SLUG_RE = re.compile(r"^[a-z][a-z0-9-]{0,47}[a-z0-9]$")


def validate_slug(slug: str) -> str:
    if not _SLUG_RE.match(slug):
        raise ValueError(
            f"Invalid slug {slug!r}; must be kebab-case, start with a letter, "
            "2-49 chars, [a-z0-9-] only."
        )
    return slug


def state_dir() -> Path:
    return REPO_ROOT / os.environ.get("HYPOKILN_STATE_DIR", ".hypokiln/state")


def state_path(slug: str) -> Path:
    return state_dir() / slug / "state.json"


def product_root(slug: str) -> Path:
    return REPO_ROOT / "products" / slug


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def load_state(slug: str) -> PipelineState | None:
    path = state_path(slug)
    if not path.exists():
        return None
    raw = json.loads(path.read_text(encoding="utf-8"))
    raw["stages"] = [StageRecord(**s) for s in raw.get("stages", [])]
    return PipelineState(**raw)


def save_state(state: PipelineState) -> None:
    path = state_path(state.slug)
    path.parent.mkdir(parents=True, exist_ok=True)
    state.updated_at = _now()
    payload = asdict(state)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _initial_stages() -> list[StageRecord]:
    return [
        StageRecord(stage=s.n, name=s.name, status="pending", delegate=s.delegate)
        for s in STAGES
    ]


def init_state(slug: str, prompt: str, *, autonomous: bool) -> PipelineState:
    validate_slug(slug)
    now = _now()
    state = PipelineState(
        slug=slug,
        prompt=prompt,
        autonomous=autonomous,
        created_at=now,
        updated_at=now,
        stages=_initial_stages(),
        gates={"1": {}},
    )
    save_state(state)
    seed_decisions_log(slug, prompt)
    return state


# ──────────────── decisions.md (cross-stage memory) ────────────────


_DECISIONS_HEADER_TEMPLATE = """# Decisions log — {slug}

This file is the cross-stage shared memory for product `{slug}`. Every
pipeline stage appends one entry here at completion (per Pass 0c in each
agent's `instructions.md`); every stage reads the existing entries
**before** starting its work.

The log is append-only — never modify a prior entry. If a later stage
disagrees with an earlier decision, surface the disagreement in a new
entry; the orchestrator preserves the full history for the operator to
audit.

Entry contract (≤10 lines per section):

```markdown
## Stage <N> — <Stage Name> (<ISO 8601 UTC timestamp>)
- **Decision:** <one-line summary>
- **Why:** <1–2 sentences>
- **Considered:** <comma-separated list of alternatives, or `n/a`>
- **Open questions:** <unresolved tradeoffs, or `none`>
```

Original user request:
> {prompt}

---

(stages will append below)
"""


def seed_decisions_log(slug: str, prompt: str) -> Path:
    """Pre-create `products/<slug>/spec/decisions.md` with the canonical header.

    Idempotent: if the file already exists (e.g. resuming an in-progress
    pipeline), it is left untouched so prior entries are not clobbered.
    Returns the file path either way.
    """
    target = product_root(slug) / "spec" / "decisions.md"
    if target.is_file():
        return target
    target.parent.mkdir(parents=True, exist_ok=True)
    short_prompt = prompt.strip().replace("\n", " ")
    if len(short_prompt) > 280:
        short_prompt = short_prompt[:277] + "…"
    target.write_text(
        _DECISIONS_HEADER_TEMPLATE.format(slug=slug, prompt=short_prompt),
        encoding="utf-8",
    )
    return target


# ──────────────── execution ────────────────


def _stage_def(n: int) -> StageDef:
    return STAGES[n - 1]


def _stage_record(state: PipelineState, n: int) -> StageRecord:
    return state.stages[n - 1]


def _next_pending(state: PipelineState, skip: Iterable[int] = ()) -> StageRecord | None:
    skipset = set(skip)
    for s in state.stages:
        if s.stage in skipset:
            continue
        if s.status in {"pending", "in_progress", "failed"}:
            return s
    return None


def step_one_stage(
    state: PipelineState,
    *,
    runner,  # callable: (state, stage_def) -> tuple[StageStatus, list[str], str]
    skip: Iterable[int] = (),
) -> StageRecord | None:
    """Advance the pipeline by one stage. Returns the executed StageRecord,
    or None if the pipeline is done (or fully skipped).

    `runner(state, stage_def)` performs the actual work and returns
    (status, artifacts, notes). In dry-run mode the runner is a no-op stub.
    """
    rec = _next_pending(state, skip=skip)
    if rec is None:
        return None

    sd = _stage_def(rec.stage)

    # Pre-stage gate check (gate sits AFTER a previous stage; we block before
    # entering the *next* stage).
    if rec.stage > 1:
        prev = _stage_def(rec.stage - 1)
        if prev.gate_after is not None:
            require_gate(product_root(state.slug), prev.gate_after, autonomous=state.autonomous)
            state.gates[str(prev.gate_after)] = {
                "signed": True,
                "verified_at": _now(),
            }

    rec.status = "in_progress"
    rec.started_at = _now()
    save_state(state)

    try:
        status, artifacts, notes = runner(state, sd)
    except Exception as exc:  # noqa: BLE001
        rec.status = "failed"
        rec.notes = f"runner error: {exc}"
        rec.completed_at = _now()
        save_state(state)
        raise

    rec.status = status
    rec.artifacts = list(artifacts)
    rec.notes = notes[:280] if notes else ""
    rec.completed_at = _now()
    save_state(state)
    return rec


def run_pipeline(
    state: PipelineState,
    *,
    runner,
    only_stages: Iterable[int] | None = None,
    skip: Iterable[int] = (),
) -> PipelineState:
    """Run the pipeline to completion (or until G1 blocks)."""
    only = set(only_stages) if only_stages else None
    while True:
        rec = _next_pending(state, skip=skip)
        if rec is None:
            break
        if only is not None and rec.stage not in only:
            rec.status = "skipped"
            save_state(state)
            continue
        executed = step_one_stage(state, runner=runner, skip=skip)
        if executed is None or executed.status == "failed":
            break

    # Final gate check: Stage 6 has a gate_after — require it once all
    # stages complete, since no further stage will trigger it.
    last_stage_def = STAGES[-1]
    if last_stage_def.gate_after is not None:
        last_rec = _stage_record(state, last_stage_def.n)
        if last_rec.status == "completed" and not state.gates.get(
            str(last_stage_def.gate_after), {}
        ).get("signed"):
            require_gate(
                product_root(state.slug),
                last_stage_def.gate_after,
                autonomous=state.autonomous,
            )
            state.gates[str(last_stage_def.gate_after)] = {
                "signed": True,
                "verified_at": _now(),
            }
            save_state(state)
    return state


def dry_run_runner(state: PipelineState, sd: StageDef):
    """No-op runner used by smoke tests and `--dry-run`. Records the stage as
    completed with a synthetic artifact path under the state dir."""
    artifact = state_dir() / state.slug / f"stage-{sd.n:02d}.dryrun.txt"
    artifact.parent.mkdir(parents=True, exist_ok=True)
    artifact.write_text(f"Dry-run for stage {sd.n} ({sd.name}) at {_now()}\n", encoding="utf-8")
    try:
        rel = str(artifact.relative_to(REPO_ROOT))
    except ValueError:
        rel = str(artifact)
    return ("completed", [rel], f"dry-run via {sd.delegate}")


__all__ = [
    "PipelineState",
    "STAGES",
    "StageDef",
    "StageRecord",
    "dry_run_runner",
    "init_state",
    "is_autonomous",
    "load_state",
    "product_root",
    "run_pipeline",
    "save_state",
    "seed_decisions_log",
    "state_dir",
    "state_path",
    "step_one_stage",
    "validate_slug",
]
