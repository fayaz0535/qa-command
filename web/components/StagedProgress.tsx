import { Loader2, CheckCircle2 } from "lucide-react";

export default function StagedProgress({ stages, currentIndex }: { stages: string[]; currentIndex: number }) {
  return (
    <div className="space-y-2.5">
      {stages.map((label, i) => {
        const isFinal = i === stages.length - 1;
        const done = i < currentIndex || (isFinal && i === currentIndex);
        const active = i === currentIndex && !isFinal;
        return (
          <div key={label} className="flex items-center gap-2.5">
            {done ? (
              <CheckCircle2 size={16} className="text-qc-accent shrink-0" />
            ) : active ? (
              <Loader2 size={16} className="text-qc-primary animate-spin shrink-0" />
            ) : (
              <div className="w-4 h-4 rounded-full border-2 border-gray-200 shrink-0" />
            )}
            <span
              className={`text-sm ${
                done ? "text-gray-400" : active ? "text-[#0D1117] font-medium" : "text-gray-300"
              }`}
            >
              {label}
            </span>
          </div>
        );
      })}
    </div>
  );
}
