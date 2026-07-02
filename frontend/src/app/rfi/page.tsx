"use client";

import { useState } from "react";
import { AppShell } from "@/components/AppShell";
import { api, type Citation, type RFIChatResponse, type SimilarRFI } from "@/lib/api";
import { Clock, MessageSquare, Sparkles } from "lucide-react";

const DEMO_QUESTIONS = [
  "What is the approved UPS battery runtime for Tier III?",
  "Has cable tray spacing been clarified before?",
  "What changed in CO-014 regarding chiller redundancy?",
  "What is the acceptance criteria for STS transfer time?",
];

type ChatMessage = {
  role: "user" | "assistant";
  content: string;
  meta?: RFIChatResponse;
};

export default function RFIPage() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function sendMessage(text: string) {
    const query = text.trim();
    if (!query || loading) return;

    setError(null);
    setLoading(true);
    setMessages((prev) => [...prev, { role: "user", content: query }]);
    setInput("");

    try {
      const res = await api.rfiChat(query);
      setMessages((prev) => [...prev, { role: "assistant", content: res.answer, meta: res }]);
    } catch {
      setError("Request failed. Ensure backend is running and demo data is seeded.");
    } finally {
      setLoading(false);
    }
  }

  const lastAssistant = [...messages].reverse().find((m) => m.role === "assistant");
  const citations: Citation[] = lastAssistant?.meta?.citations ?? [];
  const similarRfis: SimilarRFI[] = lastAssistant?.meta?.similar_rfis ?? [];

  return (
    <AppShell title="RFI Copilot">
      <div className="grid gap-6 lg:grid-cols-3">
        <div className="lg:col-span-2 flex flex-col rounded-xl border border-slate-800 bg-slate-950">
          <div className="flex-1 space-y-4 overflow-y-auto p-6" style={{ minHeight: "420px" }}>
            {messages.length === 0 && (
              <div className="text-center text-slate-500">
                <MessageSquare className="mx-auto mb-3 h-8 w-8 text-slate-600" />
                <p className="text-sm">Ask a technical or contractual question about the project.</p>
                <p className="mt-1 text-xs">Answers include citations from project documents.</p>
              </div>
            )}
            {messages.map((msg, i) => (
              <div
                key={i}
                className={`max-w-[90%] rounded-lg px-4 py-3 text-sm whitespace-pre-wrap ${
                  msg.role === "user"
                    ? "ml-auto bg-amber-500/20 text-amber-100"
                    : "bg-slate-900 text-slate-200"
                }`}
              >
                {msg.content}
              </div>
            ))}
            {loading && (
              <div className="rounded-lg bg-slate-900 px-4 py-3 text-sm text-slate-400">Searching project records…</div>
            )}
          </div>

          <div className="border-t border-slate-800 p-4">
            <div className="mb-3 flex flex-wrap gap-2">
              {DEMO_QUESTIONS.map((q) => (
                <button
                  key={q}
                  onClick={() => sendMessage(q)}
                  disabled={loading}
                  className="rounded-full border border-slate-700 px-3 py-1 text-xs text-slate-400 hover:border-amber-500/50 hover:text-amber-300 disabled:opacity-50"
                >
                  {q}
                </button>
              ))}
            </div>
            <div className="flex gap-2">
              <input
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && sendMessage(input)}
                placeholder="Ask about specs, RFIs, change orders…"
                className="flex-1 rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-slate-100 focus:border-amber-500 focus:outline-none"
              />
              <button
                onClick={() => sendMessage(input)}
                disabled={loading || !input.trim()}
                className="rounded-lg bg-amber-500 px-4 py-2 text-sm font-semibold text-slate-950 hover:bg-amber-400 disabled:opacity-50"
              >
                Send
              </button>
            </div>
            {error && <p className="mt-2 text-xs text-red-400">{error}</p>}
          </div>
        </div>

        <aside className="space-y-4">
          {lastAssistant?.meta && (
            <div className="rounded-xl border border-amber-500/30 bg-amber-500/10 p-4">
              <div className="mb-2 flex items-center gap-2 text-amber-300">
                <Clock className="h-4 w-4" />
                <span className="text-xs font-semibold uppercase tracking-wide">Time saved</span>
              </div>
              <p className="text-sm text-amber-100">
                Est. manual effort: {lastAssistant.meta.estimated_manual_minutes} min → ~12 sec
              </p>
              <p className="mt-1 text-xs text-amber-200/70">
                Confidence: {lastAssistant.meta.confidence}
                {!lastAssistant.meta.groq_used && " · RAG-only mode (set GROQ_API_KEY for full AI answers)"}
              </p>
            </div>
          )}

          <div className="rounded-xl border border-slate-800 bg-slate-950 p-4">
            <div className="mb-3 flex items-center gap-2">
              <Sparkles className="h-4 w-4 text-amber-400" />
              <h3 className="text-sm font-semibold text-slate-100">Citations</h3>
            </div>
            {citations.length === 0 ? (
              <p className="text-xs text-slate-500">Citations appear after you ask a question.</p>
            ) : (
              <ul className="space-y-3">
                {citations.map((c, i) => (
                  <li key={i} className="text-xs">
                    <p className="font-medium text-amber-400">{c.source_file}</p>
                    <p className="mt-1 text-slate-400 line-clamp-3">{c.excerpt}</p>
                  </li>
                ))}
              </ul>
            )}
          </div>

          <div className="rounded-xl border border-slate-800 bg-slate-950 p-4">
            <h3 className="mb-3 text-sm font-semibold text-slate-100">Similar resolved RFIs</h3>
            {similarRfis.length === 0 ? (
              <p className="text-xs text-slate-500">No similar RFIs found for the last query.</p>
            ) : (
              <ul className="space-y-3">
                {similarRfis.map((r) => (
                  <li key={r.id} className="rounded-lg border border-slate-800 bg-slate-900 p-3 text-xs">
                    <p className="font-medium text-amber-400">{r.number}</p>
                    <p className="mt-1 text-slate-300">{r.subject}</p>
                    <p className="mt-1 text-slate-500 line-clamp-2">{r.response}</p>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </aside>
      </div>
    </AppShell>
  );
}
