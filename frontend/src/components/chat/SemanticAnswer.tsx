import { memo, useMemo } from "react";
import { motion, useReducedMotion } from "framer-motion";
import { normalizeChatMessage } from "../../lib/answerModel";
import { prepareAnswerView } from "../../lib/answerSections";
import { MarkdownRenderer } from "../../lib/markdown";
import type { AnswerFact, AnswerType, ChatMessage } from "../../types";
import { CitationGroup } from "./CitationGroup";

/**
 * Direct-first answer surface.
 * Structured sections render only when prepareAnswerView validates them.
 */
export const SemanticAnswer = memo(function SemanticAnswer({
  message,
}: {
  message: ChatMessage;
}) {
  const answer = normalizeChatMessage(message);
  const pattern = answer.type;
  const isStreaming = message.isStreaming === true;
  const reduceMotion = useReducedMotion();

  const view = useMemo(
    () => (isStreaming ? null : prepareAnswerView(answer)),
    // eslint-disable-next-line react-hooks/exhaustive-deps -- answer object identity; fields drive render
    [
      isStreaming,
      answer.type,
      answer.title,
      answer.summary,
      answer.contentMarkdown,
      answer.keyFacts,
      answer.importantDates,
      answer.requirements,
      answer.steps,
      answer.warnings,
      answer.relatedQuestions,
      answer.sources,
    ],
  );

  if (pattern === "backend_failure" || message.isError) {
    return (
      <div className="assistantMessage assistantMessageError answerShell answerSurface">
        <p className="answerCardTitleStrong">We could not complete that answer.</p>
        <p className="answerErrorBody">
          {message.text || "I couldn’t complete that request. Please try again."}
        </p>
      </div>
    );
  }

  // Streaming: continuous editorial text only — never promote incomplete sections.
  if (isStreaming) {
    const body = message.text || answer.contentMarkdown || "";
    return (
      <div className="assistantMessage answerShell answerSurface answerSurfaceStreaming" aria-busy="true">
        <div className="answerReadingColumn">
          {body.trim() ? (
            <MarkdownRenderer content={body} hasTitle={false} />
          ) : (
            <p className="answerBody text-text-muted">Preparing your answer…</p>
          )}
        </div>
      </div>
    );
  }

  if (pattern === "no_source") {
    return (
      <div className="assistantMessage answerShell answerSurface">
        <div className="answerReadingColumn">
          <p className="answerDirectLead">
            {answer.summary ||
              answer.contentMarkdown ||
              "I could not find enough official McNeese information for that question."}
          </p>
          <p className="answerHelperText">
            Try rephrasing, or switch to McNeese only to search approved campus pages.
          </p>
        </div>
      </div>
    );
  }

  if (!view) return null;

  const hasSupporting =
    view.showDates ||
    view.showRequirements ||
    view.showSteps ||
    view.showWarnings ||
    view.showKeyFacts ||
    view.showRelated;

  const isMinimal =
    !hasSupporting &&
    !view.showSummary &&
    view.bodyMarkdown.trim().length < 280 &&
    !view.title;

  return (
    <motion.div
      className={`assistantMessage answerShell answerSurface${isMinimal ? " answerSurfaceMinimal" : ""}`}
      initial={reduceMotion ? false : { opacity: 0.01, y: 6 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: reduceMotion ? 0 : 0.22, ease: [0.2, 0, 0, 1] }}
    >
      <div className="answerReadingColumn">
        <AnswerStatus type={view.type} confidence={answer.confidence} />

        {view.title && <h2 className="answerTitle">{view.title}</h2>}

        {/* Direct answer — unboxed editorial lead */}
        {view.showSummary && view.summary && (
          <p className="answerDirectLead">{view.summary}</p>
        )}

        {view.bodyMarkdown.trim() && (
          <MarkdownRenderer content={view.bodyMarkdown} hasTitle={Boolean(view.title)} />
        )}
      </div>

      {(hasSupporting || answer.sources.length > 0) && (
        <div className="answerSupporting">
          {view.showDates && <DateCallout facts={view.importantDates} />}
          {view.showRequirements && (
            <EditorialList title="Requirements" items={view.requirements} />
          )}
          {view.showSteps && <EditorialList title="Steps" items={view.steps} ordered />}
          {view.showWarnings && (
            <EditorialList title="Please note" items={view.warnings} warning />
          )}
          {view.showKeyFacts && <EditorialFactList facts={view.keyFacts} />}

          {answer.sources.length > 0 && (
            <section className="answerSourcesBlock" data-sources>
              <CitationGroup citations={answer.sources} />
            </section>
          )}

          {view.showRelated && (
            <EditorialList title="Related questions" items={view.relatedQuestions} />
          )}
        </div>
      )}
    </motion.div>
  );
});

function AnswerStatus({
  type,
  confidence,
}: {
  type: AnswerType;
  confidence?: "high" | "medium" | "low";
}) {
  if (type === "conversational" || type === "clarification") {
    return null;
  }
  if (type === "factual") {
    return confidence === "low" ? (
      <p className="answerWarningLabel">Limited official sources</p>
    ) : null;
  }
  const labels: Partial<Record<AnswerType, string>> = {
    deadline: "Deadlines & dates",
    process: "Process guide",
    comparison: "Comparison",
    location: "Campus location",
    partial: "Partial answer",
  };
  const label = labels[type];
  if (!label) return null;
  return <p className="answerPatternLabel">{label}</p>;
}

/** Dates as a compact callout — not a bento card grid. */
function DateCallout({ facts }: { facts: AnswerFact[] }) {
  if (!facts.length) return null;
  return (
    <section className="answerSection answerCallout">
      <h3 className="answerSectionLabel">Important dates</h3>
      <ul className="answerInlineFactList">
        {facts.map((fact, index) => (
          <li key={`${fact.label}-${index}`}>
            <span className="answerInlineFactLabel">{fact.label}</span>
            <span className="answerInlineFactValue">{fact.value}</span>
          </li>
        ))}
      </ul>
    </section>
  );
}

function EditorialList({
  title,
  items,
  ordered = false,
  warning = false,
}: {
  title: string;
  items: string[];
  ordered?: boolean;
  warning?: boolean;
}) {
  if (!items.length) return null;
  const List = ordered ? "ol" : "ul";
  return (
    <section
      className={`answerSection${warning ? " answerCalloutWarning" : ""}`}
    >
      <h3 className="answerSectionLabel">{title}</h3>
      <List className={`answerList ${ordered ? "list-decimal" : "list-disc"}`}>
        {items.map((item, index) => (
          <li key={`${item.slice(0, 24)}-${index}`}>{item}</li>
        ))}
      </List>
    </section>
  );
}

/** Rare fallback — plain list, not bordered fact cards. */
function EditorialFactList({ facts }: { facts: AnswerFact[] }) {
  if (!facts.length) return null;
  return (
    <section className="answerSection">
      <h3 className="answerSectionLabel">Details</h3>
      <ul className="answerInlineFactList">
        {facts.map((fact, index) => (
          <li key={`${fact.label}-${index}`}>
            <span className="answerInlineFactLabel">{fact.label}</span>
            <span className="answerInlineFactValue">{fact.value}</span>
          </li>
        ))}
      </ul>
    </section>
  );
}
