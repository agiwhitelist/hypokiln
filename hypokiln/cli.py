"""hypokiln — top-level CLI entrypoint.

Subcommands:
  build "free-text prompt"      Kick the six-stage pipeline for a new idea.
  resume <slug>                 Pick up a paused pipeline.
  status [<slug>]               Print pipeline state.

Plus three stage-gate audit subcommands (trend-radar-audit, hypothesis-audit,
market-snapshot-audit), a `capability-scan` maintenance command for the
fresh-wedges log, and skill-pack ops (`skills list / update / clean`).

Flags on `build`:
  --slug <kebab>      Override the auto-derived slug.
  --yolo              Autonomous mode (auto-sign G1 if pre-flight clears).
  --dry-run           Use the dry-run runner; no LLM calls, no money.
  --cli-bin <bin>     Which logged-in CLI to spawn (codex / claude / gemini).
  --skip-stage N      Repeatable; skip a stage (debugging).
  --only-stage N      Repeatable; run only this stage.
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.table import Table

from . import REPO_ROOT
from . import pipeline as _pipeline
from . import skill_loader as _skill_loader
from .gates import is_autonomous

console = Console()


def _slugify(text: str) -> str:
    text = text.strip().lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    text = re.sub(r"-+", "-", text).strip("-")
    return (text[:48] or "idea").rstrip("-")


def _abort(msg: str, *, exit_code: int = 1) -> None:
    console.print(f"[bold red]✗[/] {msg}")
    sys.exit(exit_code)


def _ensure_skills_or_abort() -> None:
    try:
        _skill_loader.ensure_all_for_pipeline()
    except RuntimeError as exc:
        _abort(str(exc))


def _ensure_product_workspace(slug: str) -> Path:
    """Create the per-product folder: products/<slug>/{spec,research}/."""
    proot = _pipeline.product_root(slug)
    if proot.exists():
        return proot
    proot.mkdir(parents=True, exist_ok=True)
    (proot / "spec").mkdir(exist_ok=True)
    (proot / "research").mkdir(exist_ok=True)
    return proot


def _runner_for(
    *,
    dry_run: bool,
    cli_bin: str | None,
    user_prompt: str,
):
    """Pick the appropriate runner for this run.

    Order of precedence: --dry-run > CLI subprocess runner with critique
    wrappers on Stages 1, 3, 5.
    """
    if dry_run:
        return _pipeline.dry_run_runner

    from .runners.cli_runner import CliRunnerConfig, make_cli_runner
    from .runners.critique_runner import (
        CritiqueConfig,
        HYPOTHESIS_AUDIT_GATE,
        MARKET_SNAPSHOT_GATE,
        TREND_RADAR_GATE,
        make_critique_runner,
    )

    binary = (cli_bin or os.environ.get("HYPOKILN_CLI_BIN", "codex")).strip()
    timeout = int(os.environ.get("HYPOKILN_CLI_TIMEOUT", "1800"))
    cfg = CliRunnerConfig(binary=binary, timeout_sec=timeout)
    base = make_cli_runner(cfg, user_prompt_text=user_prompt)

    max_iter = int(os.environ.get("HYPOKILN_CRITIQUE_MAX_ITER", "3"))
    # Critique loops on the three quality-critical stages.
    # Separation of duties:
    #   Stage 1 author = Trend Scout; critic = Market Skeptic (pushes
    #     back on weak signals before they pollute Stage 3).
    #   Stage 3 author = Product Strategist; critic = Market Skeptic
    #     (same role that runs Kill Filter at Stage 4 — overlap is
    #     intentional, mortality patterns enforced early).
    #   Stage 5 author = Market Skeptic; critic = Product Strategist
    #     (the strategist uses this snapshot to score, so they vet
    #     the research first).
    critique_for_stage: dict[int, CritiqueConfig] = {
        1: CritiqueConfig(
            gate=TREND_RADAR_GATE,
            critic_delegate="Market Skeptic Agent",
            max_iterations=max_iter,
        ),
        3: CritiqueConfig(
            gate=HYPOTHESIS_AUDIT_GATE,
            critic_delegate="Market Skeptic Agent",
            max_iterations=max_iter,
        ),
        5: CritiqueConfig(
            gate=MARKET_SNAPSHOT_GATE,
            critic_delegate="Product Strategist Agent",
            max_iterations=max_iter,
        ),
    }
    if os.environ.get("HYPOKILN_DISABLE_CRITIQUE") == "1":
        critique_for_stage = {}

    wrapped_for_stage = {
        n: make_critique_runner(
            base, config=cfg_c, cli_config=cfg, user_prompt_text=user_prompt
        )
        for n, cfg_c in critique_for_stage.items()
    }

    def dispatch(state, sd):
        return wrapped_for_stage.get(sd.n, base)(state, sd)

    return dispatch


# ──────────────── click app ────────────────


@click.group()
@click.version_option(package_name="hypokiln")
def cli() -> None:
    """HypoKiln — capability-wedge-driven idea kiln."""


@cli.command("build")
@click.argument("prompt", nargs=-1, required=True)
@click.option("--slug", "slug", default=None, help="Idea slug; auto-derived from prompt if omitted.")
@click.option("--yolo", is_flag=True, help="Autonomous mode (auto-sign G1 if pre-flight clears).")
@click.option("--dry-run", is_flag=True, help="No LLM calls, no money.")
@click.option(
    "--cli-bin",
    type=click.Choice(["codex", "claude", "gemini"], case_sensitive=False),
    default=None,
    help="Which CLI to spawn (env: HYPOKILN_CLI_BIN; default: codex).",
)
@click.option(
    "--skip-stage",
    "skip_stages",
    multiple=True,
    type=int,
    help="Repeatable; stages to skip (debugging).",
)
@click.option(
    "--only-stage",
    "only_stages",
    multiple=True,
    type=int,
    help="Repeatable; run only these stages.",
)
def build(prompt: tuple[str, ...], slug: Optional[str], yolo: bool, dry_run: bool,
          cli_bin: Optional[str],
          skip_stages: tuple[int, ...], only_stages: tuple[int, ...]) -> None:
    """Kick the six-stage idea pipeline."""
    text_prompt = " ".join(prompt).strip()
    if not text_prompt:
        _abort("Empty prompt.")

    final_slug = _pipeline.validate_slug(slug or _slugify(text_prompt))
    autonomous = yolo or is_autonomous()
    if yolo:
        os.environ["HYPOKILN_AUTONOMOUS"] = "1"

    console.print(
        f"[bold]kiln build[/] slug=[cyan]{final_slug}[/] "
        f"cli_bin=[magenta]{cli_bin or os.environ.get('HYPOKILN_CLI_BIN', 'codex')}[/] "
        f"autonomous={autonomous} dry_run={dry_run}"
    )
    _ensure_product_workspace(final_slug)

    if not dry_run:
        _ensure_skills_or_abort()

    state = _pipeline.load_state(final_slug)
    if state is None:
        state = _pipeline.init_state(final_slug, text_prompt, autonomous=autonomous)
    else:
        console.print(f"[yellow]![/] Resuming existing state at {_pipeline.state_path(final_slug)}")

    try:
        _pipeline.run_pipeline(
            state,
            runner=_runner_for(
                dry_run=dry_run, cli_bin=cli_bin, user_prompt=text_prompt
            ),
            only_stages=set(only_stages) if only_stages else None,
            skip=set(skip_stages),
        )
    except BlockingIOError as exc:
        console.print(f"[bold yellow]⏸ pipeline paused[/]: {exc}")
        sys.exit(2)

    _print_status(state)


@cli.command("resume")
@click.argument("slug")
@click.option("--dry-run", is_flag=True)
@click.option("--cli-bin", type=click.Choice(["codex", "claude", "gemini"], case_sensitive=False), default=None)
def resume(slug: str, dry_run: bool, cli_bin: Optional[str]) -> None:
    """Pick up an existing pipeline."""
    state = _pipeline.load_state(_pipeline.validate_slug(slug))
    if state is None:
        _abort(f"No state for slug {slug!r}. Did you run `kiln build` first?")
        return
    if not dry_run:
        _ensure_skills_or_abort()
    try:
        _pipeline.run_pipeline(
            state,
            runner=_runner_for(
                dry_run=dry_run, cli_bin=cli_bin, user_prompt=state.prompt
            ),
        )
    except BlockingIOError as exc:
        console.print(f"[bold yellow]⏸ pipeline paused[/]: {exc}")
        sys.exit(2)
    _print_status(state)


@cli.command("status")
@click.argument("slug", required=False)
def status(slug: Optional[str]) -> None:
    """Print pipeline state for one idea, or list all."""
    if slug:
        state = _pipeline.load_state(_pipeline.validate_slug(slug))
        if state is None:
            _abort(f"No state for slug {slug!r}.")
            return
        _print_status(state)
        return

    sdir = _pipeline.state_dir()
    if not sdir.exists():
        console.print('[dim]No ideas yet. Try: kiln build "..."[/]')
        return

    table = Table(title="HypoKiln ideas")
    table.add_column("slug")
    table.add_column("autonomous")
    table.add_column("done/total")
    table.add_column("updated")
    for child in sorted(sdir.iterdir()):
        if not (child / "state.json").exists():
            continue
        state = _pipeline.load_state(child.name)
        if state is None:
            continue
        done = sum(1 for s in state.stages if s.status == "completed")
        table.add_row(state.slug, str(state.autonomous), f"{done}/{len(state.stages)}", state.updated_at)
    console.print(table)


@cli.group("skills")
def skills_group() -> None:
    """Manage external skill packs cloned into .hypokiln/skills/."""


@skills_group.command("list")
def skills_list() -> None:
    table = Table(title="HypoKiln skill packs")
    table.add_column("name")
    table.add_column("source")
    table.add_column("local")
    for name, url, present in _skill_loader.list_skills():
        table.add_row(name, url, "✓" if present else "—")
    console.print(table)


@skills_group.command("update")
@click.argument("names", nargs=-1)
def skills_update(names: tuple[str, ...]) -> None:
    """Pull-ff every (or named) skill pack. Clones missing ones."""
    results = _skill_loader.update_skills(list(names) if names else None)
    for name, status in results.items():
        marker = "[green]✓[/]" if status in {"updated", "cloned"} else "[red]✗[/]"
        console.print(f"  {marker} {name}: {status}")
    if any(s.startswith("failed") for s in results.values()):
        sys.exit(1)


@skills_group.command("clean")
@click.confirmation_option(prompt="Delete every cloned skill pack?")
def skills_clean() -> None:
    n = _skill_loader.clean_skills()
    console.print(f"Removed {n} skill pack(s) from {_skill_loader.skills_dir()}")


# ──────────────── capability-scan (the USP) ────────────────


@cli.command("capability-scan")
@click.option(
    "--archive",
    is_flag=True,
    help="Move active entries older than --max-age-days to the archived section.",
)
@click.option(
    "--max-age-days",
    type=int,
    default=90,
    show_default=True,
    help="Age threshold (in days) for an active capability wedge.",
)
def capability_scan_cmd(archive: bool, max_age_days: int) -> None:
    """Maintain `factory/00-radar/capability-wedges.md`.

    The capability-wedges file is HypoKiln's USP: it's a canonical log of
    AI/LLM/media-model releases (Anthropic, OpenAI, Google, fal, Suno,
    ElevenLabs, …) within the last 90 days that *unlock* product space.
    Every hypothesis the kiln generates must be anchored on one of these
    wedges; Market Skeptic kills any hypothesis whose wedge is missing,
    archived, or generic.

    Default (no flags): one-screen summary — active count, by provider,
    ages of oldest entries so you can see what's about to fall out of the
    90-day window.

    `--archive`: move every active entry with `Released:` older than
    `--max-age-days` from `## Active wedges` to `## Archived`. Idempotent.

    Real capability discovery (writing NEW entries) is the Trend Scout
    agent's job at pipeline Stage 1. This command is the operator's
    pruning + summary tool.
    """
    from datetime import date, timedelta

    path = REPO_ROOT / "factory" / "00-radar" / "capability-wedges.md"
    if not path.is_file():
        console.print(
            f"[red]FAIL[/] capability-scan — {path.relative_to(REPO_ROOT)} not found."
        )
        console.print(
            "  Bootstrap with the template at "
            "`factory/00-radar/capability-wedges-template.md`, or run Stage 1 "
            "(Trend Scout) to produce a fresh scan."
        )
        sys.exit(1)

    text = path.read_text(encoding="utf-8")
    entries = _parse_capability_entries(text)
    today = date.today()
    cutoff = today - timedelta(days=max_age_days)

    active = [e for e in entries if e["section"] == "active"]
    archived = [e for e in entries if e["section"] == "archived"]
    to_archive = [
        e for e in active if e.get("released_date") and e["released_date"] < cutoff
    ]

    if archive:
        if not to_archive:
            console.print(
                f"[green]OK[/] capability-scan archive=noop — "
                f"every active entry is within the last {max_age_days} days."
            )
            return
        new_text = _rewrite_with_archive(text, to_archive)
        path.write_text(new_text, encoding="utf-8")
        console.print(
            f"[bold green]OK[/] capability-scan archive — "
            f"moved {len(to_archive)} entries to Archived (cutoff={cutoff.isoformat()})"
        )
        for e in to_archive:
            console.print(
                f"  [dim]→[/] {e['id']} {e['title'][:60]} "
                f"({e['released_date'].isoformat()})"
            )
        return

    # Default: summary
    by_provider: dict[str, int] = {}
    for e in active:
        by_provider[e.get("provider", "?")] = by_provider.get(e.get("provider", "?"), 0) + 1
    console.print(
        f"capability-scan summary | active=[bold]{len(active)}[/] archived={len(archived)} "
        f"cutoff={cutoff.isoformat()}"
    )
    console.print(
        "[dim]Providers:[/] "
        + ", ".join(f"{p}={n}" for p, n in sorted(by_provider.items(), key=lambda kv: -kv[1]))
    )
    expiring_soon = sorted(
        (e for e in active if e.get("released_date") and (e["released_date"] - cutoff).days <= 14),
        key=lambda e: e["released_date"],
    )
    if expiring_soon:
        console.print(f"[yellow]Expiring within 14 days of cutoff:[/]")
        for e in expiring_soon[:10]:
            days_left = (e["released_date"] - cutoff).days
            console.print(
                f"  [yellow]{days_left:>3}d[/] {e['id']} "
                f"({e.get('provider', '?')}, {e['released_date'].isoformat()}) "
                f"{e['title'][:60]}"
            )
        console.print(
            "  [dim]Run `capability-scan --archive` to move these to the Archived section "
            "once they cross the cutoff.[/]"
        )
    if to_archive:
        console.print(
            f"[red]{len(to_archive)} entries already past cutoff[/] — "
            f"run `capability-scan --archive` to clean them up."
        )


_CAPABILITY_ENTRY_RE = re.compile(
    r"^### `(cw-\d+)`\s*—\s*(.*?)$",
    re.MULTILINE,
)
_CAPABILITY_PROVIDER_RE = re.compile(r"^-\s*\*\*Provider:\*\*\s*(.+?)$", re.MULTILINE)
_CAPABILITY_RELEASED_RE = re.compile(
    r"^-\s*\*\*Released:\*\*\s*(\d{4}-\d{2}(?:-\d{2})?)",
    re.MULTILINE,
)


def _parse_capability_entries(text: str) -> list[dict]:
    """Parse `## Active wedges` and `## Archived` sections into entries."""
    from datetime import date

    entries: list[dict] = []
    active_start = text.find("## Active wedges")
    archived_start = text.find("## Archived")
    active_block = ""
    archived_block = ""
    if active_start >= 0:
        end = archived_start if archived_start > active_start else len(text)
        active_block = text[active_start:end]
    if archived_start >= 0:
        archived_block = text[archived_start:]

    def _harvest(block: str, section: str) -> None:
        for m in _CAPABILITY_ENTRY_RE.finditer(block):
            entry_id = m.group(1)
            title = m.group(2).strip()
            body_start = m.end()
            next_m = _CAPABILITY_ENTRY_RE.search(block, body_start)
            body_end = next_m.start() if next_m else len(block)
            body = block[body_start:body_end]
            provider_m = _CAPABILITY_PROVIDER_RE.search(body)
            released_m = _CAPABILITY_RELEASED_RE.search(body)
            released_date = None
            if released_m:
                raw = released_m.group(1)
                try:
                    if len(raw) == 7:
                        released_date = date.fromisoformat(raw + "-01")
                    else:
                        released_date = date.fromisoformat(raw)
                except ValueError:
                    released_date = None
            entries.append({
                "id": entry_id,
                "title": title,
                "provider": provider_m.group(1).strip() if provider_m else "?",
                "released_date": released_date,
                "section": section,
                "body_start": body_start,
                "body_end": body_end,
            })

    _harvest(active_block, "active")
    _harvest(archived_block, "archived")
    return entries


def _rewrite_with_archive(text: str, to_archive: list[dict]) -> str:
    """Move the named entries from Active to Archived."""
    if not to_archive:
        return text

    entries = _parse_capability_entries(text)
    by_id = {e["id"]: e for e in entries if e["section"] == "active"}
    archive_ids = {e["id"] for e in to_archive}
    archived_blocks: list[str] = []
    new_text = text
    for entry in sorted(
        (by_id[i] for i in archive_ids if i in by_id),
        key=lambda e: e["body_start"],
        reverse=True,
    ):
        marker = f"### `{entry['id']}` —"
        start = new_text.find(marker)
        if start < 0:
            continue
        next_entry = new_text.find("\n### `cw-", start + 1)
        next_section = new_text.find("\n## ", start + 1)
        candidates = [c for c in (next_entry, next_section) if c >= 0]
        end = min(candidates) if candidates else len(new_text)
        if end != len(new_text):
            end += 1
        block = new_text[start:end].rstrip() + "\n\n"
        archived_blocks.append(block)
        new_text = new_text[:start] + new_text[end:]

    if not archived_blocks:
        return text
    archive_header = "## Archived"
    h_pos = new_text.find(archive_header)
    if h_pos < 0:
        new_text = new_text.rstrip() + "\n\n## Archived (> 90 days, kept for history)\n\n"
        h_pos = new_text.find(archive_header)
    insert_at = new_text.find("\n\n", h_pos)
    insert_at = (insert_at + 2) if insert_at >= 0 else len(new_text)
    archived_chunk = "".join(reversed(archived_blocks))
    return new_text[:insert_at] + archived_chunk + new_text[insert_at:]


# ──────────────── status print + main ────────────────


def _print_status(state) -> None:
    table = Table(title=f"Pipeline — {state.slug}")
    table.add_column("#")
    table.add_column("stage")
    table.add_column("status")
    table.add_column("delegate")
    table.add_column("artifacts")
    for s in state.stages:
        artifacts = ", ".join(s.artifacts[:3]) + ("…" if len(s.artifacts) > 3 else "")
        table.add_row(str(s.stage), s.name, s.status, s.delegate, artifacts)
    console.print(table)
    for gate_id, gate in state.gates.items():
        if gate:
            console.print(f"  G{gate_id}: {gate}")


# Register the audit subcommands.
from . import audits as _audits  # noqa: E402

cli.add_command(_audits.trend_radar_audit_cmd)
cli.add_command(_audits.hypothesis_audit_cmd)
cli.add_command(_audits.market_snapshot_audit_cmd)


def main() -> None:
    cli()


if __name__ == "__main__":
    main()
