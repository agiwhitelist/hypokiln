"""CLI runner: drive each pipeline stage via a logged-in coding CLI.

Supported binaries (BYO Bin via HYPOKILN_CLI_BIN):

  codex   — OpenAI Codex CLI         (`codex login` once, ChatGPT Plus/Pro)
  claude  — Anthropic Claude Code    (`claude /login`, Claude.ai Pro)
  gemini  — Google Gemini CLI        (`gemini auth`, AI Studio account)

Authentication is whatever the CLI established locally — we never touch
~/.codex, ~/.config/claude, ~/.gemini. This runner only spawns the binary
with a scoped working dir, a combined system+task prompt, and a hard timeout.

The runner is intentionally dumb: it does NOT try to feed the CLI its own
tool-use loop. Each stage is one prompt, one response. Multi-step work
inside a stage is the CLI's job (codex / claude already do agentic loops
internally).
"""

from __future__ import annotations

import os
import shutil
import subprocess
import threading
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from hypokiln import REPO_ROOT
from hypokiln.logs import ensure_log_dir, log_path
from hypokiln.skill_loader import instructions_for


# ──────────────── per-binary spec ────────────────


@dataclass(frozen=True)
class RunCtx:
    """Per-invocation context passed to argv builders."""

    slug: str
    product_dir: Path  # absolute path to products/<slug>/


@dataclass(frozen=True)
class CliSpec:
    """How to invoke one CLI binary in non-interactive mode."""

    name: str
    default_executable: str
    build_argv: Callable[[str, str, RunCtx], list[str]]
    login_hint: str
    # When True, the runner passes the prompt via stdin instead of argv.
    # Required for multi-line prompts on Windows (argv is single-line on
    # subprocess.run with shell=False) and for prompts longer than the
    # OS argv limit.
    prompt_via_stdin: bool = False


def _argv_codex(executable: str, prompt: str, ctx: RunCtx) -> list[str]:
    return [
        executable,
        "exec",
        "--full-auto",
        "--skip-git-repo-check",
        "--sandbox",
        "danger-full-access",
        "--cd",
        str(ctx.product_dir),
        "-",
    ]


def _argv_claude(executable: str, prompt: str, ctx: RunCtx) -> list[str]:
    return [
        executable,
        "-p",
        "--add-dir",
        str(ctx.product_dir),
        "--allowed-tools",
        "Bash Read Write Edit Glob Grep TodoWrite Task WebFetch WebSearch",
    ]


def _argv_gemini(executable: str, prompt: str, ctx: RunCtx) -> list[str]:
    return [executable, "-p", prompt]


SPECS: dict[str, CliSpec] = {
    "codex": CliSpec(
        name="codex",
        default_executable="codex",
        build_argv=_argv_codex,
        login_hint="Run `codex login` once (opens ChatGPT OAuth flow).",
        prompt_via_stdin=True,
    ),
    "claude": CliSpec(
        name="claude",
        default_executable="claude",
        build_argv=_argv_claude,
        login_hint="Run `claude` once and enter `/login` (Claude.ai OAuth).",
        prompt_via_stdin=True,
    ),
    "gemini": CliSpec(
        name="gemini",
        default_executable="gemini",
        build_argv=_argv_gemini,
        login_hint="Run `gemini auth` (Google AI Studio).",
    ),
}


# Env keys we strip from the subprocess. The CLI uses its own session
# token, not provider API keys.
_SECRET_PREFIXES = (
    "OPENAI_API",
    "ANTHROPIC_API",
    "GOOGLE_API",
    "STRIPE_",
    "SUPABASE_SERVICE_ROLE",
)


# ──────────────── helpers ────────────────


def resolve_spec(binary_name: str) -> CliSpec:
    if binary_name not in SPECS:
        raise ValueError(
            f"Unknown CLI {binary_name!r}; expected one of {sorted(SPECS)}"
        )
    return SPECS[binary_name]


def resolve_executable(spec: CliSpec, override: str | None = None) -> str:
    """Find the binary on PATH (with .cmd / .exe / .bat fallback on Windows)."""
    candidate = override or os.environ.get(
        f"HYPOKILN_{spec.name.upper()}_BIN", ""
    ).strip() or spec.default_executable

    if os.path.sep in candidate or candidate.startswith("."):
        return candidate

    found = shutil.which(candidate)
    if found:
        return found
    for ext in (".cmd", ".exe", ".bat"):
        found = shutil.which(candidate + ext)
        if found:
            return found
    raise FileNotFoundError(
        f"{candidate!r} not found on PATH. {spec.login_hint}"
    )


def _scrub_env() -> dict:
    return {
        k: v
        for k, v in os.environ.items()
        if not any(k.startswith(p) for p in _SECRET_PREFIXES)
    }


def _read_instructions(stage_delegate: str) -> str:
    """Find the instructions.md for the agent named `stage_delegate`.

    Maps display names ("Trend Scout Agent") to folder names
    ("trend_scout_agent") with a deterministic snake_case rule.
    """
    folder = (
        stage_delegate.lower()
        .replace(" agent", "_agent")
        .replace(" ", "_")
    )
    if not folder.endswith("_agent"):
        folder = f"{folder}_agent"
    path = REPO_ROOT / "agents" / folder / "instructions.md"
    if not path.is_file():
        return f"You are the {stage_delegate}. Follow HypoKiln factory templates."
    return path.read_text(encoding="utf-8")


def build_combined_prompt(
    *,
    instructions: str,
    stage_n: int,
    stage_name: str,
    product_slug: str,
    user_prompt: str,
) -> str:
    """Combine system instructions + stage context + user request into one prompt."""
    return (
        f"You are operating under the following HypoKiln role.\n\n"
        f"[ROLE INSTRUCTIONS]\n{instructions}\n\n"
        f"[CURRENT TASK]\n"
        f"Pipeline stage {stage_n}: {stage_name}\n"
        f"Product slug: {product_slug}\n"
        f"Working directory: products/{product_slug}/\n\n"
        f"User request that started this pipeline:\n  {user_prompt!r}\n\n"
        f"Produce the artifacts this role is responsible for. List every "
        f"file you create or modify (one per line, repo-relative path). "
        f"At the end, output a one-line summary prefixed with 'SUMMARY: '."
    )


def _extract_artifacts(stdout: str, *, slug: str) -> list[str]:
    artifacts: list[str] = []
    for raw in stdout.splitlines():
        line = raw.strip("-•*\t ")
        if line.startswith(("products/", f"products\\{slug}", "factory/")):
            artifacts.append(line)
        if len(artifacts) >= 30:
            break
    return artifacts


# ──────────────── teed subprocess (live log file) ────────────────


@dataclass
class _SubprocResult:
    """Drop-in for the subset of subprocess.CompletedProcess we use."""

    returncode: int
    stdout: str
    stderr: str = ""  # always empty: we merge stderr into stdout for the log


def _run_subprocess(
    argv: list[str],
    *,
    cwd: str,
    env: dict,
    timeout_sec: int,
    input_text: str | None,
    log_file: Path | None,
) -> _SubprocResult:
    """Spawn argv, tee combined stdout+stderr to `log_file` line by line.

    Raises FileNotFoundError if the binary is not on PATH.
    Raises subprocess.TimeoutExpired if the process exceeds `timeout_sec`.
    """
    if log_file is not None:
        log_file.parent.mkdir(parents=True, exist_ok=True)

    log_fh = None
    if log_file is not None:
        log_fh = log_file.open("w", encoding="utf-8")
        header = (
            f"# HypoKiln stage log — {datetime.now(timezone.utc).isoformat(timespec='seconds')}\n"
            f"# argv: {' '.join(argv)}\n"
            f"# cwd: {cwd}\n"
            f"# timeout: {timeout_sec}s\n"
            f"# {'-' * 60}\n"
        )
        log_fh.write(header)
        log_fh.flush()

    try:
        proc = subprocess.Popen(
            argv,
            cwd=cwd,
            env=env,
            stdin=subprocess.PIPE if input_text is not None else None,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            bufsize=1,
        )
    except FileNotFoundError:
        if log_fh is not None:
            log_fh.write("# ERROR: binary not found on PATH\n")
            log_fh.close()
        raise

    captured: list[str] = []
    timed_out = False

    def _reader() -> None:
        assert proc.stdout is not None
        for line in proc.stdout:
            captured.append(line)
            if log_fh is not None:
                log_fh.write(line)
                log_fh.flush()

    reader = threading.Thread(target=_reader, daemon=True)
    reader.start()

    if input_text is not None and proc.stdin is not None:
        try:
            proc.stdin.write(input_text)
            proc.stdin.flush()
        finally:
            proc.stdin.close()

    try:
        proc.wait(timeout=timeout_sec)
    except subprocess.TimeoutExpired:
        timed_out = True
        proc.kill()
        proc.wait()

    reader.join(timeout=10)

    if log_fh is not None:
        log_fh.write(f"# {'-' * 60}\n")
        log_fh.write(f"# exit_code={proc.returncode}\n")
        if timed_out:
            log_fh.write(f"# timed_out after {timeout_sec}s\n")
        log_fh.close()

    if timed_out:
        raise subprocess.TimeoutExpired(cmd=argv[0], timeout=timeout_sec)

    return _SubprocResult(returncode=proc.returncode, stdout="".join(captured))


def _short_summary(stdout: str) -> str:
    for raw in stdout.splitlines():
        line = raw.strip()
        if line.upper().startswith("SUMMARY:"):
            return line[len("SUMMARY:") :].strip()[:280]
    for raw in reversed(stdout.splitlines()):
        line = raw.strip()
        if line:
            return line[:280]
    return ""


# ──────────────── codex windows sandbox detector ────────────────


_CODEX_SANDBOX_MARKER = "CreateProcessAsUserW failed: 5"


def _detect_codex_sandbox_failure(stdout: str, *, threshold: int = 2) -> bool:
    """True when codex's child-process spawn is broken on Windows."""
    if not stdout:
        return False
    return stdout.count(_CODEX_SANDBOX_MARKER) >= threshold


# ──────────────── the runner ────────────────


@dataclass(frozen=True)
class CliRunnerConfig:
    binary: str
    timeout_sec: int = 1800

    def __post_init__(self) -> None:
        resolve_spec(self.binary)


def make_cli_runner(
    config: CliRunnerConfig,
    *,
    user_prompt_text: str = "",
):
    """Return a runner callable compatible with pipeline.run_pipeline.

    `user_prompt_text` is the original `kiln build "..."` text; it gets
    embedded in every per-stage prompt so each agent has shared context.
    """
    spec = resolve_spec(config.binary)

    def runner(state, sd):
        executable = resolve_executable(spec)
        base = _read_instructions(sd.delegate)
        instructions = instructions_for(sd.delegate, base_instructions=base)
        prompt = build_combined_prompt(
            instructions=instructions,
            stage_n=sd.n,
            stage_name=sd.name,
            product_slug=state.slug,
            user_prompt=user_prompt_text or state.prompt,
        )
        product_dir = (REPO_ROOT / "products" / state.slug).resolve()
        product_dir.mkdir(parents=True, exist_ok=True)
        ctx = RunCtx(slug=state.slug, product_dir=product_dir)
        argv = spec.build_argv(executable, prompt, ctx)
        cwd = product_dir

        ensure_log_dir(state.slug)
        stage_log = log_path(state.slug, sd.n)

        try:
            result = _run_subprocess(
                argv,
                cwd=str(cwd),
                env=_scrub_env(),
                timeout_sec=config.timeout_sec,
                input_text=prompt if spec.prompt_via_stdin else None,
                log_file=stage_log,
            )
        except FileNotFoundError as exc:
            return ("failed", [], f"{spec.name} not on PATH: {exc}")
        except subprocess.TimeoutExpired:
            return (
                "failed",
                [],
                f"{spec.name} exec timed out after {config.timeout_sec}s",
            )

        if result.returncode != 0:
            tail = result.stdout[-280:].strip()
            return (
                "failed",
                [],
                f"{spec.name} exit_code={result.returncode}: {tail}",
            )

        if _detect_codex_sandbox_failure(result.stdout):
            return (
                "failed",
                [],
                f"{spec.name} hit Windows sandbox bug "
                "(`CreateProcessAsUserW failed: 5`); shell exec is broken "
                "in this codex build. Switch --cli-bin to claude or gemini.",
            )

        artifacts = _extract_artifacts(result.stdout, slug=state.slug)
        notes = _short_summary(result.stdout)
        return ("completed", artifacts, notes)

    return runner


__all__ = [
    "CliRunnerConfig",
    "CliSpec",
    "RunCtx",
    "SPECS",
    "build_combined_prompt",
    "make_cli_runner",
    "resolve_executable",
    "resolve_spec",
    "_detect_codex_sandbox_failure",
    "_run_subprocess",
]
