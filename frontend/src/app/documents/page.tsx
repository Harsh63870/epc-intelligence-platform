"use client";

import { useEffect, useState } from "react";
import { AppShell } from "@/components/AppShell";
import { api, type DocumentRecord, type SearchResult } from "@/lib/api";
import { FileText, Search, Upload } from "lucide-react";

const DEMO_QUERIES = [
  "UPS battery runtime Tier III",
  "cable tray spacing",
  "CO-014 chiller redundancy",
  "STS transfer time acceptance",
];

export default function DocumentsPage() {
  const [documents, setDocuments] = useState<DocumentRecord[]>([]);
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<SearchResult[]>([]);
  const [vectorCount, setVectorCount] = useState<number | null>(null);
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  function loadDocuments() {
    api.documents().then(setDocuments).catch(() => setDocuments([]));
  }

  useEffect(() => {
    loadDocuments();
  }, []);

  async function handleSearch(searchQuery?: string) {
    const q = (searchQuery ?? query).trim();
    if (q.length < 2) return;
    setLoading(true);
    setMessage(null);
    try {
      const res = await api.search(q);
      setResults(res.results);
      setVectorCount(res.total_vectors);
      if (!searchQuery) setQuery(q);
    } catch {
      setMessage("Search failed — run Seed Demo Project first.");
    } finally {
      setLoading(false);
    }
  }

  async function handleUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploading(true);
    setMessage(null);
    try {
      await api.ingest(file);
      setMessage(`Uploaded and indexed: ${file.name}`);
      loadDocuments();
    } catch {
      setMessage("Upload failed — check file format (pdf, md, txt).");
    } finally {
      setUploading(false);
      e.target.value = "";
    }
  }

  return (
    <AppShell title="Documents">
      <div className="grid gap-6 lg:grid-cols-2">
        <section className="rounded-xl border border-slate-800 bg-slate-950 p-6">
          <div className="mb-4 flex items-center gap-2">
            <Upload className="h-5 w-5 text-amber-400" />
            <h3 className="font-semibold text-slate-100">Upload document</h3>
          </div>
          <p className="mb-4 text-sm text-slate-400">
            PDF, Markdown, or text files are parsed, chunked, and embedded into the vector store.
          </p>
          <label className="inline-flex cursor-pointer items-center gap-2 rounded-lg bg-amber-500 px-4 py-2 text-sm font-semibold text-slate-950 hover:bg-amber-400">
            {uploading ? "Uploading..." : "Choose file"}
            <input type="file" accept=".pdf,.md,.txt,.markdown" className="hidden" onChange={handleUpload} disabled={uploading} />
          </label>
          {message && <p className="mt-4 text-sm text-amber-300">{message}</p>}
        </section>

        <section className="rounded-xl border border-slate-800 bg-slate-950 p-6">
          <div className="mb-4 flex items-center gap-2">
            <Search className="h-5 w-5 text-amber-400" />
            <h3 className="font-semibold text-slate-100">Vector search</h3>
          </div>
          <div className="flex gap-2">
            <input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleSearch()}
              placeholder="e.g. UPS battery runtime"
              className="flex-1 rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-slate-100 focus:border-amber-500 focus:outline-none"
            />
            <button
              onClick={() => handleSearch()}
              disabled={loading}
              className="rounded-lg bg-slate-800 px-4 py-2 text-sm font-medium text-slate-200 hover:bg-slate-700 disabled:opacity-50"
            >
              {loading ? "..." : "Search"}
            </button>
          </div>
          <div className="mt-3 flex flex-wrap gap-2">
            {DEMO_QUERIES.map((q) => (
              <button
                key={q}
                onClick={() => handleSearch(q)}
                className="rounded-full border border-slate-700 px-3 py-1 text-xs text-slate-400 hover:border-amber-500/50 hover:text-amber-300"
              >
                {q}
              </button>
            ))}
          </div>
          {vectorCount !== null && (
            <p className="mt-3 text-xs text-slate-500">{vectorCount} vectors indexed</p>
          )}
        </section>
      </div>

      {results.length > 0 && (
        <section className="mt-6 space-y-3">
          <h3 className="font-semibold text-slate-100">Search results</h3>
          {results.map((r) => (
            <div key={r.id} className="rounded-lg border border-slate-800 bg-slate-950 p-4">
              <p className="mb-1 text-xs text-amber-400">
                {(r.metadata.source_file as string) ?? "unknown"} · chunk {(r.metadata.chunk_index as number) ?? 0}
              </p>
              <p className="text-sm text-slate-300">{r.text.slice(0, 400)}{r.text.length > 400 ? "…" : ""}</p>
            </div>
          ))}
        </section>
      )}

      <section className="mt-8">
        <div className="mb-4 flex items-center gap-2">
          <FileText className="h-5 w-5 text-slate-500" />
          <h3 className="font-semibold text-slate-100">Indexed documents ({documents.length})</h3>
        </div>
        <div className="overflow-hidden rounded-xl border border-slate-800">
          <table className="w-full text-left text-sm">
            <thead className="bg-slate-950 text-slate-400">
              <tr>
                <th className="px-4 py-3 font-medium">File</th>
                <th className="px-4 py-3 font-medium">Type</th>
                <th className="px-4 py-3 font-medium">Size</th>
              </tr>
            </thead>
            <tbody>
              {documents.map((doc) => (
                <tr key={doc.id} className="border-t border-slate-800 text-slate-300">
                  <td className="px-4 py-3">{doc.filename}</td>
                  <td className="px-4 py-3 capitalize">{doc.doc_type.replace("_", " ")}</td>
                  <td className="px-4 py-3">{doc.char_count ? `${doc.char_count.toLocaleString()} chars` : "—"}</td>
                </tr>
              ))}
              {documents.length === 0 && (
                <tr>
                  <td colSpan={3} className="px-4 py-8 text-center text-slate-500">
                    No documents yet — click Seed Demo Project on the Dashboard
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </section>
    </AppShell>
  );
}
