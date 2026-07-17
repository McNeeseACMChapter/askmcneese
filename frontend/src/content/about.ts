import type { LucideIcon } from "lucide-react";
import {
  BookOpen,
  Database,
  FileSearch,
  MessageCircleQuestion,
  PenLine,
} from "lucide-react";

export interface ProcessStage {
  id: string;
  title: string;
  description: string;
  icon: LucideIcon;
}

export interface ContributionArea {
  id: string;
  title: string;
  responsibilities: string;
}

export interface MethodologyStep {
  id: string;
  title: string;
  description: string;
}

export interface RoadmapPhase {
  id: "completed" | "current" | "next" | "future";
  title: string;
  items: string[];
}

export const aboutHero = {
  title: "AskMcNeese",
  subtitle:
    "A student-built campus intelligence platform grounded in reliable McNeese information.",
  primaryCta: { label: "Ask a Question", to: "/ask" },
  secondaryCta: { label: "About the team", to: "/about" },
};

export const aboutPurpose = {
  heading: "What AskMcNeese does",
  paragraphs: [
    "Campus information is spread across catalogs, department pages, student services portals, and policy documents. Students and campus community members need clear answers without hunting through dozens of sources.",
    "AskMcNeese brings approved McNeese sources into one retrieval-backed assistant. Answers are composed from retrieved context and presented with citations so you can verify what you read against official pages.",
    "The platform is built by the McNeese ACM Student Chapter as a student-led project focused on trusted campus information access—not a generic chatbot template.",
  ],
};

export const processStages: ProcessStage[] = [
  {
    id: "ask",
    title: "Ask",
    description: "You submit a campus question in plain language.",
    icon: MessageCircleQuestion,
  },
  {
    id: "retrieve",
    title: "Retrieve",
    description: "Approved McNeese sources are searched from the knowledge base.",
    icon: Database,
  },
  {
    id: "evaluate",
    title: "Evaluate",
    description: "Retrieved passages are ranked for relevance to your question.",
    icon: FileSearch,
  },
  {
    id: "compose",
    title: "Compose",
    description: "A structured answer is composed from the best-matching context.",
    icon: PenLine,
  },
  {
    id: "cite",
    title: "Cite",
    description: "Sources are presented with links so you can read the originals.",
    icon: BookOpen,
  },
];

export const contributionAreas: ContributionArea[] = [
  {
    id: "project-management",
    title: "Project Management",
    responsibilities:
      "Sprint planning, milestone tracking, documentation hygiene, and coordination across frontend, backend, and content workstreams.",
  },
  {
    id: "frontend-engineering",
    title: "Frontend Engineering",
    responsibilities:
      "React application shell, Ask experience, streaming UI, routing, accessibility, and visual system implementation.",
  },
  {
    id: "backend-engineering",
    title: "Backend Engineering",
    responsibilities:
      "FastAPI services, Ask pipeline, SSE activity events, structured answer contracts, and API health endpoints.",
  },
  {
    id: "ai-retrieval",
    title: "AI and Retrieval",
    responsibilities:
      "Knowledge ingestion, chunking, vector search, prompt design, and answer quality evaluation against approved sources.",
  },
  {
    id: "devops",
    title: "DevOps",
    responsibilities:
      "Local and deployment configuration, environment documentation, health checks, and build verification across frontend and backend.",
  },
  {
    id: "content-quality",
    title: "Content and Quality",
    responsibilities:
      "Source registry maintenance, citation accuracy review, test coverage, and runtime validation against real Ask scenarios.",
  },
  {
    id: "design-research",
    title: "Design and Research",
    responsibilities:
      "Editorial typography, glass surfaces, responsive composition, user research, and campus-appropriate visual identity.",
  },
];

export const advisorSection = {
  roleTitle: "Project Advisor",
  heading: "Dr. Vipin Menon",
  paragraphs: [
    "Dr. Vipin Menon provides academic direction and oversight for AskMcNeese. He validates the product vision and sprint deliverables led by Project Manager Prince Pudasaini, keeping the work aligned with McNeese expectations for responsible, source-grounded campus information.",
    "Advisor involvement includes reviewing major milestones, confirming that retrieval and citation practices meet academic integrity expectations, and helping the student team balance innovation with trustworthy campus information access.",
  ],
  responsibilities: [
    "Academic direction on project scope and methodology",
    "Validation of product vision and sprint outcomes",
    "Guidance on responsible AI and source-grounded answers",
    "Institutional alignment with McNeese information practices",
  ],
};

export const teamSection = {
  heading: "Built by McNeese ACM students",
  intro:
    "AskMcNeese sits under the McNeese ACM Student Chapter. The chain of command below shows how chapter leadership, academic advising, and the delivery team connect—then contribution areas detail the work each lane owns.",
  collaboration:
    "The team follows sprint-based development on the dev branch, with milestones promoted to main after review. Frontend, backend, retrieval, and design contributors coordinate through shared documentation and change logs.",
  governance:
    "Feature branches branch from dev. Direct pushes to main are reserved for reviewed milestones. Operational panels, health endpoints, and change logs keep the working state visible.",
  acknowledgments:
    "The McNeese ACM Student Chapter provides the organizational home for this project. Campus offices and source owners whose approved pages feed the knowledge base enable grounded answers.",
};

export const methodologyContent = {
  heading: "How answers are produced",
  intro:
    "AskMcNeese follows a retrieval-augmented pipeline. The assistant does not invent campus facts—it composes answers from approved sources and shows where information came from.",
  steps: [
    {
      id: "question",
      title: "Question",
      description: "Your prompt is received along with optional conversation history and a source scope (knowledge base or web search when enabled).",
    },
    {
      id: "retrieval",
      title: "Source retrieval",
      description: "Relevant passages are retrieved from the approved McNeese knowledge base using vector search over ingested documents.",
    },
    {
      id: "evaluation",
      title: "Relevance evaluation",
      description: "Retrieved chunks are ranked and filtered so the model receives the most pertinent context for your question.",
    },
    {
      id: "generation",
      title: "Answer generation",
      description: "A language model composes a structured answer from retrieved context, following the project's answer schema and tone guidelines.",
    },
    {
      id: "citation",
      title: "Citation presentation",
      description: "Sources are deduplicated by normalized URL and displayed with titles and links. Distinct URLs with similar titles remain separate.",
    },
    {
      id: "feedback",
      title: "Feedback and correction",
      description: "Users can report unhelpful answers. Feedback informs content review and future retrieval improvements.",
    },
  ] satisfies MethodologyStep[],
  limitations: {
    heading: "Known limitations",
    statements: [
      "Answers depend on the coverage and freshness of ingested McNeese sources. Empty or stale collections may produce incomplete responses.",
      "The assistant is not a substitute for official academic advising, financial aid counseling, or registrar decisions.",
      "Claim-level citation mapping (linking each sentence to a specific source) is not yet available.",
      "Server-side conversation history and related-question generation remain future work.",
      "Real browser zoom, mobile keyboard overlap, and mid-stream network interruption UX require additional manual validation.",
    ],
  },
};

export const transparencySection = {
  heading: "Development transparency",
  intro:
    "Major changes are recorded in repository change logs and validated with automated tests before milestone promotion.",
  currentPhase: "Visual product overhaul and public About/Updates routes following Core Stabilization Pass 1.",
  links: [
    { label: "Project updates", to: "/updates" },
  ],
};

export const finalCta = {
  heading: "Ready to ask McNeese?",
  body: "Get source-grounded campus answers with citations you can verify.",
  buttonLabel: "Ask McNeese",
  to: "/ask",
};

export const roadmapPhases: RoadmapPhase[] = [
  {
    id: "completed",
    title: "Completed",
    items: [
      "RAG-backed Ask pipeline with SSE activity events",
      "Progressive streaming with one provisional and one final assistant message",
      "Citation deduplication by normalized URL",
      "Activity narration aligned with backend events",
      "Safe Ask error surfacing and silent user abort",
      "Core Stabilization Pass 1 (2026-07-12)",
      "Frontend unit test suite (35 tests) and backend unit tests (18 tests)",
    ],
  },
  {
    id: "current",
    title: "Current",
    items: [
      "Visual system overhaul: editorial typography, glass surfaces, semantic tokens",
      "Public routes for About, Updates, Status, Settings, and Feedback",
      "Live Answer Progress panel and expanded answer article presentation",
      "Contextual sidebar and mobile navigation consolidation",
      "Runtime validation documentation for remaining manual checks",
    ],
  },
  {
    id: "next",
    title: "Next",
    items: [
      "Claim-level citation mapping",
      "Server-side conversation history",
      "Related-questions generation with backend contract",
      "Manual accessibility and responsive validation matrix",
      "ask.py service split and common/ extraction",
    ],
  },
  {
    id: "future",
    title: "Future",
    items: [
      "Authentication and role-aware access",
      "Student personalization and dashboard experiences",
      "ACM workspace for chapter operations",
      "Broad design-token revision as the system matures",
    ],
  },
];

/** About is a single page — kept empty so legacy imports stay typed. */
export const aboutNavItems: Array<{ label: string; to: string; end?: boolean }> = [];
