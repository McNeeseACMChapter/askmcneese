import { useEffect, useMemo, useRef, useState } from "react";
import { useLocation } from "react-router-dom";
import { ArrowDown, GitBranch, Search } from "lucide-react";
import { RouteEnter } from "../../components/motion/RouteEnter";
import { AREA_FILTERS, CHAPTER_BY_ID, LEGACY_HASH_ALIASES, PLANNED_DIRECTION } from "./chapters";
import { ChapterSection } from "./ChapterSection";
import { EvolutionField } from "./EvolutionField";
import {
  developmentChapters,
  developmentMetrics,
  eventByTicket,
  eventMatchesArea,
  eventMatchesQuery,
  firstHistoricalEvent,
  latestHistoricalEvent,
  projectTechnologyStack,
  projectUpdates,
  recordFreshness,
} from "./model";
import type { UpdateArea } from "./types";
import { chapterNumberLabel, formatExactDate, formatMonthDay, parseTicketHash } from "./utils";

type AreaFilter = "All" | UpdateArea;

export function DevelopmentStoryPage() {
  const location = useLocation();
  const searchRef = useRef<HTMLInputElement>(null);
  const [query, setQuery] = useState("");
  const [area, setArea] = useState<AreaFilter>("All");
  const [openChapters, setOpenChapters] = useState<Set<string>>(() => new Set());
  const [openTickets, setOpenTickets] = useState<Set<number>>(() => new Set());
  const [activeChapterId, setActiveChapterId] = useState<string | null>(developmentChapters[0]?.id ?? null);
  const appliedHash = useRef("");

  const filteredEvents = useMemo(
    () =>
      projectUpdates.filter(
        (event) =>
          eventMatchesArea(event, area) &&
          eventMatchesQuery(event, query, CHAPTER_BY_ID[event.chapterId]),
      ),
    [area, query],
  );

  const matchingTicketNos = useMemo(() => new Set(filteredEvents.map((event) => event.ticketNo)), [filteredEvents]);

  const visibleChapters = useMemo(
    () =>
      developmentChapters
        .map((chapter) => ({
          chapter,
          events: filteredEvents.filter((event) => event.chapterId === chapter.id),
        }))
        .filter((entry) => entry.events.length > 0),
    [filteredEvents],
  );

  useEffect(() => {
    const needle = query.trim();
    if (needle.length < 2) return;
    setOpenChapters(new Set(visibleChapters.map((entry) => entry.chapter.id)));
  }, [query, visibleChapters]);

  useEffect(() => {
    const raw = decodeURIComponent(location.hash.replace(/^#/, ""));
    if (!raw || appliedHash.current === raw) return;

    const target = LEGACY_HASH_ALIASES[raw] ?? raw;
    const ticketNo = parseTicketHash(target);

    if (ticketNo) {
      const event = eventByTicket(ticketNo);
      if (!event) return;
      appliedHash.current = raw;
      setOpenChapters((previous) => new Set(previous).add(event.chapterId));
      setOpenTickets((previous) => new Set(previous).add(ticketNo));
      setActiveChapterId(event.chapterId);
      window.requestAnimationFrame(() => {
        const node = document.getElementById(`ticket-${ticketNo}`);
        node?.scrollIntoView({ block: "start" });
        const toggle = node?.querySelector<HTMLButtonElement>("button");
        toggle?.focus({ preventScroll: true });
      });
      return;
    }

    if (target === "record-end" || CHAPTER_BY_ID[target]) {
      appliedHash.current = raw;
      if (CHAPTER_BY_ID[target]) {
        setOpenChapters((previous) => new Set(previous).add(target));
        setActiveChapterId(target);
      }
      window.requestAnimationFrame(() => {
        document.getElementById(target)?.scrollIntoView({ block: "start" });
      });
    }
  }, [location.hash]);

  function toggleChapter(chapterId: string) {
    setActiveChapterId(chapterId);
    setOpenChapters((previous) => {
      const next = new Set(previous);
      if (next.has(chapterId)) next.delete(chapterId);
      else next.add(chapterId);
      return next;
    });
  }

  function toggleTicket(ticketNo: number) {
    setOpenTickets((previous) => {
      const next = new Set(previous);
      if (next.has(ticketNo)) next.delete(ticketNo);
      else next.add(ticketNo);
      return next;
    });
  }

  function openTicketFromCalendar(ticketNo: number) {
    const event = eventByTicket(ticketNo);
    if (!event) return;
    setOpenChapters((previous) => new Set(previous).add(event.chapterId));
    setOpenTickets((previous) => new Set(previous).add(ticketNo));
    setActiveChapterId(event.chapterId);
  }

  const filtersActive = query.trim().length > 0 || area !== "All";
  const emptyFilter = filtersActive && filteredEvents.length === 0;
  const resultLabel = filtersActive
    ? `${filteredEvents.length} of ${projectUpdates.length} recorded events match the current search and filters.`
    : `${projectUpdates.length} recorded development events.`;

  return (
    <RouteEnter>
      <main className="updatesPage">
        <section className="updatesHero" aria-labelledby="updates-title">
          <div className="updatesHero__media" aria-hidden="true">
            <img
              src="/about/media/campus-clock.jpg"
              alt=""
              width="1200"
              height="1200"
            />
            <span className="updatesHero__wash" />
            <span className="updatesHero__grain" />
          </div>

          <div className="updatesHero__content">
            <p className="updatesKicker updatesKicker--gold">Development record / 2026</p>
            <h1 id="updates-title">
              Built in public.
              <em>Verified in the record.</em>
            </h1>
            <p className="updatesHero__lede">
              The dated decisions, corrections, and engineering work behind
              AskMcNeese—from student proposal to pre-launch system.
            </p>
            <div className="updatesHero__actions">
              <a href="#development-record" className="updatesAction updatesAction--gold">
                View activity <ArrowDown aria-hidden="true" />
              </a>
              <a href="#chapters" className="updatesAction updatesAction--ghost">
                Browse the archive
              </a>
            </div>
          </div>

          <aside className="updatesHero__artifact" aria-label="Development record summary">
            <header>
              <span><GitBranch aria-hidden="true" /> Source-linked record</span>
              <strong>Latest verified · Ticket {recordFreshness.ticketNo}</strong>
            </header>
            <div className="updatesHero__artifactLine" aria-hidden="true">
              {developmentChapters.map((chapter) => (
                <span key={chapter.id} className={chapter.turningPoint ? "is-turning" : undefined} />
              ))}
            </div>
            <dl>
              <div>
                <dt>Recorded events</dt>
                <dd>{projectUpdates.length}</dd>
              </div>
              <div>
                <dt>Story chapters</dt>
                <dd>{developmentChapters.length}</dd>
              </div>
              <div>
                <dt>Historical range</dt>
                <dd>
                  <time dateTime={firstHistoricalEvent.date}>{formatMonthDay(firstHistoricalEvent.date)}</time>
                  <span aria-hidden="true"> → </span>
                  <time dateTime={latestHistoricalEvent.date}>{formatMonthDay(latestHistoricalEvent.date)}</time>
                </dd>
              </div>
            </dl>
            <p>Canonical source · docs/pm/timeline.csv</p>
          </aside>

          <a className="updatesHero__scroll" href="#development-record">
            <span>Follow the build</span>
            <ArrowDown aria-hidden="true" />
          </a>
        </section>

        <section id="development-record" className="updatesEvolutionSection" aria-labelledby="evolution-title">
          <div className="updatesEvolutionSection__backdrop" aria-hidden="true">
            {projectUpdates.length}
          </div>
          <header>
            <p className="updatesKicker updatesKicker--gold">Activity / Verified timeline</p>
            <h2 id="evolution-title">Development activity, day by day.</h2>
            <p>
              Each square is one calendar day. Color intensity shows how many
              verified events were recorded; gold marks a turning point.
            </p>
          </header>
          <div className="updatesField">
            <EvolutionField
              chapters={developmentChapters}
              events={projectUpdates}
              activeChapterId={activeChapterId}
              matchingTicketNos={matchingTicketNos}
              filtersActive={filtersActive}
              onOpenTicket={openTicketFromCalendar}
            />
            <aside className="updatesSyncStatus" aria-label="Automatic record update status">
              <header>
                <span><i aria-hidden="true" /> Record sync</span>
                <strong>Source-linked</strong>
              </header>
              <dl>
                <div>
                  <dt>Canonical source</dt>
                  <dd>docs/pm/timeline.csv</dd>
                </div>
                <div>
                  <dt>Latest verified update</dt>
                  <dd>
                    Ticket {recordFreshness.ticketNo} ·{" "}
                    <time dateTime={recordFreshness.date}>{formatExactDate(recordFreshness.date)}</time>
                  </dd>
                </div>
                <div>
                  <dt>Automatic outputs</dt>
                  <dd>Counts · activity grid · chapter ledgers · freshness</dd>
                </div>
              </dl>
              <p>
                A verified timeline change refreshes this page immediately during
                development and is embedded again on every production build.
              </p>
            </aside>
          </div>
        </section>

        <section id="project-context" className="updatesManifesto" aria-labelledby="record-title">
          <div className="updatesManifesto__copy">
            <p className="updatesKicker">The development record</p>
            <h2 id="record-title">A campus project, shown through the work.</h2>
            <p className="updatesManifesto__statement">
              Structure came first.
              <strong> The system followed.</strong>
            </p>
            <p className="updatesManifesto__body">
              AskMcNeese has been developed iteratively by the ACM @ McNeese
              student development team. This record follows what changed, why
              it changed, and what each stage made possible—without hiding the
              maintenance, testing, corrections, or team transitions.
            </p>
          </div>
          <div className="updatesMetrics" aria-label="Development context">
            {developmentMetrics.map((metric) => (
              <div key={metric.label}>
                <span>{metric.value}</span>
                <small>{metric.label}</small>
              </div>
            ))}
          </div>
          <div className="updatesProjectStack" aria-labelledby="project-stack-title">
            <header>
              <p className="updatesKicker">Engineering stack</p>
              <h3 id="project-stack-title">Technology used to build the system.</h3>
            </header>
            <div>
              {projectTechnologyStack.map((group) => (
                <section key={group.label}>
                  <h4>{group.label}</h4>
                  <p>{group.technologies.join(" · ")}</p>
                </section>
              ))}
            </div>
          </div>
          <p className="updatesManifesto__boundary">
            AskMcNeese is an ACM student project and is not an official McNeese
            State University product.
          </p>
        </section>

        <section id="chapters" className="updatesArchive" aria-labelledby="chapters-title">
          <header className="updatesArchive__header">
            <div>
              <p className="updatesKicker">The complete archive</p>
              <h2 id="chapters-title">Explore the work behind the product.</h2>
            </div>
            <p>
              Read the project in broad chapters, or search every exact ticket,
              contributor, technology, commit, and date.
            </p>
          </header>

          <div className="updatesControls">
            <label className="updatesSearch">
              <Search size={18} strokeWidth={1.75} aria-hidden="true" />
              <span className="sr-only">Search the development record</span>
              <input
                ref={searchRef}
                type="search"
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                placeholder="Search tickets, people, commits, systems…"
                autoComplete="off"
              />
            </label>
            <div className="updatesAreaFilters" role="toolbar" aria-label="Filter by area">
              {AREA_FILTERS.map((filter) => (
                <button
                  key={filter.id}
                  type="button"
                  className="updatesFilter"
                  data-area={filter.id}
                  aria-pressed={area === filter.id}
                  onClick={() => setArea(filter.id)}
                >
                  {filter.label}
                </button>
              ))}
            </div>
            {filtersActive && (
              <button
                type="button"
                className="updatesClear"
                onClick={() => {
                  setQuery("");
                  setArea("All");
                  searchRef.current?.focus();
                }}
              >
                Clear search and filters
              </button>
            )}
            <p className="sr-only" aria-live="polite">
              {resultLabel}
            </p>
            {filtersActive && (
              <p className="updatesFilterStatus" aria-hidden="true">
                {resultLabel}
              </p>
            )}
          </div>

          <div className="updatesLayout">
            <nav className="updatesRail" aria-label="Development chapters">
              <ol>
                {developmentChapters.map((chapter) => {
                  const count = filteredEvents.filter((event) => event.chapterId === chapter.id).length;
                  const hiddenByFilter = filtersActive && count === 0;
                  return (
                    <li key={chapter.id}>
                      <a
                        href={`#${chapter.id}`}
                        className={chapter.id === activeChapterId ? "is-active" : undefined}
                        aria-current={chapter.id === activeChapterId ? "location" : undefined}
                        aria-disabled={hiddenByFilter ? true : undefined}
                        aria-label={`${chapterNumberLabel(chapter.number)}. ${chapter.title}${filtersActive ? `, ${count} matching events` : ""}`}
                        onClick={(clickEvent) => {
                          if (hiddenByFilter) {
                            clickEvent.preventDefault();
                            return;
                          }
                          setActiveChapterId(chapter.id);
                        }}
                      >
                        <span>{chapterNumberLabel(chapter.number)}</span>
                        <span>
                          {chapter.title}
                          {filtersActive && <small>{count}</small>}
                        </span>
                      </a>
                    </li>
                  );
                })}
              </ol>
            </nav>

            <div className="updatesStoryCol">
              <p className="updatesStoryCol__title">
                <span>Chronology</span>
                <span>{visibleChapters.length} chapters shown</span>
              </p>
              {emptyFilter ? (
                <p className="updatesEmpty">
                  {query.trim()
                    ? "No recorded development events match this search."
                    : "No events in this area match the current filters."}
                </p>
              ) : (
                visibleChapters.map(({ chapter, events }) => (
                  <ChapterSection
                    key={chapter.id}
                    chapter={chapter}
                    events={events}
                    open={openChapters.has(chapter.id)}
                    onToggle={() => toggleChapter(chapter.id)}
                    openTicketNos={openTickets}
                    onToggleTicket={toggleTicket}
                  />
                ))
              )}

              <aside className="updatesPlanned" aria-label="Planned work">
                <p className="updatesKicker">Planned</p>
                <h2>{PLANNED_DIRECTION.title}</h2>
                <p>{PLANNED_DIRECTION.detail}</p>
              </aside>

              <footer id="record-end" className="updatesEnd">
                <p className="updatesKicker">Full development record</p>
                <p>
                  {projectUpdates.length} / {projectUpdates.length} recorded events represented
                </p>
                <p>
                  This record is maintained from the project&apos;s timeline, sprint documentation,
                  and repository history.
                </p>
                <p className="updatesCurrent">
                  <span className="updatesKicker">Current record</span>
                  Latest documented historical event
                  {" · "}
                  <time dateTime={latestHistoricalEvent.date}>
                    {formatExactDate(latestHistoricalEvent.date)}
                  </time>
                </p>
                <p className="updatesPage__boundary">
                  AskMcNeese is an ACM @ McNeese student project. It is not an official McNeese State
                  University product. Registration, grades, billing, and other personal records remain
                  in McNeese&apos;s authenticated systems. ACM Panel is a separate chapter-management
                  system and is not part of Ask retrieval.
                </p>
              </footer>
            </div>
          </div>
        </section>
      </main>
    </RouteEnter>
  );
}
