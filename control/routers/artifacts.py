"""Read markdown / JSON artifacts produced by the pipeline."""

from __future__ import annotations


from fastapi import APIRouter, HTTPException

from hypokiln import pipeline as _pipeline
from hypokiln import REPO_ROOT

router = APIRouter(prefix="/api/runs", tags=["artifacts"])


_ALLOWED_SUFFIXES = {".md", ".json", ".txt", ".jsonl"}


@router.get("/{slug}/artifacts/{rel_path:path}")
def read_artifact(slug: str, rel_path: str) -> dict:
    """Read an artifact under products/<slug>/.

    Restricted to read-only access of text artifacts (markdown, JSON,
    plain text). Path traversal is rejected.
    """
    try:
        slug = _pipeline.validate_slug(slug)
    except ValueError as exc:
        raise HTTPException(400, str(exc))

    proot = _pipeline.product_root(slug).resolve()
    target = (proot / rel_path).resolve()
    try:
        target.relative_to(proot)
    except ValueError:
        raise HTTPException(400, "path escapes product root")
    if not target.is_file():
        raise HTTPException(404, f"no artifact at {rel_path}")
    if target.suffix.lower() not in _ALLOWED_SUFFIXES:
        raise HTTPException(415, f"unsupported file type: {target.suffix}")
    return {
        "slug": slug,
        "path": str(target.relative_to(REPO_ROOT)),
        "size": target.stat().st_size,
        "content": target.read_text(encoding="utf-8", errors="replace"),
    }


@router.get("/{slug}/artifacts-list")
def list_artifacts(slug: str) -> dict:
    """List every readable artifact under products/<slug>/."""
    try:
        slug = _pipeline.validate_slug(slug)
    except ValueError as exc:
        raise HTTPException(400, str(exc))
    proot = _pipeline.product_root(slug)
    if not proot.exists():
        raise HTTPException(404, f"no products/{slug}/ directory")
    items: list[dict] = []
    for p in sorted(proot.rglob("*")):
        if not p.is_file():
            continue
        if p.suffix.lower() not in _ALLOWED_SUFFIXES:
            continue
        try:
            rel = p.relative_to(proot).as_posix()
        except ValueError:
            continue
        items.append({"path": rel, "size": p.stat().st_size})
    return {"slug": slug, "items": items}
