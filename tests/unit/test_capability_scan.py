"""capability-scan parsing + archive rewriter."""

from __future__ import annotations

from datetime import date, timedelta


def test_parse_active_and_archived(isolated_repo):
    from hypokiln.cli import _parse_capability_entries

    text = """# Capability wedges

## Active wedges (last 90 days)

### `cw-001` — claude-sonnet-4-6 batch tool calls

- **Provider:** Anthropic
- **Released:** 2026-04-12

### `cw-002` — fal/SDXL-Turbo

- **Provider:** fal
- **Released:** 2026-03-20

## Archived (> 90 days)

### `cw-009` — old wedge

- **Provider:** OpenAI
- **Released:** 2025-08-01
"""
    entries = _parse_capability_entries(text)
    active = [e for e in entries if e["section"] == "active"]
    archived = [e for e in entries if e["section"] == "archived"]
    assert len(active) == 2
    assert len(archived) == 1
    assert active[0]["id"] == "cw-001"
    assert active[0]["provider"] == "Anthropic"
    assert active[0]["released_date"].isoformat() == "2026-04-12"


def test_rewrite_with_archive_moves_old_entries(isolated_repo):
    from hypokiln.cli import _parse_capability_entries, _rewrite_with_archive

    today = date.today()
    old_date = (today - timedelta(days=120)).isoformat()
    text = f"""# Wedges

## Active wedges (last 90 days)

### `cw-100` — old one

- **Provider:** Acme
- **Released:** {old_date}

### `cw-101` — fresh one

- **Provider:** Acme
- **Released:** {today.isoformat()}

## Archived (> 90 days)

"""
    entries = _parse_capability_entries(text)
    to_archive = [
        e for e in entries
        if e["section"] == "active" and e.get("released_date") and e["released_date"] < today - timedelta(days=90)
    ]
    assert len(to_archive) == 1
    assert to_archive[0]["id"] == "cw-100"

    new_text = _rewrite_with_archive(text, to_archive)
    # cw-100 should now appear AFTER the Archived header.
    archived_pos = new_text.find("## Archived")
    cw100_pos = new_text.find("cw-100")
    assert archived_pos > 0
    assert cw100_pos > archived_pos
