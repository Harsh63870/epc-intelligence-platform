const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export async function fetchApi<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...init?.headers,
    },
    cache: "no-store",
  });
  if (!res.ok) {
    throw new Error(`API error: ${res.status} ${res.statusText}`);
  }
  return res.json() as Promise<T>;
}

export type Project = {
  id: number;
  name: string;
  tier_target: string;
  location: string;
  status: string;
};

export type DashboardMetrics = {
  active_ncs: number;
  open_rfis: number;
  schedule_risks: number;
  at_risk_shipments: number;
  commissioning_progress_pct: number;
  hours_saved_week: number;
};

export const api = {
  health: () => fetchApi<{ status: string; database: string }>("/api/v1/health"),
  projects: () => fetchApi<Project[]>("/api/v1/projects"),
  dashboard: (projectId = 1) => fetchApi<DashboardMetrics>(`/api/v1/dashboard/metrics?project_id=${projectId}`),
  seed: () => fetchApi<{ message: string; project_id: number }>("/api/v1/seed", { method: "POST" }),
};
