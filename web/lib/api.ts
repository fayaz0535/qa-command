import type {
  MetricsTree, Insight, HierarchyTree, TrendPoint, Filters, Defect, TestCase, EmailDraft,
  AdoConnection, AdoTestConnectionResult, AdoSyncSummary, AdoPreviewResult,
} from "./types";

export const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:5001";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, init);
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`${res.status} ${res.statusText}: ${text}`);
  }
  return res.json();
}

function qs(params: Record<string, string | undefined>): string {
  const entries = Object.entries(params).filter(([, v]) => v !== undefined && v !== "");
  if (!entries.length) return "";
  return "?" + new URLSearchParams(entries as [string, string][]).toString();
}

export function fetchMetrics(owner?: string): Promise<MetricsTree> {
  return request(`/api/metrics${qs({ owner })}`);
}

export function fetchTrend(params: {
  level?: string; platform?: string; module?: string; sub_module?: string; days?: number;
}): Promise<{ trend: TrendPoint[] }> {
  const { days, ...rest } = params;
  return request(`/api/metrics/trend${qs({ ...rest, days: days ? String(days) : undefined })}`);
}

export function fetchInsights(force = false): Promise<Insight> {
  return request(`/api/insights${qs({ force: force ? "true" : undefined })}`);
}

export function fetchHierarchy(): Promise<HierarchyTree> {
  return request(`/api/hierarchy`);
}

export function fetchOwners(): Promise<{ owners: string[]; needs_review_count: number }> {
  return request(`/api/owners`);
}

export function fetchDefects(filters: Filters): Promise<{ defects: Defect[]; count: number }> {
  return request(`/api/defects${qs(filters as Record<string, string | undefined>)}`);
}

export function fetchTests(filters: Filters): Promise<{ tests: TestCase[]; count: number }> {
  return request(`/api/tests${qs(filters as Record<string, string | undefined>)}`);
}

export async function uploadFile(
  file: File, recordType: "defects" | "tests", columnMap?: Record<string, string>, signal?: AbortSignal,
): Promise<any> {
  const form = new FormData();
  form.append("file", file);
  form.append("record_type", recordType);
  if (columnMap) form.append("column_map", JSON.stringify(columnMap));
  return request(`/api/upload`, { method: "POST", body: form, signal });
}

export function completeMapping(
  filePath: string, recordType: "defects" | "tests", columnMap: Record<string, string>, signal?: AbortSignal,
): Promise<any> {
  return request(`/api/upload/complete-mapping`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ file_path: filePath, record_type: recordType, column_map: columnMap }),
    signal,
  });
}

export function draftEmail(signal?: AbortSignal): Promise<EmailDraft> {
  return request(`/api/email/draft`, { method: "POST", signal });
}

export async function downloadEml(
  subject: string, html: string, recipients: string[], cc: string[], attachments: Record<string, string>,
  signal?: AbortSignal,
): Promise<Blob> {
  const res = await fetch(`${API_URL}/api/email/eml`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ subject, html, recipients, cc, attachments }),
    signal,
  });
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
  return res.blob();
}

export function getSendConfig(): Promise<{
  recipients: string[]; cc: string[]; send_time: string; auto_send_enabled: boolean;
}> {
  return request(`/api/email/send-config`);
}

export function updateSendConfig(body: {
  recipients: string[]; cc: string[]; send_time: string;
}): Promise<any> {
  return request(`/api/email/send-config`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}

export function exportUrl(
  kind: "defects" | "tests", format: "xlsx" | "pdf" | "csv", filters: Filters,
): string {
  return `${API_URL}/api/export/${kind}${qs({ format, ...(filters as Record<string, string | undefined>) })}`;
}

/** Fetches an export as a Blob (rather than a plain <a href> navigation) so the
 * caller can show loading/timeout/error state instead of the browser silently
 * navigating away to a raw error response if the export fails. */
export async function fetchExportBlob(
  kind: "defects" | "tests", format: "xlsx" | "pdf" | "csv", filters: Filters, signal?: AbortSignal,
): Promise<Blob> {
  const res = await fetch(exportUrl(kind, format, filters), { signal });
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`${res.status} ${res.statusText}: ${text}`);
  }
  return res.blob();
}

// ── ADO (Phase 2) ────────────────────────────────────────────────────────────
// The PAT itself never round-trips back from these calls except at the instant
// the DM types it in — every response masks it, per services/crypto.py.

export function fetchAdoConnection(): Promise<AdoConnection> {
  return request(`/api/ado/connection`);
}

export function testAdoConnection(
  org_url: string, project: string, pat: string, signal?: AbortSignal,
): Promise<AdoTestConnectionResult> {
  return request(`/api/ado/test-connection`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ org_url, project, pat }),
    signal,
  });
}

export function saveAdoConnection(
  org_url: string, project: string, pat: string, wiql_query: string | null, signal?: AbortSignal,
): Promise<AdoConnection> {
  return request(`/api/ado/connection`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ org_url, project, pat, wiql_query }),
    signal,
  });
}

export function syncAdo(signal?: AbortSignal): Promise<{ fetched: number } & AdoSyncSummary> {
  return request(`/api/ado/sync`, { method: "POST", signal });
}

/** Runs a WIQL query (not necessarily the saved one) against the saved connection
 * and shows how it would parse — no Defect writes. Requires a connection already
 * be saved, since it reuses those credentials. */
export function previewAdoWiql(wiql_query: string, signal?: AbortSignal): Promise<AdoPreviewResult> {
  return request(`/api/ado/preview-wiql`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ wiql_query }),
    signal,
  });
}
