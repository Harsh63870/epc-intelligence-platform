"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  MessageSquare,
  ClipboardCheck,
  CalendarRange,
  Truck,
  Wrench,
  FileText,
} from "lucide-react";

const navItems = [
  { href: "/", label: "Dashboard", icon: LayoutDashboard },
  { href: "/documents", label: "Documents", icon: FileText },
  { href: "/rfi", label: "RFI Copilot", icon: MessageSquare },
  { href: "/compliance", label: "Spec Compliance", icon: ClipboardCheck },
  { href: "/schedule", label: "Schedule", icon: CalendarRange },
  { href: "/supply-chain", label: "Supply Chain", icon: Truck },
  { href: "/commissioning", label: "Commissioning", icon: Wrench },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="flex w-64 shrink-0 flex-col border-r border-slate-800 bg-slate-950">
      <div className="border-b border-slate-800 px-6 py-5">
        <p className="text-xs font-semibold uppercase tracking-widest text-amber-500">EPC Intelligence</p>
        <h1 className="mt-1 text-lg font-bold text-slate-100">Data Centre Platform</h1>
      </div>
      <nav className="flex flex-1 flex-col gap-1 p-4">
        {navItems.map(({ href, label, icon: Icon }) => {
          const active = pathname === href;
          return (
            <Link
              key={href}
              href={href}
              className={`flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors ${
                active
                  ? "bg-amber-500/15 text-amber-400"
                  : "text-slate-400 hover:bg-slate-900 hover:text-slate-200"
              }`}
            >
              <Icon className="h-4 w-4 shrink-0" />
              {label}
            </Link>
          );
        })}
      </nav>
      <div className="border-t border-slate-800 p-4 text-xs text-slate-500">
        Industrial Intelligence Layer
      </div>
    </aside>
  );
}
