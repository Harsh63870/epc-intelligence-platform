import { AppShell } from "@/components/AppShell";

export default function PlaceholderPage({
  title,
  description,
  status = "In development",
}: {
  title: string;
  description: string;
  status?: string;
}) {
  return (
    <AppShell title={title}>
      <div className="rounded-xl border border-dashed border-slate-700 bg-slate-950/50 p-12 text-center">
        <p className="mb-2 text-xs font-semibold uppercase tracking-widest text-amber-500">{status}</p>
        <h3 className="mb-3 text-2xl font-bold text-slate-100">{title}</h3>
        <p className="mx-auto max-w-lg text-slate-400">{description}</p>
      </div>
    </AppShell>
  );
}
