import Link from "next/link";
import { notFound } from "next/navigation";

import { RunDetail } from "./run-detail";
import { api, type RunView, type GateView } from "@/lib/api";

export const dynamic = "force-dynamic";

async function loadRun(slug: string): Promise<RunView | null> {
  try {
    return await api<RunView>(`/api/runs/${slug}`);
  } catch {
    return null;
  }
}

async function loadGate(slug: string): Promise<GateView | null> {
  try {
    return await api<GateView>(`/api/runs/${slug}/gate/1`);
  } catch {
    return null;
  }
}

export default async function RunPage(
  props: { params: Promise<{ slug: string }> },
) {
  const { slug } = await props.params;
  const [run, gate] = await Promise.all([loadRun(slug), loadGate(slug)]);
  if (!run) {
    notFound();
  }
  return (
    <div className="editorial-shell space-y-8">
      <header>
        <Link
          href="/"
          className="text-micro-label uppercase text-charcoal hover:text-amber transition-colors"
        >
          ← all ideas
        </Link>
        <div className="mt-3 flex items-baseline gap-3">
          <h1 className="font-mono text-title text-ink">{run.slug}</h1>
          {run.autonomous && (
            <span className="text-micro-label uppercase text-amber">auto</span>
          )}
        </div>
        <p className="text-body-lead text-charcoal mt-2 italic">
          “{run.prompt}”
        </p>
      </header>

      <RunDetail run={run} gate={gate} />
    </div>
  );
}
