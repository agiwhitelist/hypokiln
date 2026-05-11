"""G1 gate logic: pre-flight alarm threshold, autonomous auto-sign."""

from __future__ import annotations

import pytest


def test_gate_unsigned_when_missing(isolated_repo):
    from hypokiln.gates import read_gate
    from hypokiln.pipeline import product_root

    status = read_gate(product_root("nope"), 1)
    assert status.signed is False


def test_gate_signed_when_approved(isolated_repo):
    from hypokiln.gates import read_gate, gate_path
    from hypokiln.pipeline import product_root

    proot = product_root("yes")
    path = gate_path(proot, 1)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "```\napproved: yes\napprover: testbot\ndate: 2026-05-11\n```\n",
        encoding="utf-8",
    )
    status = read_gate(proot, 1)
    assert status.signed is True
    assert status.approver == "testbot"


def test_autosign_refuses_when_preflight_missing(isolated_repo):
    from hypokiln.gates import autosign_gate
    from hypokiln.pipeline import product_root

    proot = product_root("no-preflight")
    proot.mkdir(parents=True)
    with pytest.raises(PermissionError, match="pre-flight checklist missing"):
        autosign_gate(proot, 1, reason="probe")


def test_autosign_refuses_when_alarms_high(isolated_repo):
    from hypokiln.gates import autosign_gate
    from hypokiln.pipeline import product_root

    proot = product_root("three-alarms")
    (proot / "spec").mkdir(parents=True)
    (proot / "spec" / "gate-1-preflight.md").write_text(
        "---\nalarm_count: 3\n---\n", encoding="utf-8"
    )
    with pytest.raises(PermissionError, match="3 alarms"):
        autosign_gate(proot, 1, reason="probe")


def test_autosign_passes_when_alarms_under_threshold(isolated_repo):
    from hypokiln.gates import autosign_gate, read_gate
    from hypokiln.pipeline import product_root

    proot = product_root("two-alarms")
    (proot / "spec").mkdir(parents=True)
    (proot / "spec" / "gate-1-preflight.md").write_text(
        "---\nalarm_count: 2\n---\n", encoding="utf-8"
    )
    status = autosign_gate(proot, 1, reason="probe")
    assert status.signed is True
    assert "autonomous" in status.approver

    # Persisted on disk.
    refetched = read_gate(proot, 1)
    assert refetched.signed is True


def test_autosign_body_scan_fallback(isolated_repo):
    """If frontmatter is absent, the **Verdict.** alarm regex must count."""
    from hypokiln.gates import autosign_gate
    from hypokiln.pipeline import product_root

    proot = product_root("body-scan")
    (proot / "spec").mkdir(parents=True)
    (proot / "spec" / "gate-1-preflight.md").write_text(
        "# Pre-flight\n"
        "**Verdict.** alarm — too dangerous\n"
        "**Verdict.** alarm — incumbent owns distribution\n"
        "**Verdict.** alarm — vaporware wedge\n",
        encoding="utf-8",
    )
    with pytest.raises(PermissionError, match="alarms"):
        autosign_gate(proot, 1, reason="probe")
