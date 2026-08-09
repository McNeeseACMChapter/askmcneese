import type { Course } from "./plannerTypes";

const termId = "fall-2026";
const updatedAt = "2026-08-08T12:00:00Z";

export const PLANNER_COURSES: Course[] = [
  {
    id: "csci-308",
    subject: "CSCI",
    courseNumber: "308",
    title: "Software Engineering",
    credits: 3,
    sections: [
      {
        id: "csci-308-001", courseId: "csci-308", termId, crn: "12345", sectionNumber: "001",
        instructor: "Dr. Maya Chen", modality: "In person", seatsRemaining: 14, status: "open", updatedAt,
        meetings: [{ type: "Lecture", days: ["M", "W", "F"], startTime: "10:00", endTime: "10:50", building: "Drew", room: "214" }],
      },
      {
        id: "csci-308-002", courseId: "csci-308", termId, crn: "12346", sectionNumber: "002",
        instructor: "Marcus Thibodeaux", modality: "In person", seatsRemaining: 1, status: "open", updatedAt,
        meetings: [{ type: "Lecture", days: ["T", "R"], startTime: "09:30", endTime: "10:45", building: "Drew", room: "205" }],
      },
      {
        id: "csci-308-003", courseId: "csci-308", termId, crn: "12347", sectionNumber: "003",
        instructor: "Dr. Ana Ruiz", modality: "Hybrid", seatsRemaining: 8, status: "open", updatedAt,
        meetings: [{ type: "Lecture", days: ["T"], startTime: "18:00", endTime: "20:45", building: "Drew", room: "201" }],
      },
      {
        id: "csci-308-004", courseId: "csci-308", termId, crn: "12348", sectionNumber: "004",
        instructor: "Staff", modality: "Online", seatsRemaining: 0, status: "closed", updatedAt,
        meetings: [{ type: "Online", days: [], startTime: null, endTime: null }],
      },
    ],
  },
  {
    id: "math-191", subject: "MATH", courseNumber: "191", title: "Calculus I", credits: 4,
    sections: [
      {
        id: "math-191-001", courseId: "math-191", termId, crn: "23456", sectionNumber: "001",
        instructor: "Dr. Elise Moreau", modality: "In person", seatsRemaining: 6, status: "open", updatedAt,
        meetings: [
          { type: "Lecture", days: ["M", "W", "F"], startTime: "10:30", endTime: "11:20", building: "Kirkman", room: "105" },
          { type: "Lab", days: ["R"], startTime: "14:00", endTime: "14:50", building: "Kirkman", room: "112" },
        ],
      },
      {
        id: "math-191-002", courseId: "math-191", termId, crn: "23457", sectionNumber: "002",
        instructor: "Avery Landry", modality: "In person", seatsRemaining: 12, status: "open", updatedAt,
        meetings: [
          { type: "Lecture", days: ["M", "W", "F"], startTime: "13:00", endTime: "13:50", building: "Kirkman", room: "105" },
          { type: "Lab", days: ["T"], startTime: "14:00", endTime: "14:50", building: "Kirkman", room: "112" },
        ],
      },
    ],
  },
  {
    id: "biol-101", subject: "BIOL", courseNumber: "101", title: "General Biology I", credits: 4,
    sections: [
      {
        id: "biol-101-001", courseId: "biol-101", termId, crn: "34567", sectionNumber: "001",
        instructor: "Dr. Kennedy Wilson", modality: "In person", seatsRemaining: 20, status: "open", updatedAt,
        meetings: [
          { type: "Lecture", days: ["T", "R"], startTime: "11:00", endTime: "12:15", building: "Kaufman", room: "128" },
          { type: "Lab", days: ["W"], startTime: "14:00", endTime: "16:50", building: "Kaufman", room: "120" },
        ],
      },
      {
        id: "biol-101-090", courseId: "biol-101", termId, crn: "34568", sectionNumber: "090",
        instructor: "Dr. Kennedy Wilson", modality: "Online", seatsRemaining: null, status: "open", updatedAt,
        meetings: [{ type: "Online", days: [], startTime: null, endTime: null }],
      },
    ],
  },
  {
    id: "engl-101", subject: "ENGL", courseNumber: "101", title: "Academic Writing and Inquiry", credits: 3,
    sections: [{
      id: "engl-101-001", courseId: "engl-101", termId, crn: "45678", sectionNumber: "001",
      instructor: "Gabrielle Fontenot", modality: "In person", seatsRemaining: 9, status: "open", updatedAt,
      meetings: [{ type: "Lecture", days: ["T", "R"], startTime: "08:00", endTime: "09:15", building: "Farrar", room: "112" }],
    }],
  },
  {
    id: "hist-201", subject: "HIST", courseNumber: "201", title: "American History to 1877", credits: 3,
    sections: [{
      id: "hist-201-090", courseId: "hist-201", termId, crn: "56789", sectionNumber: "090",
      instructor: undefined, modality: "Online", seatsRemaining: 18, status: "open", updatedAt,
      meetings: [{ type: "Online", days: [], startTime: null, endTime: null }],
    }],
  },
];

export const PLANNER_TERM = {
  id: termId,
  label: "Fall 2026",
  timezone: "America/Chicago",
  classStartDate: "2026-08-24",
  classEndDate: "2026-12-07",
  noClassDates: [
    "2026-09-07",
    "2026-10-08",
    "2026-10-09",
    "2026-11-25",
    "2026-11-26",
    "2026-11-27",
    "2026-11-28",
  ],
} as const;
