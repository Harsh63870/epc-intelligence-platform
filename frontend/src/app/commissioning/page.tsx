"use client";

import { useEffect, useState } from "react";
import { AppShell } from "@/components/AppShell";
import { api, type CommissioningProgress, type CommissioningTest } from "@/lib/api";
import { CheckCircle2, ChevronLeft, ChevronRight, ClipboardList, XCircle } from "lucide-react";

const STATUS_STYLE: Record<string, string> = {
  pending: "text-slate-400",
  in_progress: "text-amber-400",
  passed: "text-emerald-400",
  failed: "text-red-400",
  nc: "text-orange-400",
};

const SYSTEMS = ["power", "cooling"];

export default function CommissioningPage() {
  const [tests, setTests] = useState<CommissioningTest[]>([]);
  const [progress, setProgress] = useState<CommissioningProgress | null>(null);
  const [systemFilter, setSystemFilter] = useState<string>("power");
  const [step, setStep] = useState(0);
  const [notes, setNotes] = useState("");
  const [measured, setMeasured] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  function load(systemType?: string) {
    Promise.all([api.commissioningTests(1, systemType), api.commissioningProgress()])
      .then(([t, p]) => {
        setTests(t);
        setProgress(p);
        setStep(0);
      })
      .catch(() => setMessage("Failed to load commissioning tests. Seed demo project first."));
  }

  useEffect(() => {
    load(systemFilter);
  }, [systemFilter]);

  const current = tests[step];
  const pendingTests = tests.filter((t) => t.status === "pending" || t.status === "in_progress");

  async function recordResult(status: string) {
    if (!current) return;
    setSubmitting(true);
    setMessage(null);
    try {
      await api.recordCommissioningTest(current.id, {
        status,
        notes: notes || undefined,
        measured_value: measured || undefined,
      });
      setNotes("");
      setMeasured("");
      setMessage(`Test recorded as ${status}.`);
      load(systemFilter);
      if (step < tests.length - 1) setStep((s) => s + 1);
    } catch {
      setMessage("Failed to record test result.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <AppShell title="Commissioning Copilot">
      <div className="mb-6 grid gap-4 sm:grid-cols-3">
        <div className="rounded-xl border border-slate-800 bg-slate-950 p-5 sm:col-span-1">
          <p className="text-xs uppercase tracking-wider text-slate-500">Overall progress</p>
          <p className="mt-2 text-3xl font-bold text-amber-400">{progress?.progress_pct ?? 0}%</p>
          <p className="mt-1 text-sm text-slate-400">
            {progress?.completed ?? 0} / {progress?.total ?? 0} tests completed
          </p>
        </div>
        <div className="rounded-xl border border-slate-800 bg-slate-950 p-5 sm:col-span-2">
          <p className="mb-3 text-xs uppercase tracking-wider text-slate-500">By system</p>
          <div className="flex flex-wrap gap-4">
            {SYSTEMS.map((sys) => {
              const data = progress?.by_system[sys];
              return (
                <button
                  key={sys}
                  onClick={() => setSystemFilter(sys)}
                  className={`rounded-lg border px-4 py-2 text-sm capitalize transition ${
                    systemFilter === sys
                      ? "border-amber-500/50 bg-amber-500/10 text-amber-300"
                      : "border-slate-700 text-slate-400 hover:border-slate-600"
                  }`}
                >
                  {sys}: {data?.progress_pct ?? 0}%
                </button>
              );
            })}
          </div>
        </div>
      </div>

      {message && (
        <div className="mb-4 rounded-lg border border-amber-500/30 bg-amber-500/10 px-4 py-3 text-sm text-amber-300">
          {message}
        </div>
      )}

      {tests.length === 0 ? (
        <div className="rounded-xl border border-dashed border-slate-700 p-12 text-center text-slate-500">
          No commissioning tests. Run Seed Demo Project from the Dashboard.
        </div>
      ) : (
        <div className="grid gap-6 lg:grid-cols-3">
          <div className="lg:col-span-2 rounded-xl border border-slate-800 bg-slate-950 p-6">
            <div className="mb-4 flex items-center justify-between">
              <span className="text-xs text-slate-500">
                Test {step + 1} of {tests.length}
              </span>
              <span className={`text-xs font-medium capitalize ${STATUS_STYLE[current?.status ?? "pending"]}`}>
                {current?.status ?? "pending"}
              </span>
            </div>

            {current && (
              <>
                <div className="mb-2 flex items-center gap-2">
                  <ClipboardList className="h-5 w-5 text-amber-400" />
                  <span className="rounded bg-slate-800 px-2 py-0.5 text-xs text-slate-400">{current.standard_ref}</span>
                </div>
                <h3 className="mb-4 text-lg font-semibold text-slate-100">{current.procedure}</h3>
                <div className="mb-6 rounded-lg border border-slate-800 bg-slate-900/50 p-4">
                  <p className="text-xs uppercase tracking-wider text-slate-500">Acceptance criteria</p>
                  <p className="mt-2 text-sm text-slate-300">{current.acceptance_criteria}</p>
                </div>

                <div className="space-y-3">
                  <input
                    type="text"
                    placeholder="Measured value (e.g. 3.2 ms transfer time)"
                    value={measured}
                    onChange={(e) => setMeasured(e.target.value)}
                    className="w-full rounded-lg border border-slate-700 bg-slate-900 px-4 py-2 text-sm text-slate-200 placeholder:text-slate-600"
                  />
                  <textarea
                    placeholder="Witness notes…"
                    value={notes}
                    onChange={(e) => setNotes(e.target.value)}
                    rows={2}
                    className="w-full rounded-lg border border-slate-700 bg-slate-900 px-4 py-2 text-sm text-slate-200 placeholder:text-slate-600"
                  />
                </div>

                <div className="mt-6 flex flex-wrap gap-3">
                  <button
                    onClick={() => recordResult("passed")}
                    disabled={submitting}
                    className="flex items-center gap-2 rounded-lg bg-emerald-600 px-4 py-2 text-sm font-semibold text-white hover:bg-emerald-500 disabled:opacity-50"
                  >
                    <CheckCircle2 className="h-4 w-4" />
                    Pass
                  </button>
                  <button
                    onClick={() => recordResult("failed")}
                    disabled={submitting}
                    className="flex items-center gap-2 rounded-lg bg-red-600/80 px-4 py-2 text-sm font-semibold text-white hover:bg-red-600 disabled:opacity-50"
                  >
                    <XCircle className="h-4 w-4" />
                    Fail
                  </button>
                  <button
                    onClick={() => recordResult("nc")}
                    disabled={submitting}
                    className="rounded-lg border border-orange-500/50 px-4 py-2 text-sm font-medium text-orange-300 hover:bg-orange-500/10 disabled:opacity-50"
                  >
                    Record NC
                  </button>
                </div>
              </>
            )}

            <div className="mt-6 flex justify-between border-t border-slate-800 pt-4">
              <button
                onClick={() => setStep((s) => Math.max(0, s - 1))}
                disabled={step === 0}
                className="flex items-center gap-1 text-sm text-slate-400 hover:text-slate-200 disabled:opacity-30"
              >
                <ChevronLeft className="h-4 w-4" />
                Previous
              </button>
              <button
                onClick={() => setStep((s) => Math.min(tests.length - 1, s + 1))}
                disabled={step >= tests.length - 1}
                className="flex items-center gap-1 text-sm text-slate-400 hover:text-slate-200 disabled:opacity-30"
              >
                Next
                <ChevronRight className="h-4 w-4" />
              </button>
            </div>
          </div>

          <div className="rounded-xl border border-slate-800 bg-slate-950 p-5">
            <h3 className="mb-4 text-sm font-semibold text-slate-300">Test queue ({systemFilter})</h3>
            <ul className="space-y-2">
              {tests.map((t, i) => (
                <li key={t.id}>
                  <button
                    onClick={() => setStep(i)}
                    className={`w-full rounded-lg px-3 py-2 text-left text-xs transition ${
                      i === step ? "bg-amber-500/20 text-amber-200" : "text-slate-400 hover:bg-slate-900"
                    }`}
                  >
                    <span className={`capitalize ${STATUS_STYLE[t.status]}`}>{t.status}</span>
                    <p className="mt-0.5 truncate text-slate-300">{t.procedure}</p>
                  </button>
                </li>
              ))}
            </ul>
            {pendingTests.length > 0 && (
              <p className="mt-4 text-xs text-slate-500">{pendingTests.length} test(s) remaining in this system</p>
            )}
          </div>
        </div>
      )}
    </AppShell>
  );
}
