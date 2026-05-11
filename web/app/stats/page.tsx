import { API_BASE } from "@/lib/api";

export const dynamic = "force-dynamic";

type PerStage = {
  n: number;
  name: string;
  delegate: string;
  runs: number;
  failures: number;
  mean_seconds: number | null;
  median_seconds: number | null;
  max_seconds: number | null;
};

type StatsResp = {
  total_runs: number;
  completed_runs: number;
  failed_runs: number;
  success_rate: number | null;
  per_stage: PerStage[];
};

async function loadStats(): Promise<StatsResp | null> {
  try {
    const r = await fetch(`${API_BASE}/api/stats`, { cache: "no-store" });
    if (!r.ok) return null;
    return await r.json();
  } catch {
    return null;
  }
}

function fmtSec(s: number | null): string {
  if (s === null) return "—";
  if (s < 60) return `${s.toFixed(0)}s`;
  if (s < 3600) return `${(s / 60).toFixed(1)}m`;
  return `${(s / 3600).toFixed(1)}h`;
}

export default async function StatsPage() {
  const data = await loadStats();
  if (!data) {
    return (
      <div className="editorial-shell">
        <h1 className="font-display text-headline text-ink">Stats</h1>
        <p className="text-charcoal mt-2">No data yet.</p>
      </div>
    );
  }
  return (
    <div className="editorial-shell space-y-8">
      <header>
        <h1 className="font-display text-headline text-ink">Stats</h1>
        <p className="text-charcoal mt-2">Cross-run telemetry.</p>
      </header>

      <section className="grid grid-cols-3 gap-4">
        <Stat label="Total runs" value={data.total_runs.toString()} />
        <Stat label="Completed" value={data.completed_runs.toString()} />
        <Stat
          label="Success rate"
          value={
            data.success_rate === null
              ? "—"
              : `${(data.success_rate * 100).toFixed(0)}%`
          }
        />
      </section>

      <section>
        <h2 className="font-display text-title text-ink mb-3">Per stage</h2>
        <table className="w-full text-supporting">
          <thead>
            <tr className="text-micro-label uppercase text-ash">
              <th className="text-left p-2">#</th>
              <th className="text-left p-2">Stage</th>
              <th className="text-left p-2">Runs</th>
              <th className="text-left p-2">Failures</th>
              <th className="text-left p-2">Median</th>
              <th className="text-left p-2">Max</th>
            </tr>
          </thead>
          <tbody>
            {data.per_stage.map((s) => (
              <tr key={s.n} className="border-t border-mist">
                <td className="p-2 font-mono">{s.n}</td>
                <td className="p-2 text-ink">{s.name}</td>
                <td className="p-2">{s.runs}</td>
                <td className="p-2">
                  {s.failures > 0 ? (
                    <span className="text-danger">{s.failures}</span>
                  ) : (
                    "0"
                  )}
                </td>
                <td className="p-2">{fmtSec(s.median_seconds)}</td>
                <td className="p-2">{fmtSec(s.max_seconds)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </div>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="border border-mist rounded-md p-4 bg-paper">
      <div className="text-micro-label uppercase text-ash">{label}</div>
      <div className="font-display text-headline text-ink mt-1">{value}</div>
    </div>
  );
}
