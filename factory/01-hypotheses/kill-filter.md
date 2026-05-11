# Kill filter (Stage 4)

Binary checks. **Any "yes" kills the hypothesis** unless explicitly overridden by the Founder Agent with a written rationale.

## Hard kills

- [ ] Requires a sales team to close the first 10 customers.
- [ ] Regulated industry (health, finance, kids) without legal counsel committed.
- [ ] Depends on a single platform (App Store, single API) whose ToS forbids the use case.
- [ ] Inference cost > $5/active-user/month at MVP scale with no path to < $1.
- [ ] Requires ≥ $10k in non-refundable upfront infra (custom hardware, model training).
- [ ] Solves a problem already saturated by 5+ free incumbents with strong distribution.
- [ ] Founder cannot reach the first 10 users via existing channels (no audience, no community, no warm intros).
- [ ] CAC > LTV by construction (e.g., $5/mo product needing paid B2C ads).
- [ ] Gross margin < 40% at scale.
- [ ] Cannot ship a useful version in ≤ 4 weeks.
- [ ] **No capability wedge** — `capability_wedge.id` does not reference an entry in `factory/00-radar/capability-wedges.md` released in the last 90 days. Generic products without a capability advantage cannot beat incumbents on craft alone.
- [ ] **No viable viral mechanic** — `viral_mechanic.type` is missing or cannot be fitted to any of the four types (shareable_output | public_artifact | n_player_wedge | before_after_proof) per `hypokiln/architecture-and-virality`. Products with no organic distribution path die in the noise.

### Mortality-class hard kills (added 2026-05-11 — strategic dead-on-arrival patterns)

These were added after the `slimproxy` post-mortem: hypotheses that the scoring formula loved on execution axes (pain × wedge × WTP × margin) but that were structurally dead because of trust, platform monopoly, weekend-cloneability, or compliance exposure. Each check is binary; any "yes" kills.

- [ ] **Trust-MITM without compliance budget.** Hypothesis requires routing user secrets / API keys / production request bodies through the founder's infrastructure (proxy, SDK shim, key vault) AND the round JSON does NOT mark `compliance_budget_usd ≥ 50000` AND the target ICP is not "indie / hobby" (those forgive). Catches "we proxy your OpenAI key" → enterprise won't touch us. Set `kill_reason: "trust MITM with no SOC2/HIPAA budget — paying ICP won't grant credential access"`.
- [ ] **Single-vendor platform killshot.** The capability wedge (`capability_wedge.provider`) is one upstream vendor AND the hypothesis has no concrete `multi_provider_plan` field describing how a competing provider's primitive substitutes within ≤ 30 days. Vendor adds a native dashboard / native primitive → product is obsolete that DevDay. Set `kill_reason: "single-vendor platform monopoly killshot — one DevDay obsoletes us"`.
- [ ] **Weekend-clonable proxy / wrapper.** The full product architecture fits in `architecture_loc_estimate ≤ 1500` lines AND the hypothesis has no concrete `distribution_lead_months ≥ 3` claim AND no `community / brand / data network` moat field. Translation: any motivated dev clones us in 5 days and undercuts. Set `kill_reason: "weekend-clone risk — no moat beyond distribution lead, race to zero"`.
- [ ] **Legal/regulatory exposure mismatch.** Hypothesis processes data the legal frameworks GDPR / HIPAA / SOX / FINRA / COPPA care about (PII at rest, PHI, financial records, child data) AND no `compliance_budget_usd` field AND no `compliance_strategy` (e.g. "EU-data-stays-in-EU", "on-prem-only", "DPA template + processor agreement on day one"). Lawsuit on month 6. Set `kill_reason: "legal exposure > compliance budget — predictable lawsuit before first paying enterprise"`.
- [ ] **Viral mechanic embarrasses paying ICP.** Hypothesis declares `viral_mechanic.type = before_after_proof | shareable_output` AND the share payload publicly reveals something the paying ICP would NOT want public (their spending number, their employer name, their margins, their PII). Engagement-then-monetization gap: free hobby tier shares, paid pro tier does not — and the price-confidence model relied on the Pro tier sharing. Set `kill_reason: "viral mechanic blocks paying ICP — virality stays trapped in non-paying segment"`.

### Mortality-class hard kills (added 2026-05-11 B-fix-2 — Patterns #8/#9/#10)

Added after the `mvp3` Agent Guardian post-mortem: the patched filter caught the slimproxy class but missed three other dead-on-arrival shapes. Each is a binary hard-kill.

- [ ] **Vaporware wedge.** The hypothesis's `capability_wedge` is NOT GA today — `wedge_shipped_today: false` OR `released` is a future date OR the wedge appears only on a public roadmap with no shipping commitment. Scheduled vendor features are vapor until the API call returns 200. Set `kill_reason: "vaporware wedge — capability_wedge.id not shipped today; product depends on a primitive that may slip or never ship"`. (Beta / private-preview wedges with confirmed founder access can score `vaporware_wedge_risk: 5` and survive — but must declare access proof in `notes`.)
- [ ] **Local-first without enforcement layer.** The hypothesis's `form_factor` is one of `local-cli | desktop-app | browser-extension | vscode-extension | mobile-pwa` AND `pricing.model in (subscription | freemium | usage)` AND `enforcement_layer` is null. A naked local binary with a local-only license check gets pirated; the conversion floor collapses. Set `kill_reason: "local-first without enforcement layer — paying tier is reverse-engineerable by any motivated dev; expected piracy rate 30%+"`. Acceptable mitigations to score `enforcement_gap_risk ≤ 5`: (a) server-validated license + server-fetched secret sauce (prompt-pack / model / config refreshed weekly), (b) GitHub Marketplace billing (platform enforces), (c) hardware-bound key, (d) hosted aggregation surface that the CLI cannot replicate locally.
- [ ] **Freemium tier covers paying ICP's expected usage.** `free_tier_units` is declared AND `expected_monthly_usage_paying` is declared AND `expected_monthly_usage_paying / free_tier_units < 1.2` (paying ICP barely exceeds the free cap). The free tier covers ~80%+ of what the paying ICP would actually use, so they never feel upgrade pressure and the conversion floor collapses below 5%. Set `kill_reason: "freemium overlap — free tier covers paying ICP's monthly usage; conversion will stay below 5% and the round's WTP thesis is structurally unreachable"`. Mitigation: shrink the free tier or move the price-fence to a different axis (seats, advanced features, retention window) so paying ICP hits the cap predictably.

## Mortality stress-test (5 personas, mandatory per surviving hypothesis)

For every hypothesis that clears the hard-kill list above, run the 5-persona stress test below. Each persona returns a verdict: `kill` | `worry` | `endorse`. If **3 or more** personas vote `kill`, the hypothesis is killed regardless of how well it scored on execution axes. Record the verdict matrix in `products/<slug>/spec/decisions.md` under the Stage 4 entry.

| # | Persona | Question they answer |
|---|---------|----------------------|
| 1 | **Enterprise CISO** | "Will I let this product near our production credentials / customer data? If no, kill." |
| 2 | **Tier-1 VC associate (Series Seed bias)** | "Why won't a competent solo dev clone this in two weekends? If no defensible answer, kill." |
| 3 | **Disgruntled month-6 customer** | "I paid $X/mo for 6 months, my counter-ROI is < charged price. Refund + churn. If 1 in 3 cohort retention < 6 mo, kill." |
| 4 | **EU regulator / state AG** | "Show me your DPA, lawful-basis statement, processor list. If 'we'll do that later' — kill." |
| 5 | **Incumbent CEO (the most credible competitor named in Stage 5)** | "I have a 24-month head start, my eng team is 8 people, my marketing budget is $50k/mo. Why won't I crush you in Q3? If no answer, kill." |

The persona stress-test runs after the hard-kill list because it is more expensive (≥ 5 verdicts × N hypotheses). The hard-kill list is the cheap filter; the persona test is the strategic-soundness filter.

### Persona verdict format

In `round-NNN.json`, append per surviving hypothesis:

```json
"persona_stress_test": {
  "ciso":           { "verdict": "kill" | "worry" | "endorse", "reason": "..." },
  "vc":             { "verdict": "...", "reason": "..." },
  "month_6":        { "verdict": "...", "reason": "..." },
  "regulator":      { "verdict": "...", "reason": "..." },
  "incumbent_ceo":  { "verdict": "...", "reason": "..." },
  "kill_count":     <int 0-5>,
  "verdict":        "killed" | "survived"
}
```

If `kill_count ≥ 3` then `verdict: "killed"` and `passed_kill_filter` flips to `false` with `kill_reason: "5-persona stress-test: <kill_count>/5 personas voted kill"`.

## Yellow flags (require explicit mitigation)

- [ ] Cold outreach is the only channel.
- [ ] Depends on user-generated content for value (cold-start problem).
- [ ] Requires a second-party integration that blocks at PM review.
- [ ] AI is the *whole* product, not a feature inside a workflow.

## Override protocol

If the Founder Agent overrides a hard kill:

```
override_for: h-NNN
overridden_check: "<exact wording>"
rationale: "<2-3 sentences with concrete evidence>"
mitigation: "<how the risk is reduced>"
approver: <name>
date: <YYYY-MM-DD>
```

Stored in the round file under `overrides: []`.
