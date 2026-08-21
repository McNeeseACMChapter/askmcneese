import type { DevelopmentChapter, ProjectUpdate } from "./types";
import { EventLedger } from "./EventLedger";
import { chapterNumberLabel } from "./utils";

interface ChapterSectionProps {
  chapter: DevelopmentChapter;
  events: ProjectUpdate[];
  open: boolean;
  onToggle: () => void;
  openTicketNos: Set<number>;
  onToggleTicket: (ticketNo: number) => void;
}

export function ChapterSection({
  chapter,
  events,
  open,
  onToggle,
  openTicketNos,
  onToggleTicket,
}: ChapterSectionProps) {
  const panelId = `${chapter.id}-panel`;
  const headingId = `${chapter.id}-title`;
  const chapterTechnologies = [...new Set(events.flatMap((event) => event.technologies))];

  return (
    <article id={chapter.id} className="updatesChapter" data-turning={chapter.turningPoint ? "true" : undefined}>
      <h3 className="sr-only" id={headingId}>
        {chapterNumberLabel(chapter.number)}. {chapter.title}
      </h3>
      <button
        type="button"
        className="updatesChapter__summary"
        aria-expanded={open}
        aria-controls={panelId}
        onClick={onToggle}
      >
        <span className="updatesChapter__meta">
          <time dateTime={chapter.startDate}>{chapter.dateLabel}</time>
          {chapter.turningPoint && <span className="updatesTurningPoint">Turning point</span>}
        </span>
        <span className="updatesChapter__identity">
          <span className="updatesChapter__number" aria-hidden="true">
            {chapterNumberLabel(chapter.number)}
          </span>
          <span className="updatesChapter__heading">{chapter.title}</span>
        </span>
        <p className="updatesChapter__lede">{chapter.summary}</p>
        <span className="updatesChapter__tags">{chapter.tags.join(" · ")}</span>
        <span className="updatesChapter__count">
          {events.length} recorded event{events.length === 1 ? "" : "s"}
        </span>
        <span className="updatesChapter__chevron" aria-hidden="true" />
      </button>

      <div id={panelId} hidden={!open} className="updatesChapter__body">
        {open ? (
          <>
            {chapterTechnologies.length > 0 && (
              <div className="updatesChapterStack">
                <span className="updatesKicker">Technology stack in this stage</span>
                <span className="updatesTechnologyList">
                  {chapterTechnologies.map((technology) => (
                    <span key={technology}>{technology}</span>
                  ))}
                </span>
              </div>
            )}
            <div className="updatesStory">
              <p>
                <span className="updatesKicker">Situation</span>
                {chapter.situation}
              </p>
              <p>
                <span className="updatesKicker">Decision</span>
                {chapter.decision}
              </p>
              <p>
                <span className="updatesKicker">Expected result</span>
                {chapter.expectedResult}
              </p>
              <p>
                <span className="updatesKicker">What changed</span>
                {chapter.narrative}
              </p>
              <p>
                <span className="updatesKicker">What it enabled</span>
                {chapter.outcome}
              </p>
            </div>

            <div className="updatesChangeFlow" aria-label="What this stage changed">
              <ol>
                {chapter.changeFlow.map((step) => (
                  <li key={step}>{step}</li>
                ))}
              </ol>
              <p>
                <span className="updatesKicker">Enabled next</span>
                {chapter.enabledNext}
              </p>
            </div>

            <EventLedger events={events} openTicketNos={openTicketNos} onToggleTicket={onToggleTicket} />
          </>
        ) : null}
      </div>
    </article>
  );
}
