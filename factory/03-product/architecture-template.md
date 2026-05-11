# Architecture — `<product-slug>`

Owned by Product Strategist Agent (Stage 6 — Selection Score). Produced
alongside the top-3 ranking and approved together at Gate 1.

This file is the canonical source of truth for **form factor**, **archetype**,
**wow moment**, and **viral mechanic** for this product. Every downstream
agent reads it before role-specific work:

- CRO Copywriter (Stage 8 Landing) — pitches the wow moment, embeds the viral mechanic
- Visual Prompt Engineer (Stage 8 visuals) — designs the screenshot-worthy artifact
- Fullstack Builder (Stage 10 MVP Build) — picks starter overlays, wires the viral mechanic
- QA Engineer (Stage 11) — writes the wow-moment Playwright test
- Traction Watch (Stage 17) — knows which signals to monitor

If a downstream agent finds this file missing, abort with
`SUMMARY: ABORTED — architecture.md not produced by Stage 6`.

---

## 1. Form factor

```yaml
form_factor: web-saas | email-first | slack-bot | chrome-ext | mobile-pwa | api-first
```

**Decision rule:** see `hypokiln/architecture-and-virality` skill pack.
Default = `web-saas` unless the wow moment is impossible without a different
shell.

**Why this form factor (1-2 sentences):**
> `<concrete reason tied to wow moment, not preference>`

**Starter:** `hypokiln-starter` (only one shipped today).
**Overlays:** `[stripe, magic-link, <viral_mechanic-specific>]` — opt-in
add-ons applied after the base starter clone.

## 2. Archetype

```yaml
archetype: monitor-or-alarm | ai-wrapper | crud-app | scheduler-app | marketplace
```

From `hypokiln/domain-patterns`. Dictates default tables, cron jobs, and
empty-state primitives in the starter.

## 3. Capability wedge (mandatory)

This product MUST rest on a capability wedge from
`factory/00-radar/capability-wedges.md`. If none applies, kill the
hypothesis — generic products without a capability wedge cannot win.

```yaml
capability_wedge:
  id: cw-NNN
  provider: <Anthropic | OpenAI | fal.ai | …>
  released: <YYYY-MM-DD>
  what_was_impossible_before: "<one sentence>"
```

## 4. Wow moment (mandatory — verified by QA at Stage 11)

The single 30-second flow that makes a stranger say "wait, what". Must be
implemented as a working flow by Stage 10 and verified by an automated
Playwright test at Stage 11.

```yaml
wow_moment:
  trigger: "When user <specific action — forwards email | uploads file | types prompt | …>"
  time_to_value: "<seconds — must be < 60 for v1>"
  output: "<specific concrete thing the user sees or receives>"
  realization: "<the insight that wasn't possible before this product>"
  playwright_spec: "tests/wow-moment.spec.ts"
```

Example (h-007 contract monitor):
```yaml
wow_moment:
  trigger: "When user forwards any vendor contract email to contracts@<product>.com"
  time_to_value: "30 seconds"
  output: "Slack message: '⚠️ RenewAlert: Salesforce ($22k/yr) — Cancel by Jan 1 or auto-renews. 47 days left.'"
  realization: "This deadline was invisible. Now it's impossible to miss."
  playwright_spec: "tests/wow-moment.spec.ts"
```

## 5. Viral mechanic (mandatory — verified at Stage 17 telemetry)

This product MUST have ONE of the four viral hooks. Without it, the
hypothesis is killed at Gate 1 — there is no organic growth path.

```yaml
viral_mechanic:
  type: shareable_output | public_artifact | n_player_wedge | before_after_proof
  trigger: "When user does X, they receive/create [thing they want to share]"
  share_surface: "Twitter | Reddit | Slack | iMessage | LinkedIn | embed-in-doc"
  shareable_object: "<URL pattern, image format, video format — the concrete artifact>"
  k_factor_hypothesis: "1 active user → ~<N> new visitors in 30 days via the mechanic"
  telemetry_event: "<analytics event name fired when share happens — must be in hypokiln/analytics-events>"
```

### Viral mechanic types — pick exactly one

| Type | Pattern | Examples |
|---|---|---|
| **shareable_output** | Product generates an artifact (image/song/video/text) that the user posts | Lensa, Suno, Wrapped, NotebookLM |
| **public_artifact** | Each user has a public URL the product hosts | read.cv, linktr.ee, Bluesky |
| **n_player_wedge** | Product is materially better with 2+ users | Slack, Figma, Linear, Notion |
| **before_after_proof** | The act of using it is screenshot-worthy | Cursor demos, Cluely overlay, Granola recap |

## 6. Decision footer

```yaml
approved_at_gate_1: false   # set true after Founder sign-off
approver: ""
date: ""
notes: ""
```
