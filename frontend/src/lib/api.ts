const DEFAULT_API_BASE = "http://127.0.0.1:8000";

export function getApiBase(): string {
  return (import.meta.env.VITE_API_BASE_URL ?? DEFAULT_API_BASE).replace(/\/+$/, "");
}

async function getJson<T>(path: string, signal?: AbortSignal): Promise<T> {
  const response = await fetch(`${getApiBase()}${path}`, {
    headers: { Accept: "application/json" },
    signal,
  });
  if (!response.ok) {
    throw new Error(`Request failed (${response.status})`);
  }
  return response.json() as Promise<T>;
}

export interface HealthResponse {
  status?: string;
  version?: string;
  knowledge_search_available?: boolean;
  official_web_search_available?: boolean;
  hybrid_retrieval_available?: boolean;
  companion_search_available?: boolean;
  rmp_available?: boolean;
  social_links_available?: boolean;
  capabilities?: {
    knowledge_search_available?: boolean;
    official_web_search_available?: boolean;
    hybrid_retrieval_available?: boolean;
    companion_search_available?: boolean;
    rmp_available?: boolean;
    social_links_available?: boolean;
    rccs_enabled?: boolean;
  };
  [key: string]: unknown;
}

export interface AskStatsResponse {
  knowledge_base?: { count?: number; [key: string]: unknown };
  pipeline?: {
    total_queries?: number;
    successful?: number;
    success_rate?: number;
    avg_latency_ms?: number;
    [key: string]: unknown;
  };
  web_search?: { enabled?: boolean; [key: string]: unknown };
  [key: string]: unknown;
}

export const fetchHealth = (signal?: AbortSignal) =>
  getJson<HealthResponse>("/health", signal);

export const fetchAskStats = (signal?: AbortSignal) =>
  getJson<AskStatsResponse>("/ask/stats", signal);
