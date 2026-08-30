"use client";

import { useEffect, useMemo, useState } from "react";
import { AlertTriangle } from "lucide-react";
import FilterBar from "@/components/FilterBar";
import ExportButton from "@/components/ExportButton";
import ErrorState from "@/components/ErrorState";
import { useFilters } from "@/lib/FilterContext";
import { fetchDefects } from "@/lib/api";
import { displayHierarchyName } from "@/lib/hierarchyLabels";
import type { Defect } from "@/lib/types";

const SEVERITY_BADGE: Record<string, string> = {
  Critical: "bg-red-50 text-red-600 border-red-200",
  High: "bg-amber-50 text-amber-600 border-amber-200",
  Medium: "bg-blue-50 text-blue-600 border-blue-200",
  Low: "bg-slate-50 text-slate-500 border-slate-200",
  TBC: "bg-slate-50 text-slate-400 border-slate-200",
};

function SummaryTile({ label, value, warn }: { label: string; value: string | number; warn?: boolean }) {
  return (
    <div className="bg-white border border-black/[0.08] rounded-xl p-4 shadow-sm">
      <div className="text-xs font-medium text-gray-500 uppercase tracking-wide">{label}</div>
      <div className={`text-2xl font-bold mt-1 ${warn ? "text-amber-600" : "text-[#0D1117]"}`}>{value}</div>
    </div>
  );
}

export default function OwnersPage() {
  const { filters } = useFilters();
  const [defects, setDefects] = useState<Defect[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadDefects = () => {
    if (!filters.owner) { setDefects([]); setError(null); return; }
    setLoading(true);
    setError(null);
    fetchDefects({ owner: filters.owner, severity: filters.severity })
      .then((r) => setDefects(r.defects))
      .catch((e) => setError(e.message || "Failed to load defects"))
      .finally(() => setLoading(false));
  };

  useEffect(loadDefects, [filters.owner, filters.severity]);

  const summary = useMemo(() => {
    const open = defects.filter((d) => !["Closed", "Deferred", "Rejected"].includes(d.state));
    const critical = open.filter((d) => d.severity === "Critical").length;
    const missingEta = open.filter((d) => !d.eta).length;
    const avgAging = open.length
      ? Math.round(open.reduce((sum, d) => sum + (d.aging_days || 0), 0) / open.length)
      : 0;
    return { openCount: open.length, critical, missingEta, avgAging };
  }, [defects]);

  return (
    <div>
      <FilterBar />
      <div className="p-6 space-y-4">
        <div className="flex items-center justify-between">
          <h1 className="text-lg font-semibold text-[#0D1117]">Owner View</h1>
          {filters.owner && <ExportButton kind="defects" />}
        </div>

        {!filters.owner ? (
          <div className="text-sm text-gray-400 bg-white border border-black/[0.08] rounded-xl p-6">
            Select an owner from the filter bar above to see their defects, aging, and ETAs.
          </div>
        ) : error ? (
          <ErrorState message={error} onRetry={loadDefects} />
        ) : (
          <>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <SummaryTile label="Open defects" value={summary.openCount} />
              <SummaryTile label="Critical" value={summary.critical} warn={summary.critical > 0} />
              <SummaryTile label="Avg aging" value={`${summary.avgAging}d`} />
              <SummaryTile label="Missing ETA" value={summary.missingEta} warn={summary.missingEta > 0} />
            </div>

            <div className="bg-white border border-black/[0.08] rounded-xl shadow-sm overflow-hidden">
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-black/[0.08] text-left text-xs text-gray-400 uppercase">
                      <th className="px-4 py-3 font-medium">ID</th>
                      <th className="px-4 py-3 font-medium">Title</th>
                      <th className="px-4 py-3 font-medium">Location</th>
                      <th className="px-4 py-3 font-medium">Severity</th>
                      <th className="px-4 py-3 font-medium">State</th>
                      <th className="px-4 py-3 font-medium">Raised</th>
                      <th className="px-4 py-3 font-medium">ETA</th>
                      <th className="px-4 py-3 font-medium">Aging</th>
                    </tr>
                  </thead>
                  <tbody>
                    {loading ? (
                      <tr><td colSpan={8} className="px-4 py-6 text-center text-gray-400">Loading…</td></tr>
                    ) : defects.length === 0 ? (
                      <tr><td colSpan={8} className="px-4 py-6 text-center text-gray-400">No defects for this owner.</td></tr>
                    ) : (
                      defects.map((d) => (
                        <tr key={d.id} className="border-b border-black/[0.04] last:border-0 hover:bg-gray-50">
                          <td className="px-4 py-2.5 text-gray-500">{d.external_id}</td>
                          <td className="px-4 py-2.5 text-gray-800 max-w-[280px] truncate" title={d.title}>
                            {d.title}
                          </td>
                          <td className="px-4 py-2.5 text-gray-500 text-xs">
                            {[d.platform, d.module, d.sub_module].filter(Boolean).map(displayHierarchyName).join(" › ")}
                          </td>
                          <td className="px-4 py-2.5">
                            <span className={`text-xs px-2 py-0.5 rounded-full border ${SEVERITY_BADGE[d.severity]}`}>
                              {d.severity}
                            </span>
                          </td>
                          <td className="px-4 py-2.5 text-gray-600">{d.state}</td>
                          <td className="px-4 py-2.5 text-gray-500">{d.raised_date || "—"}</td>
                          <td className="px-4 py-2.5">
                            {d.eta ? (
                              <span className="text-gray-500">{d.eta}</span>
                            ) : (
                              <span className="flex items-center gap-1 text-amber-600 text-xs">
                                <AlertTriangle size={12} /> Missing
                              </span>
                            )}
                          </td>
                          <td className="px-4 py-2.5 text-gray-500">
                            {d.aging_days != null ? `${d.aging_days}d` : "—"}
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
