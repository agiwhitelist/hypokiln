"""Pipeline state machine: six stages, G1 logic, dry-run runner."""

from __future__ import annotations


import pytest


def test_six_stages_with_g1_after_stage_6(isolated_repo):
    from hypokiln.pipeline import STAGES
    assert len(STAGES) == 6
    assert STAGES[-1].n == 6
    assert STAGES[-1].gate_after == 1
    for s in STAGES[:-1]:
        assert s.gate_after is None


def test_init_state_creates_six_pending_stages(isolated_repo):
    from hypokiln.pipeline import init_state, load_state

    state = init_state("my-idea", "Test prompt for HypoKiln", autonomous=False)
    assert state.slug == "my-idea"
    assert len(state.stages) == 6
    assert all(s.status == "pending" for s in state.stages)

    # Round-trip.
    reloaded = load_state("my-idea")
    assert reloaded is not None
    assert reloaded.prompt == "Test prompt for HypoKiln"


def test_validate_slug_rejects_garbage(isolated_repo):
    from hypokiln.pipeline import validate_slug

    assert validate_slug("good-slug") == "good-slug"
    with pytest.raises(ValueError):
        validate_slug("Bad Slug")
    with pytest.raises(ValueError):
        validate_slug("-leading-dash")
    with pytest.raises(ValueError):
        validate_slug("9-leading-digit")


def test_dry_run_runner_completes_all_six(isolated_repo):
    """In autonomous mode the pre-flight checklist must clear for G1 auto-sign;
    without it the run should pause at G1. The dry-run runner doesn't author
    a pre-flight, so the autosign should refuse (PermissionError → wrapped as
    BlockingIOError-equivalent by `require_gate`; but autonomous=True path
    calls `autosign_gate` which raises PermissionError directly)."""
    from hypokiln.pipeline import init_state, run_pipeline, dry_run_runner

    state = init_state("dry-run", "Dry run probe", autonomous=True)
    with pytest.raises(PermissionError):
        run_pipeline(state, runner=dry_run_runner)
    # All six author stages still completed — only the gate refused.
    assert all(s.status == "completed" for s in state.stages)


def test_dry_run_pauses_at_g1_without_autonomous(isolated_repo):
    from hypokiln.pipeline import init_state, run_pipeline, dry_run_runner

    state = init_state("manual", "Manual G1 probe", autonomous=False)
    with pytest.raises(BlockingIOError):
        run_pipeline(state, runner=dry_run_runner)
    # All six stages completed but G1 is blocking.
    assert all(s.status == "completed" for s in state.stages)


def test_decisions_log_seeded(isolated_repo):
    from hypokiln.pipeline import init_state, product_root

    init_state("with-decisions", "Decisions log seeding test", autonomous=False)
    log = product_root("with-decisions") / "spec" / "decisions.md"
    assert log.is_file()
    text = log.read_text(encoding="utf-8")
    assert "Decisions log" in text
    assert "with-decisions" in text


def test_decisions_log_idempotent(isolated_repo):
    """seed_decisions_log must not clobber existing entries on resume."""
    from hypokiln.pipeline import init_state, product_root, seed_decisions_log

    init_state("seed", "Idempotent seed test", autonomous=False)
    log = product_root("seed") / "spec" / "decisions.md"
    log.write_text(log.read_text(encoding="utf-8") + "\n## Stage 1 — Manual entry\n")
    before = log.read_text(encoding="utf-8")
    seed_decisions_log("seed", "Idempotent seed test")
    after = log.read_text(encoding="utf-8")
    assert before == after
