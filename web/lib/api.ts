/**
 * Tiny fetch wrapper around the HypoKiln control plane.
 */

export const API_BASE =
  process.env.NEXT_PUBLIC_HYPOKILN_API_URL?.replace(/\/$/, "") ||
  "http://localhost:8765";

export type RunSummary = {
  slug: string;
  prompt: string;
  autonomous: boolean;
  created_at: string;
  updated_at: string;
  done: number;
  total: number;
  current_stage: number | null;
  blocked_on_gate: number | null;
};

export type StageView = {
  stage: number;
  name: string;
  status: string;
  delegate: string;
  started_at: string | null;
  completed_at: string | null;
  artifacts: string[];
  notes: string;
};

export type RunView = {
  slug: string;
  prompt: string;
  autonomous: boolean;
  created_at: string;
  updated_at: string;
  stages: StageView[];
  gates: Record<string, { signed?: boolean; verified_at?: string }>;
};

export type GateView = {
  gate_id: number;
  signed: boolean;
  approver: string;
  signed_at: string | null;
  notes: string;
  file_exists: boolean;
  body: string;
};

export type WedgeEntry = {
  id: string;
  title: string;
  provider: string;
  released: string | null;
  age_days: number | null;
  section: "active" | "archived";
};

export type WedgesResp = {
  active: WedgeEntry[];
  archived: WedgeEntry[];
  by_provider: Record<string, number>;
  path: string;
};

export async function api<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers || {}),
    },
    cache: "no-store",
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`${res.status} ${res.statusText}: ${text}`);
  }
  return (await res.json()) as T;
}
