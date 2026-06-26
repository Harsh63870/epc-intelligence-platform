"use client";

import { useEffect, useState } from "react";
import { api, type Project } from "@/lib/api";

export function ProjectSelector() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedId, setSelectedId] = useState(1);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.projects()
      .then((data) => {
        setProjects(data);
        if (data.length > 0) setSelectedId(data[0].id);
      })
      .catch(() => setProjects([]))
      .finally(() => setLoading(false));
  }, []);

  const selected = projects.find((p) => p.id === selectedId);

  return (
    <div className="flex items-center gap-3">
      <label htmlFor="project-select" className="text-sm text-slate-400">
        Project
      </label>
      <select
        id="project-select"
        value={selectedId}
        onChange={(e) => setSelectedId(Number(e.target.value))}
        disabled={loading || projects.length === 0}
        className="rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-slate-100 focus:border-amber-500 focus:outline-none"
      >
        {projects.length === 0 ? (
          <option value={1}>No project — run seed</option>
        ) : (
          projects.map((p) => (
            <option key={p.id} value={p.id}>
              {p.name}
            </option>
          ))
        )}
      </select>
      {selected && (
        <span className="rounded-full bg-amber-500/15 px-2.5 py-1 text-xs font-medium text-amber-400">
          {selected.tier_target}
        </span>
      )}
    </div>
  );
}
