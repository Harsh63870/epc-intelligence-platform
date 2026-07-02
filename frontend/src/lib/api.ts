const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export async function fetchApi<T>(path: string, init?: RequestInit): Promise<T> {
  const isFormData = init?.body instanceof FormData;
  const res = await fetch(`${API_URL}${path}`, {
    ...init,
    headers: isFormData
      ? init?.headers
      : {
          "Content-Type": "application/json",
          ...init?.headers,
        },
    cache: "no-store",
  });
  if (!res.ok) {
    const detail = await res.text().catch(() => res.statusText);
    throw new Error(`API error: ${res.status} ${detail}`);
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

export type SeedResult = {
  message: string;
  project_id: number;
  project_name: string;
  structured: { specifications: number; rfis: number; commissioning_tests: number };
  ingestion: { ingested: number; skipped: number; errors: string[] };
  documents_in_db: number;
  vectors_in_chroma: number;
};

export type DocumentRecord = {
  id: number;
  project_id: number;
  doc_type: string;
  filename: string;
  char_count: number | null;
};

export type SearchResult = {
  id: string;
  text: string;
  metadata: Record<string, unknown>;
  distance: number | null;
};

export type SearchResponse = {
  query: string;
  results: SearchResult[];
  total_vectors: number;
};

export type Citation = {
  source_file: string;
  doc_type?: string | null;
  excerpt: string;
};

export type SimilarRFI = {
  id: number;
  number: string;
  subject: string;
  response: string | null;
  similarity: number;
};

export type RFIChatResponse = {
  answer: string;
  citations: Citation[];
  similar_rfis: SimilarRFI[];
  confidence: string;
  estimated_manual_minutes: number;
  groq_used: boolean;
};

export type ComplianceCheck = {
  spec_id: number;
  requirement_key: string;
  requirement_text: string;
  required_value: string;
  submitted_value: string;
  standard_ref: string | null;
  status: string;
};

export type NonConformance = {
  id: number;
  spec_id: number | null;
  severity: string;
  deviation: string;
  status: string;
};

export type ComplianceResult = {
  submittal_id: number;
  vendor: string;
  equipment_class: string;
  filename: string;
  parsed_attributes: Record<string, string>;
  checks: ComplianceCheck[];
  non_conformances: NonConformance[];
  passed: number;
  failed: number;
};

export type NCRecord = {
  id: number;
  submittal_id: number;
  spec_id: number | null;
  severity: string;
  deviation: string;
  status: string;
  requirement_key?: string | null;
  required_value?: string | null;
  submitted_value?: string | null;
  standard_ref?: string | null;
};

export const api = {
  health: () => fetchApi<{ status: string; database: string }>("/api/v1/health"),
  projects: () => fetchApi<Project[]>("/api/v1/projects"),
  dashboard: (projectId = 1) => fetchApi<DashboardMetrics>(`/api/v1/dashboard/metrics?project_id=${projectId}`),
  seed: () => fetchApi<SeedResult>("/api/v1/seed", { method: "POST" }),
  documents: (projectId = 1) => fetchApi<DocumentRecord[]>(`/api/v1/documents?project_id=${projectId}`),
  search: (query: string, projectId = 1) =>
    fetchApi<SearchResponse>(`/api/v1/documents/search?q=${encodeURIComponent(query)}&project_id=${projectId}`),
  ingest: (file: File, projectId = 1, docType = "other") => {
    const form = new FormData();
    form.append("file", file);
    form.append("project_id", String(projectId));
    form.append("doc_type", docType);
    return fetchApi<DocumentRecord>("/api/v1/documents/ingest", { method: "POST", body: form });
  },
  rfiChat: (query: string, projectId = 1) =>
    fetchApi<RFIChatResponse>("/api/v1/rfi/chat", {
      method: "POST",
      body: JSON.stringify({ query, project_id: projectId }),
    }),
  checkSubmittal: (file: File, vendor: string, projectId = 1) => {
    const form = new FormData();
    form.append("file", file);
    form.append("vendor", vendor);
    form.append("project_id", String(projectId));
    return fetchApi<ComplianceResult>("/api/v1/compliance/check-submittal", { method: "POST", body: form });
  },
  nonConformances: (projectId = 1, status?: string) => {
    const params = new URLSearchParams({ project_id: String(projectId) });
    if (status) params.set("status", status);
    return fetchApi<NCRecord[]>(`/api/v1/compliance/non-conformances?${params}`);
  },
  updateNCStatus: (ncId: number, status: string) =>
    fetchApi<NCRecord>(`/api/v1/compliance/nc/${ncId}/status`, {
      method: "PATCH",
      body: JSON.stringify({ status }),
    }),
};
