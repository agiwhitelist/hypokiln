# hypokiln-skills

In-repo skill packs that the HypoKiln pipeline attaches to delegate prompts via
`hypokiln/skill_loader.py`. These are **not** general-purpose Claude skills —
they are content scoped tightly to the idea-validation phase of the kiln.

Each sub-directory is a self-contained pack with one `SKILL.md` (overview +
hard rules), optionally augmented with `reference/<topic>.md` files for deep
cookbooks. Layout matches the convention used by `pbakaus/impeccable` and
`obra/superpowers`.

## Pack index

| Slug | Attached to | Purpose |
|---|---|---|
| `capability-radar` | Trend Scout, Product Strategist, Market Skeptic | Wedge taxonomy — what counts as a fresh AI capability wedge vs noise; weekly scan rules; ranking formula |
| `anti-patterns` | Product Strategist, Market Skeptic, Founder | Seven mortality patterns (trust-MITM, clone-risk, single-vendor killshot, freemium overlap, …) and how to detect them in a hypothesis |
| `architecture-and-virality` | Product Strategist (+ critic loops) | Form-factor / archetype / wow-moment / viral-mechanic contract for the Stage 6 architecture |
| `domain-patterns` | Product Strategist | Five archetypes (monitor/alarm, ai-wrapper, crud, scheduler, marketplace) — pricing, audience, retention norms |

## How the loader sees these

`hypokiln/skill_loader.py` resolves each pack through `LOCAL_SKILLS` (no
git clone, no token). On disk, every pack root is its own `SKILL.md`.
Loader honours the `HYPOKILN_SKILL_BUDGET` env var (default 131,072 chars
per pack), so the budget is generous enough that the SKILL.md is always
fully inlined.

## Editing rules

- One `SKILL.md` per pack, max ~500 words. Hard rules are numbered and
  imperative so a coding CLI can grep them.
- Optional `reference/` files are deep cookbooks: concrete checklists,
  worked examples, edge cases.
- Templates marked `OPERATOR REVIEWS BEFORE SHIP` are placeholders the
  operator must check before relying on the kiln's recommendation.

## External skill packs

In addition to the four in-repo packs above, HypoKiln also pulls two
external packs by name:

| Slug | Source | Attached to |
|---|---|---|
| `obra/superpowers` | <https://github.com/obra/superpowers> | Trend Scout, Market Skeptic, Founder |
| `ncklrs/startup-os-skills` | <https://github.com/ncklrs/startup-os-skills> | Product Strategist, Market Skeptic |

Both are resolved via `git clone --depth 1` into `.hypokiln/skills/<owner>__<repo>/`
on first use, or — if you ship the repo with `vendor/skills/<owner>__<repo>/`
pre-populated — read straight from the vendored snapshot with zero network.
