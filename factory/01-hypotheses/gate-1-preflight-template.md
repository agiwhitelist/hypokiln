# Gate 1 — pre-flight 10-question checklist

Added 2026-05-11 after the `slimproxy` post-mortem (h-002 was scored
STRONG / recommended for G1 and turned out to be structurally dead-on-
arrival). The execution-pack stack proves how to ship; this checklist
proves the product **should be shipped at all**.

## When to run

Stage 6 (Selection Score) authors `products/<slug>/spec/gate-1-preflight.md`
**after** the top-3 ranking is decided and **before** emitting the
recommendation. Each question is answered for the single recommended
hypothesis (not for every survivor). The auto-sign path (`--yolo`,
`OPENMVP_AUTONOMOUS=1`) at G1 refuses to sign if more than **two**
questions are flagged `alarm` — even in autonomous mode the operator
must review.

## File format

Stage 6 writes the file as Markdown with the exact frontmatter below.
`orchestrator/gates.py` parses the verdict line per question.

```markdown
---
slug: <product slug>
hypothesis_id: h-NNN
authored_at: <ISO 8601 UTC>
authored_by: Product Strategist Agent
recommended_for_g1: true
alarm_count: <int 0-10>
---

# Pre-flight — <product name>

## Q1. Vendor-killshot scenario

**Question.** If the upstream vendor that owns your capability wedge
(`{capability_wedge.provider}`) ships a native first-party version of
the primitive on its next DevDay / release, what value remains? Quote
the concrete non-platform feature your product still has.

**Answer.** <2-4 sentences. Cite a real defensible feature, not a hand-
wave like "we'll diversify". If the answer reduces to "we're cheaper" or
"we move faster", that is an alarm.>

**Verdict.** ok | alarm
**Rationale (if alarm).** <one line>

## Q2. Weekend-clone scenario

**Question.** A competent solo dev sees your launch tweet at 9 AM
Monday. By Friday they have an open-source clone live. What stops the
clone from undercutting you? Name the moat (audience, community,
proprietary data, network effect) and its current depth in months.

**Answer.** <…>

**Verdict.** ok | alarm
**Rationale (if alarm).** <…>

## Q3. First-customer "no" objection

**Question.** Imagine the very first prospect from the paying ICP
agreeing to pay. What is the single most likely reason they say "no"?
Write the objection in their voice, then write the concrete answer the
v1 product gives. If the answer is "we'll build that later", that is
an alarm.

**Answer.** Objection: "<…>". Answer: <…>

**Verdict.** ok | alarm
**Rationale (if alarm).** <…>

## Q4. Compliance cost-to-first-paying-enterprise

**Question.** What is the realistic compliance spend (SOC2 / HIPAA /
GDPR / SOX) required before the paying ICP's procurement team will
sign? Compare to the round JSON's `compliance_budget_usd`. If the gap
is more than 2x, that is an alarm.

**Answer.** Realistic floor: $<N>. Declared: $<M>. Gap: <…>.

**Verdict.** ok | alarm
**Rationale (if alarm).** <…>

## Q5. Open-source clone counterattack

**Question.** If a respected competitor open-sources their version of
your wedge tomorrow under MIT and runs the cloud at half your price,
what remains for paying customers to buy from you? "Quality" is not an
answer — name a concrete team-tier feature, integration, or contract
clause.

**Answer.** <…>

**Verdict.** ok | alarm
**Rationale (if alarm).** <…>

## Q6. Solo-dev / hobby tier viability

**Question.** Can a solo developer with $50/mo total tool budget pay
for this product and get net-positive value within 14 days of signup?
If the Hobby tier exists at all, the answer must be yes with concrete
numbers. If there is no Hobby tier, explicitly say so and explain why
the funnel works without it.

**Answer.** <…>

**Verdict.** ok | alarm
**Rationale (if alarm).** <…>

## Q7. Viral mechanic vs paying ICP

**Question.** Does the viral mechanic (`viral_mechanic.type`) require
the paying ICP to share something publicly? If yes, would the paying
ICP actually share it? Name the embarrassment risk (spending, PII,
employer name, margins) and explain why the funnel still closes.

**Answer.** <…>

**Verdict.** ok | alarm
**Rationale (if alarm).** <…>

## Q8. Distribution incumbency lead

**Question.** How many months of distribution lead do the named
incumbents from Stage 5 hold (largest 3, named)? What is the
circumventing wedge — new ICP, new form factor, new channel — that
lets you bypass that lead instead of racing it?

**Answer.** Largest incumbent: <name>, ~<N> months lead. Bypass: <…>.

**Verdict.** ok | alarm
**Rationale (if alarm).** <…>

## Q9. 30-day no-traction pivot path

**Question.** If at day 30 you have zero paying users, what is the
pivot path that does NOT require throwing away the v1 build? Name a
concrete shape — different ICP, different price, different form factor,
different distribution. "Try harder on the same thing" is an alarm.

**Answer.** <…>

**Verdict.** ok | alarm
**Rationale (if alarm).** <…>

## Q10. Reddest flag + neutralisation

**Question.** Of all the open questions logged in `spec/decisions.md`,
which one is the single largest unresolved risk? Name it explicitly,
quote the line, and explain how the v1 build neutralises it (not
"we'll see"). If neutralisation requires post-launch work, that is an
alarm.

**Answer.** <…>

**Verdict.** ok | alarm
**Rationale (if alarm).** <…>

---

## Verdict summary

| # | Question | Verdict |
|---|----------|---------|
| 1 | Vendor-killshot          | <…> |
| 2 | Weekend-clone            | <…> |
| 3 | First-customer "no"      | <…> |
| 4 | Compliance gap           | <…> |
| 5 | Open-source counter      | <…> |
| 6 | Hobby tier viability     | <…> |
| 7 | Viral vs paying ICP      | <…> |
| 8 | Distribution incumbency  | <…> |
| 9 | 30-day pivot path        | <…> |
| 10 | Reddest flag            | <…> |

**Alarm count.** <int 0-10>

**Sign-off rule.** ≤ 2 alarms → auto-sign permitted in `--yolo`. > 2
alarms → operator review required regardless of mode. Always blocking,
just like G3.
