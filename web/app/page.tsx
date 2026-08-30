"use client";

import { useEffect, useState } from "react";
import FilterBar from "@/components/FilterBar";
import KpiCard, { TrendDirection } from "@/components/KpiCard";
import TrendChart from "@/components/TrendChart";
import SeverityBars from "@/components/SeverityBars";
import PlatformHealthBars from "@/components/PlatformHealthBars";
import OwnerBars from "@/components/OwnerBars";
import InsightsPanel from "@/components/InsightsPanel";
import ExportButton from "@/components/ExportButton";
import { useFilters } from "@/lib/FilterContext";
import { fetchMetrics, fetchTrend } from "@/lib/api";
import { selectNodeMetrics, trendParamsFromFilters } from "@/lib/selectNode";
import type { MetricsTree, TrendPoint } from "@/lib/types";

const TARGETS = { execution: 95, pass_rate: 98, aging21: 0, avg_resolution: 5 };

function directionFrom(points: TrendPoint[], key: "execution_pct" | "pass_rate" | "open_defects"): TrendDirection {
  if (points.length < 2) return "flat";
  const last = points[points.length - 1][key];
  const prev = points[points.length - 2][key];
  if (last === prev) return "flat";
  return last > prev ? "up" : "down";
}

export default function ExecutivePage() {
  const { filters } = useFilters();
  const [tree, setTree] = useState<MetricsTree | null>(null);
  const [trend, setTrend] = useState<TrendPoint[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    fetchMetrics(filters.owner).then(setTree).catch(() => setTree(null)).finally(() => setLoading(false));
  }, [filters.owner]);

  useEffect(() => {
    fetchTrend({ ...trendParamsFromFilters(filters), days: 30 })
      .then((r) => setTrend(r.trend))
      .catch(() => setTrend([]));
  }, [filters.platform, filters.module, filters.sub_module]);

  return (
    <div>
      <FilterBar />
      <div className="p-6 space-y-6">
        <div className="flex items-center justify-between">
          <h1 className="text-lg font-semibold text-[#0D1117]">Executive Dashboard</h1>
          <div className="flex gap-2">
            <ExportButton kind="defects" />
            <ExportButton kind="tests" />
          </div>
        </div>

        {loading || !tree ? (
          <div className="text-sm text-gray-400">Loading metrics…</div>
        ) : (
          <>
            {(() => {
              const { label, metrics } = selectNodeMetrics(tree, filters);
              return (
                <>
                  {label !== "Overall" && (
                    <div className="text-xs text-gray-400 -mb-2">Scoped to {label}</div>
                  )}
                  <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                    <KpiCard
                      label="Execution"
                      value={`${metrics.execution_pct}%`}
                      target={`${TARGETS.execution}%`}
                      trend={directionFrom(trend, "execution_pct")}
                      trendIsGood={directionFrom(trend, "execution_pct") === "up"}
                    />
                    <KpiCard
                      label="Pass rate"
                      value={`${metrics.pass_rate}%`}
                      target={`${TARGETS.pass_rate}%`}
                      trend={directionFrom(trend, "pass_rate")}
                      trendIsGood={directionFrom(trend, "pass_rate") === "up"}
                    />
                    <KpiCard
                      label="Open defects"
                      value={String(metrics.open_defects)}
                      sub={`${metrics.open_by_severity.Critical || 0} critical`}
                      trend={directionFrom(trend, "open_defects")}
                      trendIsGood={directionFrom(trend, "open_defects") === "down"}
                    />
                    <KpiCard
                      label="Aging > 21d"
                      value={String(metrics.aging_gt21)}
                      target={String(TARGETS.aging21)}
                    />
                    <KpiCard
                      label="Avg resolution"
                      value={metrics.avg_resolution_days != null ? `${metrics.avg_resolution_days}d` : "—"}
                      target={`${TARGETS.avg_resolution}d`}
                    />
                  </div>

                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    <div className="bg-white border border-black/[0.08] rounded-xl p-5 shadow-sm">
                      <div className="text-sm font-semibold text-[#0D1117] mb-3">Open vs Closed (30d)</div>
                      <TrendChart data={trend} />
                    </div>
                    <div className="bg-white border border-black/[0.08] rounded-xl p-5 shadow-sm">
                      <div className="text-sm font-semibold text-[#0D1117] mb-3">Open defects by severity</div>
                      <SeverityBars data={metrics.open_by_severity} />
                    </div>
                  </div>

                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    <div className="bg-white border border-black/[0.08] rounded-xl p-5 shadow-sm">
                      <div className="text-sm font-semibold text-[#0D1117] mb-3">Platform health</div>
                      <PlatformHealthBars platforms={tree.platforms} />
                    </div>
                    <div className="bg-white border border-black/[0.08] rounded-xl p-5 shadow-sm">
                      <div className="text-sm font-semibold text-[#0D1117] mb-3">Open defects by owner</div>
                      <OwnerBars data={metrics.defects_by_owner} />
                    </div>
                  </div>
                </>
              );
            })()}

            <InsightsPanel />
          </>
        )}
      </div>
    </div>
  );
}
