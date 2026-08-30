"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { syncAdo, fetchAdoConnection } from "./api";
import { createAbortTimeout, describeError } from "./timedAction";
import type { AdoConnection, AdoSyncSummary } from "./types";

export const SYNC_STAGES = [
  "Connecting…",
  "Fetching work items…",
  "Mapping area paths…",
  "Saving…",
  "Done",
];
const SYNC_TIMEOUT_MS = 45000;

export type AdoSyncResult = { fetched: number } & AdoSyncSummary;

/** Shared by the ADO settings page (full staged panel) and the sidebar's compact
 * sync widget, so the trigger/timeout/error logic exists in exactly one place. */
export function useAdoSync() {
  const [connection, setConnection] = useState<AdoConnection | null>(null);
  const [loadingConnection, setLoadingConnection] = useState(true);
  const [syncing, setSyncing] = useState(false);
  const [stageIndex, setStageIndex] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<AdoSyncResult | null>(null);
  const timersRef = useRef<ReturnType<typeof setTimeout>[]>([]);

  const loadConnection = useCallback(() => {
    setLoadingConnection(true);
    fetchAdoConnection()
      .then(setConnection)
      .catch(() => setConnection({ connected: false }))
      .finally(() => setLoadingConnection(false));
  }, []);

  useEffect(() => { loadConnection(); }, [loadConnection]);
  useEffect(() => () => timersRef.current.forEach(clearTimeout), []);

  const sync = useCallback(async () => {
    timersRef.current.forEach(clearTimeout);
    timersRef.current = [];

    setSyncing(true);
    setError(null);
    setResult(null);
    setStageIndex(0);

    // Backend does connect -> fetch -> map -> save in one request; these timers
    // only ever advance to the last "working" stage on their own — the real
    // response is what moves it to "Done" or surfaces an error.
    timersRef.current.push(setTimeout(() => setStageIndex(1), 600));
    timersRef.current.push(setTimeout(() => setStageIndex(2), 4000));
    timersRef.current.push(setTimeout(() => setStageIndex(3), 8000));

    const { signal, clear } = createAbortTimeout(SYNC_TIMEOUT_MS);
    try {
      const res = await syncAdo(signal);
      timersRef.current.forEach(clearTimeout);
      setStageIndex(4);
      setResult(res);
      loadConnection();
      await new Promise((r) => setTimeout(r, 400));
    } catch (e) {
      timersRef.current.forEach(clearTimeout);
      setError(describeError(e, "Sync is taking longer than expected — retry?"));
    } finally {
      clear();
      setSyncing(false);
    }
  }, [loadConnection]);

  return { connection, loadingConnection, reloadConnection: loadConnection, syncing, stageIndex, error, result, sync };
}
