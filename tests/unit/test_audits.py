"""Stage-gate audits: trend-radar, hypothesis, market-snapshot."""

from __future__ import annotations

import json


def test_trend_radar_pass(isolated_repo):
    from hypokiln.audits import audit_trend_radar
    from hypokiln.pipeline import product_root

    proot = product_root("good")
    (proot / "research").mkdir(parents=True)
    (proot / "research" / "trend-radar.md").write_text(
        "# Trend radar\n\n"
        + "\n".join(
            f"## Signal {i}\nhttps://example{i}.com 2026-04-{10+i}"
            for i in range(1, 9)
        ),
        encoding="utf-8",
    )
    # Add 3 distinct hostnames.
    (proot / "research" / "trend-radar.md").write_text(
        "# Trend radar 2026-04-15\n\n"
        "## Signal 1\nhttps://news.ycombinator.com/abc 2026-04-01\n"
        "## Signal 2\nhttps://producthunt.com/abc 2026-04-02\n"
        "## Signal 3\nhttps://reddit.com/r/saas 2026-04-03\n"
        "## Signal 4\nhttps://news.ycombinator.com/def 2026-04-04\n"
        "## Signal 5\nhttps://producthunt.com/def 2026-04-05\n"
        "## Signal 6\nhttps://reddit.com/r/startups 2026-04-06\n"
        "## Signal 7\nhttps://news.ycombinator.com/ghi 2026-04-07\n"
        "## Signal 8\nhttps://producthunt.com/ghi 2026-04-08\n",
        encoding="utf-8",
    )
    result = audit_trend_radar("good")
    assert result.passed, [v.rule + ": " + v.detail for v in result.violations]


def test_trend_radar_fails_when_missing(isolated_repo):
    from hypokiln.audits import audit_trend_radar

    result = audit_trend_radar("missing")
    assert not result.passed
    assert any(v.rule == "T1" for v in result.violations)


def test_hypothesis_audit_fails_on_template_wedge(isolated_repo):
    from hypokiln.audits import audit_hypothesis
    from hypokiln.pipeline import product_root

    proot = product_root("templates")
    (proot / "research").mkdir(parents=True)
    h = {
        "id": "h-001",
        "slug": "ai-thing",
        "name": "AI Thing",
        "who": "solo developers, in side-project phase",
        "pain": "manual deploys",
        "wedge": "AI-powered",  # ← template anti-pattern
        "distribution": "Twitter",
        "willingness_to_pay": "$9/mo",
    }
    (proot / "research" / "round-001.json").write_text(
        json.dumps([h] * 8), encoding="utf-8"
    )
    result = audit_hypothesis("templates")
    assert not result.passed
    assert any(v.rule == "H4" for v in result.violations)


def test_hypothesis_audit_passes_clean_round(isolated_repo):
    from hypokiln.audits import audit_hypothesis
    from hypokiln.pipeline import product_root

    proot = product_root("clean")
    (proot / "research").mkdir(parents=True)
    h = {
        "id": "h-001",
        "slug": "ssl-monitor",
        "name": "SSL Monitor",
        "who": "solo dev, in side-project phase",
        "pain": "renewing certificates",
        "wedge": "claude-sonnet-4-6 batch tool calls drop scan cost 10x",
        "distribution": "HN show",
        "willingness_to_pay": "$3/mo",
    }
    (proot / "research" / "round-001.json").write_text(
        json.dumps([h] * 8), encoding="utf-8"
    )
    result = audit_hypothesis("clean")
    assert result.passed, [v.rule + ": " + v.detail for v in result.violations]


def test_market_snapshot_fails_without_files(isolated_repo):
    from hypokiln.audits import audit_market_snapshot
    from hypokiln.pipeline import product_root

    proot = product_root("empty-snapshot")
    (proot / "research").mkdir(parents=True)
    result = audit_market_snapshot("empty-snapshot")
    assert not result.passed
    rules = {v.rule for v in result.violations}
    # Should flag at least the missing market-snapshot.md and competitor file.
    assert "M1" in rules or "M2" in rules


def test_market_snapshot_passes_complete(isolated_repo):
    from hypokiln.audits import audit_market_snapshot
    from hypokiln.pipeline import product_root

    proot = product_root("snap-ok")
    research = proot / "research"
    research.mkdir(parents=True)
    (research / "market-snapshot.md").write_text(
        "# Market snapshot\n\n## Why now\n\n"
        "claude-sonnet-4-6 dropped on 2026-03-12, opening a new wedge.\n",
        encoding="utf-8",
    )
    (research / "competitor-analysis.md").write_text(
        "# Competitors\n\n## Alpha Inc\nhttps://alpha.example $9/mo\n\n"
        "## Beta Corp\nhttps://beta.example $19/mo\n\n"
        "## Gamma LLC\nhttps://gamma.example $29/mo\n",
        encoding="utf-8",
    )
    (research / "pricing-research.md").write_text(
        "Median: $19/mo. Top: $29/mo.", encoding="utf-8"
    )
    result = audit_market_snapshot("snap-ok")
    assert result.passed, [v.rule + ": " + v.detail for v in result.violations]
