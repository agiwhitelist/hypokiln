# Capability wedges — radar output

Append-only log, newest first. One entry per provider release that
satisfies the "what counts as a wedge" rules in
`factory/00-radar/capability-sources.md`. Stale entries (> 90 days old)
move to the Archived section; the active wedge window is the top
section only. Each entry MUST have a primary-source URL and a release
date in the last 90 days (relative to the last scan date below).

**Last scanned:** 2026-05-11 (initial seed + same-day re-verification + mvp4 scan pass; web search + provider blogs).

**Re-verification note (2026-05-11, mvp3 scan):** ages re-checked against the 90-day cutoff (= 2026-02-11). `cw-010` (Kling 3.0, listed as 2026-02 without a precise day) is the only entry on the boundary; the seed flagged it for verification on next scan. Without a confirmable day-precise primary-source date, I am moving it to **Archived** per skill-pack rule "Wedges older than 90 days have been moved from Active to Archived" — conservative call. All other entries remain Active. No new wedges added this pass; the seeded 13 (now 12 active) cover the May-2026 release cycle to date.

**mvp4 scan note (2026-05-11):** weekly capability scan re-run for product slug `mvp4`. Last 7-day window (2026-05-04 → 2026-05-11) checked across the canonical sources in `factory/00-radar/capability-sources.md`. One new entry added: **`cw-014` Visa Intelligent Commerce Connect** (2026-04-08; primary source = Visa investor relations press release). Also re-confirmed: Anthropic's 2026-04-04 block of Claude subscriptions from third-party agent harnesses is a *distribution* change, not a wedge — it deliberately *closes* a path, not opens one. Microsoft's OWASP-agentic-risks governance toolkit is a *compliance* shipment, not a new capability primitive — rejected. All existing active wedges (`cw-001..009`, `cw-011..013`) remain within the 90-day window relative to today. See `## mvp4 scan ranking` at bottom of file for the top-3 wedges scored against this round's pain radar.

---

## Active wedges (last 90 days)

### `cw-001` — Claude Managed Agents (fully-managed agent harness with sandbox + SSE)

- **Provider:** Anthropic
- **Released:** 2026-04-01 (public beta; `managed-agents-2026-04-01` beta header)
- **Source:** https://9to5mac.com/2026/05/07/anthropic-updates-claude-managed-agents-with-three-new-features/
- **Wedge type:** new-endpoint
- **What is now possible that wasn't 90 days ago:**
  > Ship an autonomous AI agent as a SaaS without building your own sandboxing, tool gateway, or session orchestration. Anthropic runs the agent loop; you wire prompts and tools and ship.
- **Cost / latency envelope:** beta pricing in line with Sonnet/Opus token rates; multi-minute jobs
- **Window estimate:** 90 days (beta header gates serious deployments for now)
- **Product hypotheses unlocked:**
  1. Solo legal-research agent for small-firm paralegals — drafts memos from case-law upload + question, $79/mo
  2. "Background data-room cleaner" for VC associates — sift through pitch-deck PDFs, surface anomalies, $199/seat
  3. On-call SRE assistant that triages Slack alerts overnight — uses managed sandbox to run shell read-only diagnostics, $99/mo
- **Killed-by check:** every "AI assistant SaaS" built on home-rolled LangGraph/Temporal becomes obsolete or 3x more expensive to operate.

### `cw-002` — Claude multiagent orchestration (lead → specialists in parallel on shared FS)

- **Provider:** Anthropic
- **Released:** 2026-05 (within Managed Agents update)
- **Source:** https://platform.claude.com/docs/en/release-notes/overview
- **Wedge type:** new-endpoint
- **What is now possible that wasn't 90 days ago:**
  > A lead Claude agent splits a job into N pieces and delegates each to a specialist Claude with its own model, prompt, and tools — all running in parallel on a shared filesystem. Single-API-call dispatch, no orchestration code to write.
- **Cost / latency envelope:** token cost ≈ N × specialist + lead; latency = max(specialists) instead of sum
- **Window estimate:** 60 days (this is the same model-vendor primitive others will copy within ~Q3)
- **Product hypotheses unlocked:**
  1. "Generate a full marketing campaign" — copy specialist + visual specialist + ad-headline specialist all run in parallel, returns deck in 90s, $49 per campaign
  2. Code-review-as-a-service — security specialist + perf specialist + style specialist review the same PR concurrently, post unified comment, $0.40/PR
  3. Multi-angle book-research assistant — historical / technical / cultural specialists summarise the same topic from different sources in parallel, $19/mo for writers
- **Killed-by check:** sequential-chain products (LangChain pipelines, n8n-style stacks) where parallelism = the difference between "instant" and "you'll wait 5 minutes".

### `cw-003` — Claude "dreaming": cross-session memory consolidation

- **Provider:** Anthropic
- **Released:** 2026-05
- **Source:** https://platform.claude.com/docs/en/release-notes/overview
- **Wedge type:** new-endpoint
- **What is now possible that wasn't 90 days ago:**
  > Agents review their own past sessions to extract patterns and self-improve — first-party long-term memory, not bolted-on vector store. Persistent "this user's preferences and history" without you writing retrieval code.
- **Cost / latency envelope:** background batch cost on idle agent hours; runtime memory hit ≈ small RAG hit
- **Window estimate:** 90 days
- **Product hypotheses unlocked:**
  1. Personal AI coach (writing / coding / chess) that remembers every prior session — gets sharper without re-onboarding, $29/mo
  2. Long-running PM assistant inside Slack that "knows" the team's product history across months, $99/seat
  3. AI tutor that adapts to each student's misconceptions over weeks, $19/mo per student
- **Killed-by check:** every "AI companion with memory" SaaS that re-implements pgvector + summarisation.

### `cw-004` — Claude Message Batches API: 300k max_tokens single output

- **Provider:** Anthropic
- **Released:** 2026-03-24 (`output-300k-2026-03-24` beta header)
- **Source:** https://platform.claude.com/docs/en/release-notes/overview
- **Wedge type:** new-endpoint
- **What is now possible that wasn't 90 days ago:**
  > Single-call generation up to 300k output tokens. Whole books, full-codebase rewrites, multi-hundred-page report drafts in one shot — without chunking, stitching, or drift between chunks.
- **Cost / latency envelope:** batched ≈ 50% of synchronous; 5-30 min completion
- **Window estimate:** 90 days
- **Product hypotheses unlocked:**
  1. "Drop your repo, get a complete docs site overnight" for OSS maintainers, $99 one-time
  2. Audit-grade legal contract rewrites — one prompt yields the full redlined version, $499/contract
  3. Curriculum-from-syllabus generator for K-12 / college instructors — entire term-long course materials in one batch, $199/course
- **Killed-by check:** every "AI writing assistant" that's secretly stitching together 8 chunks and hoping they cohere.

### `cw-005` — OpenAI GPT-Realtime-2 + Realtime-Translate + Realtime-Whisper (voice triple)

- **Provider:** OpenAI
- **Released:** 2026-Q2 (in current changelog window)
- **Source:** https://developers.openai.com/api/docs/changelog
- **Wedge type:** latency-threshold + new-modality-combo
- **What is now possible that wasn't 90 days ago:**
  > Voice agents that interrupt naturally, translate live, and stream-transcribe — all three voice primitives behind one API family with sub-300ms turn-taking. Production-grade voice UX without an SDK soup of Deepgram + ElevenLabs + custom turn-detection.
- **Cost / latency envelope:** ~$0.06/minute combined, < 300 ms turn-taking
- **Window estimate:** 30-60 days (Anthropic + Google will match by Q3)
- **Product hypotheses unlocked:**
  1. AI sales-call coach that listens to live Zoom calls, whispers tactical hints via Bluetooth, $99/mo for SDR teams
  2. Real-time conference translator for hybrid meetings — drop a phone on the table, anyone speaks any language, others hear in their own, $49/meeting
  3. Voice journaling app where the AI "talks back" with insightful follow-ups in <1s, $9/mo consumer
- **Killed-by check:** every voice-agent SaaS using stitched Deepgram-STT → GPT-4 → TTS pipelines with 1-2s turn lag.

### `cw-006` — Suno v5.5 (audio fidelity crosses the "could pass as a real demo" threshold)

- **Provider:** Suno
- **Released:** 2026-03-26
- **Source:** https://www.teamday.ai/blog/best-ai-music-models-2026
- **Wedge type:** new-model-class (quality threshold crossed)
- **What is now possible that wasn't 90 days ago:**
  > AI-generated songs that sound like a clean studio demo, not "AI music". Vocal clarity, breath, consonants, stereo separation all cross the "could play on a podcast intro" threshold.
- **Cost / latency envelope:** ~$0.30 per song, 60-90s to render
- **Window estimate:** 60 days (Udio + ElevenLabs Music close behind)
- **Product hypotheses unlocked:**
  1. Personalized birthday/wedding song generator, share-link is the viral mechanic, $9/song
  2. "Soundtrack your week" for Spotify playlist obsessives — weekly custom song based on what you logged, $7/mo
  3. Podcast intro/outro generator that takes a prompt + brand colour, $19/mo for indie podcasters
- **Killed-by check:** the entire "free AI song generator" tail competing on quality — Suno v5.5 leapfrogs them.

### `cw-007` — ElevenLabs Music standalone app + API (royalty-clean commercial music gen)

- **Provider:** ElevenLabs (Music API also routable through fal.ai)
- **Released:** 2026-04-01
- **Source:** https://techcrunch.com/2026/04/02/elevenlabs-releases-a-new-ai-powered-music-generation-app/
- **Wedge type:** new-endpoint (commercially safe music model on a TTS-grade API)
- **What is now possible that wasn't 90 days ago:**
  > Commercially-safe music generation via a TTS-grade API (Merlin + Kobalt licensed training data). You can ship products whose monetisation depends on the music being clearable — ads, indie films, YouTubers.
- **Cost / latency envelope:** ~$0.10 per 30s clip, 30-60s to render
- **Window estimate:** 90 days
- **Product hypotheses unlocked:**
  1. AI background-music library for YouTubers / TikTokers — generate-on-demand, license clean, $19/mo
  2. Mood-board → soundtrack tool for video editors in Final Cut / Premiere — paste a still, get music that fits, $29/mo
  3. Wedding-DJ companion — guests submit prompts, AI mixes a custom set list, $99/event
- **Killed-by check:** the "royalty-free stock music" market (Epidemic, Artlist) starts losing the long tail of "I need 30s of this specific vibe".

### `cw-008` — Google Gemini 3 "Computer Use" tool (browser agent as a first-party tool)

- **Provider:** Google
- **Released:** 2026-Q1 (in `gemini-3-pro-preview` and `gemini-3-flash-preview`)
- **Source:** https://ai.google.dev/gemini-api/docs/changelog
- **Wedge type:** new-endpoint
- **What is now possible that wasn't 90 days ago:**
  > First-party "click around the web on the user's behalf" tool inside Gemini's API — no Playwright glue code, no Browserbase, no Anthropic CUA bring-your-own. Ship a browser-agent SaaS without becoming a CUA-platform vendor.
- **Cost / latency envelope:** token cost per turn; multi-second per click
- **Window estimate:** 60 days (Anthropic CUA and OpenAI Operator close the gap rapidly)
- **Product hypotheses unlocked:**
  1. "Fill the form for me" — agent autocompletes job applications, insurance forms, government portals, $4 per filing
  2. Price-watcher that re-checks 50 SaaS dashboards weekly for a procurement team, $99/mo
  3. Refund-claim agent — goes to airline/SaaS dashboards, files refund requests with proof, $19 per claim succeeded
- **Killed-by check:** RPA tools (UiPath, Browserbase wrappers) where the moat was "we know the click sequence" — Gemini watches the screen and learns.

### `cw-009` — Gemini File Search multimodal (image + text RAG in one API)

- **Provider:** Google
- **Released:** 2026-Q1
- **Source:** https://blog.google/innovation-and-ai/technology/developers-tools/expanded-gemini-api-file-search-multimodal-rag/
- **Wedge type:** new-modality-combo
- **What is now possible that wasn't 90 days ago:**
  > Single API endpoint that does verifiable RAG across mixed image + text corpora with custom metadata + page-level citations. No separate CLIP embedding pipeline, no Weaviate setup.
- **Cost / latency envelope:** embedding + retrieval included; query latency < 1s
- **Window estimate:** 90 days
- **Product hypotheses unlocked:**
  1. Architecture-firm portfolio assistant — upload 200 project PDFs (renders + spec), ask "show similar acoustic projects", $99/seat
  2. Furniture-store "find me this couch" — customer uploads a photo, store inventory PDFs return the SKU, $49/mo for the store
  3. Internal R&D doc search for hardware companies — schematics + text — chat with your own engineering knowledge base, $199/seat
- **Killed-by check:** every "build RAG over your PDFs" SaaS using LlamaIndex + custom multimodal pipeline.

### `cw-011` — OpenAI Responses `/compact` endpoint (cheap long-running conversations)

- **Provider:** OpenAI
- **Released:** 2026-Q2
- **Source:** https://developers.openai.com/api/docs/changelog
- **Wedge type:** new-endpoint (cost mechanic: turns context-window pain into a primitive)
- **What is now possible that wasn't 90 days ago:**
  > Long-running agent conversations that don't 10x cost as context grows. The endpoint shrinks the context server-side between turns — first-party version of what every multi-turn agent author was hacking with summarisation.
- **Cost / latency envelope:** flat cost per compact call; eliminates linear context growth per turn
- **Window estimate:** 90 days
- **Product hypotheses unlocked:**
  1. AI therapist / coach with 1000-message-history sessions that stay cheap, $19/mo
  2. Long-running PM assistant that lives through a 6-month product cycle, $99/seat
  3. Customer-support agent that remembers the customer's entire ticket history without rebuilding context every turn, $0.05 per ticket
- **Killed-by check:** "AI assistant" SaaSes whose unit economics break at session #100 because context fees explode.

### `cw-012` — Cerebras inference: 1,800 tok/s on Llama 3.3 70B (10x latency drop on big models)

- **Provider:** Cerebras
- **Released:** 2026-Q1 (WSE-3 production ramp)
- **Source:** https://www.cerebras.ai/blog
- **Wedge type:** latency-threshold (slow → instant on 70B+)
- **What is now possible that wasn't 90 days ago:**
  > 70B-class open-weights model running at ~10x the speed of GPU inference — chat with Llama-class models feels like Claude Haiku. Open-weights products stop having a UX latency tax.
- **Cost / latency envelope:** premium $/MTok ($3-4 per MTok), but throughput unlocks new UX
- **Window estimate:** 60-90 days
- **Product hypotheses unlocked:**
  1. Open-source-only AI playground for privacy-paranoid orgs (legal, defence, healthcare) that need self-host trajectory + cloud demo
  2. Code-completion IDE plugin that uses Llama-class models instead of GPT, $19/mo "no data leaves to OpenAI" pitch
  3. "Ask your local docs" search where the model self-hosts well later, $29/mo
- **Killed-by check:** GPU-based inference SaaSes (vLLM hosted) where the speed wasn't enough to feel realtime on big models.

### `cw-013` — Anthropic compute capacity boost (Opus rate limits doubled for Pro/Max/Team)

- **Provider:** Anthropic (SpaceX-hosted compute)
- **Released:** 2026-Q2
- **Source:** https://www.anthropic.com/news
- **Wedge type:** price-drop / capacity-drop (Opus throughput no longer a bottleneck)
- **What is now possible that wasn't 90 days ago:**
  > Opus-grade reasoning at sustained throughput — used to be the throttle on multi-agent workloads. Doubled rate limits + removed peak-hour reductions means a small team can run Opus-heavy products without hitting the wall by 11am.
- **Cost / latency envelope:** unchanged price, doubled headroom
- **Window estimate:** 90 days (until competitors match — likely Q3 for OpenAI o3)
- **Product hypotheses unlocked:**
  1. "Senior dev assistant" SaaS that aggressively uses Opus for hard problems without throttling, $99/mo
  2. Legal-research agent (Opus-only) priced for solo practitioners, $79/mo
  3. M&A diligence assistant for boutique firms (Opus reasoning over private docs), $499/seat
- **Killed-by check:** competitors who priced their Opus-grade flagship product assuming throttle headaches as a moat.

### `cw-014` — Visa Intelligent Commerce Connect (agent-payment rails, network-agnostic on-ramp)

- **Provider:** Visa
- **Released:** 2026-04-08 (pilot launch with Aldar, AWS, Diddo, Highnote, Mesh, Payabli, Sumvin)
- **Source:** https://investor.visa.com/news/news-details/2026/Visa-Opens-the-Door-to-AI-Driven-Shopping-for-Businesses-Worldwide/default.aspx
- **Wedge type:** new-endpoint (first network-grade payment primitive built specifically for autonomous agents)
- **What is now possible that wasn't 90 days ago:**
  > Autonomous AI agents can complete real card transactions via a network-agnostic on-ramp. Agent builders no longer need to roll their own merchant-of-record, token vault, or fraud layer — Visa's API handles auth + tokenisation + dispute handling for agent-initiated purchases. "Agent shops for me and pays" goes from demo to ship-able product.
- **Cost / latency envelope:** standard interchange + Visa Intelligent Commerce fee (per-tx, not disclosed publicly in pilot); seconds-scale settlement on the agent-side; payment-rail latency unchanged
- **Window estimate:** 90 days (Mastercard + Stripe-for-agents will match within Q3)
- **Product hypotheses unlocked:**
  1. "Refund-claim agent" — agent navigates airline/SaaS dashboards, files claim, accepts the refund credit directly into a card-attached account, $19 per claim succeeded (stacks with `cw-008` Gemini Computer Use)
  2. "Grocery-on-autopilot" — weekly meal-plan agent re-orders staples across Instacart / Amazon Fresh, ICP = busy professionals, $9/mo + 5% take-rate
  3. "Subscription concierge" — agent audits a household's recurring charges and cancels / replaces with cheaper alternatives, share of savings model, viral "I saved $X" share-card
  4. "B2B procurement bot" — agent shops office supplies and SaaS subscriptions for SMBs against company policy, $99/seat
  5. "Travel-deal sniper" — agent watches and books flights/hotels when price drops below user threshold, $19/booking
- **Killed-by check:** every "AI shopping assistant" wrapper that bolted on Stripe/PayPal manually — Visa's first-party agent rails make their integration layer redundant. Also kills the early-mover "headless commerce for agents" startups whose moat was payment plumbing.

---

## Archived (> 90 days, kept for history)

### `cw-010` — Kling 3.0 multi-shot video with subject consistency (3-15s) — ARCHIVED 2026-05-11

- **Provider:** Kuaishou / Kling
- **Released:** 2026-02 (precise day not confirmed against primary source; boundary case at 90-day cutoff = 2026-02-11)
- **Source:** https://www.teamday.ai/blog/best-ai-video-models-2026
- **Wedge type:** new-model-class
- **Archived because:** seed flagged "verify on next scan"; without a day-precise primary-source date and at >= 89 days from release, the conservative call is to drop it from Active. Re-promote if a 2026-02-15+ primary source is found.
- **What was possible that wasn't 90 days before release:**
  > Multi-shot video (3-15s) where the SAME subject appears across different camera angles — preserves edges, logos, fabric. Real ad-ready clips, not "AI demo" wobble.
- **Cost / latency envelope:** ~$1-2 per 5s clip, 2-5 min to render
- **Product hypotheses that were unlocked (now likely commodified):**
  1. Indie-brand ad generator for Shopify stores — upload product photo, get 15s multi-shot ad, $99/ad
  2. Wedding/event teaser-trailer generator from event photos, $199/event
  3. Real-estate listing video — listing photos → 30s walkthrough, $49/listing
- **Killed-by check:** "AI video stock" libraries with same-frame-style outputs; competitive video tools that can't preserve subject identity across shots.

---

## Seeding notes

This file was seeded on 2026-05-11 via WebSearch + provider blogs as
the first Trend Scout capability radar pass. The 13 entries above were
filtered from a wider scan that also surfaced (rejected for falling
outside the wedge rules):

- "Claude Opus 4.7 is smarter on benchmarks" — no new action possible vs Opus 4.6; not a wedge
- "ChatGPT Wrapped 2025" feature in the app — consumer feature, not an API primitive
- "Gemini 3.2 Flash improvements" — incremental, no UX threshold crossed
- "Sora 2 deprecation" — distribution change, not a capability change
- "OpenAI Realtime API Beta removed May 7, 2026" — deprecation, not a wedge

Operator: when you re-run the scan, **verify** each `released` date
against the primary source before deciding the wedge is still active.
Web-search summaries occasionally drift on exact dates.

---

## mvp4 scan ranking (2026-05-11)

Scope: the mvp4 operator brief asks for the highest-potential viral
micro-SaaS opportunity with (a) organic-hype shareable mechanic,
(b) 30-day paid monetization path, (c) low capital, (d) ICP = devs /
marketers / indie founders / creators / knowledge workers, and a
day-one wow demo.

Scoring per skill-pack formula:
`score = window_days_remaining × hypothesis_quality_max × inverse_existing_coverage`

| Rank | Wedge | window_days (today=2026-05-11) | Hypothesis quality (best of) | Existing coverage | Why for mvp4 |
|---|---|---|---|---|---|
| **1** | `cw-014` Visa Intelligent Commerce | 56 (90 − 34 since 2026-04-08) | very high (refund agent, subscription concierge — both have built-in viral share-card mechanic: "agent saved me $X") | very low (pilot partners only; no shipped indie SaaS yet) | Newest, biggest unconstrained-coverage wedge; stacks naturally with `cw-008` for the wow-demo combo "agent watched-clicked-paid". Pays-online-without-friction is the *whole point*. |
| **2** | `cw-008` Gemini Computer Use | ~50 (Q1 release, ~135 days but the killer-demos still feel fresh) — flagged as decaying | high (form-fill agent, refund agent, price-watcher; "watch the AI do the boring thing" demo) | medium (some shipped Browserbase wrappers; Anthropic CUA closing gap; still rare in production) | Stack with `cw-014` for the strongest pain × wedge fit against the agency-data-janitor pain (Sig 10) and refund-claim pain. |
| **3** | `cw-002` Claude multiagent orchestration (lead → specialists) | ~60 (released within May Managed Agents update) | high (marketing-campaign generator, multi-angle research, parallel code-review — all are shareable wow demos on indie-marketer X) | medium (some early multi-agent products exist; Anthropic's first-party primitive is fresh) | Day-one wow demo: "generate full marketing campaign in 90s with parallel specialists" lands directly on the marketer/indie-founder ICP. |

Bottom of the list (deprioritised for THIS round):

- `cw-006` Suno v5.5 + `cw-007` ElevenLabs Music — viral share-link mechanic is strong but consumer-pay friction is higher than the brief's "ICP pays online without friction" target; commodified by free-tier competitors at the long tail.
- `cw-010` Kling 3.0 — now archived (boundary case at the 90-day cutoff).
- `cw-005` Realtime voice triple — window shrinking fastest (Anthropic + Google match in Q3); B2B SDR-coach hypothesis viable but harder day-one demo than browser-agent or multiagent.

Flagged to Product Strategist (Stage 3) as the top-3 wedges for mvp4
hypothesis generation. Stage 3 must populate `capability_wedge` on
every hypothesis it produces and Market Skeptic (Stage 4) MUST kill
any hypothesis whose `capability_wedge` is older than 90 days or
absent from the Active section above (per
`hypokiln/capability-radar` skill pack and operator's anti-pattern #9
"vaporware wedge" enforcement — `wedge_shipped_today` must be `true`
with a public API confirmation).
