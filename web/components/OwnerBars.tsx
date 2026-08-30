import Link from "next/link";

export default function OwnerBars({ data }: { data: Record<string, number> }) {
  const entries = Object.entries(data).sort((a, b) => b[1] - a[1]);
  const max = Math.max(1, ...entries.map(([, v]) => v));

  if (!entries.length) {
    return <div className="text-sm text-gray-400">No open defects assigned yet.</div>;
  }

  return (
    <div className="space-y-2.5">
      {entries.map(([owner, count]) => {
        const needsReview = owner.toLowerCase().includes("review");
        return (
          <Link
            key={owner}
            href={needsReview ? "#" : "/owners"}
            className="flex items-center gap-3 group"
          >
            <span
              className={`w-40 text-xs shrink-0 truncate ${
                needsReview ? "text-amber-600" : "text-gray-600 group-hover:text-qc-primary"
              }`}
            >
              {owner}
            </span>
            <div className="flex-1 bg-gray-100 rounded-full h-3 overflow-hidden">
              <div
                className="h-full rounded-full"
                style={{
                  width: `${(count / max) * 100}%`,
                  backgroundColor: needsReview ? "#EF9F27" : "#5B5BF6",
                }}
              />
            </div>
            <span className="w-6 text-xs text-gray-700 text-right shrink-0">{count}</span>
          </Link>
        );
      })}
    </div>
  );
}
