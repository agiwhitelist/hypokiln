# Skills

HypoKiln attaches **skill packs** to each agent's system prompt. Packs are inert markdown text — the coding CLI (codex / claude / gemini) already follows prose, so no framework API is needed. The `[ATTACHED SKILL PACKS]` section gets appended to every per-stage prompt; the agent's `Pass 0` reads them as the canonical rulebook (skill pack wins over `instructions.md` and `factory/...` templates in case of conflict).

## The four in-repo packs

Each lives at `skills/hypokiln-skills/<name>/SKILL.md`.

| Pack | Purpose | Used by |
|---|---|---|
| `hypokiln/capability-radar` | Wedge taxonomy — what counts as a fresh AI capability wedge vs noise; weekly scan rules; ranking formula. The kiln's USP lives here. | Trend Scout (S1), Market Skeptic (S4/5), Product Strategist (S3/6) |
| `hypokiln/anti-patterns` | Seven mortality patterns — trust-MITM, weekend-clonable proxy, single-vendor killshot, freemium overlap, viral-mechanic embarrasses ICP, vaporware wedge, local-first without enforcement — and how to detect them in a hypothesis. | Product Strategist (S6 scoring), Market Skeptic (S4/5), Founder (G1 pre-flight) |
| `hypokiln/architecture-and-virality` | The form_factor / archetype / wow_moment / viral_mechanic contract for Stage 6's `architecture.md`. Four viral mechanic types: `shareable_output`, `public_artifact`, `n_player_wedge`, `before_after_proof`. | Product Strategist (S6), Market Skeptic (S4 viral check), Founder (G1 review) |
| `hypokiln/domain-patterns` | Five archetypes (monitor/alarm, ai-wrapper, crud, scheduler, marketplace) — pricing norms, audience patterns, retention defaults. Stage 6 uses this to pick the archetype field. | Product Strategist (S6) |

## The two external packs

Pulled in from public repos by name. Resolved by `hypokiln/skill_loader.py:ensure_skill` in this order:

1. `LOCAL_SKILLS` (in-repo) — checked first
2. `VENDORED_SKILLS` (pinned snapshot under `vendor/skills/<owner>__<repo>/`) — second
3. `SKILL_REGISTRY` (`git clone --depth 1` into `.hypokiln/skills/<owner>__<repo>/`) — last-resort fallback on first use

| Pack | Source | Scoped to | Used by |
|---|---|---|---|
| `obra/superpowers` | <https://github.com/obra/superpowers> | `skills/brainstorming`, `skills/verification-before-completion` | Trend Scout, Market Skeptic, Founder |
| `ncklrs/startup-os-skills` | <https://github.com/ncklrs/startup-os-skills> | `skills/product-discovery`, `skills/product-specs-writer`, `skills/pricing-strategist`, `skills/competitive-strategist` | Product Strategist, Market Skeptic |

The `pack:subpath` syntax (`"ncklrs/startup-os-skills:skills/product-discovery"`) scopes a big multi-skill pack to one sub-skill. Without it the per-pack budget would get eaten by whichever sub-skill comes first alphabetically.

## Per-delegate attachment

Defined in `hypokiln/skill_loader.py:DELEGATE_SKILLS`:

```python
DELEGATE_SKILLS = {
    "Trend Scout Agent": (
        "obra/superpowers:skills/brainstorming",
        "obra/superpowers:skills/verification-before-completion",
        "hypokiln/capability-radar",
    ),
    "Product Strategist Agent": (
        "ncklrs/startup-os-skills:skills/product-discovery",
        "ncklrs/startup-os-skills:skills/product-specs-writer",
        "ncklrs/startup-os-skills:skills/pricing-strategist",
        "ncklrs/startup-os-skills:skills/competitive-strategist",
        "hypokiln/capability-radar",
        "hypokiln/architecture-and-virality",
        "hypokiln/domain-patterns",
        "hypokiln/anti-patterns",
    ),
    "Market Skeptic Agent": (
        "obra/superpowers:skills/brainstorming",
        "obra/superpowers:skills/verification-before-completion",
        "ncklrs/startup-os-skills:skills/competitive-strategist",
        "hypokiln/capability-radar",
        "hypokiln/architecture-and-virality",
        "hypokiln/anti-patterns",
    ),
    "Founder Agent": (
        "obra/superpowers:skills/brainstorming",
        "obra/superpowers:skills/verification-before-completion",
        "hypokiln/anti-patterns",
        "hypokiln/architecture-and-virality",
    ),
}
```

## Budget

Per-pack budget defaults to **131,072 chars** (`HYPOKILN_SKILL_BUDGET`). The loader walks each pack and inlines markdown in priority order:

1. `SKILL.md` / `skill.md` (top-level + nested)
2. `reference/*.md`, `references/*.md`, `rules/*.md`, `RULES.md`, `PATTERNS.md`
3. `README.md`, `AGENTS.md`, `CLAUDE.md` (fallback)

Multi-host dotdir mirrors (`.claude/...`, `.cursor/...`, `.gemini/...`) are deduplicated against `.agents/...` to avoid shipping the same SKILL.md 14 times.

## CLI

```bash
kiln skills list                  # show every registered pack + on-disk state
kiln skills update                # pull every external pack (git pull --ff-only)
kiln skills update obra/superpowers  # update just one
kiln skills clean                 # delete the .hypokiln/skills/ cache
```

## Adding a new pack

1. **In-repo:** create `skills/hypokiln-skills/<name>/SKILL.md`, add a `LOCAL_SKILLS` entry to `hypokiln/skill_loader.py`.
2. **External:** add a `SKILL_REGISTRY` entry with the upstream URL, optionally also a `VENDORED_SKILLS` entry pointing at `vendor/skills/<owner>__<repo>/`.
3. Attach to one or more delegates by adding the pack name to `DELEGATE_SKILLS`.
4. Test: `HYPOKILN_SKIP_SKILLS=1 python -m pytest tests/` should still pass.

## Bypassing

For tests and air-gapped runs:

```bash
export HYPOKILN_SKIP_SKILLS=1
```

This short-circuits `instructions_for()` — agents see only their bare `instructions.md` with no `[ATTACHED SKILL PACKS]` section.
