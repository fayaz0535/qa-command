import Link from "next/link";
import RagBadge from "./RagBadge";
import ProgressBar from "./ProgressBar";
import { displayHierarchyName } from "@/lib/hierarchyLabels";
import type { PlatformNode } from "@/lib/types";

export default function PlatformHealthBars({ platforms }: { platforms: Record<string, PlatformNode> }) {
  const entries = Object.entries(platforms);

  if (!entries.length) {
    return <div className="text-sm text-gray-400">No platforms yet — upload a CSV to get started.</div>;
  }

  return (
    <div className="space-y-3">
      {entries.map(([name, p]) => (
        <Link
          key={name}
          href="/delivery"
          className="flex items-center gap-4 group"
        >
          <span className="w-32 text-sm text-gray-700 shrink-0 group-hover:text-qc-primary truncate">
            {displayHierarchyName(name)}
          </span>
          <div className="flex-1">
            <ProgressBar pct={p.metrics.execution_pct} health={p.metrics.health} />
          </div>
          <span className="w-12 text-xs text-gray-500 text-right shrink-0">{p.metrics.execution_pct}%</span>
          <RagBadge health={p.metrics.health} />
        </Link>
      ))}
    </div>
  );
}
