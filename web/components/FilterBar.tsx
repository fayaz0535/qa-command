"use client";

import { useEffect, useState } from "react";
import { X } from "lucide-react";
import { useFilters } from "@/lib/FilterContext";
import { fetchHierarchy, fetchOwners } from "@/lib/api";
import type { HierarchyTree } from "@/lib/types";

const SEVERITIES = ["Critical", "High", "Medium", "Low", "TBC"];
const PHASES = ["SIT", "UAT", "BVT", "Parallel Run"];

function Select({
  label, value, onChange, options,
}: {
  label: string; value: string | undefined; onChange: (v: string | undefined) => void; options: string[];
}) {
  return (
    <select
      value={value || ""}
      onChange={(e) => onChange(e.target.value || undefined)}
      className="text-sm border border-black/10 rounded-md px-2.5 py-1.5 bg-white text-gray-700
                 focus:outline-none focus:ring-2 focus:ring-qc-primary/30 min-w-[130px]"
    >
      <option value="">{label}</option>
      {options.map((o) => (
        <option key={o} value={o}>{o}</option>
      ))}
    </select>
  );
}

export default function FilterBar({ showPhase = false }: { showPhase?: boolean }) {
  const { filters, setFilter, clearFilters } = useFilters();
  const [hierarchy, setHierarchy] = useState<HierarchyTree>({ platforms: [] });
  const [owners, setOwners] = useState<string[]>([]);

  useEffect(() => {
    fetchHierarchy().then(setHierarchy).catch(() => {});
    fetchOwners().then((r) => setOwners(r.owners)).catch(() => {});
  }, []);

  const platform = hierarchy.platforms.find((p) => p.name === filters.platform);
  const modules = platform?.modules || [];
  const mod = modules.find((m) => m.name === filters.module);
  const subModules = mod?.sub_modules || [];

  const hasActiveFilters = Object.values(filters).some(Boolean);

  return (
    <div className="flex flex-wrap items-center gap-2 px-6 py-3 bg-white border-b border-black/[0.08] sticky top-0 z-10">
      <Select label="Platform" value={filters.platform} onChange={(v) => setFilter("platform", v)}
              options={hierarchy.platforms.map((p) => p.name)} />
      <Select label="Module" value={filters.module} onChange={(v) => setFilter("module", v)}
              options={modules.map((m) => m.name)} />
      <Select label="Sub-module" value={filters.sub_module} onChange={(v) => setFilter("sub_module", v)}
              options={subModules} />
      <Select label="Severity" value={filters.severity} onChange={(v) => setFilter("severity", v)}
              options={SEVERITIES} />
      {showPhase && (
        <Select label="Phase" value={filters.phase} onChange={(v) => setFilter("phase", v)} options={PHASES} />
      )}
      <Select label="Owner" value={filters.owner} onChange={(v) => setFilter("owner", v)} options={owners} />
      {hasActiveFilters && (
        <button
          onClick={clearFilters}
          className="flex items-center gap-1 text-sm text-gray-500 hover:text-gray-800 px-2 py-1.5"
        >
          <X size={14} /> Clear
        </button>
      )}
    </div>
  );
}
