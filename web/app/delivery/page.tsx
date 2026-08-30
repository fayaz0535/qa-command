"use client";

import { useEffect, useState } from "react";
import { ChevronRight, ChevronDown } from "lucide-react";
import FilterBar from "@/components/FilterBar";
import RagBadge from "@/components/RagBadge";
import ProgressBar from "@/components/ProgressBar";
import ExportButton from "@/components/ExportButton";
import ErrorState from "@/components/ErrorState";
import { useFilters } from "@/lib/FilterContext";
import { fetchMetrics } from "@/lib/api";
import { displayHierarchyName } from "@/lib/hierarchyLabels";
import type { MetricsTree, NodeMetrics, ModuleNode, SubModuleNode } from "@/lib/types";

function MetricRow({ metrics }: { metrics: NodeMetrics }) {
  return (
    <div className="flex items-center gap-6 shrink-0">
      <div className="w-32">
        <ProgressBar pct={metrics.execution_pct} health={metrics.health} />
      </div>
      <span className="text-xs text-gray-500 w-16">{metrics.execution_pct}% exec</span>
      <span className="text-xs text-gray-500 w-16">{metrics.pass_rate}% pass</span>
      <span className="text-xs text-gray-500 w-20">{metrics.open_defects} open</span>
      <span className="text-xs text-gray-500 w-32">
        &gt;7d {metrics.aging_gt7} · &gt;14d {metrics.aging_gt14} · &gt;21d {metrics.aging_gt21}
      </span>
      <RagBadge health={metrics.health} />
    </div>
  );
}

function NoBreakdownNote({ text }: { text: string }) {
  return (
    <div className="py-2.5 pl-14 pr-4 text-xs text-gray-400 italic border-b border-black/[0.04] last:border-0">
      {text}
    </div>
  );
}

function SubModuleRow({ name, node }: { name: string; node: SubModuleNode }) {
  return (
    <div className="flex items-center justify-between py-2.5 pl-14 pr-4 border-b border-black/[0.04] last:border-0">
      <span className="text-sm text-gray-600">{displayHierarchyName(name)}</span>
      <MetricRow metrics={node.metrics} />
    </div>
  );
}

function ModuleRow({
  name, node, expanded, onToggle,
}: {
  name: string; node: ModuleNode; expanded: boolean; onToggle: () => void;
}) {
  const subEntries = Object.entries(node.sub_modules);
  const hasSubModules = subEntries.length > 0;

  return (
    <div className="border-b border-black/[0.04] last:border-0">
      <button
        onClick={onToggle}
        disabled={!hasSubModules}
        className={`w-full flex items-center justify-between py-3 pl-8 pr-4 text-left ${
          hasSubModules ? "hover:bg-gray-50" : "cursor-default"
        }`}
      >
        <span className="flex items-center gap-1.5 text-sm font-medium text-gray-700">
          {hasSubModules && (expanded ? <ChevronDown size={14} /> : <ChevronRight size={14} />)}
          {displayHierarchyName(name)}
        </span>
        <MetricRow metrics={node.metrics} />
      </button>
      {!hasSubModules && <NoBreakdownNote text="No sub-module breakdown — defects tracked at module level." />}
      {hasSubModules && expanded && subEntries.map(([subName, subNode]) => (
        <SubModuleRow key={subName} name={subName} node={subNode} />
      ))}
    </div>
  );
}

export default function DeliveryPage() {
  const { filters } = useFilters();
  const [tree, setTree] = useState<MetricsTree | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expandedPlatforms, setExpandedPlatforms] = useState<Set<string>>(new Set());
  const [expandedModules, setExpandedModules] = useState<Set<string>>(new Set());

  const loadMetrics = () => {
    setLoading(true);
    setError(null);
    fetchMetrics(filters.owner)
      .then(setTree)
      .catch((e) => setError(e.message || "Failed to load metrics"))
      .finally(() => setLoading(false));
  };

  useEffect(loadMetrics, [filters.owner]);

  const togglePlatform = (name: string) => {
    setExpandedPlatforms((prev) => {
      const next = new Set(prev);
      next.has(name) ? next.delete(name) : next.add(name);
      return next;
    });
  };

  const toggleModule = (key: string) => {
    setExpandedModules((prev) => {
      const next = new Set(prev);
      next.has(key) ? next.delete(key) : next.add(key);
      return next;
    });
  };

  // tree.platforms may legitimately be {} for a brand-new empty install, but every
  // key it DOES have must render — a platform with no module breakdown is still a
  // real platform with real metrics, not something to filter out.
  const platformEntries = tree
    ? Object.entries(tree.platforms).filter(([name]) => !filters.platform || name === filters.platform)
    : [];

  return (
    <div>
      <FilterBar />
      <div className="p-6 space-y-4">
        <div className="flex items-center justify-between">
          <h1 className="text-lg font-semibold text-[#0D1117]">Delivery Drill-down</h1>
          <div className="flex gap-2">
            <ExportButton kind="defects" />
            <ExportButton kind="tests" />
          </div>
        </div>
        <p className="text-xs text-gray-400">Platform › Module › Sub-module — click a row to expand.</p>

        {error ? (
          <ErrorState message={error} onRetry={loadMetrics} />
        ) : loading || !tree ? (
          <div className="text-sm text-gray-400">Loading metrics…</div>
        ) : platformEntries.length === 0 ? (
          <div className="text-sm text-gray-400">No platforms match the current filters.</div>
        ) : (
          <div className="bg-white border border-black/[0.08] rounded-xl shadow-sm overflow-hidden">
            {platformEntries.map(([platformName, platformNode]) => {
              const isExpanded = expandedPlatforms.has(platformName) || filters.platform === platformName;
              const moduleEntries = Object.entries(platformNode.modules || {});
              const hasModules = moduleEntries.length > 0;

              return (
                <div key={platformName} className="border-b border-black/[0.06] last:border-0">
                  <button
                    onClick={() => togglePlatform(platformName)}
                    disabled={!hasModules}
                    className={`w-full flex items-center justify-between py-4 px-4 text-left ${
                      hasModules ? "hover:bg-gray-50" : "cursor-default"
                    }`}
                  >
                    <span className="flex items-center gap-2 text-sm font-semibold text-[#0D1117]">
                      {hasModules && (isExpanded ? <ChevronDown size={16} /> : <ChevronRight size={16} />)}
                      {displayHierarchyName(platformName)}
                    </span>
                    <MetricRow metrics={platformNode.metrics} />
                  </button>
                  {!hasModules && (
                    <NoBreakdownNote text="No module breakdown — defects tracked at platform level." />
                  )}
                  {hasModules && isExpanded && moduleEntries.map(([moduleName, moduleNode]) => {
                    const key = `${platformName}::${moduleName}`;
                    return (
                      <ModuleRow
                        key={key}
                        name={moduleName}
                        node={moduleNode}
                        expanded={expandedModules.has(key) ||
                          (filters.platform === platformName && filters.module === moduleName)}
                        onToggle={() => toggleModule(key)}
                      />
                    );
                  })}
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
