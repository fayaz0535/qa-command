import type { Health } from "@/lib/types";

const STYLES: Record<Health, string> = {
  red: "bg-red-50 text-red-600 border-red-200",
  amber: "bg-amber-50 text-amber-600 border-amber-200",
  green: "bg-emerald-50 text-emerald-600 border-emerald-200",
};

const DOT: Record<Health, string> = {
  red: "bg-red-500",
  amber: "bg-amber-500",
  green: "bg-emerald-500",
};

export default function RagBadge({ health, label }: { health: Health; label?: string }) {
  return (
    <span
      className={`inline-flex items-center gap-1.5 text-xs font-medium px-2 py-0.5 rounded-full border ${STYLES[health]}`}
    >
      <span className={`w-1.5 h-1.5 rounded-full ${DOT[health]}`} />
      {label || health.toUpperCase()}
    </span>
  );
}
