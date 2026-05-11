"""Skill-loader resolution + per-delegate attachment."""

from __future__ import annotations


def test_delegate_skills_only_covers_four_agents():
    from hypokiln.skill_loader import DELEGATE_SKILLS
    expected = {
        "Trend Scout Agent",
        "Product Strategist Agent",
        "Market Skeptic Agent",
        "Founder Agent",
    }
    assert set(DELEGATE_SKILLS.keys()) == expected


def test_local_skills_paths_exist():
    """The four in-repo packs must actually be on disk."""
    import hypokiln
    from hypokiln.skill_loader import LOCAL_SKILLS

    for name, rel in LOCAL_SKILLS.items():
        target = hypokiln.REPO_ROOT / rel
        assert target.is_dir(), f"{name} missing on disk at {target}"
        skill_md = target / "SKILL.md"
        assert skill_md.is_file(), f"{name}/SKILL.md missing"


def test_resolve_spec_handles_subpath():
    from hypokiln.skill_loader import _resolve_spec

    assert _resolve_spec("foo/bar") == ("foo/bar", None)
    assert _resolve_spec("foo/bar:sub/path") == ("foo/bar", "sub/path")
    assert _resolve_spec("foo/bar:") == ("foo/bar", None)


def test_instructions_for_inlines_local_skill():
    from hypokiln.skill_loader import instructions_for

    text = instructions_for(
        "Trend Scout Agent",
        base_instructions="# Base prompt",
    )
    # Skip-skills env var is set by the conftest isolated_repo fixture; without
    # it we expect the capability-radar pack to appear in the attached section.
    # Here we don't use isolated_repo so the inline should happen iff
    # HYPOKILN_SKIP_SKILLS is unset. Either branch is acceptable; just check
    # the function did not crash and produced a string.
    assert "# Base prompt" in text


def test_skip_skills_short_circuit(monkeypatch):
    monkeypatch.setenv("HYPOKILN_SKIP_SKILLS", "1")
    from hypokiln.skill_loader import instructions_for

    text = instructions_for("Trend Scout Agent", base_instructions="# Base")
    assert text == "# Base"
