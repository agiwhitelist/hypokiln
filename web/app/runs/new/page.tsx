"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

import { API_BASE } from "@/lib/api";

export default function NewRunPage() {
  const router = useRouter();
  const [prompt, setPrompt] = useState("");
  const [yolo, setYolo] = useState(true);
  const [cliBin, setCliBin] = useState<"codex" | "claude" | "gemini">("codex");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setBusy(true);
    try {
      const res = await fetch(`${API_BASE}/api/runs`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ prompt, yolo, cli_bin: cliBin }),
      });
      if (!res.ok) {
        throw new Error(await res.text());
      }
      const data = (await res.json()) as { slug: string };
      router.push(`/runs/${data.slug}`);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
      setBusy(false);
    }
  }

  return (
    <div className="editorial-shell max-w-3xl space-y-8">
      <header>
        <p className="text-micro-label uppercase text-amber">New idea</p>
        <h1 className="font-display text-headline text-ink mt-2">
          Light the kiln
        </h1>
        <p className="text-charcoal text-body-lead mt-3">
          One paragraph. Pricing, audience, and the rough capability angle if
          you have one. The Trend Scout will start by scanning fresh AI wedges
          from the last 90 days against your prompt.
        </p>
      </header>

      <form onSubmit={submit} className="space-y-6">
        <div>
          <label
            htmlFor="prompt"
            className="block text-micro-label uppercase text-charcoal mb-2"
          >
            Idea prompt
          </label>
          <textarea
            id="prompt"
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            rows={6}
            required
            minLength={12}
            placeholder='Example: "Build me a $9/mo Slack-bot for solo founders that scans their Stripe + GitHub once a day and posts a one-line burn / runway / shipped-features tally."'
            className="w-full border border-mist rounded-md p-4 bg-paper text-ink font-body focus:border-amber focus:outline-none"
          />
          <p className="text-micro-label text-ash mt-1">
            Include price (e.g. $9/mo), audience, and the wedge angle if you
            already see one. Vague prompts get vague hypotheses.
          </p>
        </div>

        <div className="grid grid-cols-2 gap-6">
          <div>
            <label className="block text-micro-label uppercase text-charcoal mb-2">
              Coding CLI
            </label>
            <select
              value={cliBin}
              onChange={(e) =>
                setCliBin(e.target.value as "codex" | "claude" | "gemini")
              }
              className="w-full border border-mist rounded-md p-3 bg-paper text-ink"
            >
              <option value="codex">codex (ChatGPT Plus / Pro)</option>
              <option value="claude">claude (Claude.ai Pro)</option>
              <option value="gemini">gemini (Google AI Studio)</option>
            </select>
          </div>
          <div>
            <label className="block text-micro-label uppercase text-charcoal mb-2">
              G1 auto-sign
            </label>
            <label className="flex items-center gap-2 border border-mist rounded-md p-3 bg-paper cursor-pointer">
              <input
                type="checkbox"
                checked={yolo}
                onChange={(e) => setYolo(e.target.checked)}
              />
              <span className="text-ink text-supporting">
                Auto-sign G1 if pre-flight clears (≤2 alarms)
              </span>
            </label>
          </div>
        </div>

        {error && (
          <div className="border border-danger/30 bg-danger/10 text-danger p-3 rounded-md text-supporting whitespace-pre-wrap">
            {error}
          </div>
        )}

        <div className="flex items-center gap-3">
          <button
            type="submit"
            disabled={busy || prompt.trim().length < 12}
            className="bg-ink text-paper px-5 py-2.5 rounded-md hover:bg-amber transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {busy ? "Lighting…" : "Light the kiln"}
          </button>
          <a
            href="/"
            className="text-charcoal hover:text-amber transition-colors text-supporting"
          >
            Back to ideas
          </a>
        </div>
      </form>
    </div>
  );
}
