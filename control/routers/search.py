"""Cross-run search: grep prompts + research/ + spec/ + logs."""

from __future__ import annotations

import re
from pathlib import Path

from fastapi import APIRouter, HTTPException

from hypokiln import pipeline as _pipeline
from hypokiln import REPO_ROOT

router = APIRouter(prefix="/api/search", tags=["search"])


_SEARCHABLE_GLOBS = ("research/*.md", "research/*.json", "spec/*.md")
_LOG_GLOB = "logs/stage-*.log"


@router.get("")
def search(q: str) -> dict:
    """Grep `q` across every active slug's prompt, research/, spec/, logs/."""
    q = q.strip()
    if not q:
        raise HTTPException(400, "empty query")
    if len(q) > 200:
        raise HTTPException(400, "query too long")
    needle = re.compile(re.escape(q), re.IGNORECASE)

    sdir = _pipeline.state_dir()
    hits = []
    if not sdir.exists():
        return {"q": q, "hits": []}

    for child in sorted(sdir.iterdir()):
        if not (child / "state.json").is_file():
            continue
        state = _pipeline.load_state(child.name)
        if state is None:
            continue
        # Prompt match
        if needle.search(state.prompt):
            hits.append({
                "slug": state.slug,
                "file": "(prompt)",
                "line": 1,
                "snippet": state.prompt[:200],
            })
        # File matches
        proot = _pipeline.product_root(state.slug)
        files: list[Path] = []
        if proot.is_dir():
            for pattern in _SEARCHABLE_GLOBS:
                files.extend(proot.glob(pattern))
        for p in (child / "logs").glob("stage-*.log") if (child / "logs").is_dir() else []:
            files.append(p)
        for f in files:
            try:
                text = f.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            for i, line in enumerate(text.splitlines(), start=1):
                if needle.search(line):
                    try:
                        rel = f.relative_to(REPO_ROOT).as_posix()
                    except ValueError:
                        rel = str(f)
                    hits.append({
                        "slug": state.slug,
                        "file": rel,
                        "line": i,
                        "snippet": line.strip()[:200],
                    })
                    if len(hits) >= 200:
                        return {"q": q, "hits": hits, "truncated": True}
    return {"q": q, "hits": hits}
