import { useState, useCallback, useRef } from "react";
import type { AskResponse, ChatMessage, Citation, PipelineStep } from "../types";

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";

export type AskStatus = 
  | "idle" 
  | "connecting" 
  | "searching" 
  | "generating" 
  | "complete" 
  | "error";

export interface PipelineInfo {
  currentStep: string;
  message: string;
  steps: PipelineStep[];
  retrievalMs?: number;
  generationMs?: number;
  totalMs?: number;
  sourcesFound?: number;
}

interface UseAskReturn {
  ask: (question: string, onStreamUpdate?: (text: string) => void) => Promise<ChatMessage>;
  isLoading: boolean;
  status: AskStatus;
  pipeline: PipelineInfo;
  error: string | null;
}

const initialPipeline: PipelineInfo = {
  currentStep: "",
  message: "",
  steps: [],
};

export function useAsk(): UseAskReturn {
  const [isLoading, setIsLoading] = useState(false);
  const [status, setStatus] = useState<AskStatus>("idle");
  const [pipeline, setPipeline] = useState<PipelineInfo>(initialPipeline);
  const [error, setError] = useState<string | null>(null);
  const abortRef = useRef<AbortController | null>(null);

  const ask = useCallback(async (
    question: string, 
    onStreamUpdate?: (text: string) => void
  ): Promise<ChatMessage> => {
    // Cancel any in-flight request
    if (abortRef.current) {
      abortRef.current.abort();
    }
    abortRef.current = new AbortController();

    setIsLoading(true);
    setError(null);
    setStatus("connecting");
    setPipeline({ ...initialPipeline, currentStep: "connecting", message: "Connecting to server..." });

    try {
      // Use streaming for real-time updates
      const useStream = !!onStreamUpdate;
      
      if (useStream) {
        return await askWithStream(question, onStreamUpdate, abortRef.current.signal, setStatus, setPipeline);
      } else {
        return await askWithoutStream(question, setStatus, setPipeline);
      }
      
    } catch (err) {
      if (err instanceof Error && err.name === "AbortError") {
        return createErrorMessage("Request was cancelled");
      }
      
      setStatus("error");
      const errorMessage = err instanceof Error ? err.message : "Unknown error";
      setError(errorMessage);
      setPipeline(prev => ({ ...prev, currentStep: "error", message: errorMessage }));
      
      return createErrorMessage(getErrorMessage(errorMessage));
    } finally {
      setIsLoading(false);
    }
  }, []);

  return { ask, isLoading, status, pipeline, error };
}

async function askWithoutStream(
  question: string,
  setStatus: (s: AskStatus) => void,
  setPipeline: (fn: (p: PipelineInfo) => PipelineInfo) => void,
): Promise<ChatMessage> {
  setStatus("searching");
  setPipeline(prev => ({ 
    ...prev, 
    currentStep: "retrieval", 
    message: "Searching knowledge base...",
    steps: [{ step: "retrieval", status: "started", message: "Searching..." }]
  }));

  const res = await fetch(`${API_BASE}/ask`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question, stream: false }),
  });

  if (!res.ok) {
    const errorText = await res.text().catch(() => "Unknown error");
    throw new Error(`API error ${res.status}: ${errorText}`);
  }

  const data: AskResponse = await res.json();
  
  setStatus("complete");
  setPipeline(prev => ({
    ...prev,
    currentStep: "complete",
    message: "Done",
    retrievalMs: data.retrieval_ms,
    generationMs: data.generation_ms,
    totalMs: data.total_ms,
    sourcesFound: data.num_results,
    steps: [
      { step: "retrieval", status: "completed", message: `Found ${data.num_results} sources`, duration_ms: data.retrieval_ms },
      ...(data.generation_ms ? [{ step: "generation", status: "completed" as const, message: "Answer generated", duration_ms: data.generation_ms }] : []),
    ]
  }));

  return transformResponse(data);
}

async function askWithStream(
  question: string,
  onStreamUpdate: (text: string) => void,
  signal: AbortSignal,
  setStatus: (s: AskStatus) => void,
  setPipeline: (fn: (p: PipelineInfo) => PipelineInfo) => void,
): Promise<ChatMessage> {
  setStatus("searching");
  setPipeline(prev => ({ 
    ...prev, 
    currentStep: "retrieval", 
    message: "Searching knowledge base...",
  }));

  const res = await fetch(`${API_BASE}/ask`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question, stream: true }),
    signal,
  });

  if (!res.ok) {
    const errorText = await res.text().catch(() => "Unknown error");
    throw new Error(`API error ${res.status}: ${errorText}`);
  }

  const reader = res.body?.getReader();
  if (!reader) throw new Error("No response body");

  const decoder = new TextDecoder();
  let fullText = "";
  let citations: Citation[] = [];
  let queryId = "";
  let retrievalMs = 0;
  let generationMs = 0;
  let totalMs = 0;
  let numResults = 0;

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    const chunk = decoder.decode(value, { stream: true });
    const lines = chunk.split("\n");

    for (const line of lines) {
      if (line.startsWith("event: ")) {
        continue;
      }
      if (line.startsWith("data: ")) {
        try {
          const data = JSON.parse(line.slice(6));
          
          // Handle different event types based on the data structure
          if (data.step) {
            // Step event
            const step = data as PipelineStep;
            if (step.step === "retrieval") {
              if (step.status === "started") {
                setStatus("searching");
                setPipeline(prev => ({ ...prev, currentStep: "retrieval", message: step.message }));
              } else if (step.status === "completed") {
                retrievalMs = step.duration_ms || 0;
                setPipeline(prev => ({ 
                  ...prev, 
                  message: step.message,
                  retrievalMs,
                  steps: [...prev.steps, step]
                }));
              }
            } else if (step.step === "generation") {
              if (step.status === "started") {
                setStatus("generating");
                setPipeline(prev => ({ ...prev, currentStep: "generation", message: step.message }));
              } else if (step.status === "completed") {
                generationMs = step.duration_ms || 0;
                setPipeline(prev => ({ 
                  ...prev, 
                  message: step.message,
                  generationMs,
                  steps: [...prev.steps, step]
                }));
              }
            }
          } else if (data.citations) {
            // Citations event
            citations = data.citations.map((c: { id: string; title: string; url: string; snippet?: string }) => ({
              id: c.id,
              title: c.title,
              url: c.url,
              snippet: c.snippet,
            }));
            numResults = citations.length;
            setPipeline(prev => ({ ...prev, sourcesFound: numResults }));
          } else if (data.text !== undefined) {
            // Chunk event
            fullText += data.text;
            onStreamUpdate(fullText);
          } else if (data.query_id) {
            // Done event
            queryId = data.query_id;
            totalMs = data.total_ms || 0;
            setStatus("complete");
            setPipeline(prev => ({ 
              ...prev, 
              currentStep: "complete", 
              message: "Done",
              totalMs,
            }));
          } else if (data.message && !data.step) {
            // Error event
            throw new Error(data.message);
          }
        } catch (e) {
          if (e instanceof SyntaxError) continue; // Incomplete JSON
          throw e;
        }
      }
    }
  }

  return {
    id: `a-${Date.now()}-${queryId.slice(0, 8)}`,
    role: "assistant",
    text: fullText,
    citations: citations.length > 0 ? citations : undefined,
    isDemo: false,
    timestamp: new Date(),
  };
}

function transformResponse(data: AskResponse): ChatMessage {
  const citations: Citation[] = data.chunks.map((chunk) => ({
    id: chunk.chunk_id,
    title: chunk.title,
    url: chunk.source_url,
    snippet: chunk.text.slice(0, 200) + (chunk.text.length > 200 ? "..." : ""),
  }));

  return {
    id: `a-${Date.now()}-${data.query_id?.slice(0, 8) || ""}`,
    role: "assistant",
    text: data.answer,
    citations: citations.length > 0 ? citations : undefined,
    isDemo: false,
    timestamp: new Date(),
  };
}

function createErrorMessage(text: string): ChatMessage {
  return {
    id: `e-${Date.now()}`,
    role: "assistant",
    text,
    isDemo: true,
    timestamp: new Date(),
  };
}

function getErrorMessage(error: string): string {
  if (error.includes("fetch") || error.includes("network") || error.includes("Failed")) {
    return "I'm having trouble connecting to the server. Please make sure the backend is running.";
  }
  if (error.includes("404")) {
    return "The API endpoint is not available. Please check that the backend is updated.";
  }
  if (error.includes("500")) {
    return "The server encountered an error. This might mean the knowledge base needs to be populated or the API key needs to be configured.";
  }
  if (error.includes("ANTHROPIC") || error.includes("API key")) {
    return "The AI service is not configured. Please check the ANTHROPIC_API_KEY in the backend .env file.";
  }
  return `Something went wrong: ${error}. Please try again.`;
}
