"use client";

import {
  ResponsiveContainer, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
} from "recharts";
import type { TrendPoint } from "@/lib/types";

export default function TrendChart({ data }: { data: TrendPoint[] }) {
  if (!data.length) {
    return (
      <div className="h-64 flex items-center justify-center text-sm text-gray-400">
        No trend history yet — check back after tomorrow's upload.
      </div>
    );
  }

  return (
    <ResponsiveContainer width="100%" height={260}>
      <LineChart data={data} margin={{ top: 8, right: 16, bottom: 0, left: -16 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#F0F0F3" />
        <XAxis dataKey="date" tick={{ fontSize: 11, fill: "#9ca3af" }} />
        <YAxis tick={{ fontSize: 11, fill: "#9ca3af" }} allowDecimals={false} />
        <Tooltip
          contentStyle={{ fontSize: 12, borderRadius: 8, border: "1px solid #E5E7EB" }}
        />
        <Legend wrapperStyle={{ fontSize: 12 }} />
        <Line type="monotone" dataKey="open_defects" name="Open" stroke="#D4537E" strokeWidth={2} dot={false} />
        <Line type="monotone" dataKey="closed_defects" name="Closed" stroke="#00C9A7" strokeWidth={2} dot={false} />
      </LineChart>
    </ResponsiveContainer>
  );
}
