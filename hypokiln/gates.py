"""Human-gate logic for HypoKiln.

HypoKiln ships ONE gate:

  G1 — Idea approval   (after Stage 6 — Selection Score)

Autonomous mode (`HYPOKILN_AUTONOMOUS=1` or `--yolo`) auto-signs G1 *if and
only if* the pre-flight 10-question checklist clears (≤2 alarms); otherwise
operator review is required regardless of flag.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

GateId = Literal[1]
ALL_GATES: tuple[GateId, ...] = (1,)


@dataclass(frozen=True)
class GateStatus:
    gate_id: GateId
    signed: bool
    approver: str
    signed_at: str | None
    notes: str


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def gate_path(product_root: Path, gate_id: GateId) -> Path:
    return product_root / "spec" / f"gate-{gate_id}-approval.md"


def is_autonomous() -> bool:
    return os.environ.get("HYPOKILN_AUTONOMOUS", "0").strip() in {"1", "true", "yes"}


def read_gate(product_root: Path, gate_id: GateId) -> GateStatus:
    """Parse a gate file. A gate is 'signed' iff its body contains
    `approved: yes` and a non-empty `approver:` line."""
    path = gate_path(product_root, gate_id)
    if not path.exists():
        return GateStatus(
            gate_id=gate_id, signed=False, approver="", signed_at=None, notes="missing file"
        )

    text = path.read_text(encoding="utf-8")
    approved = False
    approver = ""
    signed_at: str | None = None
    for raw in text.splitlines():
        line = raw.strip()
        if line.lower().startswith("approved:"):
            value = line.split(":", 1)[1].strip().lower()
            approved = value in {"yes", "true", "y"}
        elif line.lower().startswith("approver:"):
            approver = line.split(":", 1)[1].strip()
        elif line.lower().startswith("date:"):
            signed_at = line.split(":", 1)[1].strip()

    signed = approved and bool(approver)
    notes = "" if signed else f"approved={approved}, approver={approver!r}"
    return GateStatus(gate_id=gate_id, signed=signed, approver=approver, signed_at=signed_at, notes=notes)


_PREFLIGHT_ALARM_RE = re.compile(
    r"^\s*\*\*Verdict\.\*\*\s*alarm\b", re.IGNORECASE | re.MULTILINE
)
_PREFLIGHT_FRONTMATTER_RE = re.compile(
    r"^alarm_count:\s*(\d+)\s*$", re.IGNORECASE | re.MULTILINE
)

# The G1 auto-sign refuses when the pre-flight checklist carries more
# than this many `alarm` verdicts. Two alarms = manageable risk; three
# or more = fundamental strategic problems that must not auto-pass.
PREFLIGHT_MAX_ALARMS = 2


def _read_preflight_alarms(product_root: Path) -> tuple[int, str]:
    """Return (alarm_count, source) for the pre-flight checklist.

    Reads `products/<slug>/spec/gate-1-preflight.md`. Prefers the
    `alarm_count` line in the YAML frontmatter (authored by Stage 6).
    Falls back to counting `**Verdict.** alarm` occurrences in the body
    so a checklist authored without frontmatter still scores.

    Returns (-1, "missing") when no pre-flight file exists at all —
    callers treat that as "operator must review", not auto-pass.
    """
    pf_path = product_root / "spec" / "gate-1-preflight.md"
    if not pf_path.exists():
        return (-1, "missing")
    body = pf_path.read_text(encoding="utf-8")
    match = _PREFLIGHT_FRONTMATTER_RE.search(body)
    if match:
        try:
            return (int(match.group(1)), "frontmatter")
        except ValueError:
            pass
    return (len(_PREFLIGHT_ALARM_RE.findall(body)), "body-scan")


def autosign_gate(product_root: Path, gate_id: GateId, *, reason: str) -> GateStatus:
    """Write an autonomous-mode signature into the gate file.

    G1 auto-sign requires the pre-flight checklist to exist and to report
    ≤ PREFLIGHT_MAX_ALARMS alarms. Operator review is required otherwise.
    """
    if gate_id == 1:
        alarm_count, source = _read_preflight_alarms(product_root)
        if alarm_count < 0:
            raise PermissionError(
                "Gate 1 cannot be auto-signed: pre-flight checklist missing at "
                f"{product_root / 'spec' / 'gate-1-preflight.md'}. Stage 6 must "
                "author it before auto-sign. Template: "
                "factory/01-hypotheses/gate-1-preflight-template.md."
            )
        if alarm_count > PREFLIGHT_MAX_ALARMS:
            raise PermissionError(
                f"Gate 1 cannot be auto-signed: pre-flight checklist reports "
                f"{alarm_count} alarms ({source}); threshold is "
                f"{PREFLIGHT_MAX_ALARMS}. Operator review required. See "
                f"{product_root / 'spec' / 'gate-1-preflight.md'}."
            )
    path = gate_path(product_root, gate_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    now = _now_iso()
    body = (
        f"# Gate {gate_id} — autonomous sign-off\n\n"
        "```\n"
        "approved: yes\n"
        "approver: hypokiln-autonomous\n"
        f"date: {now}\n"
        f"notes: {reason}\n"
        "```\n\n"
        "## Why auto-signed\n\n"
        "`HYPOKILN_AUTONOMOUS=1` (or `--yolo`) was active when the orchestrator "
        "reached this gate and the pre-flight checklist cleared with ≤"
        f"{PREFLIGHT_MAX_ALARMS} alarms.\n\n"
        "## What G1 approved\n\n"
        "G1 approves a bundle: top hypothesis + "
        "`products/<slug>/spec/architecture.md` (form_factor + archetype + "
        "capability_wedge + wow_moment + viral_mechanic) + decisions.md. "
        "See `factory/01-hypotheses/gate-1-approval-template.md` for the "
        "review checklist.\n"
    )
    path.write_text(body, encoding="utf-8")
    return GateStatus(
        gate_id=gate_id, signed=True, approver="hypokiln-autonomous", signed_at=now, notes=reason
    )


def require_gate(product_root: Path, gate_id: GateId, *, autonomous: bool) -> GateStatus:
    """Block until gate is signed. In autonomous mode, auto-sign G1
    if pre-flight clears; otherwise raise BlockingIOError."""
    status = read_gate(product_root, gate_id)
    if status.signed:
        return status

    if autonomous:
        return autosign_gate(
            product_root,
            gate_id,
            reason=f"autonomous mode bypass for G{gate_id}",
        )

    raise BlockingIOError(
        f"Gate G{gate_id} unsigned at {gate_path(product_root, gate_id)}. "
        "Edit the file: set `approved: yes` and fill `approver:`, then re-run "
        "`kiln resume <slug>`."
    )


__all__ = [
    "ALL_GATES",
    "GateId",
    "GateStatus",
    "PREFLIGHT_MAX_ALARMS",
    "autosign_gate",
    "gate_path",
    "is_autonomous",
    "read_gate",
    "require_gate",
]
