# Capability wedges — radar output

Append-only log, newest first. One entry per provider release that
satisfies the "what counts as a wedge" rules in
`factory/00-radar/capability-sources.md`. Stale entries (> 90 days old)
are kept for history; the active wedge window is the top section only.

Each entry MUST have a source URL and a release date in the last 90 days.

---

## Active wedges (last 90 days)

### `cw-NNN` — `<one-line capability summary>`

- **Provider:** `<Anthropic | OpenAI | Google | fal.ai | …>`
- **Released:** `<YYYY-MM-DD>`
- **Source:** `<primary URL — release note, blog post, docs>`
- **Wedge type:** `new-endpoint | new-model-class | price-drop-10x | latency-threshold | new-modality-combo`
- **What is now possible that wasn't 90 days ago:**
  > `<plain-English sentence, no jargon. e.g. "Real-time voice agent that interrupts naturally for <$0.10/minute.">`
- **Cost / latency envelope:** `<$/request, $/minute, ms latency>`
- **Window estimate:** `<30 | 60 | 90 days>` until 5+ competitors ship the obvious wrapper
- **Product hypotheses unlocked (3-5):**
  1. `<for whom> + <jobs-to-be-done> + <wedge of THIS capability>`
  2. ...
  3. ...
- **Killed-by check:** which existing product class becomes obsolete or 10x worse?

---

## Archived (> 90 days, kept for history)

(move entries here once they age out)
