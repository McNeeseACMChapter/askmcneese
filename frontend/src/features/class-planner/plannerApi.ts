import { getApiBase } from "../../lib/api";
import type { Course, PlannerFilters, Section } from "./plannerTypes";

export type PlannerDataMode = "mock" | "staging" | "live";

export interface PlannerSource {
  name: string;
  url?: string;
  fetchedAt?: string;
  mode?: PlannerDataMode;
}

interface ApiEnvelope<T> {
  data: T;
  source: PlannerSource;
}

const configuredPlannerMode = import.meta.env.MODE === "test"
  ? "mock"
  : import.meta.env.VITE_CLASS_DATA_MODE;

export const PLANNER_DATA_MODE: PlannerDataMode =
  configuredPlannerMode === "live"
    ? "live"
    : configuredPlannerMode === "staging"
      ? "staging"
      : "mock";

export const API_PLANNER_TERM_ID = import.meta.env.VITE_CLASS_TERM_ID ?? "202660";

async function plannerGet<T>(path: string, signal?: AbortSignal): Promise<ApiEnvelope<T>> {
  const response = await fetch(`${getApiBase()}${path}`, {
    headers: { Accept: "application/json" },
    signal,
  });
  if (!response.ok) {
    throw new Error(response.status === 503
      ? "Class information is temporarily unavailable."
      : `Class data request failed (${response.status}).`);
  }
  return response.json() as Promise<ApiEnvelope<T>>;
}

export function searchPlannerCourses(
  termId: string,
  query: string,
  filters: PlannerFilters,
  signal?: AbortSignal,
): Promise<ApiEnvelope<Course[]>> {
  const params = new URLSearchParams({
    term: termId,
    q: query,
    open: String(filters.openOnly),
    online: String(filters.onlineOnly),
    days: filters.days.join(","),
    time: filters.time,
  });
  return plannerGet<Course[]>(`/class-planner/courses?${params}`, signal);
}

export function fetchPlannerSection(
  sectionId: string,
  signal?: AbortSignal,
): Promise<ApiEnvelope<Section & Pick<Course, "subject" | "courseNumber" | "title">>> {
  return plannerGet(`/class-planner/sections/${encodeURIComponent(sectionId)}`, signal);
}

