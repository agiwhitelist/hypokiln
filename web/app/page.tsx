import Link from "next/link";

import { api, type RunSummary } from "@/lib/api";
import { StagePill } from "@/components/stage-pill";

export const dynamic = "force-dynamic";

async function loadRuns(): Promise<RunSummary[]> {
  try {
    return await api<RunSummary[]>("/api/runs");
  } catch {
    return [];
  }
}

function fmtDate(s: string): string {
  try {
    return new Date(s).toLocaleString();
  } catch {
    return s;
  }
}

export default async function HomePage() {
  const runs = await loadRuns();
  return (
    <div className="editorial-shell space-y-12">
      <section>
        <p className="text-micro-label uppercase text-amber mb-3">
          Capability · Wedge · Ideas
        </p>
        <h1 className="text-display font-display text-ink leading-none mb-4">
          The idea kiln.
        </h1>
        <p className="text-body-lead max-w-2xl text-charcoal">
          Six stages from frontier-AI signals to a ranked top-3 of validated
          micro-SaaS hypotheses, with a built-in Market Skeptic that kills
          weak ideas before you spend a token building them. Every hypothesis
          is anchored on a capability wedge less than 90 days old —
          competitors haven't shipped against it yet.
        </p>
        <div className="mt-6 flex gap-3">
          <Link
            href="/runs/new"
            className="bg-ink text-paper px-5 py-2.5 rounded-md hover:bg-amber transition-colors"
          >
            Start a new idea
          </Link>
          <Link
            href="/wedges"
            className="border border-mist text-charcoal px-5 py-2.5 rounded-md hover:border-amber hover:text-amber transition-colors"
          >
            Browse active wedges →
          </Link>
        </div>
      </section>

      <hr className="editorial-rule" />

      <section>
        <h2 className="font-display text-title text-ink mb-6">
          Recent ideas {runs.length > 0 && <span className="text-ash text-supporting">({runs.length})</span>}
        </h2>

        {runs.length === 0 && (
          <div className="border border-dashed border-mist rounded-lg p-8 text-center">
            <p className="text-charcoal">
              No ideas yet. The kiln is cold.
            </p>
            <Link
              href="/runs/new"
              className="inline-block mt-4 text-amber hover:underline"
            >
              Light it up →
            </Link>
          </div>
        )}

        <ul className="space-y-2">
          {runs.map((r) => (
            <li key={r.slug}>
              <Link
                href={`/runs/${r.slug}`}
                className="block border border-mist rounded-md p-4 hover:border-amber hover:bg-paper transition-colors"
              >
                <div className="flex items-baseline justify-between gap-4">
                  <div className="min-w-0">
                    <div className="flex items-baseline gap-2 mb-1">
                      <span className="font-mono text-supporting text-charcoal">
                        {r.slug}
                      </span>
                      {r.autonomous && (
                        <span className="text-micro-label uppercase text-amber">
                          auto
                        </span>
                      )}
                      {r.blocked_on_gate && (
                        <span className="text-micro-label uppercase text-warning">
                          waiting on G{r.blocked_on_gate}
                        </span>
                      )}
                    </div>
                    <p className="text-ink truncate">{r.prompt}</p>
                  </div>
                  <div className="text-right whitespace-nowrap">
                    <div className="text-supporting text-charcoal">
                      {r.done}/{r.total} stages
                    </div>
                    <div className="text-micro-label text-ash mt-1">
                      {fmtDate(r.updated_at)}
                    </div>
                  </div>
                </div>
                <div className="mt-3 flex gap-1">
                  {Array.from({ length: r.total }).map((_, i) => {
                    const done = i < r.done;
                    const current = i === r.done && r.current_stage === i + 1;
                    return (
                      <span
                        key={i}
                        className={
                          done
                            ? "h-1.5 flex-1 rounded-full bg-amber"
                            : current
                              ? "h-1.5 flex-1 rounded-full bg-amber-pale"
                              : "h-1.5 flex-1 rounded-full bg-mist"
                        }
                      />
                    );
                  })}
                </div>
              </Link>
            </li>
          ))}
        </ul>
      </section>
    </div>
  );
}
