/**
 * Question-aware answer section validation.
 * Render sections only when content is non-empty, non-generic, and non-duplicative.
 * One fact → one surface: never show the same caveat in body + dates + warnings.
 */

import type { AnswerFact, AnswerType, StructuredAnswer } from "../types";

export type AnswerSectionKind =
  | "direct_answer"
  | "details"
  | "requirements"
  | "steps"
  | "dates"
  | "contacts"
  | "warning"
  | "comparison"
  | "list"
  | "table"
  | "sources"
  | "key_facts";

const GENERIC_PATTERNS = [
  /^no information available\.?$/i,
  /^n\/?a\.?$/i,
  /^none\.?$/i,
  /^not available\.?$/i,
  /^see above\.?$/i,
  /^as mentioned above\.?$/i,
  /^placeholder/i,
  /^example requirement/i,
  /^lorem /i,
  /^dummy /i,
];

const NOTE_LABELS = new Set([
  "note",
  "notes",
  "important",
  "important note",
  "please note",
  "warning",
  "tip",
  "reminder",
  "caveat",
]);

export function normalizeComparableText(value: string): string {
  return value
    .toLowerCase()
    .replace(/[#*_`>\-\[\]().,:;!?"']/g, " ")
    .replace(/\s+/g, " ")
    .trim();
}

function stripInlineMarkdown(value: string): string {
  return value.replace(/\*\*|__/g, "").trim();
}

function isNoteLabel(label: string): boolean {
  return NOTE_LABELS.has(normalizeComparableText(label));
}

function isGenericSentence(value: string): boolean {
  const trimmed = value.trim();
  if (!trimmed) return true;
  if (GENERIC_PATTERNS.some((re) => re.test(trimmed))) return true;
  // One very short vague clause with no digits or proper nouns.
  if (trimmed.length < 12 && !/\d/.test(trimmed)) return true;
  return false;
}

function overlapsDirect(content: string, directAnswer: string): boolean {
  const a = normalizeComparableText(content);
  const b = normalizeComparableText(directAnswer);
  if (!a || !b) return false;
  if (a === b) return true;
  const slice = Math.min(48, a.length, b.length);
  if (slice < 20) return a.includes(b) || b.includes(a);
  return a.includes(b.slice(0, slice)) || b.includes(a.slice(0, slice));
}

function textsOverlap(a: string, b: string): boolean {
  const left = normalizeComparableText(a);
  const right = normalizeComparableText(b);
  if (!left || !right) return false;
  if (left === right) return true;
  const slice = Math.min(60, left.length, right.length);
  if (slice < 24) return left.includes(right) || right.includes(left);
  return left.includes(right.slice(0, slice)) || right.includes(left.slice(0, slice));
}

export function shouldRenderTextSection(
  content: string | undefined,
  directAnswer: string,
): boolean {
  if (!content?.trim()) return false;
  if (isGenericSentence(content)) return false;
  if (overlapsDirect(content, directAnswer)) return false;
  return true;
}

export function shouldRenderFactSection(
  facts: AnswerFact[] | undefined,
  directAnswer: string,
): boolean {
  const usable = (facts ?? []).filter(
    (fact) => fact.label.trim() && fact.value.trim() && !isGenericSentence(fact.value),
  );
  if (usable.length === 0) return false;
  // Reject if every fact merely restates the direct answer.
  const meaningful = usable.filter(
    (fact) => !overlapsDirect(`${fact.label}: ${fact.value}`, directAnswer),
  );
  return meaningful.length > 0;
}

export function shouldRenderItemSection(
  items: string[] | undefined,
  directAnswer: string,
  options?: { minItems?: number; kind?: AnswerSectionKind },
): boolean {
  const minItems = options?.minItems ?? 1;
  const kind = options?.kind;
  const usable = (items ?? [])
    .map((item) => item.trim())
    .filter((item) => item && !isGenericSentence(item))
    .filter((item) => !overlapsDirect(item, directAnswer));
  if (usable.length < minItems) return false;
  // Single obvious sentence should stay in the body, not a "Next steps" card.
  if (kind === "steps" && usable.length < 2) return false;
  return true;
}

export interface PreparedAnswerView {
  type: AnswerType;
  title?: string;
  directAnswer: string;
  bodyMarkdown: string;
  showSummary: boolean;
  summary?: string;
  importantDates: AnswerFact[];
  requirements: string[];
  steps: string[];
  warnings: string[];
  keyFacts: AnswerFact[];
  relatedQuestions: string[];
  showDates: boolean;
  showRequirements: boolean;
  showSteps: boolean;
  showWarnings: boolean;
  showKeyFacts: boolean;
  showRelated: boolean;
}

function stripLeadingTitle(markdown: string, title?: string): string {
  if (!title) return markdown;
  const lines = markdown.split("\n");
  const first = lines[0]?.trim() ?? "";
  const heading = first.replace(/^#{1,3}\s+/, "").replace(/^\*\*|\*\*$/g, "").trim();
  if (heading.toLowerCase() === title.toLowerCase()) {
    return lines.slice(1).join("\n").replace(/^\n+/, "");
  }
  return markdown;
}

function summaryOverlapsMarkdown(summary: string | undefined, markdown: string): boolean {
  if (!summary?.trim() || !markdown.trim()) return false;
  const s = normalizeComparableText(summary);
  const m = normalizeComparableText(markdown);
  if (!s || !m) return false;
  if (m.startsWith(s.slice(0, Math.min(48, s.length)))) return true;
  const firstPara = m.split(/\n+/).find((p) => p.trim().length > 20) ?? m;
  return (
    firstPara.startsWith(s.slice(0, Math.min(40, s.length))) ||
    s.startsWith(firstPara.slice(0, 40))
  );
}

/** Drop Note:/Important: lines whose body was promoted into warnings or date cards. */
function stripPromotedLines(markdown: string, promoted: string[]): string {
  if (!promoted.length) return markdown;
  const keys = promoted.map(normalizeComparableText).filter(Boolean);
  const kept: string[] = [];
  for (const line of markdown.split("\n")) {
    const raw = line.trim().replace(/^[-*•]\s+/, "");
    const noteMatch = raw.match(
      /^(?:\*\*)?(note|important|warning|tip|please note)(?:\*\*)?:\s*(.+)$/i,
    );
    if (noteMatch) {
      const body = normalizeComparableText(stripInlineMarkdown(noteMatch[2] ?? ""));
      if (
        keys.some(
          (key) =>
            body.includes(key.slice(0, Math.min(48, key.length))) ||
            key.includes(body.slice(0, Math.min(48, body.length))),
        )
      ) {
        continue;
      }
    }
    // Also drop bare paragraphs that are verbatim duplicates of a promoted caveat.
    const plain = normalizeComparableText(stripInlineMarkdown(raw));
    if (
      plain.length > 40 &&
      keys.some(
        (key) =>
          plain === key ||
          (plain.length > 60 && key.includes(plain.slice(0, 60))) ||
          (key.length > 60 && plain.includes(key.slice(0, 60))),
      )
    ) {
      continue;
    }
    kept.push(line);
  }
  return kept
    .join("\n")
    .replace(/\n{3,}/g, "\n\n")
    .trim();
}

function isProseNoteFact(fact: AnswerFact): boolean {
  if (isNoteLabel(fact.label)) return true;
  // Long caveat prose is not a date card.
  return fact.value.trim().length > 160;
}

/**
 * Build a render-ready view: direct answer first; optional sections only when justified.
 */
export function prepareAnswerView(answer: StructuredAnswer): PreparedAnswerView {
  let bodyMarkdown = stripLeadingTitle(answer.contentMarkdown, answer.title);

  // Dates: keep real calendar facts only — never Note/Important prose cards.
  const importantDates = (answer.importantDates ?? []).filter(
    (f) => f.label.trim() && f.value.trim() && !isProseNoteFact(f),
  );

  let warnings = (answer.warnings ?? [])
    .map((item) => stripInlineMarkdown(item))
    .filter(Boolean);

  // Cross-dedupe warnings against date values (and each other).
  const dateValues = importantDates.map((f) => f.value);
  warnings = warnings.filter(
    (warning, index) =>
      !warnings.slice(0, index).some((prior) => textsOverlap(prior, warning)) &&
      !dateValues.some((value) => textsOverlap(value, warning)),
  );

  // One surface: if a caveat appears in the body and in warnings, strip body copy.
  bodyMarkdown = stripPromotedLines(bodyMarkdown, [
    ...warnings,
    ...importantDates.map((f) => `${f.label}: ${f.value}`),
  ]);

  const showSummary =
    Boolean(answer.summary?.trim()) &&
    !summaryOverlapsMarkdown(answer.summary, bodyMarkdown) &&
    shouldRenderTextSection(answer.summary, bodyMarkdown);

  const directAnswer =
    (showSummary ? answer.summary : undefined)?.trim() ||
    bodyMarkdown
      .split(/\n+/)
      .map((line) => line.replace(/^#{1,3}\s+/, "").replace(/\*\*/g, "").trim())
      .find((line) => line.length > 0) ||
    bodyMarkdown.trim();

  // After body strip, drop warnings that still only restate the remaining lead.
  warnings = warnings.filter((warning) => !overlapsDirect(warning, directAnswer));

  const requirements = (answer.requirements ?? []).map((i) => i.trim()).filter(Boolean);
  const steps = (answer.steps ?? []).map((i) => i.trim()).filter(Boolean);
  const keyFacts = (answer.keyFacts ?? []).filter((f) => f.label.trim() && f.value.trim());
  const relatedQuestions = (answer.relatedQuestions ?? []).map((i) => i.trim()).filter(Boolean);

  // Factual / location / short answers: suppress card grids even if backend sent leftovers.
  const suppressCards =
    answer.type === "factual" ||
    answer.type === "location" ||
    answer.type === "conversational" ||
    answer.type === "clarification";

  const showDates =
    shouldRenderFactSection(importantDates, directAnswer) &&
    (answer.type === "deadline" || importantDates.length >= 2 || !suppressCards);

  const showRequirements =
    shouldRenderItemSection(requirements, directAnswer, { minItems: 1, kind: "requirements" }) &&
    (answer.type === "process" ||
      requirements.length >= 2 ||
      bodyMarkdown.length > 280 ||
      !suppressCards);

  const showSteps = shouldRenderItemSection(steps, directAnswer, {
    minItems: 2,
    kind: "steps",
  });

  const showWarnings = shouldRenderItemSection(warnings, directAnswer, {
    minItems: 1,
    kind: "warning",
  });

  // Key facts cards are last-resort only — never default "Key Information".
  const showKeyFacts =
    !suppressCards &&
    !showDates &&
    !showRequirements &&
    shouldRenderFactSection(keyFacts, directAnswer) &&
    keyFacts.length >= 3 &&
    (answer.type === "comparison" || answer.type === "partial");

  const showRelated = shouldRenderItemSection(relatedQuestions, directAnswer, {
    minItems: 1,
    kind: "list",
  });

  return {
    type: answer.type,
    title: answer.title,
    directAnswer,
    bodyMarkdown,
    showSummary,
    summary: answer.summary,
    importantDates,
    requirements,
    steps,
    warnings,
    keyFacts,
    relatedQuestions,
    showDates,
    showRequirements,
    showSteps,
    showWarnings,
    showKeyFacts,
    showRelated,
  };
}
