"""Cross-platform subprocess helpers.

On Windows, common CLIs (`npm`, `codex`, `claude`) ship as `.cmd` shims, and
`subprocess.run(["npm", ...])` fails with FileNotFoundError unless we resolve
the actual binary via `shutil.which` (or pass `shell=True`, which makes
argument quoting fragile — we don't).
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from typing import Sequence


def resolve(binary: str) -> str:
    """Return the absolute path of `binary` on PATH; raise if missing.

    On Windows this also tries `binary + '.cmd'` / `.exe` / `.bat`.
    """
    found = shutil.which(binary)
    if found:
        return found
    for ext in (".cmd", ".exe", ".bat"):
        found = shutil.which(binary + ext)
        if found:
            return found
    raise FileNotFoundError(f"{binary!r} not found on PATH")


def run(
    argv: Sequence[str],
    *,
    cwd: str | Path | None = None,
    env: dict | None = None,
    timeout: int = 600,
    check: bool = False,
) -> subprocess.CompletedProcess:
    """`subprocess.run` wrapper that resolves argv[0] via shutil.which."""
    if not argv:
        raise ValueError("empty argv")
    resolved = list(argv)
    resolved[0] = resolve(argv[0])
    return subprocess.run(
        resolved,
        cwd=str(cwd) if cwd is not None else None,
        env=env,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=check,
    )
