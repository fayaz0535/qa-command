import { ArrowUp, ArrowDown, Minus } from "lucide-react";

export type TrendDirection = "up" | "down" | "flat";

interface KpiCardProps {
  label: string;
  value: string;
  target?: string;
  trend?: TrendDirection;
  trendIsGood?: boolean; // whether the trend direction is a good sign for this metric
  sub?: string;
}

export default function KpiCard({ label, value, target, trend, trendIsGood, sub }: KpiCardProps) {
  const TrendIcon = trend === "up" ? ArrowUp : trend === "down" ? ArrowDown : Minus;
  const trendColor =
    trend === "flat" || trend === undefined
      ? "text-gray-400"
      : trendIsGood
      ? "text-emerald-600"
      : "text-red-500";

  return (
    <div className="bg-white border border-black/[0.08] rounded-xl p-4 shadow-sm">
      <div className="text-xs font-medium text-gray-500 uppercase tracking-wide">{label}</div>
      <div className="flex items-end gap-2 mt-1.5">
        <span className="text-2xl font-bold text-[#0D1117]">{value}</span>
        {trend && (
          <span className={`flex items-center gap-0.5 text-xs font-medium mb-1 ${trendColor}`}>
            <TrendIcon size={12} />
          </span>
        )}
      </div>
      <div className="text-xs text-gray-400 mt-1">
        {target && <span>Target {target}</span>}
        {target && sub && <span> · </span>}
        {sub && <span>{sub}</span>}
      </div>
    </div>
  );
}
