import { useEffect, useState } from "react";
import type { HealthStatus } from "../types";
import { fetchHealth, getApiBase, type HealthResponse } from "../lib/api";

export interface RetrievalCapabilities {
  knowledgeSearchAvailable: boolean;
  officialWebSearchAvailable: boolean;
  hybridRetrievalAvailable: boolean;
  companionSearchAvailable: boolean;
  rmpAvailable: boolean;
  socialLinksAvailable: boolean;
}

interface UseHealthResult {
  status: HealthStatus;
  version: string | null;
  apiBase: string;
  capabilities: RetrievalCapabilities;
}

const DEFAULT_CAPS: RetrievalCapabilities = {
  knowledgeSearchAvailable: true,
  // Optimistic until health responds — avoid locking Web before we know.
  officialWebSearchAvailable: true,
  hybridRetrievalAvailable: false,
  companionSearchAvailable: false,
  rmpAvailable: false,
  socialLinksAvailable: false,
};

function mapCapabilities(data: HealthResponse): RetrievalCapabilities {
  const c = data.capabilities;
  return {
    knowledgeSearchAvailable:
      data.knowledge_search_available ?? c?.knowledge_search_available ?? true,
    officialWebSearchAvailable:
      data.official_web_search_available ?? c?.official_web_search_available ?? true,
    hybridRetrievalAvailable:
      data.hybrid_retrieval_available ?? c?.hybrid_retrieval_available ?? false,
    companionSearchAvailable:
      data.companion_search_available ?? c?.companion_search_available ?? false,
    rmpAvailable: data.rmp_available ?? c?.rmp_available ?? false,
    socialLinksAvailable: data.social_links_available ?? c?.social_links_available ?? false,
  };
}

/** Polls the backend `GET /health` and reports Online / Offline / Checking. */
export function useHealth(pollMs = 15000): UseHealthResult {
  const [status, setStatus] = useState<HealthStatus>("checking");
  const [version, setVersion] = useState<string | null>(null);
  const [capabilities, setCapabilities] = useState<RetrievalCapabilities>(DEFAULT_CAPS);

  useEffect(() => {
    let active = true;

    async function check() {
      try {
        const data = await fetchHealth();
        if (!active) return;
        setStatus("online");
        setVersion(data.version ?? null);
        setCapabilities(mapCapabilities(data));
      } catch {
        if (!active) return;
        setStatus("offline");
        setVersion(null);
        setCapabilities({
          ...DEFAULT_CAPS,
          officialWebSearchAvailable: false,
        });
      }
    }

    check();
    const id = window.setInterval(check, pollMs);
    return () => {
      active = false;
      window.clearInterval(id);
    };
  }, [pollMs]);

  return { status, version, apiBase: getApiBase(), capabilities };
}
