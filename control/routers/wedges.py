"""Browse the capability-wedges log — the HypoKiln USP."""

from __future__ import annotations

from datetime import date
from pathlib import Path

from fastapi import APIRouter, HTTPException

from hypokiln import REPO_ROOT
from hypokiln.cli import _parse_capability_entries

router = APIRouter(prefix="/api/wedges", tags=["wedges"])


def _wedges_path() -> Path:
    return REPO_ROOT / "factory" / "00-radar" / "capability-wedges.md"


@router.get("")
def list_wedges() -> dict:
    """Return active + archived capability wedges with provider + age."""
    path = _wedges_path()
    if not path.is_file():
        raise HTTPException(404, f"capability-wedges.md missing at {path.relative_to(REPO_ROOT)}")
    text = path.read_text(encoding="utf-8")
    entries = _parse_capability_entries(text)
    today = date.today()

    def _to_dto(e: dict) -> dict:
        released = e.get("released_date")
        age_days = (today - released).days if released else None
        return {
            "id": e["id"],
            "title": e["title"],
            "provider": e.get("provider", "?"),
            "released": released.isoformat() if released else None,
            "age_days": age_days,
            "section": e["section"],
        }

    active = [_to_dto(e) for e in entries if e["section"] == "active"]
    archived = [_to_dto(e) for e in entries if e["section"] == "archived"]
    return {
        "active": active,
        "archived": archived,
        "by_provider": _by_provider(active),
        "path": str(path.relative_to(REPO_ROOT)),
    }


@router.get("/raw")
def read_wedges_raw() -> dict:
    path = _wedges_path()
    if not path.is_file():
        raise HTTPException(404, f"capability-wedges.md missing at {path.relative_to(REPO_ROOT)}")
    return {
        "path": str(path.relative_to(REPO_ROOT)),
        "content": path.read_text(encoding="utf-8"),
    }


def _by_provider(active: list[dict]) -> dict[str, int]:
    out: dict[str, int] = {}
    for e in active:
        out[e["provider"]] = out.get(e["provider"], 0) + 1
    return dict(sorted(out.items(), key=lambda kv: -kv[1]))
