"use client";

import { useEffect, useState } from "react";
import { Sparkles, RefreshCw, TrendingUp, AlertTriangle, Target } from "lucide-react";
import { fetchInsights } from "@/lib/api";
import type { Insight } from "@/lib/types";

export default function InsightsPanel() {
  const [insight, setInsight] = useState<Insight | null>(null);
  const [loading, setLoading] = useState(true);

  const load = (force = false) => {
    setLoading(true);
    fetchInsights(force)
      .then(setInsight)
      .catch(() => setInsight(null))
      .finally(() => setLoading(false));
  };

  useEffect(() => { load(); }, []);

  return (
    <div className="bg-white border border-black/[0.08] rounded-xl p-5 shadow-sm">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Sparkles size={16} className="text-qc-primary" />
          <span className="text-sm font-semibold text-[#0D1117]">AI Insights</span>
          {insight?.generated_at && (
            <span className="text-xs text-gray-400">· {insight.generated_at}</span>
          )}
        </div>
        <button
          onClick={() => load(true)}
          disabled={loading}
          className="flex items-center gap-1 text-xs text-gray-500 hover:text-qc-primary disabled:opacity-50"
        >
          <RefreshCw size={12} className={loading ? "animate-spin" : ""} /> Regenerate
        </button>
      </div>

      {loading && !insight ? (
        <div className="text-sm text-gray-400">Generating today's insight…</div>
      ) : (
        <div className="space-y-3">
          <Row icon={<TrendingUp size={14} className="text-qc-accent" />} label="Progress"
               text={insight?.progress || "—"} />
          <Row icon={<AlertTriangle size={14} className="text-amber-500" />} label="Risk"
               text={insight?.risk || "—"} />
          <Row icon={<Target size={14} className="text-qc-primary" />} label="Ask"
               text={insight?.ask || "—"} />
        </div>
      )}
    </div>
  );
}

function Row({ icon, label, text }: { icon: React.ReactNode; label: string; text: string }) {
  return (
    <div className="flex gap-3">
      <div className="mt-0.5 shrink-0">{icon}</div>
      <div>
        <div className="text-xs font-medium text-gray-400 uppercase tracking-wide">{label}</div>
        <div className="text-sm text-[#0D1117] mt-0.5 leading-relaxed">{text}</div>
      </div>
    </div>
  );
}
