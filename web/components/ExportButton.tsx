"use client";

import { useState, useRef, useEffect } from "react";
import { Download, ChevronDown, Loader2 } from "lucide-react";
import { useFilters } from "@/lib/FilterContext";
import { fetchExportBlob } from "@/lib/api";
import { createAbortTimeout, describeError } from "@/lib/timedAction";

const EXPORT_TIMEOUT_MS = 45000;

const FORMATS: { format: "xlsx" | "pdf" | "csv"; label: string }[] = [
  { format: "xlsx", label: "Excel (.xlsx)" },
  { format: "pdf", label: "PDF" },
  { format: "csv", label: "CSV" },
];

export default function ExportButton({ kind = "defects" as "defects" | "tests" }: { kind?: "defects" | "tests" }) {
  const { filters } = useFilters();
  const [open, setOpen] = useState(false);
  const [pending, setPending] = useState<"xlsx" | "pdf" | "csv" | null>(null);
  const [error, setError] = useState<string | null>(null);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const onClick = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) { setOpen(false); }
    };
    document.addEventListener("click", onClick);
    return () => document.removeEventListener("click", onClick);
  }, []);

  const handleExport = async (format: "xlsx" | "pdf" | "csv") => {
    setPending(format);
    setError(null);
    const { signal, clear } = createAbortTimeout(EXPORT_TIMEOUT_MS);
    try {
      const blob = await fetchExportBlob(kind, format, filters, signal);
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `qa-command-${kind}.${format}`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
      setOpen(false);
    } catch (e) {
      setError(describeError(e, "Export is taking longer than expected — retry?"));
    } finally {
      clear();
      setPending(null);
    }
  };

  return (
    <div className="relative" ref={ref}>
      <button
        onClick={() => setOpen((o) => !o)}
        disabled={pending !== null}
        className="flex items-center gap-1.5 text-sm border border-black/10 rounded-md px-3 py-1.5
                   bg-white text-gray-700 hover:bg-gray-50 disabled:opacity-50"
      >
        {pending ? <Loader2 size={14} className="animate-spin" /> : <Download size={14} />}
        {pending ? `Preparing ${pending}…` : `Export ${kind}`}
        <ChevronDown size={14} />
      </button>
      {open && (
        <div className="absolute right-0 mt-1 w-52 bg-white border border-black/10 rounded-md shadow-md z-20 py-1">
          {FORMATS.map(({ format, label }) => (
            <button
              key={format}
              onClick={() => handleExport(format)}
              disabled={pending !== null}
              className="w-full flex items-center justify-between px-3 py-1.5 text-sm text-gray-700
                         hover:bg-gray-50 disabled:opacity-50 text-left"
            >
              {label}
              {pending === format && <Loader2 size={12} className="animate-spin" />}
            </button>
          ))}
          {error && (
            <div className="px-3 py-2 text-xs text-red-500 border-t border-black/[0.06]">
              {error}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
