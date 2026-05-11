# SKILL: hypokiln/capability-radar

Weekly scan of AI/platform release notes. Outputs a ranked list of
"capability wedges" — things that became *possible* in the last 90 days
and are not yet covered by 5+ obvious-wrapper products.

Attached to Trend Scout Agent (Stage 1) and Market Skeptic Agent
(Stage 4, as kill-filter input). When this pack is attached, its rules
are authoritative.

## When to apply

- **Stage 1 (Trend Radar)** — Trend Scout runs a capability scan in parallel with the regular trend radar. Output goes to `factory/00-radar/capability-wedges.md` (template in the factory dir).
- **Stage 4 (Kill Filter)** — Market Skeptic kills any hypothesis whose `capability_wedge` field references a wedge older than 90 days or that doesn't appear in the radar file at all.

## Why this exists

Generic "$5/mo niche SaaS" products mostly die in the noise. The 1-in-50
products that go viral all rest on a capability wedge that opened a
30-90-day first-mover window. Cluely (overlay AI), Granola (silent
meeting notes), Suno (music gen), Cursor (LLM-IDE) — every one of them
shipped within ~60 days of a capability that didn't exist before.

The factory's only realistic path to viral output is **early detection
of wedges + same-week shipping into them**. Without a fresh wedge, the
hypothesis competes on craft against teams with more craft than us.

## Source list

`factory/00-radar/capability-sources.md` is the canonical list. Scan
weekly. Prefer primary sources (provider blogs, release notes, docs
changelogs) over aggregators.

## What counts as a wedge

A wedge **MUST** be one of:

1. **New API endpoint** — vision input, tool use, structured output, streaming, batched, long context, multi-turn audio, realtime voice
2. **New model class** — reasoning, multimodal, real-time voice, music gen, video gen, 1M+ context, on-device foundation model
3. **Price drop ≥ 10x** on existing capability — turns infeasible economics into feasible
4. **Latency drop crossing a UX threshold** — slow → instant, > 5s → < 1s text, > 30s → < 5s image, > 5min → < 30s video, > 200ms → < 50ms voice
5. **New modality combination** — audio in → image out, video in → text out, image in → 3D out, etc

A wedge is **NOT**:

- "Model X is now smarter on benchmark Y" — no new action possible
- "Now available in your region" — distribution, not capability
- "Lower latency" without crossing a UX threshold
- "Better at code" without a specific new capability
- "New SDK" wrapping the same underlying API
- "Free tier doubled" — pricing tier, not price-drop economics

## Output format

Append to `factory/00-radar/capability-wedges.md` using the entry template:

```markdown
### `cw-NNN` — `<one-line capability summary>`

- **Provider:** Anthropic | OpenAI | …
- **Released:** YYYY-MM-DD
- **Source:** <primary URL>
- **Wedge type:** new-endpoint | new-model-class | price-drop-10x | latency-threshold | new-modality-combo
- **What is now possible that wasn't 90 days ago:** "<plain English>"
- **Cost / latency envelope:** $X/request, Yms latency
- **Window estimate:** 30 | 60 | 90 days
- **Product hypotheses unlocked (3-5):** ...
- **Killed-by check:** which existing product class becomes obsolete?
```

## Ranking

For each scan, rank the new wedges 1-N by **window-leverage product**:

```
score = window_days_remaining × hypothesis_quality_max × inverse_existing_coverage
```

Where:
- `window_days_remaining` = 90 − days_since_release
- `hypothesis_quality_max` = the best-pain-strength × best-distribution-score among unlocked hypotheses
- `inverse_existing_coverage` = 1 / (1 + count_of_shipped_competitors_using_this_wedge)

Report top-3 to the operator each week. Bottom of the list = wedges to
deprioritise for THIS round of hypotheses.

## Anti-patterns

- **Citing a wedge from > 90 days ago.** It's not a wedge anymore. Move it to the archived section.
- **Stacking wedges** — "product uses three different new capabilities". Stick to one anchor wedge per product, or you're hiding "we have no real wedge" behind stack complexity.
- **Wedges without product hypotheses** — if you can't write 3-5 product ideas in 10 minutes, the wedge is either too narrow or you don't understand it. Set it aside.
- **Aggregator-only sourcing** — if every URL is some "AI weekly newsletter", you're seeing what 50k other people see. Primary sources only.

## Definition of done (weekly scan)

- [ ] Every source in `factory/00-radar/capability-sources.md` was checked for new posts in the last 7 days
- [ ] Each new wedge has a primary-source URL
- [ ] Each new wedge has 3-5 product hypotheses below it
- [ ] Wedges older than 90 days moved from "Active" to "Archived"
- [ ] Top-3 ranked entries flagged for Product Strategist Stage 3 input
