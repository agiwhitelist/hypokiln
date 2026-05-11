"use client";

import { useEffect, useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import rehypeHighlight from "rehype-highlight";

import { API_BASE, type GateView, type RunView } from "@/lib/api";
import { StagePill } from "@/components/stage-pill";

type Artifact = { path: string; size: number };

export function RunDetail({ run, gate }: { run: RunView; gate: GateView | null }) {
  const [state, setState] = useState<RunView>(run);
  const [gateState, setGateState] = useState<GateView | null>(gate);
  const [tick, setTick] = useState(0);
  const [artifacts, setArtifacts] = useState<Artifact[]>([]);
  const [openArtifact, setOpenArtifact] = useState<string | null>(null);
  const [artifactBody, setArtifactBody] = useState<string>("");

  useEffect(() => {
    const es = new EventSource(`${API_BASE}/api/events/stream`);
    es.addEventListener("state", (ev: MessageEvent) => {
      if (ev.data === state.slug) setTick((t) => t + 1);
    });
    return () => es.close();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    let alive = true;
    if (tick === 0) return;
    (async () => {
      try {
        const fresh = await fetch(`${API_BASE}/api/runs/${state.slug}`, {
          cache: "no-store",
        }).then((r) => r.json());
        const freshGate = await fetch(`${API_BASE}/api/runs/${state.slug}/gate/1`, {
          cache: "no-store",
        }).then((r) => r.json());
        if (alive) {
          setState(fresh);
          setGateState(freshGate);
        }
      } catch {
        /* ignore */
      }
    })();
    return () => {
      alive = false;
    };
  }, [tick, state.slug]);

  useEffect(() => {
    let alive = true;
    (async () => {
      try {
        const data = await fetch(`${API_BASE}/api/runs/${state.slug}/artifacts-list`, {
          cache: "no-store",
        }).then((r) => r.json());
        if (alive && Array.isArray(data.items)) setArtifacts(data.items);
      } catch {
        /* ignore */
      }
    })();
    return () => {
      alive = false;
    };
  }, [state.slug, tick]);

  async function openArt(path: string) {
    setOpenArtifact(path);
    setArtifactBody("Loading…");
    try {
      const data = await fetch(
        `${API_BASE}/api/runs/${state.slug}/artifacts/${path}`,
        { cache: "no-store" },
      ).then((r) => r.json());
      setArtifactBody(data.content || "");
    } catch (e) {
      setArtifactBody(e instanceof Error ? e.message : String(e));
    }
  }

  const blocked = state.stages.length === 6 &&
    state.stages[5].status === "completed" &&
    !(gateState?.signed);

  return (
    <div className="grid grid-cols-1 lg:grid-cols-[1fr_360px] gap-8">
      <div className="space-y-6">
        <section>
          <h2 className="font-display text-title text-ink mb-3">Pipeline</h2>
          <ol className="space-y-2">
            {state.stages.map((s) => (
              <li
                key={s.stage}
                className="border border-mist rounded-md p-3 flex items-center justify-between gap-3"
              >
                <div className="flex items-center gap-3 min-w-0">
                  <span className="font-mono text-charcoal text-supporting w-6">
                    {s.stage}
                  </span>
                  <div className="min-w-0">
                    <div className="font-body text-ink">{s.name}</div>
                    <div className="text-micro-label text-ash">
                      {s.delegate}
                    </div>
                  </div>
                </div>
                <div className="flex items-center gap-3 whitespace-nowrap">
                  <StagePill status={s.status} />
                </div>
              </li>
            ))}
          </ol>
        </section>

        <section>
          <h2 className="font-display text-title text-ink mb-3">Artifacts</h2>
          {artifacts.length === 0 ? (
            <p className="text-charcoal text-supporting">
              No artifacts yet — the kiln is still warming up.
            </p>
          ) : (
            <ul className="space-y-1">
              {artifacts.map((a) => (
                <li key={a.path}>
                  <button
                    onClick={() => openArt(a.path)}
                    className="font-mono text-supporting text-charcoal hover:text-amber transition-colors"
                  >
                    {a.path}{" "}
                    <span className="text-ash">({a.size} bytes)</span>
                  </button>
                </li>
              ))}
            </ul>
          )}
        </section>

        {openArtifact && (
          <section className="border border-mist rounded-md p-4 bg-paper">
            <div className="flex items-center justify-between mb-2">
              <div className="font-mono text-supporting text-charcoal">
                {openArtifact}
              </div>
              <button
                onClick={() => setOpenArtifact(null)}
                className="text-charcoal hover:text-amber text-supporting"
              >
                close
              </button>
            </div>
            <div className="prose-editorial">
              {openArtifact.endsWith(".md") ? (
                <ReactMarkdown
                  remarkPlugins={[remarkGfm]}
                  rehypePlugins={[rehypeHighlight]}
                >
                  {artifactBody}
                </ReactMarkdown>
              ) : (
                <pre className="hljs whitespace-pre-wrap">{artifactBody}</pre>
              )}
            </div>
          </section>
        )}
      </div>

      <aside className="space-y-4">
        <section
          className={
            "border rounded-md p-4 " +
            (gateState?.signed
              ? "border-success/40 bg-success/5"
              : blocked
                ? "border-warning/40 bg-warning/5"
                : "border-mist bg-paper")
          }
        >
          <div className="flex items-center justify-between mb-2">
            <h3 className="font-display text-title text-ink">G1 — Idea</h3>
            <span
              className={
                gateState?.signed
                  ? "text-micro-label uppercase text-success"
                  : "text-micro-label uppercase text-warning"
              }
            >
              {gateState?.signed ? "signed" : "unsigned"}
            </span>
          </div>
          {gateState?.signed ? (
            <div className="text-supporting text-charcoal">
              <p>
                <span className="text-ash">approver:</span>{" "}
                <span className="text-ink">{gateState.approver}</span>
              </p>
              <p>
                <span className="text-ash">date:</span>{" "}
                <span className="text-ink">{gateState.signed_at}</span>
              </p>
            </div>
          ) : (
            <SignForm slug={state.slug} onSigned={() => setTick((t) => t + 1)} />
          )}
        </section>

        <section className="border border-mist rounded-md p-4 bg-paper">
          <h3 className="font-display text-title text-ink mb-2">Updated</h3>
          <p className="text-supporting text-charcoal">
            {new Date(state.updated_at).toLocaleString()}
          </p>
        </section>
      </aside>
    </div>
  );
}

function SignForm({
  slug,
  onSigned,
}: {
  slug: string;
  onSigned: () => void;
}) {
  const [approver, setApprover] = useState("");
  const [notes, setNotes] = useState("");
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  async function sign(approved: boolean) {
    setErr(null);
    setBusy(true);
    try {
      const res = await fetch(`${API_BASE}/api/runs/${slug}/gate/1`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ approver, notes, approved }),
      });
      if (!res.ok) throw new Error(await res.text());
      onSigned();
    } catch (e) {
      setErr(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="space-y-2">
      <p className="text-supporting text-charcoal">
        G1 approves the bundle: top hypothesis + architecture + viral
        mechanic + wow moment.
      </p>
      <input
        type="text"
        placeholder="approver (your name)"
        value={approver}
        onChange={(e) => setApprover(e.target.value)}
        className="w-full border border-mist rounded p-2 text-supporting bg-paper"
      />
      <textarea
        placeholder="notes (optional)"
        value={notes}
        onChange={(e) => setNotes(e.target.value)}
        rows={2}
        className="w-full border border-mist rounded p-2 text-supporting bg-paper"
      />
      {err && (
        <div className="text-danger text-micro-label">{err}</div>
      )}
      <div className="flex gap-2">
        <button
          onClick={() => sign(true)}
          disabled={busy || !approver.trim()}
          className="flex-1 bg-success text-paper px-3 py-1.5 rounded text-supporting disabled:opacity-50"
        >
          Approve
        </button>
        <button
          onClick={() => sign(false)}
          disabled={busy || !approver.trim()}
          className="flex-1 border border-danger text-danger px-3 py-1.5 rounded text-supporting disabled:opacity-50"
        >
          Reject
        </button>
      </div>
    </div>
  );
}
