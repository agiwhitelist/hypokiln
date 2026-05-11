"""Seed demo runs into .hypokiln/state/ so the UI has something to render.

Creates four ideas in different states:
  - signed-and-shipped     — all six stages complete, G1 signed (autonomous)
  - waiting-on-g1          — all six stages complete, G1 unsigned
  - mid-kill-filter        — stages 1-3 done, Stage 4 in progress
  - early-stage            — Stage 1 in progress

Run:
    python scripts/seed_demo.py
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from hypokiln import REPO_ROOT
from hypokiln.pipeline import STAGES, init_state, save_state, product_root


def _now_minus(days: int, hours: int = 0) -> str:
    return (datetime.now(timezone.utc) - timedelta(days=days, hours=hours)).isoformat(timespec="seconds")


def seed_signed_and_shipped() -> None:
    state = init_state(
        "ssl-renewal-alarm",
        'Build me a $3/mo SSL renewal alarm for solo devs running side-project domains',
        autonomous=True,
    )
    base = _now_minus(2)
    for i, s in enumerate(state.stages):
        s.status = "completed"
        s.started_at = _now_minus(2, hours=i * 2)
        s.completed_at = _now_minus(2, hours=i * 2 + 1)
        s.notes = f"stage-{s.stage} demo completion"
        s.artifacts = [f"products/ssl-renewal-alarm/research/round-001.json"] if s.stage == 3 else []
    state.gates["1"] = {"signed": True, "verified_at": _now_minus(1, hours=20)}
    save_state(state)

    # Seed the architecture + decisions + preflight for realism
    proot = product_root("ssl-renewal-alarm")
    (proot / "spec").mkdir(parents=True, exist_ok=True)
    (proot / "research").mkdir(parents=True, exist_ok=True)
    (proot / "spec" / "gate-1-preflight.md").write_text(
        "---\nalarm_count: 1\n---\n# Pre-flight\n\n**Verdict.** ok across 9/10 questions.\n",
        encoding="utf-8",
    )
    (proot / "spec" / "architecture.md").write_text(
        "# Architecture — ssl-renewal-alarm\n\n"
        "- **form_factor:** email-first\n"
        "- **archetype:** monitor/alarm\n"
        "- **wow_moment:** \"first cert scanned in <45s\"\n"
        "- **viral_mechanic:** before_after_proof — embeds a one-line status badge per domain\n",
        encoding="utf-8",
    )
    (proot / "spec" / "gate-1-approval.md").write_text(
        "# Gate 1 — operator sign-off\n\n"
        "```\napproved: yes\napprover: demo-operator\ndate: " + _now_minus(1, hours=20) + "\n```\n",
        encoding="utf-8",
    )


def seed_waiting_on_g1() -> None:
    state = init_state(
        "stripe-burn-bot",
        'A $9/mo Slack-bot that scans solo founders Stripe + GitHub once a day and posts burn / runway',
        autonomous=False,
    )
    for i, s in enumerate(state.stages):
        s.status = "completed"
        s.started_at = _now_minus(0, hours=6 - i)
        s.completed_at = _now_minus(0, hours=5 - i)
        s.notes = f"stage-{s.stage} draft"
    save_state(state)


def seed_mid_kill_filter() -> None:
    state = init_state(
        "ai-changelog",
        'AI-generated changelogs from commit messages for solo OSS maintainers at $5/mo',
        autonomous=True,
    )
    for i, s in enumerate(state.stages):
        if s.stage <= 3:
            s.status = "completed"
            s.started_at = _now_minus(0, hours=3 - i)
            s.completed_at = _now_minus(0, hours=2 - i)
        elif s.stage == 4:
            s.status = "in_progress"
            s.started_at = _now_minus(0, hours=0)
            s.notes = "running 13 hard-kill checks"
        else:
            s.status = "pending"
    save_state(state)


def seed_early_stage() -> None:
    state = init_state(
        "voice-meeting-summary",
        'Real-time voice transcript + decision extraction for async standups, $12/mo per team',
        autonomous=False,
    )
    state.stages[0].status = "in_progress"
    state.stages[0].started_at = _now_minus(0, hours=0)
    state.stages[0].notes = "Trend Scout scanning HN + ProductHunt + Reddit"
    save_state(state)


def main() -> None:
    print(f"Seeding demo into {REPO_ROOT / '.hypokiln' / 'state'} …")
    seed_signed_and_shipped()
    print("  ✓ ssl-renewal-alarm (all six stages complete, G1 signed)")
    seed_waiting_on_g1()
    print("  ✓ stripe-burn-bot (all six complete, G1 unsigned — waiting on human)")
    seed_mid_kill_filter()
    print("  ✓ ai-changelog (Stage 4 in progress)")
    seed_early_stage()
    print("  ✓ voice-meeting-summary (Stage 1 in progress)")
    print()
    print("Now: `make dev` and open http://localhost:3000")


if __name__ == "__main__":
    main()
