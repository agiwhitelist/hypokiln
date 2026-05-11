# HypoKiln brand notes

## Concept
HypoKiln = **hypothesis kiln**. The pipeline takes raw signals from the AI capability frontier (last 90 days of provider releases), bakes them into product hypotheses, then fires the weak ones in a high-temperature kiln (Market Skeptic critic loop + deterministic kill filter). Top-3 survive to the human gate.

Two readings, both load-bearing:
1. **Kiln as forge** — high heat shapes brittle material into something usable.
2. **Kill filter** — the Market Skeptic stage that murders ideas with no defensible wedge.

## Color palette (OKLCH)

| Token             | Value                       | Use                                       |
|-------------------|-----------------------------|-------------------------------------------|
| `--paper`         | `oklch(96% 0.02 80)`        | Page background — warm cream              |
| `--paper-darker`  | `oklch(92% 0.025 80)`       | Cards, table headers                      |
| `--ink`           | `oklch(20% 0.02 40)`        | Body text, kiln dome                      |
| `--ink-muted`     | `oklch(40% 0.02 40)`        | Secondary copy, taglines                  |
| `--amber`         | `oklch(60% 0.18 50)`        | Primary accent — kiln flame, links, CTAs |
| `--amber-bright`  | `oklch(70% 0.22 55)`        | Hover, active flame                       |
| `--amber-pale`    | `oklch(88% 0.18 80)`        | Flame highlight, soft badges              |
| `--success`       | `oklch(55% 0.15 145)`       | PASS gate badges                          |
| `--danger`        | `oklch(55% 0.18 25)`        | FAIL gate badges, kill-filter rejects     |

## Dark mode
Flip via `data-theme="dark"` — same hues, inverted lightness. Amber holds; paper becomes ink, ink becomes paper.

| Token             | Dark value                  |
|-------------------|-----------------------------|
| `--paper`         | `oklch(18% 0.02 40)`        |
| `--paper-darker`  | `oklch(22% 0.02 40)`        |
| `--ink`           | `oklch(94% 0.02 80)`        |
| `--ink-muted`     | `oklch(72% 0.02 80)`        |

## Typography

| Role     | Family                     | Notes                              |
|----------|----------------------------|------------------------------------|
| Display  | Cormorant Garamond, serif | Italic for the wordmark            |
| Body     | Instrument Sans, sans      | UI labels, copy                    |
| Mono     | Space Grotesk, JetBrains   | CLI snippets, IDs, slugs           |

## Logo
- `docs/logo.svg` — full lockup with wordmark (480×120)
- `docs/logo-mark.svg` — square mark only (96×96)
- `docs/favicon.svg` — 32×32 favicon

## Voice
Editorial, not corporate. Confident, slightly skeptical (because Market Skeptic is built in). Short sentences. The pipeline murders bad ideas; the docs shouldn't apologize for that.
