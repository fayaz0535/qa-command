"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { LayoutDashboard, GitBranch, Users, Mail, Upload, Plug, Map } from "lucide-react";
import AdoSyncStatus from "./AdoSyncStatus";

const NAV_ITEMS = [
  { href: "/", label: "Executive", icon: LayoutDashboard },
  { href: "/delivery", label: "Delivery", icon: GitBranch },
  { href: "/owners", label: "Owners", icon: Users },
  { href: "/email", label: "Daily Report", icon: Mail },
  { href: "/upload", label: "Upload", icon: Upload },
];

const SETTINGS_ITEMS = [
  { href: "/settings/ado", label: "ADO Connection", icon: Plug },
  { href: "/settings/mapping", label: "Area Mapping", icon: Map },
];

export default function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="w-56 shrink-0 h-screen sticky top-0 bg-white border-r border-black/[0.08] flex flex-col">
      <div className="px-5 py-5 border-b border-black/[0.08]">
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-md bg-qc-primary flex items-center justify-center">
            <span className="text-white text-xs font-bold">QA</span>
          </div>
          <span className="font-semibold text-[15px] text-[#0D1117]">QA Command</span>
        </div>
        <div className="text-[11px] text-gray-400 mt-1">ZAIMAH TECHNOLOGIES</div>
      </div>
      <nav className="flex-1 px-3 py-4 space-y-1">
        {NAV_ITEMS.map(({ href, label, icon: Icon }) => {
          const active = pathname === href;
          return (
            <Link
              key={href}
              href={href}
              className={`flex items-center gap-2.5 px-3 py-2 rounded-lg text-sm transition-colors ${
                active
                  ? "bg-qc-primary/10 text-qc-primary font-medium"
                  : "text-gray-600 hover:bg-gray-50 hover:text-gray-900"
              }`}
            >
              <Icon size={16} />
              {label}
            </Link>
          );
        })}

        <div className="pt-3 mt-3 border-t border-black/[0.06]">
          <div className="px-3 pb-1.5 text-[11px] font-medium text-gray-400 uppercase tracking-wide">
            Settings
          </div>
          {SETTINGS_ITEMS.map(({ href, label, icon: Icon }) => {
            const active = pathname === href;
            return (
              <Link
                key={href}
                href={href}
                className={`flex items-center gap-2.5 px-3 py-2 rounded-lg text-sm transition-colors ${
                  active
                    ? "bg-qc-primary/10 text-qc-primary font-medium"
                    : "text-gray-600 hover:bg-gray-50 hover:text-gray-900"
                }`}
              >
                <Icon size={16} />
                {label}
              </Link>
            );
          })}
        </div>
      </nav>
      <AdoSyncStatus />
      <div className="px-4 py-4 border-t border-black/[0.08] text-[11px] text-gray-400">
        Phase 1 CSV + Phase 2 ADO
      </div>
    </aside>
  );
}
