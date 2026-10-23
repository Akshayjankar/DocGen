"use client";

import { useCallback, useEffect, useState } from "react";
import {
  clearAll,
  deleteDoc,
  isHistoryEnabled,
  listDocs,
  setHistoryEnabled,
  storageStats,
  type LibraryDoc,
} from "@/lib/library-db";

export function useLibrary() {
  const [docs, setDocs] = useState<LibraryDoc[]>([]);
  const [historyOn, setHistoryOn] = useState(true);
  const [bytes, setBytes] = useState(0);
  const [ready, setReady] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    try {
      const [list, on, stats] = await Promise.all([
        listDocs(),
        isHistoryEnabled(),
        storageStats(),
      ]);
      setDocs(list);
      setHistoryOn(on);
      setBytes(stats.bytes);
      setError(null);
    } catch {
      setError("Library unavailable in this browser (private mode or blocked storage).");
      setDocs([]);
    } finally {
      setReady(true);
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  const remove = useCallback(
    async (id: string) => {
      await deleteDoc(id);
      await refresh();
    },
    [refresh],
  );

  const clear = useCallback(async () => {
    await clearAll();
    await refresh();
  }, [refresh]);

  const toggleHistory = useCallback(
    async (on: boolean) => {
      await setHistoryEnabled(on);
      setHistoryOn(on);
      await refresh();
    },
    [refresh],
  );

  return { docs, historyOn, bytes, ready, error, refresh, remove, clear, toggleHistory };
}
