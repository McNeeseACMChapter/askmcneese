import { useCallback, useState } from "react";
import type { AskCommand, AskResponse } from "../types";

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";

export interface AskOutcome {
  response: AskResponse | null;
  error: string | null;
}

interface UseAskResult {
  ask: (question: string) => Promise<AskOutcome>;
  data: AskResponse | null;
  loading: boolean;
  error: string | null;
  reset: () => void;
  apiBase: string;
}

/** Sends a question to `POST /ask` and tracks loading / error / result state. */
export function useAsk(): UseAskResult {
  const [data, setData] = useState<AskResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const reset = useCallback(() => {
    setData(null);
    setError(null);
    setLoading(false);
  }, []);

  const ask = useCallback(async (question: string): Promise<AskOutcome> => {
    const trimmed = question.trim();
    if (!trimmed) return { response: null, error: null };

    setLoading(true);
    setError(null);

    const body: AskCommand = { question: trimmed };

    try {
      const res = await fetch(`${API_BASE}/ask`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });

      if (!res.ok) {
        let message = `Request failed (${res.status})`;
        try {
          const errBody = (await res.json()) as { detail?: unknown };
          if (typeof errBody.detail === "string") message = errBody.detail;
        } catch {
          // ignore non-JSON error bodies
        }
        throw new Error(message);
      }

      const result = (await res.json()) as AskResponse;
      setData(result);
      return { response: result, error: null };
    } catch (err) {
      const message = err instanceof Error ? err.message : "Something went wrong";
      setError(message);
      setData(null);
      return { response: null, error: message };
    } finally {
      setLoading(false);
    }
  }, []);

  return { ask, data, loading, error, reset, apiBase: API_BASE };
}
