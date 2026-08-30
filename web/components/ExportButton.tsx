"use client";

import { useState, useRef, useEffect } from "react";
import { Download, ChevronDown } from "lucide-react";
import { useFilters } from "@/lib/FilterContext";
import { exportUrl } from "@/lib/api";

const FORMATS: { format: "xlsx" | "pdf" | "csv"; label: string }[] = [
  { format: "xlsx", label: "Excel (.xlsx)" },
  { format: "pdf", label: "PDF" },
  { format: "csv", label: "CSV" },
];

export default function ExportButton({ kind = "defects" as "defects" | "tests" }: { kind?: "defects" | "tests" }) {
  const { filters } = useFilters();
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const onClick = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener("click", onClick);
    return () => document.removeEventListener("click", onClick);
  }, []);

  return (
    <div className="relative" ref={ref}>
      <button
        onClick={() => setOpen((o) => !o)}
        className="flex items-center gap-1.5 text-sm border border-black/10 rounded-md px-3 py-1.5
                   bg-white text-gray-700 hover:bg-gray-50"
      >
        <Download size={14} /> Export {kind} <ChevronDown size={14} />
      </button>
      {open && (
        <div className="absolute right-0 mt-1 w-44 bg-white border border-black/10 rounded-md shadow-md z-20 py-1">
          {FORMATS.map(({ format, label }) => (
            <a
              key={format}
              href={exportUrl(kind, format, filters)}
              className="block px-3 py-1.5 text-sm text-gray-700 hover:bg-gray-50"
              onClick={() => setOpen(false)}
            >
              {label}
            </a>
          ))}
        </div>
      )}
    </div>
  );
}
