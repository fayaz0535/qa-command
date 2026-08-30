import type { MetricsTree, NodeMetrics, Filters } from "./types";
import { displayHierarchyName } from "./hierarchyLabels";

/** Picks the most specific node's metrics for the current platform/module/sub_module
 * filter — the tree already has every level pre-computed, so no extra API call needed. */
export function selectNodeMetrics(tree: MetricsTree, filters: Filters): { label: string; metrics: NodeMetrics } {
  if (filters.platform) {
    const p = tree.platforms[filters.platform];
    const platformLabel = displayHierarchyName(filters.platform);
    if (!p) return { label: "Overall", metrics: tree.metrics };
    if (filters.module) {
      const m = p.modules[filters.module];
      const moduleLabel = displayHierarchyName(filters.module);
      if (!m) return { label: platformLabel, metrics: p.metrics };
      if (filters.sub_module) {
        const s = m.sub_modules[filters.sub_module];
        const subLabel = displayHierarchyName(filters.sub_module);
        if (!s) return { label: `${platformLabel} › ${moduleLabel}`, metrics: m.metrics };
        return { label: `${platformLabel} › ${moduleLabel} › ${subLabel}`, metrics: s.metrics };
      }
      return { label: `${platformLabel} › ${moduleLabel}`, metrics: m.metrics };
    }
    return { label: platformLabel, metrics: p.metrics };
  }
  return { label: "Overall", metrics: tree.metrics };
}

/** Maps the current platform/module/sub_module filter to the trend endpoint's
 * level + node params — mirrors selectNodeMetrics' specificity logic. */
export function trendParamsFromFilters(filters: Filters) {
  if (filters.sub_module && filters.platform && filters.module) {
    return { level: "sub_module", platform: filters.platform, module: filters.module, sub_module: filters.sub_module };
  }
  if (filters.module && filters.platform) {
    return { level: "module", platform: filters.platform, module: filters.module };
  }
  if (filters.platform) {
    return { level: "platform", platform: filters.platform };
  }
  return { level: "overall" };
}
