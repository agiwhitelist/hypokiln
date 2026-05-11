"use client";

import { useEffect, useState } from "react";

import { API_BASE } from "@/lib/api";

type Template = { name: string; prompt: string; notes: string };

export default function TemplatesPage() {
  const [items, setItems] = useState<Template[]>([]);
  const [draft, setDraft] = useState<Template>({ name: "", prompt: "", notes: "" });
  const [err, setErr] = useState<string | null>(null);

  async function load() {
    try {
      const data = await fetch(`${API_BASE}/api/templates`, {
        cache: "no-store",
      }).then((r) => r.json());
      setItems(Array.isArray(data) ? data : []);
    } catch (e) {
      setErr(e instanceof Error ? e.message : String(e));
    }
  }
  useEffect(() => {
    load();
  }, []);

  async function save() {
    setErr(null);
    try {
      const res = await fetch(
        `${API_BASE}/api/templates/${encodeURIComponent(draft.name)}`,
        {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(draft),
        },
      );
      if (!res.ok) throw new Error(await res.text());
      setDraft({ name: "", prompt: "", notes: "" });
      await load();
    } catch (e) {
      setErr(e instanceof Error ? e.message : String(e));
    }
  }

  async function remove(name: string) {
    if (!confirm(`Delete template ${name}?`)) return;
    try {
      const res = await fetch(
        `${API_BASE}/api/templates/${encodeURIComponent(name)}`,
        { method: "DELETE" },
      );
      if (!res.ok) throw new Error(await res.text());
      await load();
    } catch (e) {
      setErr(e instanceof Error ? e.message : String(e));
    }
  }

  return (
    <div className="editorial-shell space-y-8">
      <header>
        <h1 className="font-display text-headline text-ink">Templates</h1>
        <p className="text-charcoal mt-2">
          Save successful prompts as launch presets.
        </p>
      </header>

      <section>
        <h2 className="font-display text-title text-ink mb-3">New template</h2>
        <div className="space-y-2">
          <input
            placeholder="kebab-case-name"
            value={draft.name}
            onChange={(e) => setDraft({ ...draft, name: e.target.value })}
            className="w-full border border-mist rounded p-2 bg-paper text-ink"
          />
          <textarea
            rows={3}
            placeholder="prompt"
            value={draft.prompt}
            onChange={(e) => setDraft({ ...draft, prompt: e.target.value })}
            className="w-full border border-mist rounded p-2 bg-paper text-ink"
          />
          <textarea
            rows={2}
            placeholder="notes (optional)"
            value={draft.notes}
            onChange={(e) => setDraft({ ...draft, notes: e.target.value })}
            className="w-full border border-mist rounded p-2 bg-paper text-ink"
          />
          {err && <div className="text-danger text-supporting">{err}</div>}
          <button
            onClick={save}
            disabled={!draft.name || !draft.prompt}
            className="bg-ink text-paper px-4 py-2 rounded-md hover:bg-amber transition-colors disabled:opacity-50"
          >
            Save
          </button>
        </div>
      </section>

      <section>
        <h2 className="font-display text-title text-ink mb-3">Saved</h2>
        <ul className="space-y-2">
          {items.map((t) => (
            <li key={t.name} className="border border-mist rounded-md p-3">
              <div className="flex items-baseline justify-between">
                <span className="font-mono text-supporting text-charcoal">
                  {t.name}
                </span>
                <button
                  onClick={() => remove(t.name)}
                  className="text-danger text-micro-label"
                >
                  delete
                </button>
              </div>
              <p className="text-ink mt-1">{t.prompt}</p>
              {t.notes && (
                <p className="text-supporting text-charcoal mt-1">{t.notes}</p>
              )}
            </li>
          ))}
        </ul>
      </section>
    </div>
  );
}
