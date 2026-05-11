# Hypothesis template

Each round of hypotheses lives in `factory/01-hypotheses/round-NNN.json` as an array of objects shaped like the schema below. This Markdown file is the human-readable reference.

## Schema

```jsonc
{
  "id": "h-001",                  // string, unique within round
  "slug": "ai-meeting-recap",     // kebab-case, used as folder name
  "name": "AI Meeting Recap",     // display name
  "who": "PMs at 50-500 person SaaS companies",
  "pain": "Spends 30 min/day rewriting meeting notes; loses action items.",
  "solution": "Browser extension that joins the call, drafts notes + action items, syncs to Linear.",
  "wedge": "Linear-native action items (competitors only export to Notion/Slack).",
  "pricing": { "model": "per-seat", "monthly_usd": 12 },
  "distribution": ["product hunt", "linkedin operator content", "linear marketplace"],

  // Capability wedge — MUST reference an entry in factory/00-radar/capability-wedges.md
  // released in the last 90 days. Hypotheses without a capability wedge are
  // killed at Stage 4. See hypokiln/capability-radar skill pack.
  "capability_wedge": {
    "id": "cw-NNN",
    "provider": "Anthropic | OpenAI | fal.ai | …",
    "released": "YYYY-MM-DD",
    "what_was_impossible_before": "one-sentence plain-English summary"
  },

  // Viral mechanic — MUST be one of four types. Hypotheses without a viable
  // viral mechanic are killed at Stage 4. See hypokiln/architecture-and-virality.
  "viral_mechanic": {
    "type": "shareable_output | public_artifact | n_player_wedge | before_after_proof",
    "trigger": "When user does X, they receive/create <shareable thing>",
    "telemetry_event": "<analytics event name fired on share>"
  },

  // Scoring inputs (0-10 unless noted)
  "speed": 8,
  "pain_strength": 7,
  "distribution_score": 6,
  "margin": 7,
  "cheapness": 7,
  "wow_factor": 5,
  "payment_simplicity": 9,

  // Risk inputs (0-10, higher = more risk; subtracted from score).
  // 2026-05-11 (B-fix): five new mortality axes added after the
  // slimproxy post-mortem — execution-strong hypotheses were over-
  // scored because trust / clone / incumbency exposure was never
  // priced in. ANY axis at 10 is an automatic hard-kill regardless
  // of how strong the positive axes are. See scripts/score-hypotheses.ts.
  "legal_risk": 2,                       // GDPR/HIPAA/SOX/COPPA exposure breadth
  "inference_cost_risk": 5,              // $/1k token cost vs charged price
  "platform_dependency_risk": 4,         // single-vendor wedge killshot risk
  "trust_exposure_risk": 1,              // credentials/PII/keys MITM exposure
  "weekend_clone_risk": 3,               // architecture replicable in <1 weekend
  "distribution_incumbency_risk": 4,     // months of distribution lead held by incumbents
  "viral_mechanic_mismatch_risk": 2,     // viral mechanic blocks the paying ICP
  "compliance_gap_risk": 2,              // GDPR/HIPAA/SOX exposure vs declared compliance budget
  // 2026-05-11 B-fix-2 (mvp3 Agent Guardian post-mortem):
  "vaporware_wedge_risk": 1,             // wedge depends on un-shipped platform primitive
  "enforcement_gap_risk": 1,             // local binary without server anchor → piracy/DIY risk
  "freemium_overlap_risk": 2,            // free tier covers paying ICP's expected usage

  // Mitigation fields read by Stage 4 hard-kill rules (added 2026-05-11)
  "compliance_budget_usd": 0,            // declared $ budget for SOC2/HIPAA/GDPR
  "compliance_strategy": null,           // e.g. "EU-data-stays-in-EU", "on-prem-only"
  "multi_provider_plan": null,           // e.g. "Anthropic adapter ships week 2"
  "distribution_lead_months": 0,         // founder's pre-launch audience/community lead
  "architecture_loc_estimate": 5000,     // rough LOC of v1 product (clone-risk proxy)
  // 2026-05-11 B-fix-2 mitigation fields:
  "wedge_shipped_today": true,           // is the wedge primitive shipped + GA today?
  "enforcement_layer": null,             // e.g. "server-validated license + remote prompt-pack", "GitHub Marketplace billing", "hardware-bound key"
  "expected_monthly_usage_paying": 0,    // paying ICP's expected monthly usage units
  "free_tier_units": 0                   // free tier monthly cap in same units

  // Kill filter outputs
  "passed_kill_filter": null,     // boolean, set by Stage 4
  "kill_reason": null,

  "notes": "Test with 10 PMs from r/ProductManagement before any build."
}
```

## Field guide

- **wedge** — required. The single specific reason a target user switches *today*. "AI-powered" is not a wedge; "Linear-native" is.
- **capability_wedge** — required (since 2026-05). What providers shipped in the last 90 days that makes this product possible NOW and was infeasible before. Generic products without this are killed at Stage 4 — see `hypokiln/capability-radar`.
- **viral_mechanic** — required (since 2026-05). One of four types. Without it there is no organic growth path, and the factory can't carry paid distribution — see `hypokiln/architecture-and-virality`.
- **pricing.model** — `per-seat` | `flat` | `usage` | `freemium`.
- **distribution** — concrete channels with proof of access, not aspirational ones.
- **wow_factor** — does the demo make someone screenshot it? 0–10.
- **payment_simplicity** — Stripe-friendly? B2C self-serve = 9. Enterprise procurement = 1.
- **inference_cost_risk** — how badly does $/1k tokens kill margin? 10 = "every request is GPT-4o image".
- **trust_exposure_risk** — does the paying ICP have to grant us credential / PII / production-data access for the product to work? 0 = none. 5 = limited OAuth scope. 9 = full OpenAI/Anthropic key. 10 = root credentials + production data → automatic kill.
- **weekend_clone_risk** — could a competent solo dev replicate the v1 architecture in ≤ 1 weekend (≤ 1500 LOC, no proprietary model, no data network)? 0 = no, deep moat. 10 = yes + no distribution lead → automatic kill.
- **distribution_incumbency_risk** — how many months of distribution lead do the named incumbents (Stage 5) hold? 0 = greenfield. 5 = ~12 mo. 10 = > 36 mo + dominant SEO + brand → automatic kill unless we have a circumventing wedge (new ICP / form factor / channel).
- **viral_mechanic_mismatch_risk** — does the declared `viral_mechanic` align with what the **paying** ICP would actually share publicly? Hobby ICP shares freely → 0. Paying enterprise ICP would NOT share spending/PII/margins → 7+. 10 = viral mechanic is structurally embarrassing for the paying segment → automatic kill.
- **compliance_gap_risk** — gap between regulatory exposure (legal_risk dimension) and declared `compliance_budget_usd` + `compliance_strategy`. 0 = no regulated data. 10 = HIPAA/GDPR/SOX exposure with zero budget and no strategy → automatic kill.
- **vaporware_wedge_risk** (2026-05-11 B-fix-2) — does the wedge depend on a platform primitive that is NOT shipped today? Scheduled vendor features are not real until they ship. 0 = wedge is fully GA today. 5 = beta / private-preview the founder has confirmed access to. 9 = public roadmap mention with no shipping date. 10 = the wedge IS an unshipped feature → automatic kill. Mitigation field: `wedge_shipped_today: true` is the only way to honestly score this at 0.
- **enforcement_gap_risk** (2026-05-11 B-fix-2) — for products that ship a local binary / CLI / browser-extension / desktop app, can a competent dev pirate or DIY-clone the product without paying? 0 = product is server-side, no client to crack. 3 = local client but server-validated license + remote prompt-pack / model / config (cracking removes critical functionality). 7 = local client with local-only license check (binary-patch crack feasible in an evening). 10 = open-source client + no server-side moat → automatic kill. Mitigation field: `enforcement_layer` must enumerate a concrete anchor (e.g. "server-validated license + remote prompt-pack updated weekly", "GitHub Marketplace billing").
- **freemium_overlap_risk** (2026-05-11 B-fix-2) — does the declared free tier cover the paying ICP's expected monthly usage? If yes, the paying ICP never feels upgrade pressure and conversion stays below the freemium floor (~5%). 0 = no free tier OR free tier is meaningfully below paying ICP usage (paying ICP hits cap in week 1). 5 = free tier covers ~50% of paying ICP usage (some pressure). 9 = free tier covers ≥80% of paying ICP usage. 10 = paying ICP can live indefinitely on free → automatic kill. Mitigation fields: `expected_monthly_usage_paying` + `free_tier_units` must be declared honestly in the same units (calls/mo, MB/mo, projects/mo) for the gap to be calculable.
- **wedge_shipped_today** — boolean. True iff the wedge primitive is GA and publicly callable. False forces `vaporware_wedge_risk ≥ 9` per Stage 4 hard-kill.
- **enforcement_layer** — string or null. Required when `form_factor in (local-cli, desktop-app, browser-extension, vscode-extension, mobile-pwa)`. Null forces `enforcement_gap_risk ≥ 7`.
- **expected_monthly_usage_paying** — integer. Realistic monthly usage of the paying ICP at the SAME usage unit as the free tier cap. e.g. for "100 reviews/mo free tier", the paying ICP's monthly review count.
- **free_tier_units** — integer. The free tier cap in the same unit. If the ratio `expected_monthly_usage_paying / free_tier_units < 1.2` (paying ICP barely hits free cap), `freemium_overlap_risk` should be ≥ 8.
- **compliance_budget_usd** — declared $ commitment for SOC2 / HIPAA / GDPR / SOX work. Set the realistic figure; an aspirational $0 here forces compliance_gap_risk to 10 when the legal_risk axis is non-trivial.
- **compliance_strategy** — concrete mitigation (e.g. `"EU-data-stays-in-EU + DPA template"`, `"on-prem-only deployment"`, `"redact PII at ingest"`). `null` is OK only if `legal_risk ≤ 2`.
- **multi_provider_plan** — concrete fallback when the single-vendor wedge dies (e.g. `"Anthropic prompt-caching adapter ships within 30 days"`). `null` is OK only if `platform_dependency_risk ≤ 3`.
- **distribution_lead_months** — founder's pre-launch audience or warm channel lead in months. 0 if you are starting cold; ≥ 3 if you have an audience, community, or warm intros lined up.
- **architecture_loc_estimate** — rough LOC of the v1 product. Proxy for "weekend clonability" — a product that fits in ≤ 1500 LOC and has no data/network moat triggers `weekend_clone_risk` hard-kill.

## Workflow

1. Generate ≥ 10 hypotheses per round. Every hypothesis MUST include all eleven risk axes (legacy three + five mortality axes + three Pattern-8/9/10 axes) and the nine mitigation fields — Stage 4 hard-kill rules read these directly.
2. Save the round JSON.
3. Run kill filter (Stage 4) — Market Skeptic Agent applies hard-kill list + 5-persona stress test (≥ 3 kill votes flips `passed_kill_filter` to false). Update `passed_kill_filter` and `persona_stress_test` matrix.
4. Run scoring CLI: `npm run foundry:score -- factory/01-hypotheses/round-NNN.json`. The CLI applies the per-axis penalty formula AND the "any-axis-at-10" hard-kill rule (separate from Stage 4's logic). Hypotheses flagged HARD by scoring are out even if `passed_kill_filter: true`.
5. Take top-3 (clears BOTH Stage-4 filter AND scoring hard-kill) to Gate 1.
6. **If zero hypotheses survive both filters, regenerate the round** with mortality criteria in mind. Do not soften the filters.
