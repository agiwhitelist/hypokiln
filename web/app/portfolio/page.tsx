import { API_BASE } from "@/lib/api";

export const dynamic = "force-dynamic";

type PortfolioStage = {
  n: number;
  status: string;
  started_at: string | null;
  completed_at: string | null;
};

type PortfolioRow = {
  slug: string;
  prompt: string;
  created_at: string;
  updated_at: string;
  autonomous: boolean;
  stages: PortfolioStage[];
};

async function loadPortfolio(): Promise<PortfolioRow[]> {
  try {
    const res = await fetch(`${API_BASE}/api/portfolio`, {
      cache: "no-store",
    });
    if (!res.ok) return [];
    const data = await res.json();
    return data.rows as PortfolioRow[];
  } catch {
    return [];
  }
}

const STATUS_TINT: Record<string, string> = {
  completed: "bg-amber",
  in_progress: "bg-amber-pale",
  pending: "bg-mist",
  failed: "bg-danger",
  skipped: "bg-ash/40",
};

export default async function PortfolioPage() {
  const rows = await loadPortfolio();
  return (
    <div className="editorial-shell space-y-6">
      <header>
        <h1 className="font-display text-headline text-ink">Portfolio</h1>
        <p className="text-charcoal mt-2">
          Every idea on a single timeline, one row per slug. Spot which is
          racing through and which is stuck on a long stage.
        </p>
      </header>
      {rows.length === 0 ? (
        <div className="border border-dashed border-mist rounded-md p-8 text-center text-charcoal">
          No runs yet.
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-supporting">
            <thead>
              <tr className="text-micro-label uppercase text-ash">
                <th className="text-left p-2">Slug</th>
                <th className="text-left p-2">Stage 1</th>
                <th className="text-left p-2">2</th>
                <th className="text-left p-2">3</th>
                <th className="text-left p-2">4</th>
                <th className="text-left p-2">5</th>
                <th className="text-left p-2">6</th>
                <th className="text-left p-2">Updated</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((r) => (
                <tr key={r.slug} className="border-t border-mist">
                  <td className="p-2 font-mono">
                    <a href={`/runs/${r.slug}`} className="hover:text-amber">
                      {r.slug}
                    </a>
                  </td>
                  {r.stages.map((s) => (
                    <td key={s.n} className="p-2">
                      <span
                        title={s.status}
                        className={`inline-block w-6 h-3 rounded-sm ${STATUS_TINT[s.status] ?? "bg-mist"}`}
                      />
                    </td>
                  ))}
                  <td className="p-2 text-ash">
                    {new Date(r.updated_at).toLocaleString()}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
