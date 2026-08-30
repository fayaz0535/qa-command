"use client";

import { useEffect, useState } from "react";
import { Loader2, RefreshCw, Save, AlertTriangle, Eye } from "lucide-react";
import {
  fetchAreaPaths, overrideAreaPath, fetchMappingRule, updateMappingRule,
  previewMappingRule, discoverAdoPaths,
} from "@/lib/api";
import { createAbortTimeout, describeError } from "@/lib/timedAction";
import ErrorState from "@/components/ErrorState";
import type { AreaPathMapping, AreaPathMappingRule, AreaPathPreviewRow } from "@/lib/types";

const ACTION_TIMEOUT_MS = 45000;

function RuleField({ label, value, onChange }: { label: string; value: number; onChange: (v: number) => void }) {
  return (
    <label className="text-xs text-gray-500">
      {label}
      <input
        type="number"
        min={0}
        value={value}
        onChange={(e) => onChange(Math.max(0, parseInt(e.target.value, 10) || 0))}
        className="mt-1 w-full border border-black/10 rounded-md px-2.5 py-1.5 text-sm text-gray-700"
      />
    </label>
  );
}

function EditableRow({ row, onSaved }: { row: AreaPathMapping; onSaved: (r: AreaPathMapping) => void }) {
  const [platform, setPlatform] = useState(row.platform || "");
  const [module, setModule] = useState(row.module || "");
  const [subModule, setSubModule] = useState(row.sub_module || "");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const save = async () => {
    setSaving(true);
    setError(null);
    try {
      const updated = await overrideAreaPath(row.id, platform || null, module || null, subModule || null);
      onSaved(updated);
    } catch (e) {
      setError(describeError(e, "Save timed out — retry?"));
    } finally {
      setSaving(false);
    }
  };

  return (
    <tr className={`border-b border-black/[0.04] last:border-0 ${row.needs_review ? "bg-amber-50/40" : ""}`}>
      <td className="px-4 py-2.5 text-xs text-gray-600 font-mono max-w-[260px] truncate" title={row.area_path}>
        {row.area_path}
      </td>
      <td className="px-2 py-2">
        <input value={platform} onChange={(e) => setPlatform(e.target.value)}
               className="w-full border border-black/10 rounded px-2 py-1 text-xs" />
      </td>
      <td className="px-2 py-2">
        <input value={module} onChange={(e) => setModule(e.target.value)}
               className="w-full border border-black/10 rounded px-2 py-1 text-xs" />
      </td>
      <td className="px-2 py-2">
        <input value={subModule} onChange={(e) => setSubModule(e.target.value)}
               className="w-full border border-black/10 rounded px-2 py-1 text-xs" />
      </td>
      <td className="px-2 py-2 text-center">
        {row.needs_review && !row.is_override && (
          <span title="Needs review"><AlertTriangle size={13} className="text-amber-500 inline" /></span>
        )}
        {row.is_override && <span className="text-[10px] text-qc-primary font-medium">override</span>}
      </td>
      <td className="px-2 py-2">
        <button onClick={save} disabled={saving}
                className="flex items-center gap-1 text-xs text-qc-primary hover:underline disabled:opacity-50">
          {saving ? <Loader2 size={12} className="animate-spin" /> : <Save size={12} />}
          Save
        </button>
        {error && <div className="text-[10px] text-red-500 mt-0.5">{error}</div>}
      </td>
    </tr>
  );
}

export default function AreaMappingPage() {
  const [rows, setRows] = useState<AreaPathMapping[]>([]);
  const [needsReviewCount, setNeedsReviewCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);

  const [rule, setRule] = useState<AreaPathMappingRule>({ drop_root_segments: 1, platform_segments: 1, module_segments: 1 });
  const [preview, setPreview] = useState<AreaPathPreviewRow[] | null>(null);
  const [previewing, setPreviewing] = useState(false);
  const [applying, setApplying] = useState(false);
  const [ruleError, setRuleError] = useState<string | null>(null);

  const [discovering, setDiscovering] = useState(false);
  const [discoverError, setDiscoverError] = useState<string | null>(null);
  const [discoverResult, setDiscoverResult] = useState<string | null>(null);

  const loadAll = () => {
    setLoading(true);
    setLoadError(null);
    Promise.all([fetchAreaPaths(), fetchMappingRule()])
      .then(([paths, r]) => {
        setRows(paths.area_paths);
        setNeedsReviewCount(paths.needs_review_count);
        setRule(r);
      })
      .catch((e) => setLoadError(describeError(e, "Failed to load")))
      .finally(() => setLoading(false));
  };

  useEffect(loadAll, []);

  const handleDiscover = async () => {
    setDiscovering(true);
    setDiscoverError(null);
    setDiscoverResult(null);
    const { signal, clear } = createAbortTimeout(ACTION_TIMEOUT_MS);
    try {
      const res = await discoverAdoPaths(signal);
      setDiscoverResult(`${res.fetched} work items scanned · ${res.new_paths} new path(s) found (${res.total_paths} total).`);
      loadAll();
    } catch (e) {
      setDiscoverError(describeError(e, "Discovery timed out — retry?"));
    } finally {
      clear();
      setDiscovering(false);
    }
  };

  const handlePreview = async () => {
    setPreviewing(true);
    setRuleError(null);
    try {
      const res = await previewMappingRule(rule);
      setPreview(res.preview);
    } catch (e) {
      setRuleError(describeError(e, "Preview timed out — retry?"));
    } finally {
      setPreviewing(false);
    }
  };

  const handleApply = async () => {
    setApplying(true);
    setRuleError(null);
    try {
      await updateMappingRule(rule);
      setPreview(null);
      loadAll();
    } catch (e) {
      setRuleError(describeError(e, "Apply timed out — retry?"));
    } finally {
      setApplying(false);
    }
  };

  return (
    <div className="p-6 max-w-4xl mx-auto space-y-5">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-lg font-semibold text-[#0D1117]">Area Path Mapping</h1>
          <p className="text-sm text-gray-500 mt-1">
            ADO Area Paths are the only source of Platform/Module/Sub-module — unmapped paths are
            flagged, never guessed.
          </p>
        </div>
        <button
          onClick={handleDiscover}
          disabled={discovering}
          className="flex items-center gap-1.5 text-sm border border-black/10 rounded-md px-3 py-1.5
                     bg-white text-gray-700 hover:bg-gray-50 disabled:opacity-50 shrink-0"
        >
          {discovering ? <Loader2 size={14} className="animate-spin" /> : <RefreshCw size={14} />}
          {discovering ? "Scanning ADO…" : "Discover paths"}
        </button>
      </div>

      {discoverError && <ErrorState message={discoverError} onRetry={handleDiscover} />}
      {discoverResult && <div className="text-sm text-emerald-700 bg-emerald-50 rounded-lg px-3 py-2">{discoverResult}</div>}

      <div className="bg-white border border-black/[0.08] rounded-xl p-5 shadow-sm space-y-3">
        <div className="text-sm font-semibold text-[#0D1117]">Default rule</div>
        <p className="text-xs text-gray-400">
          E.g. "EIB\FCCM\Alerts\Sanctions" with drop 1 / platform 1 / module 1 segments →
          Platform=FCCM, Module=Alerts, Sub-module=Sanctions. A path with too few segments to fill
          Platform+Module is flagged for review instead of guessed. Per-path overrides below always win.
        </p>
        <div className="grid grid-cols-3 gap-3">
          <RuleField label="Drop root segments" value={rule.drop_root_segments}
                     onChange={(v) => setRule((r) => ({ ...r, drop_root_segments: v }))} />
          <RuleField label="Platform segments" value={rule.platform_segments}
                     onChange={(v) => setRule((r) => ({ ...r, platform_segments: v }))} />
          <RuleField label="Module segments" value={rule.module_segments}
                     onChange={(v) => setRule((r) => ({ ...r, module_segments: v }))} />
        </div>
        {ruleError && <div className="text-sm text-red-500">{ruleError}</div>}
        <div className="flex gap-2">
          <button
            onClick={handlePreview}
            disabled={previewing}
            className="flex items-center gap-1.5 text-sm border border-black/10 rounded-md px-3 py-1.5
                       bg-white text-gray-700 hover:bg-gray-50 disabled:opacity-50"
          >
            {previewing ? <Loader2 size={14} className="animate-spin" /> : <Eye size={14} />}
            Preview
          </button>
          <button
            onClick={handleApply}
            disabled={applying}
            className="flex items-center gap-1.5 bg-qc-primary text-white text-sm font-medium px-4 py-1.5
                       rounded-md hover:bg-qc-primary-hover disabled:opacity-50"
          >
            {applying && <Loader2 size={14} className="animate-spin" />}
            {applying ? "Applying…" : "Apply rule"}
          </button>
        </div>

        {preview && (
          <div className="mt-3 border border-black/[0.08] rounded-lg overflow-hidden max-h-64 overflow-y-auto">
            <table className="w-full text-xs">
              <thead className="bg-gray-50 sticky top-0">
                <tr>
                  <th className="px-3 py-1.5 text-left font-medium text-gray-500">Area Path</th>
                  <th className="px-3 py-1.5 text-left font-medium text-gray-500">Platform</th>
                  <th className="px-3 py-1.5 text-left font-medium text-gray-500">Module</th>
                  <th className="px-3 py-1.5 text-left font-medium text-gray-500">Sub-module</th>
                </tr>
              </thead>
              <tbody>
                {preview.map((p) => (
                  <tr key={p.area_path} className={p.needs_review ? "bg-amber-50/40" : ""}>
                    <td className="px-3 py-1.5 font-mono truncate max-w-[200px]" title={p.area_path}>{p.area_path}</td>
                    <td className="px-3 py-1.5">{p.platform || "—"}</td>
                    <td className="px-3 py-1.5">{p.module || "—"}</td>
                    <td className="px-3 py-1.5">{p.sub_module || "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      <div className="bg-white border border-black/[0.08] rounded-xl shadow-sm overflow-hidden">
        <div className="px-4 py-2.5 border-b border-black/[0.08] text-xs text-gray-500 flex items-center justify-between">
          <span>{rows.length} known area path(s)</span>
          {needsReviewCount > 0 && (
            <span className="flex items-center gap-1 text-amber-600">
              <AlertTriangle size={12} /> {needsReviewCount} need review
            </span>
          )}
        </div>
        {loading ? (
          <div className="p-6 text-sm text-gray-400">Loading…</div>
        ) : loadError ? (
          <div className="p-4"><ErrorState message={loadError} onRetry={loadAll} /></div>
        ) : rows.length === 0 ? (
          <div className="p-6 text-sm text-gray-400">
            No area paths discovered yet — click "Discover paths" or run a sync from the ADO Connection page.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-xs text-gray-400 uppercase border-b border-black/[0.08]">
                  <th className="px-4 py-2 font-medium">Area Path</th>
                  <th className="px-2 py-2 font-medium">Platform</th>
                  <th className="px-2 py-2 font-medium">Module</th>
                  <th className="px-2 py-2 font-medium">Sub-module</th>
                  <th className="px-2 py-2 font-medium"></th>
                  <th className="px-2 py-2 font-medium"></th>
                </tr>
              </thead>
              <tbody>
                {rows.map((row) => (
                  <EditableRow
                    key={row.id}
                    row={row}
                    onSaved={(updated) => setRows((prev) => prev.map((r) => (r.id === updated.id ? updated : r)))}
                  />
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
