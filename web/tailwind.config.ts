import type { Config } from "tailwindcss";

/**
 * HypoKiln design tokens — editorial warm-paper layer with an amber accent
 * (the kiln's flame), inspired by impeccable.design's typography rules.
 *
 *   Accent: oklch(60% 0.18 50)  — kiln flame amber
 *   Display: Cormorant Garamond (serif)
 *   Body: Instrument Sans
 *   Mono: Space Grotesk
 */
const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        paper: "var(--paper)",
        cream: "var(--bg)",
        mist: "var(--mist)",
        ink: "var(--ink)",
        charcoal: "var(--charcoal)",
        ash: "var(--ash)",
        ash2: "oklch(70% 0 0)",
        // accent — kiln amber
        amber: "oklch(60% 0.18 50)",
        "amber-bright": "oklch(70% 0.22 55)",
        "amber-pale": "oklch(88% 0.18 80)",
        "amber-whisper": "oklch(60% 0.18 50 / 0.15)",
        "amber-veil": "oklch(60% 0.18 50 / 0.25)",
        // semantic
        success: "oklch(55% 0.15 145)",
        warning: "oklch(72% 0.18 70)",
        danger: "oklch(55% 0.18 25)",
      },
      fontFamily: {
        display: ["Cormorant Garamond", "Georgia", "ui-serif", "serif"],
        body: [
          "Instrument Sans",
          "ui-sans-serif",
          "system-ui",
          "-apple-system",
          "sans-serif",
        ],
        mono: ["Space Grotesk", "JetBrains Mono", "ui-monospace", "monospace"],
      },
      fontSize: {
        display: [
          "clamp(2.5rem, 7vw, 4.5rem)",
          { lineHeight: "1", fontWeight: "300" },
        ],
        headline: [
          "clamp(1.75rem, 4vw, 2.5rem)",
          { lineHeight: "1.2", fontWeight: "400" },
        ],
        title: [
          "clamp(1.125rem, 2.5vw, 1.5rem)",
          { lineHeight: "1.3", fontWeight: "400" },
        ],
        "body-lead": ["1.0625rem", { lineHeight: "1.65" }],
        supporting: ["0.875rem", { lineHeight: "1.6" }],
        "micro-label": [
          "0.6875rem",
          { lineHeight: "1.4", letterSpacing: "0.1em", fontWeight: "500" },
        ],
      },
      spacing: {
        "2xs": "4px",
        "3xl": "120px",
      },
      borderRadius: {
        sm: "4px",
        md: "8px",
        lg: "12px",
        xl: "16px",
      },
      transitionTimingFunction: {
        "out-quint": "cubic-bezier(0.22, 1, 0.36, 1)",
        editorial: "cubic-bezier(0.16, 1, 0.3, 1)",
      },
      maxWidth: {
        editorial: "1100px",
      },
    },
  },
  plugins: [],
};

export default config;
