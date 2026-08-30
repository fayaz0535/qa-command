import type { Health } from "@/lib/types";

const COLOR: Record<Health, string> = {
  red: "#D4537E",
  amber: "#EF9F27",
  green: "#00C9A7",
};

export default function ProgressBar({
  pct, health, height = 8,
}: { pct: number; health?: Health; height?: number }) {
  const clamped = Math.max(0, Math.min(100, pct));
  const color = health ? COLOR[health] : "#5B5BF6";

  return (
    <div className="w-full bg-gray-100 rounded-full overflow-hidden" style={{ height }}>
      <div
        className="h-full rounded-full transition-all"
        style={{ width: `${clamped}%`, backgroundColor: color }}
      />
    </div>
  );
}
