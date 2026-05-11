"use client";

import { useState } from "react";

import { API_BASE } from "@/lib/api";

type Hit = { slug: string; file: string; line: number; snippet: string };

export default function SearchPage() {
  const [q, setQ] = useState("");
  const [hits, setHits] = useState<Hit[]>([]);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  async function go(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setErr(null);
    try {
      const r = await fetch(
        `${API_BASE}/api/search?q=${encodeURIComponent(q)}`,
        { cache: "no-store" },
      );
      if (!r.ok) throw new Error(await r.text());
      const data = await r.json();
      setHits(data.hits || []);
    } catch (e) {
      setErr(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="editorial-shell space-y-6">
      <header>
        <h1 className="font-display text-headline text-ink">Search</h1>
        <p className="text-charcoal mt-2">
          Grep every active idea's prompt, research, spec, and per-stage logs.
        </p>
      </header>
      <form onSubmit={go} className="flex gap-2">
        <input
          autoFocus
          value={q}
          onChange={(e) => setQ(e.target.value)}
          placeholder="search across runs…"
          className="flex-1 border border-mist rounded-md p-2 bg-paper text-ink"
        />
        <button
          disabled={busy || !q.trim()}
          className="bg-ink text-paper px-4 py-2 rounded-md hover:bg-amber transition-colors disabled:opacity-50"
        >
          {busy ? "Searching…" : "Search"}
        </button>
      </form>
      {err && <div className="text-danger text-supporting">{err}</div>}
      <ul className="space-y-2">
        {hits.map((h, i) => (
          <li key={i} className="border border-mist rounded-md p-3">
            <div className="flex items-baseline justify-between text-supporting">
              <a
                href={`/runs/${h.slug}`}
                className="font-mono text-charcoal hover:text-amber"
              >
                {h.slug}
              </a>
              <span className="text-ash">
                {h.file}
                {h.line > 0 && `:${h.line}`}
              </span>
            </div>
            <div className="mt-1 font-mono text-supporting text-ink">
              {h.snippet}
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}
