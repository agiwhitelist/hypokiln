import { api, type WedgesResp } from "@/lib/api";

export const dynamic = "force-dynamic";

async function loadWedges(): Promise<WedgesResp | null> {
  try {
    return await api<WedgesResp>("/api/wedges");
  } catch {
    return null;
  }
}

export default async function WedgesPage() {
  const data = await loadWedges();
  if (!data) {
    return (
      <div className="editorial-shell">
        <h1 className="font-display text-headline text-ink mb-3">Capability wedges</h1>
        <p className="text-charcoal">
          No <code className="font-mono">factory/00-radar/capability-wedges.md</code> yet —
          run <code className="font-mono">kiln capability-scan</code> after Stage 1 to seed it.
        </p>
      </div>
    );
  }
  return (
    <div className="editorial-shell space-y-10">
      <header>
        <p className="text-micro-label uppercase text-amber">The kiln's fuel</p>
        <h1 className="font-display text-headline text-ink mt-2">Capability wedges</h1>
        <p className="text-body-lead text-charcoal mt-3 max-w-2xl">
          Every active hypothesis the kiln generates must be anchored on one of these.
          Wedges older than 90 days fall out automatically — the wedge is the unfair
          advantage that incumbents cannot match for the time the window stays open.
        </p>
      </header>

      <section>
        <div className="flex items-baseline justify-between mb-4">
          <h2 className="font-display text-title text-ink">
            Active <span className="text-ash text-supporting">({data.active.length})</span>
          </h2>
          <div className="text-supporting text-charcoal">
            {Object.entries(data.by_provider).map(([p, n]) => (
              <span key={p} className="ml-3">
                <span className="text-ash">{p}</span> {n}
              </span>
            ))}
          </div>
        </div>
        <ul className="space-y-2">
          {data.active.map((w) => (
            <li
              key={w.id}
              className="border border-mist rounded-md p-3 hover:border-amber transition-colors"
            >
              <div className="flex items-baseline justify-between gap-3">
                <div className="min-w-0">
                  <span className="font-mono text-supporting text-amber">{w.id}</span>{" "}
                  <span className="text-ink">{w.title}</span>
                </div>
                <div className="text-micro-label text-ash whitespace-nowrap">
                  {w.provider} · {w.released}
                  {w.age_days !== null && (
                    <span className={w.age_days > 76 ? " text-warning" : ""}>
                      {" · "}
                      {w.age_days}d old
                    </span>
                  )}
                </div>
              </div>
            </li>
          ))}
        </ul>
      </section>

      {data.archived.length > 0 && (
        <section>
          <h2 className="font-display text-title text-ink mb-4">
            Archived <span className="text-ash text-supporting">({data.archived.length})</span>
          </h2>
          <ul className="space-y-1">
            {data.archived.map((w) => (
              <li key={w.id} className="text-supporting text-charcoal">
                <span className="font-mono text-ash">{w.id}</span> · {w.title}
                <span className="text-ash"> ({w.provider}, {w.released})</span>
              </li>
            ))}
          </ul>
        </section>
      )}

      <p className="text-micro-label text-ash">
        Source: <code className="font-mono">{data.path}</code>. Bump with{" "}
        <code className="font-mono">kiln capability-scan --archive</code>.
      </p>
    </div>
  );
}
