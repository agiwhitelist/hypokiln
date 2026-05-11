# SKILL: hypokiln/architecture-and-virality

Picks **form factor**, **archetype**, **wow moment**, and **viral mechanic**
for a hypothesis at Stage 6. The artifact is
`products/<slug>/spec/architecture.md` (template lives at
`factory/03-product/architecture-template.md`).

When this pack is attached, its rules are authoritative. The factory's
single highest-leverage decision is whether a product has a real viral
mechanic — without one, no amount of starter quality or design polish
produces a "talked-about" product.

## When to apply

- **Stage 6 (Selection Score)** — every top-3 hypothesis MUST get an
  `architecture.md`. The operator approves it at Gate 1 alongside the pick.
- **Stage 8 (Landing First)** — CRO Copywriter reads `architecture.md`
  before writing copy. Landing pitches the wow moment + makes the viral
  mechanic obvious.
- **Stage 10 (MVP Build)** — Fullstack Builder reads `architecture.md`
  to decide which starter overlays to apply and to wire the viral mechanic
  into the product.

## Hard rule — no viral mechanic, no ship

Every product MUST declare ONE of the four viral mechanic types. If the
hypothesis can't be fitted to any of them, it gets killed at Stage 6 with
`kill_reason: "no viable viral mechanic"`. There is no organic growth path
without one, and the factory cannot afford to ship products that need
paid distribution to find their first 100 users.

## Form factor — decision guide

The default is `web-saas`. Switch only when the wow moment is materially
impossible inside a web shell.

| Form factor | Switch when | Examples |
|---|---|---|
| `web-saas` | Dashboard / paid flow / artifact creation flows are the product. Default. | Linear, Notion, most B2B SaaS |
| `email-first` | The wow moment trigger = an email forward. User never visits the dashboard until they trust the product. | Forward-a-contract → renew-alert. Forward-an-expense → categorise. |
| `slack-bot` | The audience already lives in Slack and the wow moment fires inside a channel. Extra UI = friction. | Internal-ops bots, on-call companions, standup tools. |
| `chrome-ext` | The wow moment requires being **inside** another website (Gmail, LinkedIn, Twitter, GitHub) at the moment of action. | Cluely-style overlays, "summarise this thread" tools, "rewrite as cold-email-style". |
| `mobile-pwa` | The use case happens on phone, in motion, touch-first. The web shell on desktop is degraded. | Voice journaling, location-aware tools, photo-in-flow capture. |
| `api-first` | The end user is a developer; UI is documentation. | Inference price wrappers, niche embedding endpoints. |

If a hypothesis fits two form factors, pick the one where the **wow moment
is 30 seconds faster**.

## Archetype — decision guide

From `hypokiln/domain-patterns`. Pick exactly one.

| Archetype | Wow pattern | Default tables |
|---|---|---|
| `monitor-or-alarm` | Detect → notify → user sees they would have missed it | `subjects`, `incidents`, `notifications` |
| `ai-wrapper` | Prompt → output → save → share | `prompts`, `generations`, `outputs` |
| `crud-app` | Create → list → detail | `items`, `tags`, `attachments` |
| `scheduler-app` | Schedule → fire on time → log | `schedules`, `runs`, `recipients` |
| `marketplace` | Listing → discovery → message | `listings`, `inquiries`, `reviews` |

## Wow moment — contract

```yaml
wow_moment:
  trigger: "When user <specific action>"     # MUST start with "When user"
  time_to_value: "<seconds>"                  # MUST be < 60 for v1
  output: "<concrete thing user sees>"        # MUST be specific enough to test
  realization: "<the insight>"                # what wasn't possible before
  playwright_spec: "tests/wow-moment.spec.ts"
```

### Rules

1. **Time-to-value < 60 seconds.** If the v1 wow moment is "after 5 days of usage" — kill. The factory cannot ship products that need a week of patience to become magical.
2. **Output must be concrete enough to assert in a test.** "User sees insights" — kill. "User sees a Slack message saying 'Salesforce $22k/yr renews in 47 days, cancel by Jan 1'" — fine.
3. **One wow moment per product.** Not three. Pick the one with the highest "stranger says wait what" potential.
4. **No login required for wow moment trigger** if humanly possible. Sign-up after the magic, not before.

## Viral mechanic — the four types

Pick exactly one. Each has a defining example, a trigger pattern, and a
telemetry event that Stage 17 watches.

### 1. shareable_output

The product creates a discrete artifact (image, song, video, text snippet,
recap) that the user wants to post unprompted. The artifact carries the
brand and the product URL.

- **Pattern:** "Look what I made with X" → screenshot → Twitter/iMessage.
- **Examples:** Lensa avatars, Suno songs, NotebookLM podcasts, Wrapped, Replicate community generations, Cluely's "I just generated my answer" screenshot.
- **Trigger event:** `<artifact_type>_shared` (e.g. `song_shared`, `avatar_downloaded`).
- **Engineering requirement:** the artifact MUST have product branding baked in (watermark, slug URL, "made with X"). No branding = no virality.

### 2. public_artifact

Every active user has a hosted public URL on the product's domain. The user
pulls traffic to the product because that URL = their identity / portfolio /
profile / page.

- **Pattern:** user shares their URL in Twitter bio, email signature, business card.
- **Examples:** read.cv, linktr.ee, Bluesky profiles, dev.to articles, Substack newsletters.
- **Trigger event:** `public_page_visited_by_anon`.
- **Engineering requirement:** SEO must be top-notch (server-render, OG image, JSON-LD). Public page must be 95th-percentile-loadable in 800ms.

### 3. n_player_wedge

The product is materially worse with 1 user; the active user is incentivised
to invite their teammates / collaborators / friends because it makes the
product better for THEM.

- **Pattern:** "I need my team on this so we can X together."
- **Examples:** Slack, Figma, Linear, Notion shared spaces, Roam graphs.
- **Trigger event:** `teammate_invited`, `workspace_created_with_n_members`.
- **Engineering requirement:** invite flow must be 1-step (paste emails, send). No "verify your domain first" friction.

### 4. before_after_proof

The act of using the product is itself screenshot-worthy or screencast-worthy.
Viral moment = users post videos of themselves using it because the
demo IS the marketing.

- **Pattern:** Twitter screencast → "look at this".
- **Examples:** Cursor (AI-writes-my-code screencasts), Cluely (overlay in interview), Granola (meeting-notes-without-bot), Suno (live song generation).
- **Trigger event:** `screencast_session_started` (proxy: long active session with high action density).
- **Engineering requirement:** the product UX must be visibly different from anything else in the category at first glance. Generic shadcn dashboard = no demo virality.

## Anti-patterns — kill the hypothesis if any apply

- **No viral mechanic possible.** Generic CRUD tool with no shareable output, no public page, no n-player wedge, no demo-worthy moment. KILL.
- **Wow moment > 2 minutes to first value.** Onboarding-heavy products don't survive in 2026.
- **Wow moment requires payment first.** Try-before-buy is mandatory.
- **Form factor chosen for engineering convenience, not the wow moment.** "Web-saas because the starter is web-saas" → re-evaluate.
- **Multiple wow moments.** Pick one. The "we do everything" pitch never goes viral.
- **Capability wedge missing.** Architecture must rest on a wedge from `factory/00-radar/capability-wedges.md`. No wedge = generic = no organic distribution.

## Definition of done (Stage 6 architecture pass)

- [ ] `products/<slug>/spec/architecture.md` exists and is fully filled
- [ ] `form_factor` chosen with a one-sentence justification tied to the wow moment
- [ ] `archetype` matches `hypokiln/domain-patterns` exactly
- [ ] `capability_wedge.id` references a real entry in `factory/00-radar/capability-wedges.md`
- [ ] `wow_moment` has all 5 fields filled; `time_to_value < 60` seconds
- [ ] `viral_mechanic.type` is one of the four; `telemetry_event` is named
- [ ] At least one alternative form_factor was considered and recorded in `decisions.md`
