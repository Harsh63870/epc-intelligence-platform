"use client";

import { useEffect, useState } from "react";
import { AppShell } from "@/components/AppShell";
import { api, type DashboardMetrics } from "@/lib/api";
import { AlertTriangle, Clock, MessageSquare, Package, ShieldCheck, Zap } from "lucide-react";

function MetricCard({
  label,
  value,
  sub,
  icon: Icon,
  accent,
}: {
  label: string;
  value: string | number;
  sub?: string;
  icon: React.ComponentType<{ className?: string }>;
  accent?: boolean;
}) {
  return (
    <div className="rounded-xl border border-slate-800 bg-slate-950 p-6">
      <div className="mb-4 flex items-center justify-between">
        <p className="text-sm text-slate-400">{label}</p>
        <Icon className={`h-5 w-5 ${accent ? "text-amber-400" : "text-slate-500"}`} />
      </div>
      <p className={`text-3xl font-bold ${accent ? "text-amber-400" : "text-slate-100"}`}>{value}</p>
      {sub && <p className="mt-1 text-xs text-slate-500">{sub}</p>}
    </div>
  );
}

export default function DashboardPage() {
  const [metrics, setMetrics] = useState<DashboardMetrics | null>(null);
  const [dbStatus, setDbStatus] = useState<string>("checking...");
  const [seeding, setSeeding] = useState(false);
  const [seedResult, setSeedResult] = useState<string | null>(null);

  useEffect(() => {
    api.health().then((h) => setDbStatus(h.database)).catch(() => setDbStatus("unreachable"));
    api.dashboard().then(setMetrics).catch(() => setMetrics(null));
  }, []);

  async function handleSeed() {
    setSeeding(true);
    setSeedResult(null);
    try {
      const res = await api.seed();
      setSeedResult(
        `${res.message} — ${res.documents_in_db} documents, ${res.vectors_in_chroma} vectors, ${res.structured.rfis} RFIs, ${res.structured.procurement_items ?? 0} shipments, ${res.structured.schedule_tasks ?? 0} schedule tasks`
      );
      const m = await api.dashboard();
      setMetrics(m);
    } catch {
      setSeedResult("Seed failed — is the backend running?");
    } finally {
      setSeeding(false);
    }
  }

  return (
    <AppShell title="Dashboard">
      <div className="mb-8 flex items-start justify-between">
        <div>
          <p className="text-sm text-slate-400">Operational intelligence layer</p>
          <p className="mt-1 text-xs text-slate-500">API database: {dbStatus}</p>
        </div>
        <button
          onClick={handleSeed}
          disabled={seeding}
          className="rounded-lg bg-amber-500 px-4 py-2 text-sm font-semibold text-slate-950 hover:bg-amber-400 disabled:opacity-50"
        >
          {seeding ? "Seeding..." : "Seed Demo Project"}
        </button>
      </div>
      {seedResult && (
        <div className="mb-6 rounded-lg border border-amber-500/30 bg-amber-500/10 px-4 py-3 text-sm text-amber-300">
          {seedResult}
        </div>
      )}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <MetricCard label="Active Non-Conformances" value={metrics?.active_ncs ?? "—"} icon={ShieldCheck} />
        <MetricCard label="Open RFIs" value={metrics?.open_rfis ?? "—"} icon={MessageSquare} />
        <MetricCard label="Schedule Risks (14d)" value={metrics?.schedule_risks ?? "—"} icon={AlertTriangle} />
        <MetricCard label="At-Risk Shipments" value={metrics?.at_risk_shipments ?? "—"} icon={Package} />
        <MetricCard
          label="Commissioning Progress"
          value={metrics ? `${metrics.commissioning_progress_pct}%` : "—"}
          icon={Zap}
        />
        <MetricCard
          label="Hours Saved (Week)"
          value={metrics?.hours_saved_week ?? "—"}
          sub="Estimated from logged actions"
          icon={Clock}
          accent
        />
      </div>
      <div className="mt-8 rounded-xl border border-slate-800 bg-slate-950 p-6">
        <h3 className="mb-2 font-semibold text-slate-100">Project overview</h3>
        <p className="text-sm text-slate-400">
          Six intelligence modules connected: Documents, RFI Copilot, Spec Compliance, Schedule Risk, Supply Chain,
          and Commissioning. Run Seed Demo Project to load the full Mumbai Hyperscale DC-01 dataset.
        </p>
      </div>
    </AppShell>
  );
}
