import { Sidebar } from "@/components/Sidebar";
import { ProjectSelector } from "@/components/ProjectSelector";

export function AppShell({ children, title }: { children: React.ReactNode; title: string }) {
  return (
    <div className="flex min-h-screen bg-slate-900 text-slate-100">
      <Sidebar />
      <div className="flex flex-1 flex-col">
        <header className="flex items-center justify-between border-b border-slate-800 bg-slate-950 px-8 py-4">
          <h2 className="text-xl font-semibold text-slate-100">{title}</h2>
          <ProjectSelector />
        </header>
        <main className="flex-1 overflow-auto p-8">{children}</main>
      </div>
    </div>
  );
}
