# Gate 1 — Idea approval (checklist + signature)

The operator copies this template to
`products/<slug>/spec/gate-1-approval.md` after reviewing the artifacts
listed below, fills the approval block at the top, and re-runs
`hypokiln build --resume <slug>`. The orchestrator parses the
`approved: yes` + `approver:` lines and unblocks Stage 7.

Under `--yolo` / `HYPOKILN_AUTONOMOUS=1`, this file is auto-written;
the checklist below is still the **mental model** the autonomous run
embodies — every item must hold or the run shouldn't have reached G1.

---

## Signature

```yaml
approved: <yes | no>
approver: <name or 'hypokiln-autonomous'>
date: <YYYY-MM-DDTHH:MM:SSZ>
notes: |
  <1-3 sentences on why you signed (or why not)>
```

---

## What G1 approves (since 2026-05)

Three artifacts as a **bundle** — sign all or none:

1. **Top hypothesis** from `products/<slug>/research/round-NNN.json`
2. **Architecture** at `products/<slug>/spec/architecture.md`
3. **Decisions log** at `products/<slug>/spec/decisions.md`

If any artifact is missing, do NOT sign — re-run the pipeline.

## Review checklist (8 items)

### Hypothesis (3 items)

- [ ] **Wedge is sharp.** "AI-powered" or "fast" is NOT a wedge.
      A wedge names ONE concrete reason a user switches today.
- [ ] **Pain has a real verbatim quote** with a URL in the last 90 days.
- [ ] **Distribution channel is named and accessible** to the operator
      (not "we'll get on TechCrunch" — concrete: "post in r/SaaS,
      author has 800 karma there").

### Architecture (3 items)

- [ ] **`form_factor` matches the wow moment.** If the wow moment is
      "AI summarises my Slack thread", `form_factor: slack-bot` is
      almost certainly correct; `web-saas` would force friction.
- [ ] **`capability_wedge.id` references a real entry** in
      `factory/00-radar/capability-wedges.md` released in the last
      90 days. Generic products without a fresh capability die fast.
- [ ] **`wow_moment.time_to_value` < 60 seconds** and
      `wow_moment.output` is specific enough to assert in a Playwright
      test ("the user receives a Slack message saying X" — not "the
      user gets insights").

### Viral mechanic (2 items)

- [ ] **`viral_mechanic.type` is one of the four** (`shareable_output`,
      `public_artifact`, `n_player_wedge`, `before_after_proof`).
      If the operator can't see how this product produces organic
      traffic via ONE of these, the bet is "paid distribution will
      save us" — kill.
- [ ] **`viral_mechanic.telemetry_event` is named** so Stage 17
      (Traction Watch) has signals to monitor at D7/D30/D90.

## Common reasons to refuse G1

- The architecture form_factor was chosen for engineering convenience
  ("starter is web-saas") rather than the wow moment. Re-run Stage 6.
- The wow moment is "after the user spends a week with the product" —
  cannot survive in 2026. Re-run Stage 3.
- The viral mechanic is "users will tweet about us" with no concrete
  shareable artifact. Kill the hypothesis.
- The capability wedge is older than 90 days. Re-scan
  `factory/00-radar/capability-wedges.md` or kill.
- The decisions log shows Product Strategist overrode Market Skeptic's
  Stage 4 kill without a documented mitigation. Refuse until the
  override has evidence.

## After signing

The orchestrator picks up the signature at the start of Stage 7 (Brand
Naming). Stage 7-10 then ship the landing + MVP build. Gate 2 (offer +
landing, live page review) is the next human checkpoint.
