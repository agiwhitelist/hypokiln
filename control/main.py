"""HypoKiln control plane — FastAPI entrypoint.

Run:
    uvicorn control.main:app --reload --port 8765

The web frontend talks to this on :8765. CORS is open in dev for
localhost:3000 (Next.js dev server).
"""

from __future__ import annotations

import logging
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers import (
    artifacts,
    events,
    gates,
    logs,
    portfolio,
    runs,
    search,
    stats,
    templates,
    wedges,
)

log = logging.getLogger("hypokiln.control")


def _allowed_origins() -> list[str]:
    raw = os.environ.get(
        "HYPOKILN_WEB_ORIGINS",
        "http://localhost:3000,http://127.0.0.1:3000",
    )
    return [o.strip() for o in raw.split(",") if o.strip()]


app = FastAPI(
    title="HypoKiln control plane",
    version="0.1.0",
    description=(
        "Visual wrapper for the HypoKiln pipeline. List ideas, start runs, "
        "approve G1, watch state + logs over SSE, browse capability wedges."
    ),
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins(),
    allow_credentials=False,
    allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)


app.include_router(runs.router)
app.include_router(gates.router)
app.include_router(logs.router)
app.include_router(artifacts.router)
app.include_router(stats.router)
app.include_router(portfolio.router)
app.include_router(search.router)
app.include_router(templates.router)
app.include_router(events.router)
app.include_router(wedges.router)


@app.get("/healthz", tags=["meta"])
def healthz() -> dict:
    return {"status": "ok", "service": "hypokiln-control-plane"}
