"""Critique-loop wrapper around the per-stage CLI runner.

Why this exists
---------------
The default pipeline stage is one prompt, one response, zero iterations:
the author produces a draft and the pipeline moves on. There is no peer
review mid-flight; a downstream gate failure only surfaces as a stage
failure that the operator has to chase manually.

This runner wraps a base stage runner with the loop:

    for iteration in 1..N:
        author_status = base_runner(state, sd)          # one CLI session
        gate_result   = gate.run(slug)                  # deterministic check
        if gate_result.passed:    return ("completed", …)
        if iteration == N:        return ("failed", …, "exhausted")
        critic_status = spawn_critic(...)               # critic CLI session
        # critic writes products/<slug>/.critique-log/stage-N.feedback.md
        # author reads that file on the next iteration (Pass 0b)

Memory model
------------
All cross-iteration state is filesystem-backed; no in-process memory
across iterations. Files live under `products/<slug>/.critique-log/`.
"""

from __future__ import annotations

import json
import subprocess
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from hypokiln import REPO_ROOT
from hypokiln.runners.cli_runner import (
    CliRunnerConfig,
    RunCtx,
    _run_subprocess,
    _scrub_env,
    _read_instructions,
    resolve_executable,
    resolve_spec,
)
from hypokiln.skill_loader import instructions_for


# ──────────────── gate primitives ────────────────


@dataclass(frozen=True)
class GateResult:
    """Outcome of a deterministic gate check."""

    passed: bool
    raw_stdout: str
    raw_stderr: str = ""
    returncode: int = 0


@dataclass(frozen=True)
class CritiqueGate:
    """A deterministic command whose exit code determines pass/fail."""

    name: str
    argv: tuple[str, ...]
    timeout_sec: int = 180
    cwd: Path | None = None
    cwd_template: str | None = None

    def _resolved_cwd(self, slug: str) -> str:
        if self.cwd_template is not None:
            rel = self.cwd_template.format(slug=slug)
            return str((REPO_ROOT / rel).resolve())
        if self.cwd is not None:
            return str(self.cwd)
        return str(REPO_ROOT)

    def run(self, slug: str) -> GateResult:
        cmd = [tok.format(slug=slug) for tok in self.argv]
        cwd = self._resolved_cwd(slug)
        try:
            proc = subprocess.run(
                cmd,
                cwd=cwd,
                env=_scrub_env(),
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=self.timeout_sec,
            )
        except subprocess.TimeoutExpired as exc:
            return GateResult(
                passed=False,
                raw_stdout="",
                raw_stderr=f"gate {self.name!r} timed out after {self.timeout_sec}s: {exc}",
                returncode=124,
            )
        except FileNotFoundError as exc:
            return GateResult(
                passed=False,
                raw_stdout="",
                raw_stderr=f"gate {self.name!r} binary not on PATH: {exc}",
                returncode=127,
            )
        return GateResult(
            passed=(proc.returncode == 0),
            raw_stdout=proc.stdout or "",
            raw_stderr=proc.stderr or "",
            returncode=proc.returncode,
        )


@dataclass(frozen=True)
class CritiqueConfig:
    """Per-stage configuration for the critique wrapper."""

    gate: CritiqueGate
    critic_delegate: str
    max_iterations: int = 3


# ──────────────── transcript / feedback paths ────────────────


def _log_dir(slug: str) -> Path:
    d = REPO_ROOT / "products" / slug / ".critique-log"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _paths(slug: str, stage_n: int) -> dict[str, Path]:
    d = _log_dir(slug)
    return {
        "transcript": d / f"stage-{stage_n:02d}.transcript.jsonl",
        "feedback": d / f"stage-{stage_n:02d}.feedback.md",
        "gate_output": d / f"stage-{stage_n:02d}.gate-output.txt",
        "critic_log": d / f"stage-{stage_n:02d}.critic.log",
    }


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


_TRANSIENT_AUTHOR_ERROR_SIGNATURES: tuple[str, ...] = (
    "api error: internal server error",
    "api error: overloaded",
    "rate_limit",
    "rate limit",
    "rate-limit",
    "openai: server_error",
    "openai: rate_limit_exceeded",
    "connection reset",
    "connection refused",
    "timeout",
    "504 gateway",
    "502 bad gateway",
    "503 service unavailable",
)


_TRANSIENT_RETRY_DELAYS: tuple[int, ...] = (10, 30)


def _looks_transient(notes: str | None) -> bool:
    if not notes:
        return False
    low = notes.lower()
    return any(sig in low for sig in _TRANSIENT_AUTHOR_ERROR_SIGNATURES)


def _run_author_with_transient_retry(
    base_runner: Callable,
    state,
    sd,
    *,
    transcript_path: Path,
    iteration: int,
) -> tuple[str, list[str], str]:
    """Call `base_runner`; retry on transient API errors only."""
    last: tuple[str, list[str], str] = ("failed", [], "")
    for attempt_idx, delay in enumerate(((0,) + _TRANSIENT_RETRY_DELAYS), start=1):
        if delay > 0:
            time.sleep(delay)
            _append_transcript(
                transcript_path,
                {
                    "event": "author_retry",
                    "iter": iteration,
                    "attempt": attempt_idx,
                    "delay_s": delay,
                    "reason": "transient API error on previous attempt",
                },
            )
        status, artifacts, notes = base_runner(state, sd)
        last = (status, list(artifacts) if artifacts else [], notes or "")
        if status == "completed":
            return last
        if not _looks_transient(notes):
            return last
    return last


def _append_transcript(path: Path, payload: dict) -> None:
    payload = {"ts": _now(), **payload}
    line = json.dumps(payload, ensure_ascii=False) + "\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(line)


# ──────────────── critic spawn ────────────────


def _build_critic_prompt(
    *,
    critic_delegate: str,
    state,
    sd,
    feedback_rel: str,
    gate_output_rel: str,
    gate_name: str,
    iteration: int,
    user_prompt_text: str,
) -> str:
    """Compose the critic's prompt."""
    base = _read_instructions(critic_delegate)
    instructions = instructions_for(critic_delegate, base_instructions=base)
    return (
        f"You are operating under the following HypoKiln role, in CRITIQUE MODE.\n\n"
        f"[ROLE INSTRUCTIONS]\n{instructions}\n\n"
        f"[CRITIQUE TASK]\n"
        f"Stage {sd.n} ({sd.name}) of product {state.slug!r} ran and FAILED the "
        f"deterministic gate `{gate_name}`.\n"
        f"This is iteration {iteration} of the critique loop.\n"
        f"You are the CRITIC, not the author. You do NOT modify any artifact "
        f"files. You produce one structured critique that the author reads "
        f"on its next iteration.\n\n"
        f"## What to do\n"
        f"1. Read the gate output at `{gate_output_rel}` (relative to repo "
        f"root). Violations there are the AUTHORITATIVE list of what is "
        f"broken. Quote them by their identifier in your critique.\n"
        f"2. Read the artifacts under `products/{state.slug}/` (especially "
        f"`spec/` and `research/`).\n"
        f"3. Decide for each violation: who fixes it, what specifically to "
        f"change. Be concrete and testable.\n"
        f"4. WRITE your critique to `{feedback_rel}`. OVERWRITE any existing "
        f"content there. Use this exact structure:\n\n"
        f"   ```markdown\n"
        f"   # Critique for stage {sd.n} ({sd.name}) — iteration {iteration}\n"
        f"   \n"
        f"   ## Verdict: REJECT\n"
        f"   \n"
        f"   ## Violations (from `{gate_name}`)\n"
        f"   - R1: <quote the violation as printed by the gate>\n"
        f"   - R3: <next violation>\n"
        f"   \n"
        f"   ## Required actions (the author MUST do these before next gate run)\n"
        f"   - <one-line directive, concrete enough to be checked>\n"
        f"   - <…>\n"
        f"   \n"
        f"   ## What to keep\n"
        f"   <2-3 sentences: which parts of the current draft are good>\n"
        f"   ```\n\n"
        f"## Hard rules\n"
        f"- Do NOT edit, delete, or move any file other than `{feedback_rel}`.\n"
        f"- Do NOT run `kiln` or `python -m hypokiln.cli`. The gate was already "
        f"run; trust its output.\n"
        f"- Do NOT spawn long-running work. Read, judge, write. <5 minutes.\n\n"
        f"User request that started this pipeline:\n  {user_prompt_text!r}\n\n"
        f"When done, emit: `SUMMARY: critique written to {feedback_rel}`\n"
    )


def _run_critic(
    *,
    critic_delegate: str,
    state,
    sd,
    iteration: int,
    paths_: dict[str, Path],
    gate: CritiqueGate,
    config: CliRunnerConfig,
    product_dir: Path,
    user_prompt_text: str,
) -> tuple[str, str]:
    """Spawn one critic CLI invocation. Returns (status, notes)."""
    spec = resolve_spec(config.binary)
    try:
        executable = resolve_executable(spec)
    except FileNotFoundError as exc:
        return ("failed", f"{spec.name} not on PATH: {exc}")

    feedback_rel = paths_["feedback"].relative_to(REPO_ROOT).as_posix()
    gate_output_rel = paths_["gate_output"].relative_to(REPO_ROOT).as_posix()
    prompt = _build_critic_prompt(
        critic_delegate=critic_delegate,
        state=state,
        sd=sd,
        feedback_rel=feedback_rel,
        gate_output_rel=gate_output_rel,
        gate_name=gate.name,
        iteration=iteration,
        user_prompt_text=user_prompt_text,
    )

    ctx = RunCtx(slug=state.slug, product_dir=product_dir)
    argv = spec.build_argv(executable, prompt, ctx)

    try:
        result = _run_subprocess(
            argv,
            cwd=str(product_dir),
            env=_scrub_env(),
            timeout_sec=config.timeout_sec,
            input_text=prompt if spec.prompt_via_stdin else None,
            log_file=paths_["critic_log"],
        )
    except FileNotFoundError as exc:
        return ("failed", f"{spec.name} not on PATH: {exc}")
    except subprocess.TimeoutExpired:
        return ("failed", f"{spec.name} critic timed out after {config.timeout_sec}s")

    if result.returncode != 0:
        tail = (result.stdout or "")[-280:].strip()
        return ("failed", f"{spec.name} critic exit_code={result.returncode}: {tail}")
    if not paths_["feedback"].is_file():
        return (
            "failed",
            f"critic finished cleanly but did not write {feedback_rel}; "
            "the critic prompt was probably ignored or the model did not "
            "understand the task.",
        )
    return ("completed", f"feedback written ({paths_['feedback'].stat().st_size} bytes)")


# ──────────────── runner factory ────────────────


def make_critique_runner(
    base_runner: Callable,
    *,
    config: CritiqueConfig,
    cli_config: CliRunnerConfig,
    user_prompt_text: str = "",
):
    """Wrap `base_runner` with the critique loop pattern."""

    def runner(state, sd):
        product_dir = (REPO_ROOT / "products" / state.slug).resolve()
        product_dir.mkdir(parents=True, exist_ok=True)
        paths_ = _paths(state.slug, sd.n)

        paths_["feedback"].unlink(missing_ok=True)
        paths_["gate_output"].unlink(missing_ok=True)
        _append_transcript(
            paths_["transcript"],
            {
                "event": "stage_start",
                "stage": sd.n,
                "stage_name": sd.name,
                "delegate": sd.delegate,
                "critic": config.critic_delegate,
                "gate": config.gate.name,
                "max_iterations": config.max_iterations,
            },
        )

        last_artifacts: list[str] = []
        for iteration in range(1, config.max_iterations + 1):
            iter_started = time.monotonic()

            status, artifacts, notes = _run_author_with_transient_retry(
                base_runner, state, sd, transcript_path=paths_["transcript"],
                iteration=iteration,
            )
            last_artifacts = list(artifacts) if artifacts else []
            _append_transcript(
                paths_["transcript"],
                {
                    "event": "author_done",
                    "iter": iteration,
                    "status": status,
                    "duration_s": round(time.monotonic() - iter_started, 2),
                    "artifacts": last_artifacts[:20],
                    "notes": (notes or "")[:280],
                },
            )
            if status != "completed":
                return (
                    status,
                    last_artifacts,
                    f"author failed at iter {iteration}/{config.max_iterations}: {notes}",
                )

            gate_result = config.gate.run(state.slug)
            paths_["gate_output"].write_text(
                gate_result.raw_stdout + "\n" + gate_result.raw_stderr,
                encoding="utf-8",
            )
            _append_transcript(
                paths_["transcript"],
                {
                    "event": "gate",
                    "iter": iteration,
                    "name": config.gate.name,
                    "passed": gate_result.passed,
                    "returncode": gate_result.returncode,
                    "stdout_tail": gate_result.raw_stdout[-500:],
                },
            )
            if gate_result.passed:
                paths_["feedback"].unlink(missing_ok=True)
                return (
                    "completed",
                    last_artifacts,
                    f"passed {config.gate.name} after {iteration} iteration(s)",
                )

            if iteration >= config.max_iterations:
                _append_transcript(
                    paths_["transcript"],
                    {
                        "event": "exhausted",
                        "iter": iteration,
                        "name": config.gate.name,
                    },
                )
                return (
                    "failed",
                    last_artifacts,
                    f"critique loop for {config.gate.name} exhausted after "
                    f"{config.max_iterations} iterations; see "
                    f"{paths_['transcript'].relative_to(REPO_ROOT).as_posix()}",
                )

            critic_status, critic_notes = _run_critic(
                critic_delegate=config.critic_delegate,
                state=state,
                sd=sd,
                iteration=iteration,
                paths_=paths_,
                gate=config.gate,
                config=cli_config,
                product_dir=product_dir,
                user_prompt_text=user_prompt_text,
            )
            _append_transcript(
                paths_["transcript"],
                {
                    "event": "critic_done",
                    "iter": iteration,
                    "status": critic_status,
                    "notes": critic_notes[:280],
                },
            )
            if critic_status != "completed":
                return (
                    "failed",
                    last_artifacts,
                    f"critic failed at iter {iteration}: {critic_notes}",
                )

        return ("failed", last_artifacts, "critique runner reached unreachable state")

    return runner


# ──────────────── prebuilt gates ────────────────


# Stage 1 (Trend Radar). Lint of `products/<slug>/research/trend-radar.md`:
# minimum signal count, every signal has a URL, ≥3 distinct sources, dated.
TREND_RADAR_GATE = CritiqueGate(
    name="trend-radar-audit",
    argv=("python", "-m", "hypokiln.cli", "trend-radar-audit", "{slug}"),
)


# Stage 3 (Hypothesis Generator). Validates the latest
# `products/<slug>/research/round-*.json`: ≥8 hypotheses, valid JSON,
# every hypothesis has the required keys, no template-shaped wedges.
HYPOTHESIS_AUDIT_GATE = CritiqueGate(
    name="hypothesis-audit",
    argv=("python", "-m", "hypokiln.cli", "hypothesis-audit", "{slug}"),
)


# Stage 5 (Market Snapshot). Lint of three Market Skeptic outputs:
# market-snapshot.md, competitor-analysis.md, pricing-research.md.
MARKET_SNAPSHOT_GATE = CritiqueGate(
    name="market-snapshot-audit",
    argv=("python", "-m", "hypokiln.cli", "market-snapshot-audit", "{slug}"),
)


__all__ = [
    "CritiqueConfig",
    "CritiqueGate",
    "GateResult",
    "HYPOTHESIS_AUDIT_GATE",
    "MARKET_SNAPSHOT_GATE",
    "TREND_RADAR_GATE",
    "make_critique_runner",
]
