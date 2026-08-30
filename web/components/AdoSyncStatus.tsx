"use client";

import Link from "next/link";
import { RefreshCw, AlertTriangle, PlugZap } from "lucide-react";
import { useAdoSync, SYNC_STAGES } from "@/lib/useAdoSync";

function timeAgo(iso: string): string {
  const diffMs = Date.now() - new Date(iso).getTime();
  const mins = Math.floor(diffMs / 60000);
  if (mins < 1) return "just now";
  if (mins < 60) return `${mins}m ago`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours}h ago`;
  return `${Math.floor(hours / 24)}d ago`;
}

export default function AdoSyncStatus() {
  const { connection, loadingConnection, syncing, stageIndex, error, sync } = useAdoSync();

  if (loadingConnection) {
    return <div className="px-4 py-3 text-[11px] text-gray-400">Checking ADO connection…</div>;
  }

  if (!connection?.connected) {
    return (
      <Link
        href="/settings/ado"
        className="flex items-center gap-2 px-4 py-3 text-[11px] text-gray-400 hover:text-qc-primary"
      >
        <PlugZap size={13} />
        Connect ADO
      </Link>
    );
  }

  return (
    <div className="px-4 py-3 border-t border-black/[0.08]">
      <div className="flex items-center justify-between">
        <span className="text-[11px] font-medium text-gray-500 truncate">{connection.project}</span>
        <button
          onClick={sync}
          disabled={syncing}
          className="flex items-center gap-1 text-[11px] text-qc-primary hover:underline disabled:opacity-50 shrink-0"
        >
          <RefreshCw size={11} className={syncing ? "animate-spin" : ""} />
          Sync
        </button>
      </div>
      <div className="text-[11px] text-gray-400 mt-0.5">
        {syncing
          ? SYNC_STAGES[stageIndex]
          : connection.last_synced_at
          ? `Synced ${timeAgo(connection.last_synced_at)}`
          : "Never synced"}
      </div>
      {error && (
        <div className="flex items-center gap-1 text-[11px] text-red-500 mt-1">
          <AlertTriangle size={11} className="shrink-0" />
          <span className="truncate">{error}</span>
        </div>
      )}
    </div>
  );
}
