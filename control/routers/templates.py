"""Prompt templates — save successful prompts as launch presets."""

from __future__ import annotations

import json
import re
from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from hypokiln import REPO_ROOT

router = APIRouter(prefix="/api/templates", tags=["templates"])


def _dir() -> Path:
    d = REPO_ROOT / ".hypokiln" / "templates"
    d.mkdir(parents=True, exist_ok=True)
    return d


_NAME_RE = re.compile(r"^[a-z][a-z0-9-]{0,47}[a-z0-9]$")


class Template(BaseModel):
    name: str = Field(..., pattern=r"^[a-z][a-z0-9-]{0,47}[a-z0-9]$")
    prompt: str = Field(..., min_length=4)
    notes: str = ""


@router.get("")
def list_templates() -> list[Template]:
    out: list[Template] = []
    for p in sorted(_dir().glob("*.json")):
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            out.append(Template(**data))
        except Exception:  # noqa: BLE001
            continue
    return out


@router.put("/{name}")
def upsert(name: str, body: Template) -> Template:
    if not _NAME_RE.match(name):
        raise HTTPException(400, "invalid template name")
    if body.name != name:
        raise HTTPException(400, "name mismatch")
    path = _dir() / f"{name}.json"
    path.write_text(body.model_dump_json(indent=2) + "\n", encoding="utf-8")
    return body


@router.delete("/{name}")
def delete(name: str) -> dict:
    if not _NAME_RE.match(name):
        raise HTTPException(400, "invalid template name")
    path = _dir() / f"{name}.json"
    if not path.exists():
        raise HTTPException(404, f"template {name!r} not found")
    path.unlink()
    return {"name": name, "deleted": True}
