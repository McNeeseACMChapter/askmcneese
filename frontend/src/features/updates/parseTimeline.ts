import type { Contributor, ProjectUpdate, TimelineRecord, UpdateArea } from "./types";

const EMAIL_RE = /[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}/gi;
const PR_RE = /PR\s*#(\d+)/gi;
const COMMIT_RE = /\bcommits?\s+([a-f0-9]{7,40}(?:\s+[a-f0-9]{7,40})*)/i;
const COMMIT_RANGE_RE = /\bcommits?\s+([a-f0-9]{7,40})\.\.([a-f0-9]{7,40})/i;
const SPRINT_RE = /\bSprint\s+(\d+)\b/i;

const TURNING_POINT_TICKETS = new Set([29, 42, 75, 87]);

/**
 * Canonical chapter membership is explicit by ticket number.
 * Dates alone would misclassify ticket 26 (Jun 19 design-system work
 * that belongs with the /ask chapter) and tickets 27–28 (Jun 15 foundation).
 * Ticket 107 (Aug 20 security documentation) extends chapter 11 past the
 * Aug 17 cutoff described in earlier planning notes — repository CSV wins.
 */
export const CHAPTER_TICKETS: Record<string, number[]> = {
  "project-origin": range(1, 2),
  research: range(3, 5),
  foundation: [...range(6, 25), 27, 28],
  "ask-pipeline": [26, ...range(29, 31)],
  "retrieval-reliability": range(32, 40),
  rccs: range(41, 52),
  governance: range(53, 62),
  "closed-beta": range(63, 76),
  "class-planner-production": range(77, 83),
  grounding: range(84, 87),
  transition: range(88, 107),
};

const AREA_RULES: Array<[UpdateArea, RegExp]> = [
  ["ACM", /\bACM\b|GOV-0|chapter panel|chapter governance|chapter-management|Presence\.io/i],
  ["Class Planner", /Class Planner|Class Search|PostgreSQL|term 202660|1606|Alembic|availability refresh|subject fetch/i],
  ["Crawler", /crawler|ChromaDB|PyPDF2|ingest audit|chunk/i],
  ["Knowledge", /source_registry|domain pack|registry coverage|knowledge\/|taxonomy/i],
  ["Retrieval", /\/ask|\bRAG\b|RCCS|retriev|rerank|citation|hybrid|intent classif|persona|grounding|page read/i],
  ["Frontend", /frontend|React|Framer Motion|composer|mobile|UI\/UX|design system|splash|Vite|Tailwind|TypeScript/i],
  ["Backend", /backend|FastAPI|Django|SSE|Claude|\/health|db schema|orchestrator|supervisor/i],
  ["DevOps", /\.gitignore|GitHub Actions|\bCI\b|Render|Hostinger|subdomain|deploy|\.env|PWA/i],
  ["QA", /\btests?\b|\bQA\b|contract tests|7\/7/i],
  ["Docs", /document|docs\/|README|developer guide|timeline|Hard Stoppage|brand rules/i],
  ["Product", /Sprint|team formation|Project Manager|backlog|reassignment|closed beta|Beta Version/i],
];

const TECHNOLOGY_RULES: Array<[string, RegExp]> = [
  ["React", /\bReact\b/i],
  ["TypeScript", /\bTypeScript\b|\bTS\b/i],
  ["Vite", /\bVite\b/i],
  ["Tailwind CSS", /\bTailwind\b/i],
  ["Framer Motion", /\bFramer Motion\b/i],
  ["Python", /\bPython\b|Python venv/i],
  ["FastAPI", /\bFastAPI\b/i],
  ["Django", /\bDjango\b/i],
  ["Server-Sent Events", /\bSSE\b|server-sent events?/i],
  ["Anthropic Claude", /\bClaude\b|Anthropic/i],
  ["ChromaDB", /\bChromaDB\b/i],
  ["RCCS", /\bRCCS\b/i],
  ["PostgreSQL", /\bPostgreSQL\b/i],
  ["SQLAlchemy", /\bSQLAlchemy\b/i],
  ["Alembic", /\bAlembic\b/i],
  ["Playwright", /\bPlaywright\b/i],
  ["Beautiful Soup", /\bBeautiful Soup\b|BeautifulSoup/i],
  ["PyPDF2", /\bPyPDF2\b/i],
  ["GitHub Actions", /\bGitHub Actions\b|\bCI\b/i],
  ["Render", /\bRender\b/i],
  ["Cloudflare", /\bCloudflare\b/i],
  ["Hostinger", /\bHostinger\b/i],
  ["Node.js / npm", /\bNode\b|npm/i],
  ["Git / GitHub", /\bGitHub\b|git merge|\.gitignore/i],
  ["PWA", /\bPWA\b|service worker/i],
];

const AREA_TECHNOLOGIES: Partial<
  Record<UpdateArea, { introducedAt: number; technologies: string[] }>
> = {
  Frontend: { introducedAt: 20, technologies: ["React", "TypeScript", "Vite"] },
  Backend: { introducedAt: 19, technologies: ["Python", "FastAPI"] },
  Retrieval: {
    introducedAt: 29,
    technologies: ["Python", "FastAPI", "ChromaDB", "Anthropic Claude"],
  },
  Crawler: { introducedAt: 18, technologies: ["Python"] },
  Knowledge: { introducedAt: 38, technologies: ["CSV / JSON"] },
  "Class Planner": {
    introducedAt: 75,
    technologies: ["React", "TypeScript", "FastAPI"],
  },
  Docs: { introducedAt: 18, technologies: ["Plain text / Markdown"] },
};

function range(from: number, to: number): number[] {
  return Array.from({ length: to - from + 1 }, (_, i) => from + i);
}

export function parseCsv(text: string): string[][] {
  const rows: string[][] = [];
  let row: string[] = [];
  let field = "";
  let inQuotes = false;

  for (let i = 0; i < text.length; i += 1) {
    const char = text[i];
    const next = text[i + 1];

    if (inQuotes) {
      if (char === '"' && next === '"') {
        field += '"';
        i += 1;
      } else if (char === '"') {
        inQuotes = false;
      } else {
        field += char;
      }
      continue;
    }

    if (char === '"') {
      inQuotes = true;
    } else if (char === ",") {
      row.push(field);
      field = "";
    } else if (char === "\n" || (char === "\r" && next === "\n")) {
      if (char === "\r") i += 1;
      row.push(field);
      if (row.some((cell) => cell.length > 0)) rows.push(row);
      row = [];
      field = "";
    } else if (char !== "\r") {
      field += char;
    }
  }

  if (field.length > 0 || row.length > 0) {
    row.push(field);
    if (row.some((cell) => cell.length > 0)) rows.push(row);
  }

  return rows;
}

export function stripPrivateData(value: string): string {
  return value
    .replace(EMAIL_RE, "")
    .replace(/\s*email:\s*/gi, " ")
    .replace(/\s{2,}/g, " ")
    .replace(/\s+;/g, ";")
    .trim();
}

export function parseContributors(who: string): Contributor[] {
  return who
    .split(/\s+\+\s+/)
    .map((part) => part.trim())
    .filter(Boolean)
    .map((part) => {
      const match = part.match(/^(.*?)\s+\((.+)\)\s*$/);
      if (!match) return { name: part };
      return { name: match[1].trim(), role: match[2].trim() };
    });
}

export function inferAreas(record: TimelineRecord): UpdateArea[] {
  const haystack = `${record.title} ${record.who} ${record.method} ${record.notes}`;
  const found = AREA_RULES.filter(([, pattern]) => pattern.test(haystack)).map(([area]) => area);
  return found.length > 0 ? [...new Set(found)] : ["Product"];
}

/**
 * Keep delivery tooling and implementation technology separate.
 * Explicit timeline mentions win; after implementation begins, area defaults
 * add the repository-backed stack for records whose How column is abbreviated.
 */
export function inferTechnologies(record: TimelineRecord): string[] {
  const haystack = `${record.title} ${record.method} ${record.notes}`;
  const technologies = TECHNOLOGY_RULES
    .filter(([, pattern]) => pattern.test(haystack))
    .map(([technology]) => technology);

  if (record.ticketNo >= 18) {
    for (const area of inferAreas(record)) {
      const stageStack = AREA_TECHNOLOGIES[area];
      if (stageStack && record.ticketNo >= stageStack.introducedAt) {
        technologies.push(...stageStack.technologies);
      }
    }
  }
  if (record.ticketNo >= 77 && inferAreas(record).includes("Class Planner")) {
    technologies.push("PostgreSQL");
  }

  return [...new Set(technologies)];
}

export function extractCommit(notes: string): string | undefined {
  const rangeMatch = notes.match(COMMIT_RANGE_RE);
  if (rangeMatch) return `${rangeMatch[1]}..${rangeMatch[2]}`;
  const match = notes.match(COMMIT_RE);
  if (!match) {
    const bare = notes.match(/\b([a-f0-9]{7})\b/);
    return bare && /commit/i.test(notes) ? bare[1] : undefined;
  }
  return match[1].split(/\s+/)[0];
}

export function extractPullRequests(notes: string): string | undefined {
  const ids = [...notes.matchAll(PR_RE)].map((match) => match[1]);
  if (ids.length === 0) return undefined;
  return [...new Set(ids)].map((id) => `PR #${id}`).join(" · ");
}

export function extractSprint(notes: string, title: string, method: string): string | undefined {
  const match = `${title} ${method} ${notes}`.match(SPRINT_RE);
  return match ? `Sprint ${match[1]}` : undefined;
}

export function chapterIdForTicket(ticketNo: number): string {
  const found = Object.entries(CHAPTER_TICKETS).find(([, tickets]) => tickets.includes(ticketNo));
  if (!found) {
    throw new Error(`Ticket ${ticketNo} is not assigned to a development chapter`);
  }
  return found[0];
}

export function recordsFromCsv(csv: string): TimelineRecord[] {
  const rows = parseCsv(csv);
  const header = rows[0]?.map((cell) => cell.trim());
  if (!header || header[0] !== "TicketNo") {
    throw new Error("Canonical timeline.csv is missing the TicketNo header");
  }

  return rows.slice(1).map((cells) => {
    const ticketNo = Number(cells[0]);
    if (!Number.isInteger(ticketNo)) {
      throw new Error(`Invalid ticket number: ${cells[0]}`);
    }
    return {
      ticketNo,
      title: (cells[1] ?? "").trim(),
      date: (cells[2] ?? "").trim(),
      who: (cells[3] ?? "").trim(),
      method: (cells[4] ?? "").trim(),
      notes: stripPrivateData(cells[5] ?? ""),
    };
  });
}

export function toProjectUpdate(record: TimelineRecord): ProjectUpdate {
  return {
    ticketNo: record.ticketNo,
    date: record.date,
    title: record.title,
    contributors: parseContributors(record.who),
    method: record.method || undefined,
    notes: record.notes || undefined,
    chapterId: chapterIdForTicket(record.ticketNo),
    areas: inferAreas(record),
    technologies: inferTechnologies(record),
    commit: extractCommit(record.notes),
    pullRequest: extractPullRequests(record.notes),
    sprint: extractSprint(record.notes, record.title, record.method),
    status: "completed",
    turningPoint: TURNING_POINT_TICKETS.has(record.ticketNo),
  };
}

export function assignedTicketNumbers(): number[] {
  return Object.values(CHAPTER_TICKETS).flat().sort((a, b) => a - b);
}
