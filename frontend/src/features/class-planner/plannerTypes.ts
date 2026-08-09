export type MeetingDay = "M" | "T" | "W" | "R" | "F" | "S" | "U";

export interface Meeting {
  type: "Lecture" | "Lab" | "Online" | "Class";
  days: MeetingDay[];
  startTime: string | null;
  endTime: string | null;
  startDate?: string | null;
  endDate?: string | null;
  building?: string | null;
  room?: string | null;
  isOnline?: boolean;
  isTba?: boolean;
}

export interface Section {
  id: string;
  courseId: string;
  termId: string;
  crn: string;
  sectionNumber: string;
  credits?: number;
  instructor?: string;
  meetings: Meeting[];
  modality: "In person" | "Online" | "Hybrid";
  seatsRemaining: number | null;
  status: "open" | "closed";
  updatedAt: string;
  capacity?: number | null;
  enrolled?: number | null;
  available?: number | null;
  partOfTerm?: string | null;
  sourceUrl?: string;
}

export interface Course {
  id: string;
  subject: string;
  courseNumber: string;
  title: string;
  credits: number;
  sections: Section[];
}

export interface ScheduleConflict {
  candidateId: string;
  existingId: string;
  existingCourseId: string;
  days: MeetingDay[];
  overlapMinutes: number;
  candidateStart: string;
  candidateEnd: string;
  existingStart: string;
  existingEnd: string;
}

export interface PlannerFilters {
  openOnly: boolean;
  onlineOnly: boolean;
  days: MeetingDay[];
  time: "any" | "morning" | "afternoon" | "evening";
}
