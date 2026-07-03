"use client";

import { useEffect, useState } from "react";
import { AppShell } from "@/components/AppShell";
import { api, type MitigationResponse, type ScheduleTask } from "@/lib/api";
import { AlertTriangle, Calendar, Lightbulb, RefreshCw } from "lucide-react";

const RISK_STYLE: Record<string, string> = {
  high: "bg-red-500/20 text-red-300 border-red-500/40",
  medium: "bg-amber-500/20 text-amber-300 border-amber-500/40",
  low: "bg-emerald-500/20 text-emerald-300 border-emerald-500/40",
};

function formatDate(iso: string | null) {
  if (!iso) return "—";
  return new Date(iso).toLocaleDateString("en-IN", { day: "numeric", month: "short", year: "numeric" });
}

export default function SchedulePage() {
  const [tasks, setTasks] = useState<ScheduleTask[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [mitigations, setMitigations] = useState<MitigationResponse | null>(null);
  const [mitigating, setMitigating] = useState<number | null>(null);

  function loadTasks() {
    setLoading(true);
    setError(null);
    api
      .scheduleTasks()
      .then(setTasks)
      .catch(() => setError("Failed to load schedule. Seed demo project from Dashboard first."))
      .finally(() => setLoading(false));
  }

  useEffect(() => {
    loadTasks();
  }, []);

  async function handleMitigate(taskId: number) {
    setMitigating(taskId);
    setMitigations(null);
    try {
      const res = await api.scheduleMitigate(taskId);
      setMitigations(res);
    } catch {
      setError("Mitigation request failed.");
    } finally {
      setMitigating(null);
    }
  }

  const highRisk = tasks.filter((t) => t.risk_score >= 0.5);

  return (
    <AppShell title="Schedule Risk">
      <div className="mb-6 flex items-center justify-between">
        <p className="text-sm text-slate-400">
          Critical-path tasks cross-referenced with procurement ETAs. {highRisk.length} high-risk task(s) detected.
        </p>
        <button
          onClick={loadTasks}
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

      {mitigations && (
        <div className="mb-6 rounded-xl border border-amber-500/30 bg-amber-500/10 p-5">
          <div className="mb-3 flex items-center gap-2">
            <Lightbulb className="h-5 w-5 text-amber-400" />
            <h3 className="font-semibold text-amber-200">Mitigation options — {mitigations.task_name}</h3>
          </div>
          <ol className="list-decimal space-y-2 pl-5 text-sm text-amber-100/90">
            {mitigations.mitigations.map((m, i) => (
              <li key={i}>{m}</li>
            ))}
          </ol>
        </div>
      )}

      <div className="overflow-hidden rounded-xl border border-slate-800 bg-slate-950">
        <table className="w-full text-left text-sm">
          <thead className="border-b border-slate-800 bg-slate-900/50 text-xs uppercase tracking-wider text-slate-500">
            <tr>
              <th className="px-4 py-3">Task</th>
              <th className="px-4 py-3">Planned start</th>
              <th className="px-4 py-3">Equipment</th>
              <th className="px-4 py-3">Delay</th>
              <th className="px-4 py-3">Risk</th>
              <th className="px-4 py-3"></th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800">
            {loading && (
              <tr>
                <td colSpan={6} className="px-4 py-8 text-center text-slate-500">
                  Loading schedule…
                </td>
              </tr>
            )}
            {!loading && tasks.length === 0 && (
              <tr>
                <td colSpan={6} className="px-4 py-8 text-center text-slate-500">
                  No schedule tasks. Run Seed Demo Project from the Dashboard.
                </td>
              </tr>
            )}
            {tasks.map((task) => (
              <tr key={task.task_id} className="hover:bg-slate-900/40">
                <td className="px-4 py-3">
                  <div className="font-medium text-slate-200">{task.name}</div>
                  {task.critical_path && (
                    <span className="mt-1 inline-block rounded bg-amber-500/20 px-1.5 py-0.5 text-xs text-amber-400">
                      Critical path
                    </span>
                  )}
                </td>
                <td className="px-4 py-3 text-slate-400">
                  <div className="flex items-center gap-1">
                    <Calendar className="h-3.5 w-3.5" />
                    {formatDate(task.planned_start)}
                  </div>
                </td>
                <td className="px-4 py-3 text-slate-400">{task.procurement_equipment ?? "—"}</td>
                <td className="px-4 py-3">
                  {task.delay_days > 0 ? (
                    <span className="text-red-400">+{task.delay_days}d late</span>
                  ) : (
                    <span className="text-emerald-400">On time</span>
                  )}
                </td>
                <td className="px-4 py-3">
                  <span
                    className={`inline-flex items-center gap-1 rounded border px-2 py-0.5 text-xs font-medium ${RISK_STYLE[task.risk_level] ?? RISK_STYLE.low}`}
                  >
                    {task.risk_level === "high" && <AlertTriangle className="h-3 w-3" />}
                    {(task.risk_score * 100).toFixed(0)}%
                  </span>
                </td>
                <td className="px-4 py-3">
                  {task.risk_score >= 0.3 && (
                    <button
                      onClick={() => handleMitigate(task.task_id)}
                      disabled={mitigating === task.task_id}
                      className="rounded bg-amber-500/20 px-3 py-1 text-xs font-medium text-amber-300 hover:bg-amber-500/30 disabled:opacity-50"
                    >
                      {mitigating === task.task_id ? "…" : "Mitigate"}
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </AppShell>
  );
}
