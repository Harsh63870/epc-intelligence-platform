"use client";

import { useEffect, useState } from "react";
import { AppShell } from "@/components/AppShell";
import { api, type Shipment, type SupplyAlert } from "@/lib/api";
import { AlertTriangle, MapPin, Package, RefreshCw, Ship } from "lucide-react";

const STATUS_STYLE: Record<string, string> = {
  on_track: "bg-emerald-500/20 text-emerald-300",
  at_risk: "bg-amber-500/20 text-amber-300",
  delayed: "bg-red-500/20 text-red-300",
  delivered: "bg-slate-500/20 text-slate-300",
};

function formatDate(iso: string | null) {
  if (!iso) return "—";
  return new Date(iso).toLocaleDateString("en-IN", { day: "numeric", month: "short", year: "numeric" });
}

function ShipmentMap({ shipments }: { shipments: Shipment[] }) {
  const withCoords = shipments.filter((s) => s.current_lat != null && s.current_lng != null);
  if (withCoords.length === 0) return null;

  const lats = withCoords.flatMap((s) => [s.current_lat!, s.dest_lat ?? 19.076]);
  const lngs = withCoords.flatMap((s) => [s.current_lng!, s.dest_lng ?? 72.877]);
  const minLat = Math.min(...lats);
  const maxLat = Math.max(...lats);
  const minLng = Math.min(...lngs);
  const maxLng = Math.max(...lngs);

  function pos(lat: number, lng: number) {
    const x = maxLng === minLng ? 50 : ((lng - minLng) / (maxLng - minLng)) * 90 + 5;
    const y = maxLat === minLat ? 50 : (1 - (lat - minLat) / (maxLat - minLat)) * 80 + 10;
    return { left: `${x}%`, top: `${y}%` };
  }

  return (
    <div className="relative h-64 overflow-hidden rounded-xl border border-slate-800 bg-slate-900/50">
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,_var(--tw-gradient-stops))] from-slate-800/30 to-transparent" />
      <p className="absolute left-3 top-3 text-xs font-medium uppercase tracking-wider text-slate-500">
        Shipment routes → Mumbai
      </p>
      {withCoords.map((s) => {
        const p = pos(s.current_lat!, s.current_lng!);
        const color =
          s.status === "delayed" ? "bg-red-400" : s.status === "at_risk" ? "bg-amber-400" : "bg-emerald-400";
        return (
          <div
            key={s.id}
            className="absolute -translate-x-1/2 -translate-y-1/2"
            style={{ left: p.left, top: p.top }}
            title={`${s.equipment_type} — ${s.status}`}
          >
            <div className={`h-3 w-3 rounded-full ${color} ring-2 ring-slate-950`} />
          </div>
        );
      })}
      <div className="absolute bottom-3 right-3 flex items-center gap-1 text-xs text-slate-500">
        <MapPin className="h-3 w-3" />
        Mumbai DC-01
      </div>
    </div>
  );
}

export default function SupplyChainPage() {
  const [shipments, setShipments] = useState<Shipment[]>([]);
  const [alerts, setAlerts] = useState<SupplyAlert[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  function load() {
    setLoading(true);
    setError(null);
    Promise.all([api.shipments(), api.supplyAlerts()])
      .then(([s, a]) => {
        setShipments(s);
        setAlerts(a);
      })
      .catch(() => setError("Failed to load supply chain data. Seed demo project from Dashboard first."))
      .finally(() => setLoading(false));
  }

  useEffect(() => {
    load();
  }, []);

  return (
    <AppShell title="Supply Chain">
      <div className="mb-6 flex items-center justify-between">
        <p className="text-sm text-slate-400">
          Critical equipment shipments with delivery risk alerts linked to schedule impact.
        </p>
        <button
          onClick={load}
          className="flex items-center gap-2 rounded-lg border border-slate-700 px-3 py-1.5 text-sm text-slate-300 hover:bg-slate-900"
        >
          <RefreshCw className="h-4 w-4" />
          Refresh
        </button>
      </div>

      {error && (
        <div className="mb-4 rounded-lg border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-300">
          {error}
        </div>
      )}

      {alerts.length > 0 && (
        <div className="mb-6 space-y-2">
          {alerts.map((alert, i) => (
            <div
              key={i}
              className={`flex items-start gap-3 rounded-lg border px-4 py-3 text-sm ${
                alert.severity === "high"
                  ? "border-red-500/30 bg-red-500/10 text-red-200"
                  : "border-amber-500/30 bg-amber-500/10 text-amber-200"
              }`}
            >
              <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
              <div>
                <p>{alert.message}</p>
                <p className="mt-1 text-xs opacity-70">ETA: {formatDate(alert.eta)}</p>
              </div>
            </div>
          ))}
        </div>
      )}

      <div className="mb-6">
        <ShipmentMap shipments={shipments} />
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {loading && <p className="col-span-full text-center text-slate-500">Loading shipments…</p>}
        {!loading && shipments.length === 0 && (
          <p className="col-span-full text-center text-slate-500">
            No shipments. Run Seed Demo Project from the Dashboard.
          </p>
        )}
        {shipments.map((s) => (
          <div key={s.id} className="rounded-xl border border-slate-800 bg-slate-950 p-5">
            <div className="mb-3 flex items-start justify-between">
              <Ship className="h-5 w-5 text-slate-500" />
              <span className={`rounded px-2 py-0.5 text-xs font-medium ${STATUS_STYLE[s.status] ?? STATUS_STYLE.on_track}`}>
                {s.status.replace("_", " ")}
              </span>
            </div>
            <h3 className="font-semibold text-slate-100">{s.equipment_type}</h3>
            <p className="mt-1 text-sm text-slate-400">{s.supplier}</p>
            <div className="mt-4 space-y-1 text-xs text-slate-500">
              <div className="flex items-center gap-1">
                <Package className="h-3 w-3" />
                ETA: {formatDate(s.eta)}
              </div>
              <div>Risk score: {(s.risk_score * 100).toFixed(0)}%</div>
            </div>
          </div>
        ))}
      </div>
    </AppShell>
  );
}
