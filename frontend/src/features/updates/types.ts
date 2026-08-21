export const UPDATE_AREAS = [
  "Product",
  "Frontend",
  "Backend",
  "Retrieval",
  "Knowledge",
  "Crawler",
  "Class Planner",
  "DevOps",
  "QA",
  "Docs",
  "ACM",
] as const;

export type UpdateArea = (typeof UPDATE_AREAS)[number];
export type UpdateStatus = "completed" | "planned";

export interface Contributor {
  name: string;
  role?: string;
}

export interface ProjectUpdate {
  ticketNo: number;
  date: string;
  title: string;
  contributors: Contributor[];
  method?: string;
  notes?: string;
  chapterId: string;
  areas: UpdateArea[];
  technologies: string[];
  commit?: string;
  pullRequest?: string;
  sprint?: string;
  status: UpdateStatus;
  turningPoint?: boolean;
}

export interface DevelopmentChapter {
  id: string;
  number: number;
  title: string;
  dateLabel: string;
  startDate: string;
  endDate: string;
  summary: string;
  situation: string;
  decision: string;
  expectedResult: string;
  narrative: string;
  outcome: string;
  enabledNext: string;
  changeFlow: string[];
  ticketIds: number[];
  tags: UpdateArea[];
  turningPoint?: boolean;
}

export interface TimelineRecord {
  ticketNo: number;
  title: string;
  date: string;
  who: string;
  method: string;
  notes: string;
}
