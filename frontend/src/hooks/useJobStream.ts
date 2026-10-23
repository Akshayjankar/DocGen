"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { jobEventsUrl } from "@/lib/api";
import type { JobEvent, JobStatus } from "@/types/api";

interface UseJobStreamOptions {
  jobId: string | null;
  enabled?: boolean;
  onEvent?: (event: JobEvent) => void;
  onDone?: (event: JobEvent) => void;
  onError?: (message: string) => void;
}

interface UseJobStreamResult {
  status: JobStatus | null;
  progress: number;
  message: string;
  lastEvent: JobEvent | null;
  connected: boolean;
  disconnect: () => void;
}

export function useJobStream({
  jobId,
  enabled = true,
  onEvent,
  onDone,
  onError,
}: UseJobStreamOptions): UseJobStreamResult {
  const [status, setStatus] = useState<JobStatus | null>(null);
  const [progress, setProgress] = useState(0);
  const [message, setMessage] = useState("");
  const [lastEvent, setLastEvent] = useState<JobEvent | null>(null);
  const [connected, setConnected] = useState(false);
  const sourceRef = useRef<EventSource | null>(null);
  const onEventRef = useRef(onEvent);
  const onDoneRef = useRef(onDone);
  const onErrorRef = useRef(onError);
  const closedRef = useRef(false);

  onEventRef.current = onEvent;
  onDoneRef.current = onDone;
  onErrorRef.current = onError;

  const disconnect = useCallback(() => {
    closedRef.current = true;
    sourceRef.current?.close();
    sourceRef.current = null;
    setConnected(false);
  }, []);

  useEffect(() => {
    if (!jobId || !enabled) {
      disconnect();
      return;
    }

    closedRef.current = false;
    const es = new EventSource(jobEventsUrl(jobId));
    sourceRef.current = es;
    setConnected(true);

    const handlePayload = (raw: string) => {
      if (!raw || raw === "{}") return;
      try {
        const data = JSON.parse(raw) as JobEvent;
        setLastEvent(data);
        setStatus(data.status);
        setProgress(data.progress);
        setMessage(data.message);
        onEventRef.current?.(data);

        if (data.status === "done") {
          onDoneRef.current?.(data);
          closedRef.current = true;
          es.close();
          setConnected(false);
        }
        if (data.status === "failed") {
          onErrorRef.current?.(data.error || data.message || "Job failed");
          closedRef.current = true;
          es.close();
          setConnected(false);
        }
      } catch {
        onErrorRef.current?.("Malformed job event");
      }
    };

    es.onmessage = (msg) => handlePayload(msg.data);
    es.addEventListener("progress", ((msg: MessageEvent) => {
      handlePayload(msg.data);
    }) as EventListener);

    es.onerror = () => {
      // EventSource fires error on brief reconnects; only treat as fatal after close
      if (closedRef.current || es.readyState === EventSource.CLOSED) {
        if (!closedRef.current) {
          onErrorRef.current?.("Lost connection to job stream");
        }
        es.close();
        setConnected(false);
      }
    };

    return () => {
      closedRef.current = true;
      es.close();
      sourceRef.current = null;
      setConnected(false);
    };
  }, [jobId, enabled, disconnect]);

  return { status, progress, message, lastEvent, connected, disconnect };
}
