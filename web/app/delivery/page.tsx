"use client";

import { useEffect, useState } from "react";
import { ChevronRight, ChevronDown } from "lucide-react";
import FilterBar from "@/components/FilterBar";
import RagBadge from "@/components/RagBadge";
import ProgressBar from "@/components/ProgressBar";
import ExportButton from "@/components/ExportButton";
import { useFilters } from "@/lib/FilterContext";
import { fetchMetrics } from "@/lib/api";
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

function SubModuleRow({ name, node }: { name: string; node: SubModuleNode }) {
  return (
    <div className="flex items-center justify-between py-2.5 pl-14 pr-4 border-b border-black/[0.04] last:border-0">
      <span className="text-sm text-gray-600">{name}</span>
      <MetricRow metrics={node.metrics} />
    </div>
  );
}

function ModuleRow({
  platformName, name, node, expanded, onToggle,
}: {
  platformName: string; name: string; node: ModuleNode; expanded: boolean; onToggle: () => void;
}) {
  const subEntries = Object.entries(node.sub_modules);
  return (
    <div className="border-b border-black/[0.04] last:border-0">
      <button
        onClick={onToggle}
        className="w-full flex items-center justify-between py-3 pl-8 pr-4 hover:bg-gray-50 text-left"
      >
        <span className="flex items-center gap-1.5 text-sm font-medium text-gray-700">
          {subEntries.length > 0 && (expanded ? <ChevronDown size={14} /> : <ChevronRight size={14} />)}
          {name}
        </span>
        <MetricRow metrics={node.metrics} />
      </button>
      {expanded && subEntries.map(([subName, subNode]) => (
        <SubModuleRow key={subName} name={subName} node={subNode} />
      ))}
    </div>
  );
}

export default function DeliveryPage() {
  const { filters } = useFilters();
  const [tree, setTree] = useState<MetricsTree | null>(null);
  const [loading, setLoading] = useState(true);
  const [expandedPlatforms, setExpandedPlatforms] = useState<Set<string>>(new Set());
  const [expandedModules, setExpandedModules] = useState<Set<string>>(new Set());

  useEffect(() => {
    setLoading(true);
    fetchMetrics(filters.owner).then(setTree).catch(() => setTree(null)).finally(() => setLoading(false));
  }, [filters.owner]);

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

        {loading || !tree ? (
          <div className="text-sm text-gray-400">Loading metrics…</div>
        ) : platformEntries.length === 0 ? (
          <div className="text-sm text-gray-400">No platforms match the current filters.</div>
        ) : (
          <div className="bg-white border border-black/[0.08] rounded-xl shadow-sm overflow-hidden">
            {platformEntries.map(([platformName, platformNode]) => {
              const isExpanded = expandedPlatforms.has(platformName) || filters.platform === platformName;
              const moduleEntries = Object.entries(platformNode.modules);
              return (
                <div key={platformName} className="border-b border-black/[0.06] last:border-0">
                  <button
                    onClick={() => togglePlatform(platformName)}
                    className="w-full flex items-center justify-between py-4 px-4 hover:bg-gray-50 text-left"
                  >
                    <span className="flex items-center gap-2 text-sm font-semibold text-[#0D1117]">
                      {moduleEntries.length > 0 && (isExpanded ? <ChevronDown size={16} /> : <ChevronRight size={16} />)}
                      {platformName}
                    </span>
                    <MetricRow metrics={platformNode.metrics} />
                  </button>
                  {isExpanded && moduleEntries.map(([moduleName, moduleNode]) => {
                    const key = `${platformName}::${moduleName}`;
                    return (
                      <ModuleRow
                        key={key}
                        platformName={platformName}
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
