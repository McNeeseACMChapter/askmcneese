import { useMemo } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { BentoFactGrid, type BentoFact } from "./BentoFactGrid";

interface AnswerCardProps {
  content: string;
}

interface ParsedAnswer {
  title: string | null;
  summary: string;
  facts: BentoFact[];
  notes: string[];
  bodyContent: string;
}

export function AnswerCard({ content }: AnswerCardProps) {
  const parsed = useMemo(() => parseAnswerContent(content), [content]);

  return (
    <div className="rounded-2xl rounded-bl-md border border-border bg-surface shadow-soft overflow-hidden">
      {/* Title */}
      {parsed.title && (
        <div className="border-b border-border-subtle bg-surface-sunken px-4 py-3">
          <h3 className="text-sm font-semibold text-text-primary flex items-center gap-2">
            <svg className="h-4 w-4 text-mcneese-blue flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            {parsed.title}
          </h3>
        </div>
      )}

      <div className="p-4 space-y-4">
        {/* Summary */}
        {parsed.summary && (
          <p className="text-sm text-text-secondary leading-relaxed">
            {parsed.summary}
          </p>
        )}

        {/* Bento Facts Grid */}
        {parsed.facts.length > 0 && (
          <BentoFactGrid facts={parsed.facts} />
        )}

        {/* Body content (rendered markdown) */}
        {parsed.bodyContent && (
          <div className="prose-answer">
            <ReactMarkdown
              remarkPlugins={[remarkGfm]}
              components={markdownComponents}
            >
              {parsed.bodyContent}
            </ReactMarkdown>
          </div>
        )}

        {/* Notes/Callouts */}
        {parsed.notes.length > 0 && (
          <div className="space-y-2">
            {parsed.notes.map((note, idx) => (
              <div
                key={idx}
                className="flex gap-2 rounded-lg bg-accent-subtle/50 p-3 text-xs text-text-secondary"
              >
                <svg className="h-4 w-4 text-mcneese-gold flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
                <span>{note}</span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function parseAnswerContent(content: string): ParsedAnswer {
  const lines = content.split("\n");
  let title: string | null = null;
  let summary = "";
  const facts: BentoFact[] = [];
  const notes: string[] = [];
  const bodyLines: string[] = [];

  let inFactSection = false;
  let foundFirstParagraph = false;

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i].trim();

    // Skip empty lines at the start
    if (!line && !foundFirstParagraph) continue;

    // Extract title from ## or ###
    if (line.startsWith("## ") || line.startsWith("### ")) {
      const extractedTitle = line.replace(/^#{2,3}\s*/, "").trim();
      if (!title) {
        title = extractedTitle;
        continue;
      }
    }

    // Extract title from **Title** format at the start
    if (!title && line.startsWith("**") && line.endsWith("**")) {
      title = line.replace(/^\*\*|\*\*$/g, "").trim();
      continue;
    }

    // Detect deadline/fact patterns
    const factMatch = line.match(/^[-•*]\s*\*?\*?([^:*]+)\*?\*?:\s*(.+)$/);
    if (factMatch) {
      const label = factMatch[1].replace(/\*\*/g, "").trim();
      const value = factMatch[2].replace(/\*\*/g, "").trim();
      
      // Check if this looks like a date/deadline or key fact
      if (isKeyFact(label, value)) {
        facts.push({ label, value, icon: getFactIcon(label) });
        inFactSection = true;
        continue;
      }
    }

    // Detect "Label: Value" pattern (without bullet)
    const colonMatch = line.match(/^\*?\*?([^:*]+)\*?\*?:\s*(.+)$/);
    if (colonMatch && !line.startsWith("http") && !line.includes("://")) {
      const label = colonMatch[1].replace(/\*\*/g, "").trim();
      const value = colonMatch[2].replace(/\*\*/g, "").trim();
      
      if (isKeyFact(label, value) && label.length < 30) {
        facts.push({ label, value, icon: getFactIcon(label) });
        inFactSection = true;
        continue;
      }
    }

    // Detect notes/important callouts
    if (line.toLowerCase().startsWith("note:") || 
        line.toLowerCase().startsWith("important:") ||
        line.toLowerCase().startsWith("tip:")) {
      notes.push(line.replace(/^(note|important|tip):\s*/i, ""));
      continue;
    }

    // Skip source references in the body
    if (line.toLowerCase().includes("source:") || 
        line.toLowerCase().startsWith("sources:") ||
        line.match(/^\[\d+\]/) ||
        line.match(/^source\s*\d*:/i)) {
      continue;
    }

    // First non-title paragraph becomes summary
    if (!foundFirstParagraph && line && !line.startsWith("-") && !line.startsWith("*") && !line.startsWith("#")) {
      summary = cleanMarkdown(line);
      foundFirstParagraph = true;
      continue;
    }

    // Everything else goes to body
    if (line && !inFactSection) {
      bodyLines.push(line);
    }

    // Reset fact section on empty line
    if (!line) {
      inFactSection = false;
    }
  }

  // Clean up body content - remove source references and clean markdown
  let bodyContent = bodyLines
    .filter(line => !line.toLowerCase().includes("source"))
    .filter(line => !line.match(/^\[\d+\]/))
    .join("\n")
    .trim();

  // If we have facts, don't duplicate them in body
  if (facts.length > 0) {
    bodyContent = "";
  }

  return { title, summary, facts, notes, bodyContent };
}

function isKeyFact(label: string, value: string): boolean {
  const dateKeywords = ["deadline", "date", "application", "fall", "spring", "summer", "semester", "due", "start", "end", "open", "close"];
  const factKeywords = ["gpa", "score", "requirement", "fee", "cost", "time", "hours", "location", "phone", "email", "address"];
  
  const labelLower = label.toLowerCase();
  
  // Check if label contains date/fact keywords
  if (dateKeywords.some(k => labelLower.includes(k)) || factKeywords.some(k => labelLower.includes(k))) {
    return true;
  }
  
  // Check if value looks like a date
  if (value.match(/\b(january|february|march|april|may|june|july|august|september|october|november|december)\b/i)) {
    return true;
  }
  
  // Check if value is short (likely a fact, not a sentence)
  if (value.length < 50 && !value.includes(".")) {
    return true;
  }
  
  return false;
}

function getFactIcon(label: string): "calendar" | "info" | "clock" | "location" | "dollar" {
  const labelLower = label.toLowerCase();
  
  if (labelLower.includes("deadline") || labelLower.includes("date") || labelLower.includes("application")) {
    return "calendar";
  }
  if (labelLower.includes("time") || labelLower.includes("hours")) {
    return "clock";
  }
  if (labelLower.includes("location") || labelLower.includes("address") || labelLower.includes("where")) {
    return "location";
  }
  if (labelLower.includes("fee") || labelLower.includes("cost") || labelLower.includes("price")) {
    return "dollar";
  }
  
  return "info";
}

function cleanMarkdown(text: string): string {
  return text
    .replace(/\*\*/g, "")
    .replace(/\*/g, "")
    .replace(/#{1,6}\s*/g, "")
    .replace(/\[([^\]]+)\]\([^)]+\)/g, "$1")
    .trim();
}

const markdownComponents = {
  p: ({ children }: { children?: React.ReactNode }) => (
    <p className="text-sm text-text-primary leading-relaxed mb-2 last:mb-0">{children}</p>
  ),
  ul: ({ children }: { children?: React.ReactNode }) => (
    <ul className="text-sm text-text-primary space-y-1 ml-4 list-disc">{children}</ul>
  ),
  ol: ({ children }: { children?: React.ReactNode }) => (
    <ol className="text-sm text-text-primary space-y-1 ml-4 list-decimal">{children}</ol>
  ),
  li: ({ children }: { children?: React.ReactNode }) => (
    <li className="text-sm text-text-primary">{children}</li>
  ),
  a: ({ href, children }: { href?: string; children?: React.ReactNode }) => (
    <a 
      href={href} 
      target="_blank" 
      rel="noopener noreferrer"
      className="text-mcneese-blue hover:underline"
    >
      {children}
    </a>
  ),
  strong: ({ children }: { children?: React.ReactNode }) => (
    <strong className="font-semibold text-text-primary">{children}</strong>
  ),
  em: ({ children }: { children?: React.ReactNode }) => (
    <em className="italic">{children}</em>
  ),
  h1: ({ children }: { children?: React.ReactNode }) => (
    <h4 className="text-base font-semibold text-text-primary mt-3 mb-1">{children}</h4>
  ),
  h2: ({ children }: { children?: React.ReactNode }) => (
    <h4 className="text-base font-semibold text-text-primary mt-3 mb-1">{children}</h4>
  ),
  h3: ({ children }: { children?: React.ReactNode }) => (
    <h5 className="text-sm font-semibold text-text-primary mt-2 mb-1">{children}</h5>
  ),
  code: ({ children }: { children?: React.ReactNode }) => (
    <code className="bg-bg-secondary px-1.5 py-0.5 rounded text-xs font-mono">{children}</code>
  ),
  blockquote: ({ children }: { children?: React.ReactNode }) => (
    <blockquote className="border-l-2 border-mcneese-blue/30 pl-3 italic text-text-secondary">{children}</blockquote>
  ),
};
