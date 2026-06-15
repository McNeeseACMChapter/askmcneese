import type { ChatMessage } from "../types";

// Sprint 1 dummy content — clearly labeled demo. NOT real institutional answers.
export const sampleMessages: ChatMessage[] = [
  {
    id: "m1",
    role: "user",
    text: "When is the deadline to apply for admission?",
  },
  {
    id: "m2",
    role: "assistant",
    isDemo: true,
    text: "This is demo content. Once connected to approved McNeese sources, the assistant will answer here with a cited deadline from the official admissions page.",
  },
  {
    id: "m3",
    role: "user",
    text: "Where do I find financial aid information?",
  },
  {
    id: "m4",
    role: "assistant",
    isDemo: true,
    text: "Demo response — real answers will link to the official McNeese Financial Aid page with a last-checked date.",
  },
];
