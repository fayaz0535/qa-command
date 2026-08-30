"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { CheckCircle2, XCircle, Loader2, RefreshCw, ShieldCheck } from "lucide-react";
import {
  fetchAdoConnection, testAdoConnection, saveAdoConnection,
} from "@/lib/api";
import { createAbortTimeout, describeError } from "@/lib/timedAction";
import { useAdoSync, SYNC_STAGES } from "@/lib/useAdoSync";
import StagedProgress from "@/components/StagedProgress";
import ErrorState from "@/components/ErrorState";
import { DEFAULT_ADO_WIQL } from "@/lib/constants";
import type { AdoConnection } from "@/lib/types";

const CONNECT_TIMEOUT_MS = 30000;

export default function AdoSettingsPage() {
  const [connection, setConnection] = useState<AdoConnection | null>(null);
  const [loading, setLoading] = useState(true);

  const [orgUrl, setOrgUrl] = useState("");
  const [project, setProject] = useState("");
  const [pat, setPat] = useState("");
  const [wiqlQuery, setWiqlQuery] = useState("");

  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState<{ ok: boolean; message: string } | null>(null);

  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);

  const sync = useAdoSync();

  const loadConnection = () => {
    setLoading(true);
    fetchAdoConnection()
      .then((c) => {
        setConnection(c);
        if (c.connected) {
          setOrgUrl(c.org_url || "");
          setProject(c.project || "");
          setWiqlQuery(c.wiql_query || DEFAULT_ADO_WIQL);
        } else {
          setWiqlQuery(DEFAULT_ADO_WIQL);
        }
      })
      .catch(() => setConnection({ connected: false }))
      .finally(() => setLoading(false));
  };

  useEffect(loadConnection, []);

  const handleTest = async () => {
    if (!orgUrl || !project || !pat) {
      setTestResult({ ok: false, message: "Organization URL, project, and PAT are all required to test." });
      return;
    }
    setTesting(true);
    setTestResult(null);
    const { signal, clear } = createAbortTimeout(CONNECT_TIMEOUT_MS);
    try {
      const res = await testAdoConnection(orgUrl, project, pat, signal);
      setTestResult(res.ok
        ? { ok: true, message: `Connected — project "${res.project_name || project}" found.` }
        : { ok: false, message: res.error || "Connection test failed." });
    } catch (e) {
      setTestResult({ ok: false, message: describeError(e, "Test timed out — check the org URL and retry.") });
    } finally {
      clear();
      setTesting(false);
    }
  };

  const handleSave = async () => {
    if (!orgUrl || !project || !pat) {
      setSaveError("Organization URL, project, and PAT are all required to save.");
      return;
    }
    setSaving(true);
    setSaveError(null);
    const { signal, clear } = createAbortTimeout(CONNECT_TIMEOUT_MS);
    try {
      const saved = await saveAdoConnection(orgUrl, project, pat, wiqlQuery || null, signal);
      setConnection(saved);
      setPat(""); // never keep the plaintext PAT in memory longer than the save call needs it
      setTestResult(null);
    } catch (e) {
      setSaveError(describeError(e, "Save timed out — retry?"));
    } finally {
      clear();
      setSaving(false);
    }
  };

  if (loading) {
    return <div className="p-6 text-sm text-gray-400">Loading connection…</div>;
  }

  return (
    <div className="p-6 max-w-2xl mx-auto space-y-5">
      <div>
        <h1 className="text-lg font-semibold text-[#0D1117]">Azure DevOps Connection</h1>
        <p className="text-sm text-gray-500 mt-1">
          The Personal Access Token is encrypted at rest and never shown again once saved — only
          a masked placeholder. All ADO calls happen server-side; the browser only ever sees mapped metrics.
        </p>
      </div>

      {connection?.connected && (
        <div className="flex items-center gap-2 bg-emerald-50 border border-emerald-200 rounded-lg px-4 py-2.5 text-sm text-emerald-700">
          <ShieldCheck size={16} />
          Connected to <span className="font-medium">{connection.project}</span>
          {connection.last_synced_at && ` · last synced ${new Date(connection.last_synced_at).toLocaleString()}`}
        </div>
      )}

      <div className="bg-white border border-black/[0.08] rounded-xl p-5 shadow-sm space-y-4">
        <label className="block text-xs text-gray-500">
          Organization URL
          <input
            value={orgUrl}
            onChange={(e) => setOrgUrl(e.target.value)}
            placeholder="https://dev.azure.com/your-org"
            className="mt-1 w-full border border-black/10 rounded-md px-2.5 py-1.5 text-sm text-gray-700"
          />
        </label>
        <label className="block text-xs text-gray-500">
          Project name
          <input
            value={project}
            onChange={(e) => setProject(e.target.value)}
            placeholder="EIB-Digital"
            className="mt-1 w-full border border-black/10 rounded-md px-2.5 py-1.5 text-sm text-gray-700"
          />
        </label>
        <label className="block text-xs text-gray-500">
          Personal Access Token {connection?.connected && "(leave blank to keep the current one)"}
          <input
            type="password"
            value={pat}
            onChange={(e) => setPat(e.target.value)}
            placeholder={connection?.pat_masked || "PAT with Work Items (Read) scope"}
            autoComplete="off"
            className="mt-1 w-full border border-black/10 rounded-md px-2.5 py-1.5 text-sm text-gray-700"
          />
        </label>
        <label className="block text-xs text-gray-500">
          WIQL query (defaults to all Bug work items)
          <textarea
            value={wiqlQuery}
            onChange={(e) => setWiqlQuery(e.target.value)}
            rows={3}
            className="mt-1 w-full border border-black/10 rounded-md px-2.5 py-1.5 text-sm text-gray-700 font-mono text-xs"
          />
        </label>

        {testResult && (
          <div className={`flex items-center gap-2 text-sm rounded-lg px-3 py-2 ${
            testResult.ok ? "bg-emerald-50 text-emerald-700" : "bg-red-50 text-red-600"
          }`}>
            {testResult.ok ? <CheckCircle2 size={14} /> : <XCircle size={14} />}
            {testResult.message}
          </div>
        )}
        {saveError && <div className="text-sm text-red-500">{saveError}</div>}

        <div className="flex gap-2">
          <button
            onClick={handleTest}
            disabled={testing || saving}
            className="flex items-center gap-1.5 text-sm border border-black/10 rounded-md px-3 py-1.5
                       bg-white text-gray-700 hover:bg-gray-50 disabled:opacity-50"
          >
            {testing && <Loader2 size={14} className="animate-spin" />}
            {testing ? "Testing…" : "Test connection"}
          </button>
          <button
            onClick={handleSave}
            disabled={saving || testing}
            className="flex items-center gap-1.5 bg-qc-primary text-white text-sm font-medium px-4 py-1.5
                       rounded-md hover:bg-qc-primary-hover disabled:opacity-50"
          >
            {saving && <Loader2 size={14} className="animate-spin" />}
            {saving ? "Saving…" : "Save connection"}
          </button>
        </div>
      </div>

      {connection?.connected && (
        <div className="bg-white border border-black/[0.08] rounded-xl p-5 shadow-sm space-y-4">
          <div className="flex items-center justify-between">
            <div className="text-sm font-semibold text-[#0D1117]">Sync now</div>
            <button
              onClick={sync.sync}
              disabled={sync.syncing}
              className="flex items-center gap-1.5 text-sm border border-black/10 rounded-md px-3 py-1.5
                         bg-white text-gray-700 hover:bg-gray-50 disabled:opacity-50"
            >
              <RefreshCw size={14} className={sync.syncing ? "animate-spin" : ""} />
              {sync.syncing ? SYNC_STAGES[sync.stageIndex] : "Sync now"}
            </button>
          </div>
          <p className="text-xs text-gray-400">
            Manual only — Phase 2 has no scheduled sync. Reuses the same remarks-preservation and
            reopen-detection logic as CSV uploads.
          </p>

          {sync.syncing && <StagedProgress stages={SYNC_STAGES} currentIndex={sync.stageIndex} />}

          {sync.error && <ErrorState message={sync.error} onRetry={sync.sync} />}

          {!sync.syncing && sync.result && (
            <div className="text-sm text-gray-700 bg-gray-50 rounded-lg p-3 space-y-1">
              <div>{sync.result.fetched} fetched · {sync.result.created} new · {sync.result.updated} updated
                · {sync.result.reopened} reopened</div>
              {sync.result.unmapped_count > 0 && (
                <div className="text-amber-600">
                  {sync.result.unmapped_count} defects have an unmapped area path —{" "}
                  <Link href="/settings/mapping" className="underline font-medium">review the mapping</Link>.
                </div>
              )}
              {sync.result.new_area_paths > 0 && (
                <div className="text-gray-500">{sync.result.new_area_paths} new area path(s) discovered.</div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
