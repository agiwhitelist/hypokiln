"""Pytest fixtures for HypoKiln unit tests.

The pipeline + audits read state from `REPO_ROOT / .hypokiln/state/` and
products from `REPO_ROOT / products/<slug>/`. Every test that touches the
filesystem gets a fresh tmp_path-based REPO_ROOT via monkeypatching.
"""

from __future__ import annotations

import importlib
import os
import sys
from pathlib import Path

import pytest


@pytest.fixture
def isolated_repo(monkeypatch, tmp_path) -> Path:
    """Point HYPOKILN_STATE_DIR + REPO_ROOT at a fresh tmp directory.

    Re-imports hypokiln modules so they pick up the new root.
    """
    # Reset the singletons.
    for mod in list(sys.modules):
        if mod.startswith("hypokiln"):
            del sys.modules[mod]

    # Patch the env so the loader picks up the tmp state dir.
    monkeypatch.setenv("HYPOKILN_STATE_DIR", ".hypokiln/state")
    monkeypatch.setenv("HYPOKILN_SKIP_SKILLS", "1")  # tests don't need real skills

    # Patch REPO_ROOT inside hypokiln to tmp_path.
    import hypokiln
    monkeypatch.setattr(hypokiln, "REPO_ROOT", tmp_path)
    import hypokiln.pipeline as _pipeline
    monkeypatch.setattr(_pipeline, "REPO_ROOT", tmp_path)
    import hypokiln.gates as _gates  # noqa: F401
    import hypokiln.audits as _audits
    monkeypatch.setattr(_audits, "REPO_ROOT", tmp_path)

    return tmp_path
