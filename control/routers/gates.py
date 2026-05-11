"""G1 read + sign endpoint."""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from hypokiln import pipeline as _pipeline
from hypokiln.gates import gate_path, read_gate

router = APIRouter(prefix="/api/runs", tags=["gates"])


class GateView(BaseModel):
    gate_id: int
    signed: bool
    approver: str
    signed_at: str | None
    notes: str
    file_exists: bool
    body: str


class SignGate(BaseModel):
    approver: str
    notes: str = ""
    approved: bool = True


@router.get("/{slug}/gate/{gate_id}", response_model=GateView)
def get_gate(slug: str, gate_id: int) -> GateView:
    try:
        slug = _pipeline.validate_slug(slug)
    except ValueError as exc:
        raise HTTPException(400, str(exc))
    if gate_id != 1:
        raise HTTPException(404, f"HypoKiln only ships G1; G{gate_id} is out of scope.")

    proot = _pipeline.product_root(slug)
    status = read_gate(proot, 1)
    path = gate_path(proot, 1)
    body = path.read_text(encoding="utf-8") if path.exists() else ""
    return GateView(
        gate_id=1,
        signed=status.signed,
        approver=status.approver,
        signed_at=status.signed_at,
        notes=status.notes,
        file_exists=path.exists(),
        body=body,
    )


@router.post("/{slug}/gate/{gate_id}")
def sign_gate(slug: str, gate_id: int, body: SignGate) -> GateView:
    try:
        slug = _pipeline.validate_slug(slug)
    except ValueError as exc:
        raise HTTPException(400, str(exc))
    if gate_id != 1:
        raise HTTPException(404, f"HypoKiln only ships G1; G{gate_id} is out of scope.")
    if not body.approver.strip():
        raise HTTPException(400, "approver must not be empty")

    proot = _pipeline.product_root(slug)
    path = gate_path(proot, 1)
    path.parent.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    approved_yes = "yes" if body.approved else "no"
    content = (
        f"# Gate 1 — operator sign-off\n\n"
        "```\n"
        f"approved: {approved_yes}\n"
        f"approver: {body.approver.strip()}\n"
        f"date: {now}\n"
        f"notes: {body.notes.strip()}\n"
        "```\n\n"
        "## What G1 approved\n\n"
        "G1 approves a bundle: top hypothesis + `spec/architecture.md` "
        "(form_factor + archetype + capability_wedge + wow_moment + viral_mechanic) "
        "+ `spec/decisions.md` + `spec/gate-1-preflight.md` (≤2 alarms).\n"
    )
    path.write_text(content, encoding="utf-8")
    return get_gate(slug, gate_id)
