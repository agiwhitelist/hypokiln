# Capability radar sources

A capability wedge = a product action that became *possible* in the last
~90 days because some provider shipped a new API, model, or price drop.
Catching a wedge in its 30-90-day first-mover window is the only realistic
path to a viral product out of this factory (see
`docs/wow-factory-design.md` and the Trend Scout's Stage 1 capability scan).

Scan these weekly. Output goes to
`factory/00-radar/capability-wedges.md` (see template).

## LLM providers

- **Anthropic** — `https://www.anthropic.com/news`, `https://docs.anthropic.com/en/release-notes/api`
- **OpenAI** — `https://openai.com/news/`, `https://platform.openai.com/docs/changelog`
- **Google DeepMind / AI Studio** — `https://deepmind.google/discover/blog/`, `https://ai.google.dev/gemini-api/docs/changelog`
- **xAI** — `https://x.ai/news`
- **Mistral** — `https://mistral.ai/news/`
- **Cohere** — `https://docs.cohere.com/changelog`

## Inference platforms (price + latency + new models)

- **Groq** — `https://groq.com/blog/` (token throughput + price floor)
- **Together AI** — `https://www.together.ai/blog`
- **Replicate** — `https://replicate.com/explore` (new community models)
- **fal.ai** — `https://fal.ai/models` (image/video, sub-second turnarounds)
- **Modal** — `https://modal.com/blog` (serverless GPU)
- **Cerebras** — `https://www.cerebras.ai/blog` (huge-context inference)

## Modality providers

- **Image / video**: Runware, fal.ai, Stability, Black Forest Labs (Flux), Veo, Sora, Kling, Runway
- **Audio / music**: ElevenLabs, Cartesia, Suno, Udio, PlayHT
- **Speech-to-text**: Deepgram, AssemblyAI, OpenAI Whisper, Groq Whisper
- **Embeddings / search**: Voyage AI, Cohere Embed, Jina
- **3D**: Luma, Tripo, Meshy
- **Realtime**: OpenAI Realtime API, ElevenLabs Conversational AI, Vapi, Retell

## Platform-side openings

- **Apple** — `https://developer.apple.com/news/releases/` (new on-device APIs, Vision Pro, Foundation Models framework)
- **Google** — Android release notes, Chrome extension API, Workspace add-ons
- **Microsoft** — Copilot extensibility, Teams app platform, Windows AI APIs
- **Slack / Discord / Notion / Linear / Figma** — extension/plugin platforms
- **Browser**: Chrome / Safari / Arc extension API changes

## What counts as a "capability wedge" (vs. noise)

A wedge **MUST** be one of:

1. **New API endpoint** that does something prior endpoints couldn't (vision input, tool use, streaming, batched, long context, multi-turn audio).
2. **New model class** with capability prior models didn't have (reasoning, multimodal, real-time voice, music gen, video gen, 1M+ context).
3. **Price drop ≥ 10x** on existing capability (turns infeasible economics into feasible — Whisper-on-Groq dropped STT cost ~50x).
4. **Latency drop crossing a UX threshold** (slow → instant, > 5s → < 1s for text, > 30s → < 5s for image, > 5 min → < 30s for video).
5. **New modality combination** (audio in → image out, video in → text out, etc).

A wedge is **NOT**:

- "Model X is now smarter on benchmark Y" (no new action possible)
- "Now available in your region" (distribution, not capability)
- "Lower latency" without a UX threshold crossed
- "Better at code" without a specific new capability
- "New SDK" wrapping the same underlying API

## Anti-sources (skip)

- Generic AI news aggregators that summarise without primary URLs.
- Threads about "the future of AI" — talk not capability.
- VC newsletters speculating on which models *will* ship.
- Anything > 90 days old (the wedge window has closed).
