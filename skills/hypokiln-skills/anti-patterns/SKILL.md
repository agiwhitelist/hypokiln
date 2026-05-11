# SKILL: hypokiln/anti-patterns

Mortality patterns the factory previously failed to catch — execution-
strong hypotheses that were structurally dead-on-arrival. Added
2026-05-11 after the `slimproxy` post-mortem: the round scored h-002
at 7.85 STRONG and recommended it for Gate 1 sign-off despite the
hypothesis having (a) full MITM access to paying-ICP credentials,
(b) one-DevDay platform-vendor killshot exposure, and (c) ≤ 1500 LOC
weekend-clone replicability. None of the existing skill packs are
written to catch those.

Attached to Market Skeptic Agent (Stages 4 + 5), Product Strategist
Agent (Stage 6 selection), and the upcoming pre-flight checklist
runner at Gate 1. When this pack is attached, its rules are authoritative.

## When to apply

- **Stage 4 (Kill Filter)** — Market Skeptic applies the seven Mortality Patterns below as binary hard-kills, in addition to the existing kill-filter rules in `factory/01-hypotheses/kill-filter.md`. Any pattern matched → set `passed_kill_filter: false` with the corresponding `kill_reason`.
- **Stage 5 (Market Snapshot)** — Market Skeptic uses the patterns as a checklist when assessing competitor moat depth and writing the `## Moat depth assessment` section in `competitor-analysis.md`.
- **Stage 6 (Selection Score)** — Product Strategist references the patterns when filling the eight risk axes (`trust_exposure_risk`, `weekend_clone_risk`, `compliance_gap_risk`, …) read by `scripts/score-hypotheses.ts`.
- **Gate 1 pre-flight** — checklist authoring agent uses the patterns to author each of the 10 brutal questions in `factory/01-hypotheses/gate-1-preflight-template.md`.

## Why this exists

The execution-pack stack the factory carries (capability-radar,
architecture-and-virality, copywriting, page-cro, seo-meta, …) is
optimised for "ship a good landing fast". Every pack teaches *how to
make the product better*. None teach *how to recognise that this
product should not exist*.

The result, before this pack landed: hypotheses with surface-strong
execution axes (pain × wedge × WTP × margin × speed) coasted through
Stage 4 + Stage 6 even when their structural risk profile guaranteed
they could not survive a year. Anti-patterns plugs that gap.

## The ten mortality patterns

### 1. Trust-MITM without compliance budget

The product requires the paying ICP to grant credential, API-key, or
production-data access through the founder's infrastructure (HTTP
proxy, SDK shim, key vault, agent operating-system) **and** there is
no SOC2 / HIPAA / GDPR budget set, **and** the target ICP is not
"indie / hobby" (those forgive credential exposure for ≤ $20/mo
products).

> Example: `slimproxy` (h-002 in the May 2026 round). Pitches itself
> as "drop-in `OPENAI_BASE_URL` proxy that auto-compacts every call".
> The Pro tier targets dev teams with $200-500/mo OpenAI bills — the
> exact segment whose CISO will refuse credential MITM without SOC2
> Type 2. The product cannot reach paid PMF without ~$50-100k of
> compliance work that is not budgeted.

Set `trust_exposure_risk: 8-10` and `compliance_gap_risk: 7-10`. Any
single axis at 10 is an automatic scoring hard-kill (see
`scripts/score-hypotheses.ts`).

### 2. Single-vendor platform killshot

The capability wedge points at **one** upstream vendor's primitive
(OpenAI `/compact`, Anthropic `dreaming`, Stripe Issuing, Discord
Activities) **and** the hypothesis has no concrete `multi_provider_plan`
field describing a competing vendor's primitive that substitutes
within ≤ 30 days, **and** the vendor has a track record of moving the
underlying primitive into a first-party feature within a year.

> Example: `slimproxy` (again). The wedge IS OpenAI's `/compact` API.
> OpenAI has a usage dashboard already; one DevDay adds an
> "auto-compact" toggle to it and the product is obsolete by Friday.
> The week-2 Anthropic adapter named as mitigation is itself
> single-vendor — just a different one.

Set `platform_dependency_risk: 7-10`. Mitigation MUST be **two or
more** independent providers, not "we'll diversify later".

### 3. Weekend-clonable proxy / wrapper

The full v1 architecture fits in ≤ 1500 LOC and uses only
public-API primitives **and** the hypothesis has no concrete moat
field — no distribution lead, no community, no proprietary data, no
network effect. After the first viral share, the product surface is
visible enough that a motivated solo dev clones it in five days and
undercuts on price.

> Example: `slimproxy`'s v1 is roughly: Cloudflare Worker that proxies
> `*/v1/responses` → `openai.com/v1/responses` with a `/compact`
> insert. ~ 400 lines. The savings dashboard is another 600 lines.
> Total ~ 1000 LOC. The first $487 → $63 share-card tweet wakes up
> the open-source clones.

Set `weekend_clone_risk: 7-10` and demand a `distribution_lead_months
≥ 3` claim with proof (audience, community, integration).

### 4. Compliance gap vs declared budget

The product processes data the legal frameworks GDPR / HIPAA / SOX /
COPPA / FINRA care about — PII at rest, PHI, financial records,
child data, prompts that themselves contain customer data — **and**
the round JSON does not declare `compliance_budget_usd` ≥ the
realistic floor (≥ $25k for GDPR DPA + processor agreements,
≥ $50k for SOC2 Type 1, ≥ $100k for HIPAA + BAA), **and** there is
no `compliance_strategy` (e.g. "EU-data-stays-in-EU", "on-prem
deployment only", "redact PII at ingest, never store").

Set `legal_risk: 5-10` and `compliance_gap_risk: 7-10`. The 6-month
mark hits before SOC2 ships; the first enterprise customer sues for
data exposure and the runway is gone.

### 5. Viral mechanic blocks the paying ICP

The hypothesis declares `viral_mechanic.type = before_after_proof |
shareable_output | public_artifact` **and** the share payload
publicly reveals something the paying segment would not want public
— their monthly spending, their employer, their margins, their PII,
their customer count. The free / hobby segment shares; the paying
segment never does.

> Example: `slimproxy`'s share card. "I saved $487 on my OpenAI bill"
> works on r/sideproject and indie-dev Twitter (hobby ICP — the $9
> tier). Enterprise (the $49+ tier) will never post their internal
> compute cost publicly. The funnel from virality → paid is broken
> by design.

Set `viral_mechanic_mismatch_risk: 7-10`. The hypothesis can still
ship, but the GTM math has to model the free → paid conversion
*without* assuming the paying segment shares.

### 6. "Same as X but cheaper"

The differentiation against named incumbents reduces to a price
delta, **and** the hypothesis has no defensible moat (capability,
distribution, brand, network) that justifies sustaining the price
delta when incumbents respond. Incumbents have 18+ months of
distribution and can match price for one quarter while the new
product runs out of runway.

Set `distribution_incumbency_risk: 7-10`. Mitigation MUST cite a
**non-price** wedge: new ICP, new form factor, new channel.

### 7. Open-core fails without team-tier value

The product positioning is "open-source + paid cloud tier", **and**
the paid tier value is "we host it for you" with no real team-tier
features (SSO, audit logs, fine-grained RBAC, dedicated support,
compliance docs). Helicone / Langfuse / Sentry / Mattermost / Plausible
prove the open-core model works **only** when the paid tier solves a
team-shaped problem the self-host build refuses to solve.

> Example: A naïve open-source slimproxy fork that only sells "managed
> hosting" — every paying team would just self-host on Cloudflare
> Workers for $5/mo of compute. The cloud tier must add SSO, per-route
> audit logs, team Slack alerts, SOC2 docs — features the founder
> cannot justifiably ship in the OSS image.

Set `distribution_incumbency_risk: 5-8`. Mitigation MUST enumerate
concrete team-tier features.

### 8. Local-first BYO-key without enforcement layer

Added 2026-05-11 after the `mvp3` Agent Guardian post-mortem. The
hypothesis ships a local CLI / desktop app / browser extension /
VS Code extension **and** has subscription / freemium pricing **and**
no concrete enforcement anchor outside the local binary. A motivated
solo dev binary-patches the license check in an evening; a more
ambitious one re-implements the wedge over the public capability API
in a weekend. The conversion floor collapses to whatever fraction of
users will not pirate on principle.

> Example: `mvp3` h-001 Agent Guardian was originally scored a clean
> "viable 5.95" because every other risk axis was honest. The factory
> missed that a local CLI + BYO-key + freemium $19/mo with no
> server-validated license + no remote prompt-pack would lose ~30-40%
> of paying TAM to piracy and ~5% more to DIY-clones over Anthropic's
> public `cw-002` API. The product still survives as a side-hustle —
> not as a fundable startup.

Set `enforcement_gap_risk: 6-10`. Acceptable mitigations (each pushes
the axis down by 2-3 points):

- Server-validated license + server-fetched secret sauce that is
  required for full value (curated prompt-pack refreshed weekly,
  hosted model, evaluation telemetry the local binary cannot
  produce).
- GitHub Marketplace billing or VS Code Marketplace billing — the
  platform enforces the payment flow.
- Hardware-bound key (e.g. macOS Keychain attestation, TPM).
- Hosted aggregation / share-page surface that ships only from the
  authenticated web account, so the CLI's most viral output is gated
  behind the SaaS.
- Team-tier ($X/seat, ≥3 seats) where the buyer is a company and
  cracking is not socially acceptable.

`enforcement_layer` field MUST be declared. Null + a local form factor
forces this axis to ≥ 7 and triggers Stage 4 hard-kill.

### 9. Vaporware wedge

Added 2026-05-11. The hypothesis's `capability_wedge` references a
platform primitive that is NOT shipped today. The wedge is
"announced", "in private preview", "on the public roadmap", or
"shipping next month". Vendors slip. Vendors deprecate. Vendors
re-architect. A scheduled feature is not a real moat until the API
call returns 200.

> Example: An mvp3 candidate sketch promised a multi-provider plan
> "OpenAI parallel-function-calling adapter ships in week 3" — but
> the primitive itself was not yet GA at hypothesis time. If GPT-5
> slips two quarters, the multi-provider mitigation is null and the
> hypothesis flips to a single-vendor killshot (Pattern #2). The
> wedge being un-shipped at hypothesis time is itself the kill.

Set `vaporware_wedge_risk: 7-10` when the wedge primitive is not GA
today. Mitigation: pick a wedge that is shipped today (`released`
date ≤ today AND publicly callable). Beta / private-preview wedges
with confirmed founder access can score 5 and survive — but must
attach proof (access screenshot, beta-list confirmation email
quoted in `notes`).

`wedge_shipped_today: true` is the only honest way to score this at
0. False on this field forces `vaporware_wedge_risk ≥ 9` per
Stage 4 hard-kill.

### 10. Freemium overlap

Added 2026-05-11. The hypothesis ships a freemium model where the
free tier's monthly cap is so generous that the paying ICP's
realistic usage stays inside it. The paying ICP never feels upgrade
pressure. SaaS conversion benchmarks show 2-5% freemium → paid is
the **median** floor; products where free covers paying ICP usage
sit at 0.5-1%, which collapses the entire round-001 WTP thesis.

> Example: `mvp3` h-001 declared "free tier = 100 reviews / month".
> The paying ICP (solo indie devs running Cursor / Claude Code) does
> ~30-100 agent reviews per month. The free tier covers them
> entirely; the upgrade trigger never fires. The original Stage 6
> scoring did not catch this because `freemium_overlap_risk` did
> not exist.

Set `freemium_overlap_risk: 7-10` when `expected_monthly_usage_paying
/ free_tier_units < 1.2`. Both fields must be declared in the same
unit (calls/mo, MB/mo, projects/mo). Mitigations:

- Shrink the free tier so the paying ICP hits the cap in week 1.
- Move the price-fence to a different axis: seats, advanced
  features, retention window, team integrations.
- Cap free on a binary feature (no batch export, no team sharing)
  rather than a usage volume the paying ICP barely brushes.

`expected_monthly_usage_paying` and `free_tier_units` MUST both be
declared if `pricing.model = freemium`. Missing either forces
`freemium_overlap_risk ≥ 7`.

## Quick reference card

```
Pattern                       Risk axis primarily affected
─────────────────────────────────────────────────────────────
1 Trust-MITM                  trust_exposure_risk + compliance_gap_risk
2 Single-vendor killshot      platform_dependency_risk
3 Weekend-clonable            weekend_clone_risk
4 Compliance gap              compliance_gap_risk + legal_risk
5 Viral mismatch              viral_mechanic_mismatch_risk
6 Same as X but cheaper       distribution_incumbency_risk
7 Open-core failure           distribution_incumbency_risk
8 Local-first no enforcement  enforcement_gap_risk          (2026-05-11)
9 Vaporware wedge             vaporware_wedge_risk          (2026-05-11)
10 Freemium overlap           freemium_overlap_risk         (2026-05-11)
```

Any single axis at 10 → automatic hard-kill regardless of how strong
the execution axes are. This is the scoring CLI's contribution; Stage
4 hard-kill rules in `kill-filter.md` cover the same patterns from
the audit side.

## What this pack is NOT

This pack catches **strategic** mortality. It does not catch
**execution** mortality (broken builds, unstyled UI, wrong copy) —
those are caught by the existing audit gates (`design-audit`,
`market-snapshot-audit`, `mvp-build`).

This pack is also not a license to over-pessimise. A hypothesis with
trust_exposure_risk = 4 is worth scoring; one with 9 is not. The
cliff is high single-digit on the relevant axis.
