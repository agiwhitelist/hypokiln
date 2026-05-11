# Agents

HypoKiln ships four specialist agents. Each is a folder under `agents/` with one `instructions.md` — the system prompt the coding CLI sees. No Python agent classes, no agent framework. The CLI runner reads `instructions.md` directly and spawns codex / claude / gemini as a subprocess per stage.

| Agent | Stages | Role |
|---|---|---|
| **Trend Scout** | 1 (Trend Radar), 2 (Pain Extractor) | Pulls pain signals + maintains the capability-wedge log |
| **Product Strategist** | 3 (Hypothesis Generator), 6 (Selection Score + Architecture + Pre-flight) | Anchors hypotheses to wedges, scores survivors, authors architecture.md |
| **Market Skeptic** | 4 (Kill Filter), 5 (Market Snapshot) | Applies 13 hard-kills + the 5-persona mortality stress test |
| **Founder** | G1 sign-off | Reviews the bundle, signs (or rejects) Gate 1 |

## Cross-cutting critic role

The Market Skeptic isn't only an author. It also acts as the **critic** for Stage 1 (Trend Radar) and Stage 3 (Hypothesis Generator) during the critique loop. That separation of duties forces every signal and every hypothesis to survive an adversarial pass before reaching scoring.

| Stage | Author | Critic |
|---|---|---|
| 1 — Trend Radar | Trend Scout | Market Skeptic |
| 3 — Hypothesis Generator | Product Strategist | Market Skeptic |
| 5 — Market Snapshot | Market Skeptic | Product Strategist |

Stages 2, 4, 6 are one-shot — there's a deterministic gate but no critic feedback loop. The critique loop is wired to the three stages where author judgement is highest-variance and a peer-review pass demonstrably improves output quality.

## The three "Pass 0" passes

Every `instructions.md` opens with three preflight passes the agent must complete before doing its role-specific work:

- **Pass 0** — read every attached skill pack at the bottom of the prompt. In case of conflict the pack wins over `instructions.md` and any `factory/...` template.
- **Pass 0b** — if `products/<slug>/.critique-log/stage-<N>.feedback.md` exists (iteration ≥ 2), read it first. The critique contract: `## Verdict: REJECT` + `## Violations` (authoritative) + `## Required actions` + `## What to keep`.
- **Pass 0c** — read `products/<slug>/spec/decisions.md` end-to-end. Treat every prior entry as AUTHORITATIVE. Append a new section at completion using the canonical format (decision / why / considered / open questions, ≤10 lines per section).

## Memory model

| Scope | Lives in | Lifetime |
|---|---|---|
| Within one CLI session | The CLI's own Bash / Read / Edit / Task context | One subprocess lifetime |
| Between iterations of a stage | `.critique-log/stage-N.feedback.md` + `stage-N.transcript.jsonl` | Until gate-pass or exhaust |
| Between stages | `spec/decisions.md` + artifacts on disk | Persistent across resumes |

## Why this design

Three things drove the agent design away from heavier frameworks:

1. **The CLI's own loop is enough.** codex / claude / gemini already run their own internal agentic loop with tool calls, todo lists, and read/write. Wrapping them in a second loop would either fight that or duplicate it.
2. **One prompt, one response, one log file per stage.** The runner stays a single function. Failure modes are bounded.
3. **Subscription auth, not API keys.** A long-running pipeline that owns API keys is a key-exfiltration target. HypoKiln only spawns a logged-in CLI — auth lives in the CLI's session file, not ours.

The downside: no in-process message passing between stages. That's by design — the only thing that persists across stages is what's on disk under `products/<slug>/`, which makes the pipeline trivially resumable and forensically auditable. Every decision an agent made is in `spec/decisions.md` for the next agent to read.
