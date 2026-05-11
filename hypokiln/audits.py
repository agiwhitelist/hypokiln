"""Stage-specific audit Click subcommands for HypoKiln.

Each command implements a deterministic gate for one critique-loop stage:

  Stage 1 → trend-radar-audit       gate for Trend Radar
  Stage 3 → hypothesis-audit        gate for Hypothesis Generator
  Stage 5 → market-snapshot-audit   gate for Market Snapshot

Every command writes a sibling `<slug>-audit.md` report under
`products/<slug>/spec/`, prints a `PASS|FAIL <name> slug=<…> violations=<n>`
first line so the critique-loop gate can parse stdout uniformly, and exits
0 on PASS / 1 on FAIL.

Audit logic is intentionally simple — every check is a structural lint
that an author with average attention can self-check. Subjective quality
(is the trend interesting? is the wedge sharp?) stays with the critic
agent on the LLM side.
"""

from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Sequence

import click
from rich.console import Console

from . import REPO_ROOT
from . import pipeline as _pipeline

console = Console()


# ──────────────── shared helpers ────────────────


@dataclass
class AuditViolation:
    rule: str           # e.g. "T1", "H3", "M4" — short stable identifier
    detail: str         # human-readable; becomes the bullet in feedback.md


@dataclass
class AuditResult:
    name: str
    slug: str
    violations: list[AuditViolation] = field(default_factory=list)
    inspected_files: list[Path] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return not self.violations


def _resolve_first(*candidates: Path) -> Path | None:
    """Return the first existing path, or None."""
    for p in candidates:
        if p.is_file():
            return p
    return None


_URL_RE = re.compile(r"https?://[^\s)\]>'\"]+", re.IGNORECASE)
_DATE_RE = re.compile(r"\b(20\d{2})[-/](0[1-9]|1[0-2])[-/](0[1-9]|[12]\d|3[01])\b")
_PRICE_RE = re.compile(
    r"(?:[$€£]|USD|EUR|GBP)\s?\d+(?:[.,]\d{1,2})?(?:\s?/\s?(?:mo|month|yr|year))?"
    r"|\b\d+(?:[.,]\d{1,2})?\s?(?:USD|EUR|GBP)\b",
    re.IGNORECASE,
)


def _print_verdict(result: AuditResult, *, file_count: int | None = None) -> None:
    verdict = "PASS" if result.passed else "FAIL"
    colour = "green" if result.passed else "red"
    files_part = f" files={file_count}" if file_count is not None else ""
    console.print(
        f"[bold {colour}]{verdict}[/] {result.name} slug=[cyan]{result.slug}[/] "
        f"violations={len(result.violations)}{files_part}"
    )
    for v in result.violations:
        console.print(f"  [red]{v.rule}[/]: {v.detail}")


def _write_report(result: AuditResult, target: Path) -> Path:
    target.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        f"# {result.name} — {result.slug}",
        "",
        f"Verdict: **{'PASS' if result.passed else 'FAIL'}**",
        f"Files inspected: {len(result.inspected_files)}",
        f"Violations: {len(result.violations)}",
        "",
    ]
    if result.inspected_files:
        lines.append("## Files inspected")
        for f in result.inspected_files:
            try:
                rel = f.relative_to(REPO_ROOT).as_posix()
            except ValueError:
                rel = str(f)
            lines.append(f"- `{rel}`")
        lines.append("")
    if result.violations:
        lines.append("## Violations")
        for v in result.violations:
            lines.append(f"- **{v.rule}**: {v.detail}")
    target.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return target


def _exit_with_report(result: AuditResult, no_write: bool, report_path: Path) -> None:
    _print_verdict(result, file_count=len(result.inspected_files))
    if not no_write:
        written = _write_report(result, report_path)
        console.print(f"report=[dim]{written.relative_to(REPO_ROOT).as_posix()}[/]")
    if not result.passed:
        sys.exit(1)


# ──────────────── Stage 1 — Trend Radar ────────────────


def audit_trend_radar(slug: str) -> AuditResult:
    """Stage 1 gate. Looks for a markdown file under
    `products/<slug>/research/trend-radar.md` (preferred) or
    `factory/00-radar/trend-radar.md` (legacy). Verifies:

      T1: file exists and is non-empty
      T2: ≥8 distinct signals (each `## ` heading or `- ` top-level bullet
          counts; we take the larger count)
      T3: every signal has at least one HTTP(S) URL
      T4: at least 3 distinct hostnames across signals (no single source)
      T5: at least one ISO/numeric date appears (proxy for "dated signal")
    """
    root = REPO_ROOT / "products" / slug
    candidates = [
        root / "research" / "trend-radar.md",
        REPO_ROOT / "factory" / "00-radar" / "trend-radar.md",
    ]
    path = _resolve_first(*candidates)
    result = AuditResult(name="trend-radar-audit", slug=slug)

    if path is None:
        result.violations.append(AuditViolation(
            "T1",
            f"trend-radar.md not found at any of: "
            + ", ".join(str(p.relative_to(REPO_ROOT)) for p in candidates),
        ))
        return result

    text = path.read_text(encoding="utf-8", errors="ignore")
    result.inspected_files.append(path)

    if not text.strip():
        result.violations.append(AuditViolation("T1", f"{path.name} is empty"))
        return result

    h2_signals = [ln for ln in text.splitlines() if ln.startswith("## ")]
    bullet_signals = [
        ln for ln in text.splitlines()
        if ln.lstrip().startswith("- ") and not ln.lstrip().startswith("- [")
    ]
    signal_count = max(len(h2_signals), len(bullet_signals))
    if signal_count < 8:
        result.violations.append(AuditViolation(
            "T2",
            f"only {signal_count} signal(s) found; minimum is 8 "
            "(use `## ` headings or `- ` top-level bullets to mark signals)",
        ))

    urls = _URL_RE.findall(text)
    if signal_count > 0 and len(urls) < signal_count:
        result.violations.append(AuditViolation(
            "T3",
            f"{signal_count} signals but only {len(urls)} URL(s) — every signal "
            "must cite at least one source URL",
        ))

    hosts: set[str] = set()
    for u in urls:
        m = re.match(r"https?://([^/\s]+)", u, re.IGNORECASE)
        if m:
            hosts.add(m.group(1).lower().lstrip("www."))
    if len(hosts) < 3:
        result.violations.append(AuditViolation(
            "T4",
            f"only {len(hosts)} distinct source(s): {sorted(hosts)}; "
            "minimum is 3 (HN + Reddit + ProductHunt + niche subs is the floor)",
        ))

    if not _DATE_RE.search(text):
        result.violations.append(AuditViolation(
            "T5",
            "no dated signal found (looking for ISO `YYYY-MM-DD` or `YYYY/MM/DD`); "
            "every signal should be timestamped",
        ))

    return result


@click.command("trend-radar-audit")
@click.argument("slug")
@click.option("--no-write", is_flag=True, help="Skip writing the audit report.")
def trend_radar_audit_cmd(slug: str, no_write: bool) -> None:
    """Stage 1 gate: structural lint on trend-radar.md."""
    final_slug = _pipeline.validate_slug(slug)
    result = audit_trend_radar(final_slug)
    report_path = REPO_ROOT / "products" / final_slug / "spec" / "trend-radar-audit.md"
    _exit_with_report(result, no_write, report_path)


# ──────────────── Stage 3 — Hypothesis Generator ────────────────


_TEMPLATE_WEDGES = {
    "ai-powered", "automation", "automate everything",
    "your one-stop", "the best", "leverage ai", "powered by ai",
    "<wedge>", "wedge here", "todo", "tk", "tk-tk",
}


def audit_hypothesis(slug: str) -> AuditResult:
    """Stage 3 gate. Looks for `products/<slug>/research/round-NNN.json`.
    Verifies:

      H1: at least one round-*.json file exists and is valid JSON
      H2: ≥8 hypotheses in the latest round
      H3: each hypothesis has all required keys
          (id, slug, name, who, pain, wedge, distribution, willingness_to_pay)
      H4: no `wedge` field is empty or matches a generic-template anti-pattern
      H5: each hypothesis has a `who` value with both role and segment
    """
    root = REPO_ROOT / "products" / slug / "research"
    result = AuditResult(name="hypothesis-audit", slug=slug)

    if not root.is_dir():
        result.violations.append(AuditViolation(
            "H1",
            f"products/{slug}/research/ directory missing",
        ))
        return result

    rounds = sorted(root.glob("round-*.json"))
    if not rounds:
        result.violations.append(AuditViolation(
            "H1",
            f"no round-*.json found under products/{slug}/research/",
        ))
        return result

    latest = rounds[-1]
    result.inspected_files.append(latest)
    try:
        data = json.loads(latest.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        result.violations.append(AuditViolation(
            "H1", f"{latest.name} is not valid JSON: {exc}"
        ))
        return result

    hypotheses: Sequence[dict] = (
        data if isinstance(data, list)
        else data.get("hypotheses", []) if isinstance(data, dict)
        else []
    )
    if not isinstance(hypotheses, list):
        result.violations.append(AuditViolation(
            "H1", "JSON root must be an array or `{hypotheses: [...]}`"
        ))
        return result

    if len(hypotheses) < 8:
        result.violations.append(AuditViolation(
            "H2",
            f"only {len(hypotheses)} hypothesis(es) in {latest.name}; minimum is 8",
        ))

    required_keys = {"id", "slug", "name", "who", "pain", "wedge", "distribution", "willingness_to_pay"}
    for i, h in enumerate(hypotheses):
        if not isinstance(h, dict):
            result.violations.append(AuditViolation(
                "H3", f"hypothesis #{i} is not an object"
            ))
            continue
        missing = required_keys - h.keys()
        if missing:
            result.violations.append(AuditViolation(
                "H3",
                f"hypothesis '{h.get('id', i)!s}' missing keys: {sorted(missing)}",
            ))
            continue
        wedge = str(h.get("wedge", "")).strip().lower()
        if not wedge:
            result.violations.append(AuditViolation(
                "H4", f"hypothesis '{h.get('id', i)!s}' has empty wedge"
            ))
        elif wedge in _TEMPLATE_WEDGES or any(t in wedge for t in _TEMPLATE_WEDGES):
            result.violations.append(AuditViolation(
                "H4",
                f"hypothesis '{h.get('id', i)!s}' has template wedge: {wedge!r}",
            ))
        who = str(h.get("who", "")).strip()
        if who and not (
            "," in who or " in " in who.lower() or " for " in who.lower() or " at " in who.lower()
        ):
            result.violations.append(AuditViolation(
                "H5",
                f"hypothesis '{h.get('id', i)!s}' has bare audience {who!r}; "
                "must include role + segment (e.g. 'solo dev, in side-project phase')",
            ))

    return result


@click.command("hypothesis-audit")
@click.argument("slug")
@click.option("--no-write", is_flag=True, help="Skip writing the audit report.")
def hypothesis_audit_cmd(slug: str, no_write: bool) -> None:
    """Stage 3 gate: structural lint on the latest round-*.json."""
    final_slug = _pipeline.validate_slug(slug)
    result = audit_hypothesis(final_slug)
    report_path = REPO_ROOT / "products" / final_slug / "spec" / "hypothesis-audit.md"
    _exit_with_report(result, no_write, report_path)


# ──────────────── Stage 5 — Market Snapshot ────────────────


def audit_market_snapshot(slug: str) -> AuditResult:
    """Stage 5 gate. Verifies the three Market Skeptic outputs:

      M1: market-snapshot.md exists and non-empty
      M2: ≥3 competitors named in competitor-analysis.md
      M3: each competitor has at least one URL
      M4: pricing-research.md exists and contains at least 2 price tokens
      M5: market-snapshot.md mentions "why now" and cites a recent date
    """
    root = REPO_ROOT / "products" / slug / "research"
    result = AuditResult(name="market-snapshot-audit", slug=slug)

    if not root.is_dir():
        result.violations.append(AuditViolation(
            "M1",
            f"products/{slug}/research/ directory missing",
        ))
        return result

    snapshot = root / "market-snapshot.md"
    competitors = root / "competitor-analysis.md"
    pricing = root / "pricing-research.md"

    if not snapshot.is_file() or snapshot.stat().st_size == 0:
        result.violations.append(AuditViolation(
            "M1", f"market-snapshot.md missing or empty at {snapshot.relative_to(REPO_ROOT)}"
        ))
    else:
        result.inspected_files.append(snapshot)

    if competitors.is_file():
        result.inspected_files.append(competitors)
        text = competitors.read_text(encoding="utf-8", errors="ignore")
        h2 = sum(1 for ln in text.splitlines() if ln.startswith("## "))
        rows = sum(
            1 for ln in text.splitlines()
            if ln.count("|") >= 2 and not re.match(r"\s*\|?\s*-+\s*\|", ln)
            and not ln.strip().startswith("|---")
        )
        rows = max(0, rows - 1)
        n_competitors = max(h2, rows)
        if n_competitors < 3:
            result.violations.append(AuditViolation(
                "M2",
                f"only {n_competitors} competitor(s) found; minimum is 3 "
                "(use `## <Name>` headings or a markdown table)",
            ))
        urls = _URL_RE.findall(text)
        if n_competitors > 0 and len(urls) < n_competitors:
            result.violations.append(AuditViolation(
                "M3",
                f"{n_competitors} competitor(s) but only {len(urls)} URL(s); "
                "every competitor needs a homepage or pricing-page link",
            ))
    else:
        result.violations.append(AuditViolation(
            "M2",
            f"competitor-analysis.md missing at {competitors.relative_to(REPO_ROOT)}",
        ))

    if pricing.is_file():
        result.inspected_files.append(pricing)
        prices = _PRICE_RE.findall(pricing.read_text(encoding="utf-8", errors="ignore"))
        if len(prices) < 2:
            result.violations.append(AuditViolation(
                "M4",
                f"pricing-research.md has {len(prices)} price token(s); minimum is 2 "
                r"(format: `$9/mo`, `€19`, `19 USD`)",
            ))
    else:
        result.violations.append(AuditViolation(
            "M4",
            f"pricing-research.md missing at {pricing.relative_to(REPO_ROOT)}",
        ))

    if snapshot.is_file():
        snap_text = snapshot.read_text(encoding="utf-8", errors="ignore").lower()
        if "why now" not in snap_text and "why this works now" not in snap_text:
            result.violations.append(AuditViolation(
                "M5",
                "market-snapshot.md does not contain a `why now` paragraph",
            ))
        else:
            idx = snap_text.find("why now")
            window = snap_text[idx : idx + 1200]
            if not _DATE_RE.search(window):
                result.violations.append(AuditViolation(
                    "M5",
                    "`why now` paragraph found but cites no concrete date; "
                    "anchor it with a YYYY-MM date within the last 24 months",
                ))

    return result


@click.command("market-snapshot-audit")
@click.argument("slug")
@click.option("--no-write", is_flag=True, help="Skip writing the audit report.")
def market_snapshot_audit_cmd(slug: str, no_write: bool) -> None:
    """Stage 5 gate: structural lint on Market Skeptic's three outputs."""
    final_slug = _pipeline.validate_slug(slug)
    result = audit_market_snapshot(final_slug)
    report_path = REPO_ROOT / "products" / final_slug / "spec" / "market-snapshot-audit.md"
    _exit_with_report(result, no_write, report_path)


__all__ = [
    "AuditResult",
    "AuditViolation",
    "audit_hypothesis",
    "audit_market_snapshot",
    "audit_trend_radar",
    "hypothesis_audit_cmd",
    "market_snapshot_audit_cmd",
    "trend_radar_audit_cmd",
]
