import { useEffect, useState } from "react";
import type { HealthStatus } from "../types";

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";

interface UseHealthResult {
  status: HealthStatus;
  version: string | null;
  apiBase: string;
}

/** Polls the backend `GET /health` and reports Online / Offline / Checking. */
export function useHealth(pollMs = 15000): UseHealthResult {
  const [status, setStatus] = useState<HealthStatus>("checking");
  const [version, setVersion] = useState<string | null>(null);

  useEffect(() => {
    let active = true;

    async function check() {
      try {
        const res = await fetch(`${API_BASE}/health`);
        if (!res.ok) throw new Error(`status ${res.status}`);
        const data = (await res.json()) as { version?: string };
        if (!active) return;
        setStatus("online");
        setVersion(data.version ?? null);
      } catch {
        if (!active) return;
        setStatus("offline");
        setVersion(null);
      }
    }

    check();
    const id = window.setInterval(check, pollMs);
    return () => {
      active = false;
      window.clearInterval(id);
    };
  }, [pollMs]);

  return { status, version, apiBase: API_BASE };
}
