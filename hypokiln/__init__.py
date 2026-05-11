"""HypoKiln — capability-wedge-driven idea kiln.

This package is the orchestrator + CLI. Stages spawn a logged-in coding
CLI (codex / claude / gemini) as a subprocess per stage; there is no
agent framework dependency.
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT: Path = Path(__file__).resolve().parent.parent

__all__ = ["REPO_ROOT"]
__version__ = "0.1.0"
