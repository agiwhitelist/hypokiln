# SKILL: hypokiln/domain-patterns

Five archetypes the Foundry knows how to ship. Pick exactly ONE per product. The archetype dictates default tables, cron jobs, UI primitives. When this pack is attached, treat its rules as authoritative.

## When to apply

- Stage 10 Pass 1: choose archetype before writing schema.

## How to pick

Read `products/<slug>/spec/product-brief.md`. Match the user-promise to the closest archetype. If two fit, pick the smaller one. If none fit cleanly, the product is too ambitious for an MVP — escalate to Founder.

---

## Archetype 1 — `monitor-or-alarm`

Watches an external thing, alerts when it changes.
Examples: uptime monitor, RSS-to-Slack, price-drop, GitHub-release watcher.

### Default tables (append to `schema.ts`)

```ts
monitors      (id, user_id, name, target_url, check_interval_sec, last_status, last_checked_at, created_at)
checks        (id, monitor_id, status, latency_ms, response_code, error, checked_at)
alerts        (id, monitor_id, fired_at, recovered_at, channel, dedupe_key)
notification_channels (id, user_id, kind /* email|webhook|slack */, target, verified)
```

### Cron / worker

- Tick every `min(check_interval_sec)`, batch all monitors due in this tick, parallelize checks (Promise.all with a 30s timeout each).
- Status change (UP→DOWN or DOWN→UP) inserts an `alerts` row and fires the user's notification channel.
- Dedupe within 5min on `(monitor_id, status)` to avoid storms.

### Critical UI primitives

- Status timeline (last 24h / 7d / 30d, color blocks)
- Incident list with duration
- "Pause monitor" toggle (don't make users delete + recreate)
- Test alert button (fires a fake alert to verify channel works)

### Stripe pricing fit

Per-monitor (`$2/monitor/month`), or tiered (Free=3, Pro=25, Team=unlimited).

---

## Archetype 2 — `ai-wrapper`

User submits prompt + parameters, LLM/image/audio model returns a result.
Examples: cover-letter generator, logo creator, meeting-notes summarizer.

### Default tables

```ts
generations   (id, user_id, prompt, params jsonb, status, output, error, cost_usd, created_at, completed_at)
templates     (id, user_id, name, system_prompt, default_params jsonb)
api_quotas    (user_id, period_start, generations_used, generations_limit)
```

### Worker

- Generations are async (queue or status polling); never block a request on the model.
- Cap `cost_usd` per generation (model-dependent default — Claude 4.7 Sonnet ~$0.50, gpt-image-2 ~$0.04).
- Increment `api_quotas.generations_used` ON SUCCESS only; failed runs don't count.

### Critical UI primitives

- Prompt input + parameter form (slider/dropdown beats freeform jsonb)
- "My generations" history with re-run, copy, delete
- Quota meter ("12 / 50 used this month")
- Sample gallery (5-10 hand-curated outputs to show what's possible)

### Stripe pricing fit

Tiered by quota (Free=10/mo, Pro=200/mo, Team=2000/mo). NOT per-token unless you've already validated ARPU > $50.

---

## Archetype 3 — `crud-app`

User creates, edits, lists, archives a domain object.
Examples: simple CRM, link-in-bio, content calendar, task tracker.

### Default tables

```ts
items         (id, user_id, title, body, status, sort_order, archived_at, created_at, updated_at)
item_tags     (item_id, tag) -- many-to-many
shares        (id, item_id, share_token, expires_at) -- if public-share is a feature
```

### Critical UI primitives

- List view with sort + filter + search (always all three)
- Detail view with edit-in-place
- Archive (not delete) — soft-delete via `archived_at`
- Bulk actions (select N, archive/tag/move)
- Undo toast for destructive actions

### Stripe pricing fit

Per-seat for B2B teams; freemium with item cap (Free=20, Pro=unlimited).

---

## Archetype 4 — `scheduler-app`

Time-based actions, calendars, reminders, recurring tasks.
Examples: cron-as-a-service, content scheduler, reminder bot.

### Default tables

```ts
schedules     (id, user_id, name, cron_expr, timezone, payload jsonb, enabled, next_run_at)
runs          (id, schedule_id, run_at, status, output, error)
```

### Cron

- Master tick every minute; for each `schedules WHERE enabled AND next_run_at <= NOW()` enqueue a run, recompute `next_run_at` from cron+tz.
- Use a real cron parser library; don't roll your own.

### Critical UI primitives

- Cron expression builder (visual: every X, on Y, at Z) with "Show next 5 runs" preview
- Timezone selector with the user's detected zone pre-filled
- Run history with success/failure
- Pause/resume toggle

### Stripe pricing fit

Per-schedule or by run-count quota.

---

## Archetype 5 — `marketplace`

Listings + browse + transact between two user types.
Examples: niche freelancer board, services marketplace, paid newsletter directory.

### Default tables

```ts
listings      (id, owner_id, title, body, price_cents, status /* draft|live|paused|sold */, created_at)
inquiries     (id, listing_id, asker_id, message, created_at)
favorites     (user_id, listing_id, created_at)
reviews       (id, listing_id, reviewer_id, rating /* 1-5 */, body, created_at)
```

### Critical UI primitives

- Browse with filters (category, price range, location/tags)
- Listing detail with author, contact button, reviews
- "Post a listing" form with image upload
- Favorites / saved-search

### Marketplace gotchas

- Two-sided cold start: solve buyer side first; sellers come if buyers come (not vice versa)
- Trust: ratings + verified badges + dispute flow
- Fraud: rate-limit "post listing" (1 per minute per user, 10 per day)

### Stripe pricing fit

Take rate (Stripe Connect, 5–15%) OR seller subscription (`$10/mo` for unlimited listings).

---

## Universal hard rules

- Pick ONE archetype. Don't compose two for the MVP.
- The archetype's default tables go into `src/libs/schema.ts` as one block, with a single migration `migrations/0002_<archetype>.sql`.
- Every archetype includes `userId` on every user-scoped row — no exceptions.
- Every archetype has a "demo / sample data" toggle (`is_demo=true`) seeded on first login.

## Anti-patterns

- Picking "marketplace" for an MVP without a buyer side — it'll be empty for 6 months
- Inventing a 6th archetype without escalating to Founder
- Skipping the cron tick spec for monitor / scheduler ("we'll add it later" = never)
- AI-wrapper with no quota meter (users hit your bill, not theirs)
- CRUD app without bulk actions and search (unusable past 50 rows)
