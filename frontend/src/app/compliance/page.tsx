"use client";

import { useEffect, useState } from "react";
import { AppShell } from "@/components/AppShell";
import { api, type ComplianceResult, type NCRecord } from "@/lib/api";
import { AlertTriangle, CheckCircle2, ClipboardCheck, Upload } from "lucide-react";

const SEVERITY_STYLE: Record<string, string> = {
  critical: "bg-red-500/20 text-red-300 border-red-500/40",
  major: "bg-orange-500/20 text-orange-300 border-orange-500/40",
  minor: "bg-yellow-500/20 text-yellow-300 border-yellow-500/40",
};

export default function CompliancePage() {
  const [vendor, setVendor] = useState("");
  const [result, setResult] = useState<ComplianceResult | null>(null);
  const [ncs, setNcs] = useState<NCRecord[]>([]);
  const [uploading, setUploading] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  function loadNCs() {
    api.nonConformances().then(setNcs).catch(() => setNcs([]));
  }

  useEffect(() => {
    loadNCs();
  }, []);

  async function handleUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;

    setUploading(true);
    setMessage(null);
    setResult(null);

    try {
      const res = await api.checkSubmittal(file, vendor || "Vendor");
      setResult(res);
      setMessage(`Review complete: ${res.failed} non-conformance(s) flagged, ${res.passed} passed.`);
      loadNCs();
    } catch {
      setMessage("Compliance check failed. Ensure backend is running and specs are seeded.");
    } finally {
      setUploading(false);
      e.target.value = "";
    }
  }

  async function handleNCAction(ncId: number, status: string) {
    await api.updateNCStatus(ncId, status);
    loadNCs();
    if (result) {
      setResult({
        ...result,
        non_conformances: result.non_conformances.map((nc) =>
          nc.id === ncId ? { ...nc, status } : nc
        ),
      });
    }
  }

  return (
    <AppShell title="Spec Compliance">
      <div className="mb-6 rounded-xl border border-slate-800 bg-slate-950 p-6">
        <div className="mb-4 flex items-center gap-2">
          <Upload className="h-5 w-5 text-amber-400" />
          <h3 className="font-semibold text-slate-100">Check vendor submittal</h3>
        </div>
        <div className="mb-4 flex flex-wrap gap-4">
          <input
            value={vendor}
            onChange={(e) => setVendor(e.target.value)}
            placeholder="Vendor name"
            className="rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-slate-100 focus:border-amber-500 focus:outline-none"
          />
          <label className="inline-flex cursor-pointer items-center gap-2 rounded-lg bg-amber-500 px-4 py-2 text-sm font-semibold text-slate-950 hover:bg-amber-400">
            {uploading ? "Checking…" : "Upload submittal"}
            <input
              type="file"
              accept=".pdf,.md,.txt,.markdown"
              className="hidden"
              onChange={handleUpload}
              disabled={uploading}
            />
          </label>
        </div>
        <p className="text-xs text-slate-500">
          Demo files in repo: data/submittals/ups-submittal-a.md, chiller-submittal-b.md, switchgear-submittal-c.md
        </p>
        {message && <p className="mt-3 text-sm text-amber-300">{message}</p>}
      </div>

      {result && (
        <div className="mb-6 overflow-hidden rounded-xl border border-slate-800">
          <div className="border-b border-slate-800 bg-slate-950 px-4 py-3">
            <p className="text-sm text-slate-300">
              {result.equipment_class} · {result.filename} · Vendor: {result.vendor}
            </p>
          </div>
          <table className="w-full text-left text-sm">
            <thead className="bg-slate-950 text-slate-400">
              <tr>
                <th className="px-4 py-3">Requirement</th>
                <th className="px-4 py-3">Required</th>
                <th className="px-4 py-3">Submitted</th>
                <th className="px-4 py-3">Standard</th>
                <th className="px-4 py-3">Status</th>
              </tr>
            </thead>
            <tbody>
              {result.checks.map((check) => (
                <tr key={check.spec_id} className="border-t border-slate-800 text-slate-300">
                  <td className="px-4 py-3">{check.requirement_key}</td>
                  <td className="px-4 py-3">{check.required_value}</td>
                  <td className="px-4 py-3">{check.submitted_value}</td>
                  <td className="px-4 py-3">{check.standard_ref ?? "—"}</td>
                  <td className="px-4 py-3">
                    {check.status === "pass" ? (
                      <span className="inline-flex items-center gap-1 text-green-400">
                        <CheckCircle2 className="h-4 w-4" /> Pass
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-1 text-red-400">
                        <AlertTriangle className="h-4 w-4" /> NC
                      </span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <div className="rounded-xl border border-slate-800 bg-slate-950 p-6">
        <div className="mb-4 flex items-center gap-2">
          <ClipboardCheck className="h-5 w-5 text-amber-400" />
          <h3 className="font-semibold text-slate-100">Non-conformance audit trail ({ncs.length})</h3>
        </div>
        {ncs.length === 0 ? (
          <p className="text-sm text-slate-500">No non-conformances recorded yet.</p>
        ) : (
          <div className="space-y-3">
            {ncs.map((nc) => (
              <div key={nc.id} className="rounded-lg border border-slate-800 bg-slate-900 p-4">
                <div className="mb-2 flex flex-wrap items-center gap-2">
                  <span className={`rounded-full border px-2 py-0.5 text-xs font-medium uppercase ${SEVERITY_STYLE[nc.severity] ?? ""}`}>
                    {nc.severity}
                  </span>
                  <span className="text-xs text-slate-500">{nc.requirement_key}</span>
                  <span className="text-xs text-slate-500">· {nc.status}</span>
                </div>
                <p className="text-sm text-slate-300">{nc.deviation}</p>
                {nc.status === "open" && (
                  <div className="mt-3 flex flex-wrap gap-2">
                    {["waived", "rejected", "revision_requested"].map((action) => (
                      <button
                        key={action}
                        onClick={() => handleNCAction(nc.id, action)}
                        className="rounded border border-slate-700 px-2 py-1 text-xs text-slate-400 hover:border-amber-500/50 hover:text-amber-300"
                      >
                        {action.replace("_", " ")}
                      </button>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </AppShell>
  );
}
