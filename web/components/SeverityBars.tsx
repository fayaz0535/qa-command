const SEVERITY_COLOR: Record<string, string> = {
  Critical: "#EF4444",
  High: "#F59E0B",
  Medium: "#3B82F6",
  Low: "#94A3B8",
  TBC: "#CBD5E1",
};

const ORDER = ["Critical", "High", "Medium", "Low", "TBC"];

export default function SeverityBars({ data }: { data: Record<string, number> }) {
  const max = Math.max(1, ...Object.values(data));

  return (
    <div className="space-y-2.5">
      {ORDER.filter((sev) => data[sev] !== undefined).map((sev) => (
        <div key={sev} className="flex items-center gap-3">
          <span className="w-16 text-xs text-gray-500 shrink-0">{sev}</span>
          <div className="flex-1 bg-gray-100 rounded-full h-3 overflow-hidden">
            <div
              className="h-full rounded-full"
              style={{ width: `${(data[sev] / max) * 100}%`, backgroundColor: SEVERITY_COLOR[sev] }}
            />
          </div>
          <span className="w-6 text-xs text-gray-700 text-right shrink-0">{data[sev]}</span>
        </div>
      ))}
    </div>
  );
}
