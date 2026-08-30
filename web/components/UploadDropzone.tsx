"use client";

import { useRef, useState } from "react";
import { UploadCloud, FileSpreadsheet, CheckCircle2, AlertTriangle, Loader2 } from "lucide-react";
import { uploadFile, completeMapping } from "@/lib/api";
import { createAbortTimeout, describeError } from "@/lib/timedAction";

const UPLOAD_TIMEOUT_MS = 45000;

type RecordType = "defects" | "tests";

interface MappingState {
  filePath: string;
  recordType: RecordType;
  detected: Record<string, string | null>;
  missing: string[];
  columns: string[];
}

interface ResultState {
  created: number;
  updated: number;
  reopened?: number;
  total: number;
}

const FIELD_LABELS: Record<string, string> = {
  external_id: "ID", title: "Title", assignee_email: "Assigned To", state: "State",
  severity: "Severity", raised_date: "Raised Date", eta: "ETA", platform: "Platform",
  module: "Module", sub_module: "Sub-module", tags: "Tags", status: "Status",
  phase: "Phase", executed_date: "Executed Date",
};

export default function UploadDropzone() {
  const inputRef = useRef<HTMLInputElement>(null);
  const [recordType, setRecordType] = useState<RecordType>("defects");
  const [file, setFile] = useState<File | null>(null);
  const [dragOver, setDragOver] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [mapping, setMapping] = useState<MappingState | null>(null);
  const [mappingChoices, setMappingChoices] = useState<Record<string, string>>({});
  const [result, setResult] = useState<ResultState | null>(null);

  const reset = () => {
    setFile(null); setError(null); setMapping(null); setMappingChoices({}); setResult(null);
  };

  const handleUpload = async () => {
    if (!file) return;
    setUploading(true);
    setError(null);
    const { signal, clear } = createAbortTimeout(UPLOAD_TIMEOUT_MS);
    try {
      const res = await uploadFile(file, recordType, undefined, signal);
      if (res.status === "mapping_required") {
        setMapping(res);
        setMappingChoices(
          Object.fromEntries(Object.entries(res.detected).map(([k, v]) => [k, (v as string) || ""]))
        );
      } else {
        setResult(res);
      }
    } catch (e) {
      setError(describeError(e, "This is taking longer than expected — retry?"));
    } finally {
      clear();
      setUploading(false);
    }
  };

  const handleCompleteMapping = async () => {
    if (!mapping) return;
    setUploading(true);
    setError(null);
    const { signal, clear } = createAbortTimeout(UPLOAD_TIMEOUT_MS);
    try {
      const columnMap = Object.fromEntries(
        Object.entries(mappingChoices).filter(([, v]) => v)
      );
      const res = await completeMapping(mapping.filePath, mapping.recordType, columnMap, signal);
      setResult(res);
      setMapping(null);
    } catch (e) {
      setError(describeError(e, "This is taking longer than expected — retry?"));
    } finally {
      clear();
      setUploading(false);
    }
  };

  if (result) {
    return (
      <div className="bg-white border border-black/[0.08] rounded-xl p-8 text-center shadow-sm">
        <CheckCircle2 className="mx-auto text-qc-accent" size={40} />
        <div className="text-base font-semibold text-[#0D1117] mt-3">Upload complete</div>
        <div className="text-sm text-gray-500 mt-1">
          {result.created} created · {result.updated} updated
          {typeof result.reopened === "number" && ` · ${result.reopened} reopened`} · {result.total} rows total
        </div>
        <button
          onClick={reset}
          className="mt-4 text-sm text-qc-primary font-medium hover:underline"
        >
          Upload another file
        </button>
      </div>
    );
  }

  if (mapping) {
    return (
      <div className="bg-white border border-black/[0.08] rounded-xl p-6 shadow-sm">
        <div className="flex items-center gap-2 text-amber-600 mb-1">
          <AlertTriangle size={16} />
          <span className="text-sm font-semibold">Column mapping needed</span>
        </div>
        <p className="text-xs text-gray-500 mb-4">
          We couldn't auto-detect: {mapping.missing.map((f) => FIELD_LABELS[f] || f).join(", ")}.
          Confirm the mapping below (leave blank if a column doesn't apply).
        </p>
        <div className="grid grid-cols-2 gap-3">
          {Object.keys(mapping.detected).map((field) => (
            <label key={field} className="text-xs text-gray-500">
              {FIELD_LABELS[field] || field}
              <select
                value={mappingChoices[field] || ""}
                onChange={(e) => setMappingChoices((prev) => ({ ...prev, [field]: e.target.value }))}
                className="mt-1 w-full border border-black/10 rounded-md px-2 py-1.5 text-sm text-gray-700"
              >
                <option value="">— none —</option>
                {mapping.columns.map((col) => (
                  <option key={col} value={col}>{col}</option>
                ))}
              </select>
            </label>
          ))}
        </div>
        {error && <div className="text-sm text-red-500 mt-3">{error}</div>}
        <div className="flex gap-2 mt-5">
          <button
            onClick={handleCompleteMapping}
            disabled={uploading}
            className="flex items-center gap-1.5 bg-qc-primary text-white text-sm font-medium px-4 py-2 rounded-md hover:bg-qc-primary-hover disabled:opacity-50"
          >
            {uploading && <Loader2 size={14} className="animate-spin" />}
            {uploading ? "Ingesting…" : "Confirm mapping & ingest"}
          </button>
          <button onClick={reset} className="text-sm text-gray-500 px-4 py-2">Cancel</button>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white border border-black/[0.08] rounded-xl p-6 shadow-sm space-y-4">
      <div className="flex gap-2">
        {(["defects", "tests"] as RecordType[]).map((rt) => (
          <button
            key={rt}
            onClick={() => setRecordType(rt)}
            className={`text-sm px-3 py-1.5 rounded-md font-medium ${
              recordType === rt ? "bg-qc-primary text-white" : "bg-gray-100 text-gray-600"
            }`}
          >
            {rt === "defects" ? "Defects" : "Test Cases"}
          </button>
        ))}
      </div>

      <div
        onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
        onDragLeave={() => setDragOver(false)}
        onDrop={(e) => {
          e.preventDefault();
          setDragOver(false);
          const dropped = e.dataTransfer.files?.[0];
          if (dropped) setFile(dropped);
        }}
        onClick={() => inputRef.current?.click()}
        className={`border-2 border-dashed rounded-xl py-10 flex flex-col items-center justify-center gap-2 cursor-pointer transition-colors ${
          dragOver ? "border-qc-primary bg-qc-primary/5" : "border-gray-200 hover:border-gray-300"
        }`}
      >
        <input
          ref={inputRef}
          type="file"
          accept=".csv,.xlsx,.xls"
          className="hidden"
          onChange={(e) => setFile(e.target.files?.[0] || null)}
        />
        {file ? (
          <>
            <FileSpreadsheet size={28} className="text-qc-primary" />
            <span className="text-sm text-gray-700">{file.name}</span>
          </>
        ) : (
          <>
            <UploadCloud size={28} className="text-gray-400" />
            <span className="text-sm text-gray-500">Drag & drop a CSV or XLSX, or click to browse</span>
          </>
        )}
      </div>

      {error && (
        <div className="flex items-center gap-2 text-sm text-red-500">
          {error}
          <button onClick={handleUpload} className="underline font-medium shrink-0">Retry</button>
        </div>
      )}

      <button
        onClick={handleUpload}
        disabled={!file || uploading}
        className="flex items-center gap-1.5 bg-qc-primary text-white text-sm font-medium px-4 py-2 rounded-md hover:bg-qc-primary-hover disabled:opacity-50"
      >
        {uploading && <Loader2 size={14} className="animate-spin" />}
        {uploading ? "Uploading & processing…" : `Upload ${recordType}`}
      </button>
    </div>
  );
}
