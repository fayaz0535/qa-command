"use client";

import { createContext, useContext, useMemo, useState, ReactNode } from "react";
import type { Filters } from "./types";

interface FilterContextValue {
  filters: Filters;
  setFilter: (key: keyof Filters, value: string | undefined) => void;
  clearFilters: () => void;
}

const FilterContext = createContext<FilterContextValue | null>(null);

export function FilterProvider({ children }: { children: ReactNode }) {
  const [filters, setFilters] = useState<Filters>({});

  const setFilter = (key: keyof Filters, value: string | undefined) => {
    setFilters((prev) => {
      const next = { ...prev, [key]: value || undefined };
      // Clearing a higher level in the hierarchy clears anything nested under it.
      if (key === "platform") {
        next.module = undefined;
        next.sub_module = undefined;
      }
      if (key === "module") {
        next.sub_module = undefined;
      }
      return next;
    });
  };

  const clearFilters = () => setFilters({});

  const value = useMemo(() => ({ filters, setFilter, clearFilters }), [filters]);

  return <FilterContext.Provider value={value}>{children}</FilterContext.Provider>;
}

export function useFilters(): FilterContextValue {
  const ctx = useContext(FilterContext);
  if (!ctx) throw new Error("useFilters must be used within a FilterProvider");
  return ctx;
}
