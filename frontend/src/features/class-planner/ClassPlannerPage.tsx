import {
  AlertTriangle, ArrowRight, CalendarDays, Check, ChevronDown,
  MapPin, RotateCcw, Search, SlidersHorizontal, UserRound, WifiOff, X,
} from "lucide-react";
import { AnimatePresence, motion, useReducedMotion } from "framer-motion";
import { createContext, Fragment, useContext, useEffect, useMemo, useRef, useState } from "react";
import {
  API_PLANNER_TERM_ID, fetchPlannerCourseSections, fetchPlannerSection, PLANNER_DATA_MODE, searchPlannerCourses,
  type PlannerSource,
} from "./plannerApi";
import { PLANNER_COURSES, PLANNER_TERM } from "./plannerData";
import { getSchedule, getScheduleCache, getScheduleIds, saveSchedule } from "./plannerPersistence";
import {
  formatPlannerNow, getMeetingTemporalInfo, isPlannerToday, usePlannerNow,
} from "./plannerTime";
import type { Course, Meeting, MeetingDay, PlannerFilters, ScheduleConflict, Section } from "./plannerTypes";
import {
  calculateCredits, courseCode, DAY_LABELS, findSectionConflicts, formatDuration, formatMeetingDays,
  formatTime, formatTimeRange, getCourse, getMeetingGapMinutes, getTimePosition, getTimeRatio, getTimeWidth,
  minutesFromTime, scheduleConflictCount, searchCourses, WEEKDAYS,
} from "./plannerUtils";

const DEFAULT_FILTERS: PlannerFilters = {
  openOnly: false, onlineOnly: false, days: [], time: "any",
};
const USES_API_DATA = PLANNER_DATA_MODE !== "mock";
const ACTIVE_TERM_ID = USES_API_DATA ? API_PLANNER_TERM_ID : PLANNER_TERM.id;
const PlannerCoursesContext = createContext<Course[]>(PLANNER_COURSES);
const WEEK_PULSE_RANGE = { start: 7 * 60, end: 22 * 60 };
const WEEK_PULSE_AXIS_MINUTES = [7 * 60, 12 * 60, 17 * 60, 22 * 60];

type SearchState = "initial" | "loading" | "results" | "empty" | "offline" | "error";

interface MobileScheduleEvent {
  id: string;
  section: Section;
  meeting: Meeting;
  day: MeetingDay;
}

function usePlannerCourses() {
  return useContext(PlannerCoursesContext);
}

function paletteIndex(courseId: string): number {
  let hash = 0;
  for (const character of courseId) hash = ((hash << 5) - hash + character.charCodeAt(0)) | 0;
  return Math.abs(hash) % 8;
}

function mergeCourses(existing: Course[], incoming: Course[]): Course[] {
  const merged = new Map(existing.map((course) => [course.id, course]));
  incoming.forEach((course) => {
    const current = merged.get(course.id);
    if (!current) {
      merged.set(course.id, course);
      return;
    }
    const sections = new Map(current.sections.map((section) => [section.id, section]));
    course.sections.forEach((section) => sections.set(section.id, section));
    merged.set(course.id, { ...current, ...course, sections: [...sections.values()] });
  });
  return [...merged.values()];
}

function courseFromSection(
  section: Section & Pick<Course, "subject" | "courseNumber" | "title">,
): Course {
  return {
    id: section.courseId,
    subject: section.subject,
    courseNumber: section.courseNumber,
    title: section.title,
    credits: section.credits ?? 0,
    sections: [section],
  };
}

function changedSectionFields(previous: Section, current: Section): string[] {
  const changes: string[] = [];
  if (previous.instructor !== current.instructor) changes.push("instructor");
  if (previous.seatsRemaining !== current.seatsRemaining || previous.status !== current.status) {
    changes.push("availability");
  }
  const meetingShape = (section: Section) => JSON.stringify(section.meetings.map((meeting) => ({
    days: meeting.days,
    startTime: meeting.startTime,
    endTime: meeting.endTime,
    building: meeting.building,
    room: meeting.room,
  })));
  if (meetingShape(previous) !== meetingShape(current)) changes.push("time or room");
  return changes;
}

function useDialogDismiss(
  onClose: () => void,
  initialFocus: React.RefObject<HTMLButtonElement>,
  dialogRef: React.RefObject<HTMLElement>,
) {
  useEffect(() => {
    const previouslyFocused = document.activeElement instanceof HTMLElement ? document.activeElement : null;
    initialFocus.current?.focus();
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        onClose();
        return;
      }
      if (event.key !== "Tab" || !dialogRef.current) return;
      const focusable = Array.from(
        dialogRef.current.querySelectorAll<HTMLElement>(
          'a[href], button:not([disabled]), select:not([disabled]), input:not([disabled]), [tabindex]:not([tabindex="-1"])',
        ),
      );
      if (!focusable.length) return;
      const first = focusable[0];
      const last = focusable[focusable.length - 1];
      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault();
        last.focus();
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault();
        first.focus();
      }
    };
    document.addEventListener("keydown", onKeyDown);
    return () => {
      document.removeEventListener("keydown", onKeyDown);
      previouslyFocused?.focus();
    };
  }, [dialogRef, initialFocus, onClose]);
}

export function ClassPlannerPage() {
  const savedIdsRef = useRef<string[]>(getScheduleIds(ACTIVE_TERM_ID));
  const cachedCoursesRef = useRef<Course[]>(USES_API_DATA ? getScheduleCache(ACTIVE_TERM_ID) : []);
  const [mode, setMode] = useState<"find" | "week">(
    () => savedIdsRef.current.length ? "week" : "find",
  );
  const [courses, setCourses] = useState<Course[]>(() => USES_API_DATA ? cachedCoursesRef.current : PLANNER_COURSES);
  const [apiResults, setApiResults] = useState<Course[]>([]);
  const [source, setSource] = useState<PlannerSource | null>(null);
  const [dataError, setDataError] = useState<string | null>(null);
  const [searchNonce, setSearchNonce] = useState(0);
  const [query, setQuery] = useState("");
  const [filters, setFilters] = useState(DEFAULT_FILTERS);
  const [expandedCourse, setExpandedCourse] = useState<string | null>(null);
  const [sectionPages, setSectionPages] = useState<Record<string, { total: number; nextOffset: number | null; hasMore: boolean }>>({});
  const [sectionLoading, setSectionLoading] = useState<string | null>(null);
  const [previewId, setPreviewId] = useState<string | null>(null);
  const [detailsId, setDetailsId] = useState<string | null>(null);
  const [selected, setSelected] = useState<Section[]>(() =>
    getSchedule(
      ACTIVE_TERM_ID,
      (USES_API_DATA ? cachedCoursesRef.current : PLANNER_COURSES).flatMap((course) => course.sections),
    ),
  );
  const [focusedDay, setFocusedDay] = useState<MeetingDay>("M");
  const [searchState, setSearchState] = useState<SearchState>("initial");
  const [online, setOnline] = useState(() => typeof navigator === "undefined" || navigator.onLine);
  const [notice, setNotice] = useState<{ text: string; removed?: Section } | null>(null);
  const [blockingConflict, setBlockingConflict] = useState<{
    candidate: Section;
    conflicts: ScheduleConflict[];
  } | null>(null);
  const [summaryOpen, setSummaryOpen] = useState(false);
  const [filtersOpen, setFiltersOpen] = useState(false);
  const summaryCloseRef = useRef<HTMLButtonElement>(null);

  const allSections = useMemo(() => courses.flatMap((course) => course.sections), [courses]);
  const results = useMemo(() => USES_API_DATA
    ? apiResults
    : searchCourses(courses, query, filters), [apiResults, courses, query, filters]);
  const preview = allSections.find((section) => section.id === previewId) ?? null;
  const previewConflicts = preview ? findSectionConflicts(preview, selected) : [];
  const credits = calculateCredits(selected, courses);
  const conflicts = scheduleConflictCount(selected);

  useEffect(() => {
    if (!USES_API_DATA || !savedIdsRef.current.length) return;
    const controller = new AbortController();
    Promise.all(savedIdsRef.current.map(async (id) => {
      try {
        return await fetchPlannerSection(id, controller.signal);
      } catch {
        return null;
      }
    })).then((responses) => {
      const valid = responses.filter((item) => item !== null);
      if (!valid.length) {
        setDataError("Saved class information is temporarily unavailable.");
        return;
      }
      const hydratedCourses = valid.map((item) => courseFromSection(item.data));
      setCourses((current) => mergeCourses(current, hydratedCourses));
      setSelected(valid.map((item) => item.data));
      setSource(valid[0].source);
    });
    return () => controller.abort();
  }, []);

  useEffect(() => {
    const onOnline = () => setOnline(true);
    const onOffline = () => setOnline(false);
    window.addEventListener("online", onOnline);
    window.addEventListener("offline", onOffline);
    return () => {
      window.removeEventListener("online", onOnline);
      window.removeEventListener("offline", onOffline);
    };
  }, []);

  useEffect(() => {
    if (USES_API_DATA) return;
    if (!online) {
      setSearchState("offline");
      return;
    }
    const hasFilters = filters.openOnly || filters.onlineOnly || filters.days.length > 0 || filters.time !== "any";
    if (!query.trim() && !hasFilters) {
      setSearchState("initial");
      return;
    }
    setSearchState(results.length ? "results" : "empty");
  }, [filters, online, query, results.length]);

  useEffect(() => {
    if (!USES_API_DATA) return;
    if (!online) {
      setSearchState("offline");
      return;
    }
    const hasFilters = filters.openOnly || filters.onlineOnly || filters.days.length > 0 || filters.time !== "any";
    if (!query.trim() && !hasFilters) {
      setApiResults([]);
      setSearchState("initial");
      return;
    }
    const controller = new AbortController();
    const debounce = window.setTimeout(() => {
      setSearchState("loading");
      setDataError(null);
      searchPlannerCourses(ACTIVE_TERM_ID, query, filters, controller.signal)
        .then((response) => {
          setApiResults(response.data);
          setCourses((current) => mergeCourses(current, response.data));
          setSource(response.source);
          setSearchState(response.data.length ? "results" : "empty");
        })
        .catch((error: unknown) => {
          if (controller.signal.aborted) return;
          setDataError(error instanceof Error ? error.message : "Class information is temporarily unavailable.");
          setSearchState("error");
        });
    }, 240);
    return () => {
      window.clearTimeout(debounce);
      controller.abort();
    };
  }, [filters, online, query, searchNonce]);

  useEffect(() => {
    if (!notice) return;
    const timer = window.setTimeout(() => setNotice(null), 5000);
    return () => window.clearTimeout(timer);
  }, [notice]);

  async function loadCourseSections(course: Course, offset = 0) {
    if (!USES_API_DATA || sectionLoading === course.id) return;
    setSectionLoading(course.id);
    try {
      const response = await fetchPlannerCourseSections(
        ACTIVE_TERM_ID, course.id, selected.map((item) => item.id), offset,
      );
      const incoming = response.data.sections;
      const update = (items: Course[]) => items.map((item) => {
        if (item.id !== course.id) return item;
        const merged = new Map(item.sections.map((section) => [section.id, section]));
        incoming.forEach((section) => merged.set(section.id, section));
        return { ...item, sections: [...merged.values()], sectionCount: response.data.total };
      });
      setApiResults(update);
      setCourses(update);
      setSectionPages((current) => ({ ...current, [course.id]: {
        total: response.data.total,
        nextOffset: response.data.nextOffset,
        hasMore: response.data.hasMore,
      } }));
      setSource(response.source);
    } catch (error) {
      setNotice({ text: error instanceof Error ? error.message : "Sections are temporarily unavailable." });
    } finally {
      setSectionLoading(null);
    }
  }

  function toggleCourse(course: Course) {
    if (expandedCourse === course.id) {
      setExpandedCourse(null);
      return;
    }
    setExpandedCourse(course.id);
    setDetailsId(null);
    if (USES_API_DATA && course.sections.length === 0) void loadCourseSections(course);
  }

  function persist(next: Section[]) {
    setSelected(next);
    try {
      saveSchedule(ACTIVE_TERM_ID, next, courses);
    } catch {
      setSearchState("error");
      setNotice({ text: "Schedule changed here, but could not be saved on this device." });
    }
  }

  async function addSection(section: Section) {
    if (selected.some((item) => item.id === section.id)) return;
    let candidate = section;
    let usedSnapshot = false;
    if (USES_API_DATA) {
      try {
        const response = await fetchPlannerSection(section.id, undefined, true);
        const changes = changedSectionFields(section, response.data);
        setSource(response.source);
        setCourses((current) => mergeCourses(current, [courseFromSection(response.data)]));
        if (changes.length) {
          setNotice({ text: `This section changed since you viewed it: ${changes.join(", ")}. Review it before adding.` });
          return;
        }
        candidate = response.data;
        usedSnapshot = response.verification?.status === "unavailable";
      } catch {
        usedSnapshot = true;
      }
    }
    const existingCourseSection = selected.find((item) => item.courseId === candidate.courseId);
    const otherCourses = selected.filter((item) => item.courseId !== candidate.courseId);
    const nextConflicts = findSectionConflicts(candidate, otherCourses);
    if (nextConflicts.length) {
      setPreviewId(candidate.id);
      setBlockingConflict({ candidate, conflicts: nextConflicts });
      return;
    }
    persist([...otherCourses, candidate]);
    setBlockingConflict(null);
    setNotice({
      text: usedSnapshot
        ? `Added using availability last checked ${new Date(section.availabilityVerifiedAt ?? section.updatedAt).toLocaleString()}; live recheck was unavailable.`
        : existingCourseSection
          ? `${courseCode(getCourse(courses, candidate.courseId)!)} section updated.`
          : `${getCourse(courses, candidate.courseId)?.subject ?? "Class"} added to your week.`,
    });
  }

  function removeSection(section: Section) {
    persist(selected.filter((item) => item.id !== section.id));
    setNotice({ text: `${courseCode(getCourse(courses, section.courseId)!)} removed.`, removed: section });
  }

  function undoRemove() {
    if (!notice?.removed || selected.some((item) => item.id === notice.removed?.id)) return;
    persist([...selected, notice.removed]);
    setNotice({ text: "Class restored." });
  }

  function clearFilters() {
    setFilters(DEFAULT_FILTERS);
    setQuery("");
    setSearchState("initial");
  }

  function retryPersistence() {
    try {
      saveSchedule(ACTIVE_TERM_ID, selected, courses);
      const hasSearch = query.trim() || filters.openOnly || filters.onlineOnly
        || filters.days.length > 0 || filters.time !== "any";
      setSearchState(hasSearch ? (results.length ? "results" : "empty") : "initial");
      setNotice({ text: "Schedule saved on this device." });
    } catch {
      setNotice({ text: "Schedule still could not be saved on this device." });
    }
  }

  return (
    <PlannerCoursesContext.Provider value={courses}>
    <main className="planner" aria-labelledby="planner-title">
      <header className="plannerHeader">
        <div className="plannerHeaderTitle">
          <h1 id="planner-title">Class Planner</h1>
        </div>
        <div className="plannerHeaderContext">
          <p className="plannerTerm" aria-label={`Academic term: ${PLANNER_TERM.label}`}>
            {PLANNER_TERM.label}
          </p>
          <span
            className="plannerProvenance"
            title={source?.fetchedAt ? `McNeese Class Search data fetched ${new Date(source.fetchedAt).toLocaleString()}` : undefined}
          >
            {PLANNER_DATA_MODE === "mock" ? "Demo data" : PLANNER_DATA_MODE === "live" ? "McNeese data" : "McNeese staging"}
          </span>
        </div>
      </header>

      <div className="plannerModeSwitch" role="tablist" aria-label="Planner view">
        <button role="tab" aria-selected={mode === "week"} data-tour-id="planner-week" onClick={() => setMode("week")}>
          Week{selected.length ? <span>{selected.length}</span> : null}
        </button>
        <button role="tab" aria-selected={mode === "find"} data-tour-id="planner-find" onClick={() => setMode("find")}>Find</button>
      </div>

      <div className="plannerWorkspace">
        <section className={`plannerDiscovery${mode === "find" ? " is-mobile-active" : ""}`} aria-label="Find classes">
          <div className="plannerSearchTools">
            <label className="plannerSearch">
              <Search size={19} aria-hidden />
              <span className="sr-only">Search courses, codes, or instructors</span>
              <input
                type="search"
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                placeholder="Search courses, codes, or instructors"
                autoComplete="off"
              />
              {query ? <button type="button" onClick={() => setQuery("")} aria-label="Clear search"><X size={17} /></button> : null}
            </label>
            <FilterBar filters={filters} setFilters={setFilters} open={filtersOpen} setOpen={setFiltersOpen} />
          </div>

          <div className="plannerResults" aria-live="polite" aria-busy={searchState === "loading"}>
            {searchState === "initial" && (
              <StarterCard
                hasSchedule={selected.length > 0}
                onSearch={() => document.querySelector<HTMLInputElement>(".plannerSearch input")?.focus()}
              />
            )}
            {searchState === "loading" && (apiResults.length ? (
              <div className="plannerInlineLoading" role="status"><i aria-hidden="true" />Updating matches…</div>
            ) : <CourseSkeleton />)}
            {searchState === "offline" && (
              <StateCard icon={<WifiOff />} title={selected.length ? "Connection unavailable" : "You're offline"}>
                <p>{selected.length ? "Your saved schedule is still here. Current class availability may be outdated." : "We need a connection to search current classes."}</p>
                <button type="button" onClick={() => setOnline(navigator.onLine)}>Try again</button>
              </StateCard>
            )}
            {searchState === "error" && (
              <StateCard icon={<AlertTriangle />} title={dataError ? "Class information is unavailable" : "We couldn't save that change"}>
                <p>{dataError ?? "Your schedule is still visible. Check browser storage settings and try again."}</p>
                <button type="button" onClick={dataError ? () => setSearchNonce((value) => value + 1) : retryPersistence}>Try again</button>
              </StateCard>
            )}
            {searchState === "empty" && (
              <StateCard icon={<Search />} title={`No classes found${query ? ` for “${query}”` : ""}`}>
                <p>Try checking the course number or removing a filter.</p>
                <button type="button" onClick={clearFilters}>Clear filters</button>
              </StateCard>
            )}
            {(searchState === "results" || (searchState === "loading" && apiResults.length > 0)) && results.map((course) => (
              <CourseGroup
                key={course.id}
                course={course}
                expanded={expandedCourse === course.id}
                onToggle={() => toggleCourse(course)}
                selected={selected}
                previewId={previewId}
                detailsId={detailsId}
                onDetails={setDetailsId}
                onPreview={setPreviewId}
                onAdd={addSection}
                onRemove={removeSection}
                page={sectionPages[course.id]}
                loading={sectionLoading === course.id}
                onMore={() => void loadCourseSections(course, sectionPages[course.id]?.nextOffset ?? course.sections.length)}
              />
            ))}
          </div>
        </section>

        <section className={`plannerWeekPane${mode === "week" ? " is-mobile-active" : ""}`} aria-label="My Week">
          <div className="plannerWeekHeading">
            <h2>
              {selected.length
                ? `${selected.length} ${selected.length === 1 ? "class" : "classes"} · ${credits} credits${conflicts ? ` · ${conflicts} conflict${conflicts === 1 ? "" : "s"}` : ""}`
                : "Build a week that works"}
            </h2>
            {selected.length ? (
              <button type="button" className="plannerSummaryButton" onClick={() => setSummaryOpen(true)}>
                <span className="plannerSummaryLong">Registration Summary</span>
                <span className="plannerSummaryShort">Summary</span>
                <ArrowRight size={16} />
              </button>
            ) : null}
          </div>
          {selected.length ? (
            <>
              {conflicts > 0 ? <div className="plannerConflictBanner"><AlertTriangle size={18} />{conflicts} schedule {conflicts === 1 ? "conflict" : "conflicts"} to review</div> : null}
              <DesktopSchedule selected={selected} preview={preview} previewConflicts={previewConflicts} />
              <MobileWeek selected={selected} focusedDay={focusedDay} setFocusedDay={setFocusedDay} onRemove={removeSection} />
            </>
          ) : (
            <div className="plannerWeekEmpty">
              <CalendarDays size={30} />
              <h3>Your week is open</h3>
              <p>Find a class and preview a section. Its exact meeting time will appear here before you add it.</p>
              <button type="button" onClick={() => setMode("find")}>Find classes</button>
            </div>
          )}
        </section>
      </div>

      {selected.length && mode === "find" ? (
        <button type="button" className="plannerStickySummary" onClick={() => setMode("week")}>
          <span>{selected.length} {selected.length === 1 ? "class" : "classes"} · {conflicts ? `${conflicts} conflict${conflicts === 1 ? "" : "s"}` : `${credits} credits`}</span>
          <strong>{conflicts ? "Review" : "View week"} <ArrowRight size={16} /></strong>
        </button>
      ) : null}

      {blockingConflict ? (
        <ConflictPanel
          conflicts={blockingConflict.conflicts}
          candidate={blockingConflict.candidate}
          onClose={() => setBlockingConflict(null)}
          onViewWeek={() => { setBlockingConflict(null); setMode("week"); }}
        />
      ) : null}
      {summaryOpen ? <RegistrationSummary selected={selected} credits={credits} closeRef={summaryCloseRef} onClose={() => setSummaryOpen(false)} /> : null}
      {notice ? (
        <div className="plannerToast" role="status">
          <span>{notice.text}</span>
          {notice.removed ? <button type="button" onClick={undoRemove}><RotateCcw size={15} /> Undo</button> : null}
        </div>
      ) : null}
    </main>
    </PlannerCoursesContext.Provider>
  );
}

function FilterBar({ filters, setFilters, open, setOpen }: {
  filters: PlannerFilters;
  setFilters: (value: PlannerFilters) => void;
  open: boolean;
  setOpen: (value: boolean) => void;
}) {
  const toggleDay = (day: MeetingDay) => setFilters({
    ...filters,
    days: filters.days.includes(day) ? filters.days.filter((item) => item !== day) : [...filters.days, day],
  });
  return (
    <div className="plannerFilterWrap">
      <div className="plannerFilters" aria-label="Course filters">
        <button type="button" aria-pressed={filters.openOnly} onClick={() => setFilters({ ...filters, openOnly: !filters.openOnly })}>Open</button>
        <button type="button" aria-pressed={filters.onlineOnly} onClick={() => setFilters({ ...filters, onlineOnly: !filters.onlineOnly })}>Online</button>
        <button type="button" aria-expanded={open} aria-controls="planner-advanced-filters" onClick={() => setOpen(!open)}>
          <SlidersHorizontal size={15} /> Days & time
        </button>
      </div>
      {open ? (
        <div className="plannerAdvancedFilters" id="planner-advanced-filters">
          <fieldset>
            <legend>Meeting days</legend>
            <div>{WEEKDAYS.map((day) => <button type="button" key={day} aria-pressed={filters.days.includes(day)} onClick={() => toggleDay(day)}>{day}</button>)}</div>
          </fieldset>
          <label>Time
            <select value={filters.time} onChange={(event) => setFilters({ ...filters, time: event.target.value as PlannerFilters["time"] })}>
              <option value="any">Any time</option><option value="morning">Morning</option>
              <option value="afternoon">Afternoon</option><option value="evening">Evening</option>
            </select>
          </label>
        </div>
      ) : null}
    </div>
  );
}

function StarterCard({ hasSchedule, onSearch }: { hasSchedule: boolean; onSearch: () => void }) {
  return (
    <div className={`plannerStarter${hasSchedule ? " is-compact" : ""}`}>
      {!hasSchedule ? <span><CalendarDays size={22} /></span> : null}
      <h2>{hasSchedule ? "Add another class" : "Build your week"}</h2>
      <p>
        {hasSchedule
          ? "Search above to compare another course with your current week."
          : "Start with one class from your advising plan. We'll show you where each section fits."}
      </p>
      <button type="button" onClick={onSearch}>Search classes</button>
    </div>
  );
}

function StateCard({ icon, title, children }: { icon: React.ReactNode; title: string; children: React.ReactNode }) {
  return <div className="plannerStateCard"><span>{icon}</span><h2>{title}</h2>{children}</div>;
}

function CourseSkeleton() {
  return (
    <div className="plannerSkeleton" role="status">
      <p>Finding the best matching sections…</p>
      {[0, 1, 2].map((item) => (
        <div className="plannerSkeletonRow" key={item} aria-hidden="true">
          <span className="plannerSkeletonCode" />
          <span className="plannerSkeletonTitle" />
          <span className="plannerSkeletonMeta" />
        </div>
      ))}
    </div>
  );
}

function CourseGroup(props: {
  course: Course; expanded: boolean; selected: Section[]; previewId: string | null; detailsId: string | null;
  onToggle: () => void; onDetails: (id: string | null) => void; onPreview: (id: string | null) => void;
  onAdd: (section: Section) => void; onRemove: (section: Section) => void;
  page?: { total: number; nextOffset: number | null; hasMore: boolean }; loading: boolean; onMore: () => void;
}) {
  const sectionCount = props.course.sectionCount ?? props.page?.total ?? props.course.sections.length;
  const openCount = props.course.openCount ?? props.course.sections.filter((section) => section.status === "open").length;
  return (
    <article className="plannerCourse">
      <button className="plannerCourseSummary" type="button" onClick={props.onToggle} aria-expanded={props.expanded}>
        <span><strong>{courseCode(props.course)}</strong><b>{props.course.title}</b><small>{sectionCount} {sectionCount === 1 ? "section" : "sections"} · {openCount} open</small></span>
        <span className="plannerCourseAction">{props.expanded ? "Hide" : "View sections"} <ChevronDown size={16} /></span>
      </button>
      {props.expanded ? (
        <div className="plannerSectionList">
          {props.loading && props.course.sections.length === 0 ? <div className="plannerInlineLoading" role="status"><i aria-hidden="true" />Loading sections…</div> : null}
          {props.course.sections.map((section) => (
            <SectionCard
              key={section.id} course={props.course} section={section} selected={props.selected}
              isSelected={props.selected.some((item) => item.id === section.id)}
              previewing={props.previewId === section.id} detailsOpen={props.detailsId === section.id}
              onDetails={() => props.onDetails(props.detailsId === section.id ? null : section.id)}
              onPreview={(active) => props.onPreview(active ? section.id : null)}
              onAdd={() => props.onAdd(section)} onRemove={() => props.onRemove(section)}
            />
          ))}
          {props.page?.hasMore ? (
            <button type="button" className="plannerTextButton plannerShowMore" onClick={props.onMore} disabled={props.loading}>
              {props.loading ? "Loading..." : `Show 6 more (${props.page.total - props.course.sections.length} remaining)`}
            </button>
          ) : null}
        </div>
      ) : null}
    </article>
  );
}

function SectionCard({ course, section, selected, isSelected, previewing, detailsOpen, onDetails, onPreview, onAdd, onRemove }: {
  course: Course; section: Section; selected: Section[]; isSelected: boolean; previewing: boolean; detailsOpen: boolean;
  onDetails: () => void; onPreview: (active: boolean) => void; onAdd: () => void; onRemove: () => void;
}) {
  const courses = usePlannerCourses();
  const conflicts = findSectionConflicts(section, selected);
  const first = section.meetings[0];
  const room = first?.building ? `${first.building}${first.room ? ` ${first.room}` : ""}` : section.modality === "Online" ? "Online" : "Room TBA";
  return (
    <article
      className={`plannerSection palette-${paletteIndex(section.courseId)}${previewing ? " is-previewing" : ""}${isSelected ? " is-selected" : ""}`}
      onMouseEnter={() => onPreview(true)} onMouseLeave={() => onPreview(false)}
      onFocus={() => onPreview(true)} onBlur={(event) => { if (!event.currentTarget.contains(event.relatedTarget)) onPreview(false); }}
    >
      <div className="plannerSectionTop"><strong>{section.sectionNumber}</strong><span>{course.credits} cr</span></div>
      <div className="plannerMeetingPrimary">
        <strong>{formatMeetingDays(first?.days ?? [])}</strong>
        <b>{first ? formatTimeRange(first) : "Time arranged"}</b>
      </div>
      <p className="plannerSectionMeta"><UserRound size={15} />{section.instructor || "Instructor TBA"}</p>
      <p className="plannerSectionMeta"><MapPin size={15} />{room} · {section.modality}</p>
      <div className={`plannerFit ${conflicts.length ? " is-conflict" : ""}`}>
        {conflicts.length ? <AlertTriangle size={16} /> : <Check size={16} />}
        <span>{conflicts.length ? `Conflicts with ${courseCode(getCourse(courses, conflicts[0].existingCourseId)!)}` : "Fits your week"}</span>
      </div>
      <p className="plannerSeats">
        {section.seatsRemaining === null ? "Seats not reported" : section.seatsRemaining === 0 ? "No seats open" : `${section.seatsRemaining} ${section.seatsRemaining === 1 ? "seat" : "seats"} open`}
      </p>
      {detailsOpen ? (
        <div className="plannerSectionDetails">
          {section.meetings.map((meeting, index) => (
            <p key={`${meeting.type}-${index}`}><strong>{meeting.type}</strong> · {formatMeetingDays(meeting.days)} · {formatTimeRange(meeting)} · {meeting.building ? `${meeting.building} ${meeting.room ?? ""}` : section.modality}</p>
          ))}
          <p>CRN {section.crn} · Availability verified {new Date(section.availabilityVerifiedAt ?? section.updatedAt).toLocaleString()}</p>
          {section.registrationNotes?.map((note) => <p key={note}><strong>Registration note</strong> · {note}</p>)}
          <MiniFitPreview section={section} conflicts={conflicts} />
        </div>
      ) : null}
      <div className="plannerSectionActions">
        <button type="button" className="plannerTextButton" onClick={onDetails} aria-expanded={detailsOpen}>{detailsOpen ? "Hide details" : "Details"}</button>
        <button type="button" className="plannerTextButton plannerPreviewButton" onClick={() => onPreview(!previewing)}>Preview</button>
        {isSelected ? (
          <button type="button" className="plannerRemoveButton" onClick={onRemove}>Remove</button>
        ) : (
          <button type="button" className="plannerAddButton" onClick={onAdd} disabled={section.status === "closed"}>
            {section.status === "closed" ? "Closed" : "Add"}
          </button>
        )}
      </div>
    </article>
  );
}

function MiniFitPreview({ section, conflicts }: { section: Section; conflicts: ScheduleConflict[] }) {
  const activeDays = new Set(section.meetings.flatMap((meeting) => meeting.days));
  return (
    <div className="plannerMiniFit">
      <strong>Your week</strong>
      <div>{WEEKDAYS.map((day) => <span key={day} data-active={activeDays.has(day)}>{day}<i /></span>)}</div>
      <p>{conflicts.length ? `⚠ ${conflicts[0].overlapMinutes}-minute overlap on ${conflicts[0].days.map((day) => DAY_LABELS[day]).join(", ")}` : "This section fits without a time overlap."}</p>
    </div>
  );
}

function DesktopSchedule({ selected, preview, previewConflicts }: { selected: Section[]; preview: Section | null; previewConflicts: ScheduleConflict[] }) {
  const courses = usePlannerCourses();
  const start = 7 * 60;
  const end = 21 * 60;
  const hourHeight = 68;
  const hours = Array.from({ length: 15 }, (_, index) => 7 + index);
  const viewportRef = useRef<HTMLDivElement>(null);
  const initializedRef = useRef(false);
  const reduceMotion = useReducedMotion();
  const clock = usePlannerNow();
  const todayColumn = clock.currentWeekday ? WEEKDAYS.indexOf(clock.currentWeekday) : -1;
  const showNow = clock.isInstructionDay
    && todayColumn >= 0
    && clock.currentMinutes >= start
    && clock.currentMinutes <= end;
  const blocks = [...selected.map((section) => ({ section, ghost: false }))];
  if (preview && !selected.some((section) => section.id === preview.id)) blocks.push({ section: preview, ghost: true });

  useEffect(() => {
    if (initializedRef.current || !viewportRef.current) return;
    const starts = selected.flatMap((section) =>
      section.meetings.flatMap((meeting) => meeting.startTime ? [minutesFromTime(meeting.startTime)] : []),
    );
    if (!starts.length) return;
    const targetMinutes = showNow ? clock.currentMinutes : Math.min(...starts);
    const contextOffset = showNow ? viewportRef.current.clientHeight * 0.35 : hourHeight;
    viewportRef.current.scrollTop = Math.max(0, ((targetMinutes - start) / 60) * hourHeight - contextOffset);
    initializedRef.current = true;
  }, [clock.currentMinutes, selected, showNow]);

  return (
    <div className="plannerSchedule" aria-label="Weekly schedule, Monday through Friday">
      <div className="plannerScheduleHeader">
        <span />
        {WEEKDAYS.map((day) => (
          <strong className={isPlannerToday(day, clock) ? "is-today" : ""} key={day}>
            {DAY_LABELS[day].slice(0, 3)}
            {isPlannerToday(day, clock) ? <small>Today</small> : null}
          </strong>
        ))}
      </div>
      <div className="plannerScheduleViewport" ref={viewportRef}>
        <div className="plannerScheduleBody" style={{ height: `${((end - start) / 60) * hourHeight}px` }}>
          {showNow ? (
            <motion.div
              className="plannerDesktopNow"
              style={{ top: `${((clock.currentMinutes - start) / 60) * hourHeight}px` }}
              aria-label={`Current time, ${formatPlannerNow(clock)}`}
              initial={false}
              animate={{ y: 0 }}
              transition={{ duration: reduceMotion ? 0 : 0.35, ease: "easeOut" }}
            >
              <b aria-hidden="true" />
              <i aria-hidden="true" />
              <span>{formatPlannerNow(clock)}</span>
            </motion.div>
          ) : null}
          <div className="plannerTimeLabels">
            {hours.map((hour) => <span key={hour} style={{ top: `${(hour - 7) * hourHeight}px` }}>{formatTime(`${String(hour).padStart(2, "0")}:00`).replace(":00", "")}</span>)}
          </div>
          <div className="plannerGrid">
            {hours.map((hour) => <i key={hour} style={{ top: `${(hour - 7) * hourHeight}px` }} />)}
            {blocks.flatMap(({ section, ghost }) => section.meetings.flatMap((meeting, meetingIndex) => {
              if (!meeting.startTime || !meeting.endTime) return [];
              return meeting.days.flatMap((day) => {
                const column = WEEKDAYS.indexOf(day);
                if (column < 0) return [];
                const top = ((minutesFromTime(meeting.startTime!) - start) / 60) * hourHeight;
                const height = ((minutesFromTime(meeting.endTime!) - minutesFromTime(meeting.startTime!)) / 60) * hourHeight;
                const course = getCourse(courses, section.courseId)!;
                const temporal = !ghost && day === clock.currentWeekday
                  ? getMeetingTemporalInfo(meeting, clock)
                  : { state: "inactive" as const, progress: 0, minutesRemaining: null };
                const liveDescription = temporal.state === "current"
                  ? `, in progress, ${temporal.minutesRemaining} minutes remaining`
                  : temporal.state === "completed" ? ", completed" : "";
                return (
                  <motion.div
                    layout
                    key={`${section.id}-${meetingIndex}-${day}`}
                    className={`plannerScheduleBlock palette-${paletteIndex(section.courseId)}${height < 50 ? " is-compact" : ""}${ghost ? " is-ghost" : ""}${ghost && previewConflicts.length ? " is-conflict" : ""}${temporal.state === "current" ? " is-current" : ""}${temporal.state === "completed" ? " is-completed" : ""}`}
                    style={{ left: `calc(${column * 20}% + 5px)`, width: "calc(20% - 10px)", top: `${top}px`, height: `${Math.max(height, 30)}px` }}
                    aria-label={`${courseCode(course)}, ${course.title}, ${DAY_LABELS[day]}, ${formatTimeRange(meeting)}${ghost ? ", preview" : ""}${liveDescription}`}
                    tabIndex={0}
                    initial={reduceMotion ? false : { opacity: 0, scale: 0.98 }}
                    animate={{ opacity: ghost ? 0.82 : temporal.state === "completed" ? 0.64 : 1, scale: 1 }}
                    whileHover={reduceMotion ? undefined : { y: -1 }}
                    transition={{ duration: reduceMotion ? 0 : 0.18 }}
                  >
                    <strong>{courseCode(course)}</strong>
                    <b>{course.title}</b>
                    <span>{formatTimeRange(meeting)}</span>
                    <small>{meeting.building ? `${meeting.building} ${meeting.room ?? ""}` : section.modality}</small>
                    {temporal.state === "current" ? (
                      <i className="plannerEventLiveProgress" style={{ width: `${temporal.progress * 100}%` }} aria-hidden="true" />
                    ) : null}
                  </motion.div>
                );
              });
            }))}
          </div>
        </div>
      </div>
      {preview && previewConflicts.length ? <p className="plannerGhostConflict"><AlertTriangle size={15} />{courseCode(getCourse(courses, preview.courseId)!)} overlaps {courseCode(getCourse(courses, previewConflicts[0].existingCourseId)!)} by {previewConflicts[0].overlapMinutes} minutes.</p> : null}
    </div>
  );
}

function MobileWeek({ selected, focusedDay, setFocusedDay, onRemove }: {
  selected: Section[]; focusedDay: MeetingDay; setFocusedDay: (day: MeetingDay) => void; onRemove: (section: Section) => void;
}) {
  const courses = usePlannerCourses();
  const [selectedEventId, setSelectedEventId] = useState<string | null>(null);
  const [detailEvent, setDetailEvent] = useState<MobileScheduleEvent | null>(null);
  const [direction, setDirection] = useState(0);
  const [departingDay, setDepartingDay] = useState<MeetingDay | null>(null);
  const wasDraggingRef = useRef(false);
  const departureTimerRef = useRef<number | null>(null);
  const reduceMotion = Boolean(useReducedMotion());
  const clock = usePlannerNow();
  const range = WEEK_PULSE_RANGE;
  const showPulseNow = clock.isInstructionDay
    && clock.currentWeekday !== null
    && WEEKDAYS.includes(clock.currentWeekday)
    && clock.currentMinutes >= range.start
    && clock.currentMinutes <= range.end;
  const fixedEvents: MobileScheduleEvent[] = selected.flatMap((section) => section.meetings.flatMap((meeting, meetingIndex) =>
    meeting.startTime && meeting.endTime
      ? meeting.days.filter((day) => WEEKDAYS.includes(day)).map((day) => ({
          id: `${section.id}-${meetingIndex}-${day}`,
          section,
          meeting,
          day,
        }))
      : [],
  ));
  const dayEvents = fixedEvents
    .filter((event) => event.day === focusedDay)
    .sort((a, b) => a.meeting.startTime!.localeCompare(b.meeting.startTime!));
  const dayClassCount = new Set(dayEvents.map((event) => event.section.id)).size;
  const flexibleSections = selected.filter((section) =>
    section.meetings.every((meeting) => !meeting.startTime || !meeting.endTime),
  );
  const dayDuration = dayEvents.reduce(
    (total, event) => total + minutesFromTime(event.meeting.endTime!) - minutesFromTime(event.meeting.startTime!),
    0,
  );
  const timelineIsToday = isPlannerToday(focusedDay, clock);
  const timelineNowInRange = timelineIsToday
    && clock.currentMinutes >= range.start
    && clock.currentMinutes <= range.end;
  const temporalByEvent = new Map(dayEvents.map((event) => [
    event.id,
    timelineIsToday
      ? getMeetingTemporalInfo(event.meeting, clock)
      : { state: "inactive" as const, progress: 0, minutesUntilStart: null, minutesRemaining: null },
  ]));
  const nextTimelineEvent = dayEvents.find((event) => temporalByEvent.get(event.id)?.state === "upcoming");

  useEffect(() => () => {
    if (departureTimerRef.current !== null) window.clearTimeout(departureTimerRef.current);
  }, []);

  function selectDay(day: MeetingDay) {
    const nextIndex = WEEKDAYS.indexOf(day);
    const currentIndex = WEEKDAYS.indexOf(focusedDay);
    if (nextIndex === currentIndex) return;
    if (departureTimerRef.current !== null) window.clearTimeout(departureTimerRef.current);
    if (!reduceMotion) {
      setDepartingDay(focusedDay);
      departureTimerRef.current = window.setTimeout(() => {
        setDepartingDay(null);
        departureTimerRef.current = null;
      }, 110);
    } else {
      setDepartingDay(null);
    }
    setDirection(nextIndex === currentIndex ? 0 : nextIndex > currentIndex ? 1 : -1);
    setFocusedDay(day);
  }

  function moveDay(offset: number) {
    const nextIndex = Math.max(0, Math.min(WEEKDAYS.length - 1, WEEKDAYS.indexOf(focusedDay) + offset));
    const nextDay = WEEKDAYS[nextIndex];
    if (nextDay !== focusedDay) {
      selectDay(nextDay);
      setSelectedEventId(null);
    }
  }

  function focusEvent(day: MeetingDay, eventId: string) {
    selectDay(day);
    setSelectedEventId(eventId);
    window.setTimeout(() => {
      document.getElementById(`day-lens-${eventId}`)?.scrollIntoView({
        behavior: reduceMotion ? "auto" : "smooth",
        block: "center",
      });
    }, reduceMotion ? 0 : 240);
  }

  return (
    <div className="plannerMobileWeek">
      <section className="weekPulse" aria-label="Whole week schedule">
        <div className="weekPulseRows">
          {WEEKDAYS.map((day) => {
            const events = fixedEvents.filter((event) => event.day === day);
            const classCount = new Set(events.map((event) => event.section.id)).size;
            const today = isPlannerToday(day, clock);
            return (
              <motion.div
                layout
                className={`weekPulseRow${focusedDay === day ? " is-selected" : ""}${departingDay === day ? " is-departing" : ""}${today ? " is-today" : ""}`}
                key={day}
                whileTap={reduceMotion ? undefined : { scale: 0.995 }}
                transition={{ duration: reduceMotion ? 0 : 0.14 }}
              >
                {focusedDay === day ? (
                  <motion.span
                    className="weekPulseSelection"
                    layoutId="week-pulse-day-lens"
                    transition={reduceMotion ? { duration: 0.08 } : { type: "spring", stiffness: 410, damping: 38, mass: 0.82 }}
                    aria-hidden="true"
                  />
                ) : null}
                <button
                  type="button"
                  className="weekPulseRowControl"
                  aria-pressed={focusedDay === day}
                  aria-label={`${DAY_LABELS[day]}, ${classCount} ${classCount === 1 ? "class" : "classes"}. Select ${DAY_LABELS[day]}.`}
                  onClick={() => { selectDay(day); setSelectedEventId(null); }}
                />
                <span className="weekPulseDay" aria-hidden="true">
                  <strong>{DAY_LABELS[day].slice(0, 3)}</strong>
                  <small>· {classCount}</small>
                </span>
                <div className="weekPulseRail">
                  {WEEK_PULSE_AXIS_MINUTES.map((minutes) => (
                    <span
                      className="weekPulseLandmark"
                      style={{ left: `${getTimeRatio(minutes, range) * 100}%` }}
                      key={minutes}
                      aria-hidden="true"
                    />
                  ))}
                  {today && showPulseNow ? (
                    <span
                      className="weekPulseNow"
                      style={{ left: `${getTimeRatio(clock.currentMinutes, range) * 100}%` }}
                      role="img"
                      aria-label={`Current time, ${formatPlannerNow(clock)}`}
                    >
                      <i aria-hidden="true" />
                      <motion.b
                        aria-hidden="true"
                        animate={reduceMotion ? undefined : { opacity: [0.25, 0.08, 0.25], scale: [1, 1.5, 1] }}
                        transition={reduceMotion ? undefined : { duration: 2.6, repeat: Infinity, ease: "easeInOut" }}
                      />
                    </span>
                  ) : null}
                  {events.map((event) => {
                    const course = getCourse(courses, event.section.courseId)!;
                    const eventConflicts = findSectionConflicts(event.section, selected)
                      .some((conflict) => conflict.days.includes(day));
                    const temporal = today
                      ? getMeetingTemporalInfo(event.meeting, clock)
                      : { state: "inactive" as const, progress: 0 };
                    return (
                      <motion.button
                        layout
                        type="button"
                        key={event.id}
                        className={`weekPulseSegment palette-${paletteIndex(event.section.courseId)}${selectedEventId === event.id ? " is-focused" : ""}${eventConflicts ? " is-conflict" : ""}${temporal.state === "current" ? " is-current" : ""}${temporal.state === "completed" ? " is-completed" : ""}`}
                        style={{
                          left: `${getTimePosition(event.meeting.startTime!, range)}%`,
                          width: `${getTimeWidth(event.meeting.startTime!, event.meeting.endTime!, range)}%`,
                        }}
                        aria-label={`${courseCode(course)}, ${DAY_LABELS[day]}, ${formatTimeRange(event.meeting)}${eventConflicts ? ", schedule conflict" : ""}${temporal.state === "current" ? ", in progress" : temporal.state === "completed" ? ", completed" : ""}`}
                        onClick={() => focusEvent(day, event.id)}
                        initial={reduceMotion ? false : { opacity: 0, scaleX: 0.7 }}
                        animate={{ opacity: temporal.state === "completed" ? 0.64 : 1, scaleX: 1 }}
                        exit={{ opacity: 0, scaleX: 0.7 }}
                        whileTap={reduceMotion ? undefined : { scale: 1.04 }}
                        transition={{ duration: reduceMotion ? 0 : 0.2 }}
                      >
                        {temporal.state === "current" ? (
                          <span className="weekPulseLiveProgress" style={{ width: `${temporal.progress * 100}%` }} aria-hidden="true" />
                        ) : null}
                      </motion.button>
                    );
                  })}
                </div>
              </motion.div>
            );
          })}
        </div>
        <div className="weekPulseAxis" aria-hidden="true">
          <span />
          <div className="weekPulseAxisRail">
            {WEEK_PULSE_AXIS_MINUTES.map((minutes, index) => (
              <small
                className={index === 0 ? "is-start" : index === WEEK_PULSE_AXIS_MINUTES.length - 1 ? "is-end" : ""}
                style={{ left: `${getTimeRatio(minutes, range) * 100}%` }}
                key={minutes}
              >
                {formatAxisTime(minutes)}
              </small>
            ))}
          </div>
        </div>
      </section>

      <div className="dayLensViewport">
        <AnimatePresence mode="wait" initial={false} custom={direction}>
          <motion.section
            key={focusedDay}
            className="dayLens"
            aria-labelledby={`day-lens-heading-${focusedDay}`}
            custom={direction}
            initial={reduceMotion ? { opacity: 0 } : { opacity: 0, x: direction >= 0 ? 18 : -18 }}
            animate={{ opacity: 1, x: 0 }}
            exit={reduceMotion ? { opacity: 0 } : { opacity: 0, x: direction >= 0 ? -18 : 18 }}
            transition={{ duration: reduceMotion ? 0.08 : 0.2, ease: "easeOut" }}
            drag={reduceMotion ? false : "x"}
            dragConstraints={{ left: 0, right: 0 }}
            dragElastic={0.08}
            onDragStart={() => { wasDraggingRef.current = true; }}
            onDragEnd={(_, info) => {
              if (info.offset.x < -45 || info.velocity.x < -400) moveDay(1);
              else if (info.offset.x > 45 || info.velocity.x > 400) moveDay(-1);
              window.setTimeout(() => { wasDraggingRef.current = false; }, 0);
            }}
          >
            <header className="dayLensHeader">
              <h3 id={`day-lens-heading-${focusedDay}`}>{DAY_LABELS[focusedDay]}</h3>
              <span>
                {dayClassCount
                  ? `${dayClassCount} ${dayClassCount === 1 ? "class" : "classes"} · ${formatDuration(dayDuration)}`
                  : "No fixed classes"}
              </span>
            </header>
            {dayEvents.length ? (
              <div className="dayLensTimeline">
                {dayEvents.map((event, index) => {
                  const course = getCourse(courses, event.section.courseId)!;
                  const eventConflicts = findSectionConflicts(event.section, selected)
                    .filter((conflict) => conflict.days.includes(focusedDay));
                  const temporal = temporalByEvent.get(event.id)!;
                  const isNext = nextTimelineEvent?.id === event.id;
                  const nextEvent = dayEvents[index + 1];
                  const gap = getMeetingGapMinutes(
                    event.meeting.endTime,
                    nextEvent?.meeting.startTime,
                  );
                  const nowInGap = timelineNowInRange
                    && nextEvent
                    && clock.currentMinutes >= minutesFromTime(event.meeting.endTime!)
                    && clock.currentMinutes < minutesFromTime(nextEvent.meeting.startTime!);
                  const gapProgress = nowInGap
                    ? (clock.currentMinutes - minutesFromTime(event.meeting.endTime!)) / Math.max(1, gap)
                    : 0;
                  return (
                    <Fragment key={event.id}>
                      <motion.article
                        layout
                        layoutId={`mobile-event-${event.id}`}
                        id={`day-lens-${event.id}`}
                        className={`dayLensEvent palette-${paletteIndex(event.section.courseId)}${selectedEventId === event.id ? " is-focused" : ""}${temporal.state === "current" ? " is-current" : ""}${temporal.state === "completed" ? " is-completed" : ""}`}
                        initial={reduceMotion ? false : { opacity: 0, y: 5 }}
                        animate={{ opacity: temporal.state === "completed" ? 0.64 : 1, y: 0 }}
                        exit={{ opacity: 0, scale: 0.98 }}
                        transition={{ duration: reduceMotion ? 0 : 0.18 }}
                      >
                        <button
                          type="button"
                          className="dayLensEventSelect"
                          aria-label={`View ${courseCode(course)}, ${course.title}, ${formatTimeRange(event.meeting)}${temporal.state === "current" ? `, in progress, ${temporal.minutesRemaining} minutes remaining` : temporal.state === "completed" ? ", completed" : isNext ? ", next class" : ""}`}
                          onClick={() => {
                            if (wasDraggingRef.current) return;
                            setSelectedEventId(event.id);
                            setDetailEvent(event);
                          }}
                        />
                        <time>{formatTime(event.meeting.startTime)}</time>
                        <motion.i
                          className="dayLensNode"
                          animate={selectedEventId === event.id && !reduceMotion ? { scale: 1.18 } : { scale: 1 }}
                          transition={{ type: "spring", stiffness: 400, damping: 34 }}
                          aria-hidden="true"
                        />
                        {temporal.state === "current" ? (
                          <TimelineNowMarker clock={clock} progress={temporal.progress} />
                        ) : null}
                        <div className="dayLensEventBody">
                          <div className="dayLensEventHeading">
                            <div>
                              <strong>{courseCode(course)}</strong>
                              <span>{course.title}</span>
                            </div>
                          </div>
                          <p>
                            {event.meeting.building ? `${event.meeting.building} ${event.meeting.room ?? ""}` : event.section.modality}
                            <span aria-hidden="true"> · </span>{formatTimeRange(event.meeting)}
                          </p>
                          {event.section.instructor ? <small>{event.section.instructor}</small> : null}
                          {temporal.state === "current" ? (
                            <p className="dayLensLiveStatus">In progress · {temporal.minutesRemaining} min left</p>
                          ) : isNext ? (
                            <p className="dayLensNextStatus">Next · {formatNextClassTime(temporal.minutesUntilStart, event.meeting.startTime!)}</p>
                          ) : null}
                          {eventConflicts.length ? (
                            <div className="dayLensConflict">
                              <AlertTriangle size={15} aria-hidden />
                              <span>Conflict with {courseCode(getCourse(courses, eventConflicts[0].existingCourseId)!)} · {eventConflicts[0].overlapMinutes}-minute overlap</span>
                            </div>
                          ) : null}
                          {temporal.state === "current" ? (
                            <i className="dayLensLiveProgress" style={{ width: `${temporal.progress * 100}%` }} aria-hidden="true" />
                          ) : null}
                        </div>
                      </motion.article>
                      {gap > 0 ? (
                        <div className="dayLensGap" aria-label={`${formatDuration(gap)} free before the next class`}>
                          <span>{formatDuration(gap)} free</span>
                          {nowInGap ? <TimelineNowMarker clock={clock} progress={gapProgress} /> : null}
                        </div>
                      ) : null}
                    </Fragment>
                  );
                })}
              </div>
            ) : (
              <p className="dayLensEmpty">
                No fixed classes {DAY_LABELS[focusedDay]}.
                {flexibleSections.length ? " Your online and time-arranged classes are listed below." : ""}
              </p>
            )}
          </motion.section>
        </AnimatePresence>
      </div>

      {flexibleSections.length ? (
        <section className="plannerFlexible" aria-labelledby="flexible-heading">
          <h3 id="flexible-heading">Flexible</h3>
          <div>
            <AnimatePresence initial={false}>
              {flexibleSections.map((section) => {
                const course = getCourse(courses, section.courseId)!;
                const event: MobileScheduleEvent = {
                  id: `flex-${section.id}`,
                  section,
                  meeting: section.meetings[0],
                  day: focusedDay,
                };
                return (
                  <motion.button
                    layout
                    type="button"
                    className={`plannerFlexibleRow palette-${paletteIndex(section.courseId)}`}
                    key={section.id}
                    aria-label={`View ${courseCode(course)}, ${course.title}, online, time arranged`}
                    onClick={() => setDetailEvent(event)}
                    initial={reduceMotion ? false : { opacity: 0, y: 4 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, height: 0 }}
                  >
                    <i aria-hidden="true" />
                    <span><strong>{courseCode(course)}</strong><small>{course.title}</small></span>
                    <span>Online · time arranged</span>
                    <ArrowRight size={16} aria-hidden />
                  </motion.button>
                );
              })}
            </AnimatePresence>
          </div>
        </section>
      ) : null}

      <AnimatePresence>
        {detailEvent ? (
          <CourseDetailSheet
            event={detailEvent}
            onClose={() => setDetailEvent(null)}
            onRemove={() => {
              setDetailEvent(null);
              onRemove(detailEvent.section);
            }}
          />
        ) : null}
      </AnimatePresence>
    </div>
  );
}

function TimelineNowMarker({ clock, progress }: {
  clock: ReturnType<typeof usePlannerNow>;
  progress?: number;
}) {
  const reduceMotion = Boolean(useReducedMotion());
  return (
    <div
      className="dayLensNow"
      style={progress === undefined ? undefined : { top: `${Math.max(0, Math.min(1, progress)) * 100}%` }}
      role="img"
      aria-label={`Current time, ${formatPlannerNow(clock)}`}
    >
      <span aria-hidden="true" />
      <i aria-hidden="true" />
      <motion.b
        aria-hidden="true"
        animate={reduceMotion ? undefined : { opacity: [0.22, 0.06, 0.22], scale: [1, 1.55, 1] }}
        transition={reduceMotion ? undefined : { duration: 2.6, repeat: Infinity, ease: "easeInOut" }}
      />
      <small><strong>Now</strong>{formatPlannerNow(clock)}</small>
    </div>
  );
}

function formatNextClassTime(minutesUntilStart: number | null, startTime: string): string {
  if (minutesUntilStart !== null && minutesUntilStart < 120) {
    return `Starts in ${formatDuration(minutesUntilStart)}`;
  }
  return `Starts at ${formatTime(startTime)}`;
}

function CourseDetailSheet({ event, onClose, onRemove }: {
  event: MobileScheduleEvent;
  onClose: () => void;
  onRemove: () => void;
}) {
  const courses = usePlannerCourses();
  const course = getCourse(courses, event.section.courseId)!;
  const closeRef = useRef<HTMLButtonElement>(null);
  const dialogRef = useRef<HTMLElement>(null);
  const reduceMotion = Boolean(useReducedMotion());
  useDialogDismiss(onClose, closeRef, dialogRef);

  return (
    <motion.div
      className="plannerDetailBackdrop"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      transition={{ duration: reduceMotion ? 0 : 0.18 }}
      onMouseDown={(mouseEvent) => { if (mouseEvent.target === mouseEvent.currentTarget) onClose(); }}
    >
      <motion.section
        ref={dialogRef}
        className={`plannerDetailSheet palette-${paletteIndex(event.section.courseId)}`}
        role="dialog"
        aria-modal="true"
        aria-labelledby="planner-detail-title"
        initial={reduceMotion ? { opacity: 0 } : { opacity: 0, y: 24 }}
        animate={{ opacity: 1, y: 0 }}
        exit={reduceMotion ? { opacity: 0 } : { opacity: 0, y: 24 }}
        transition={{ duration: reduceMotion ? 0 : 0.22, ease: "easeOut" }}
      >
        <span className="plannerDetailHandle" aria-hidden="true" />
        <button ref={closeRef} type="button" className="plannerDetailClose" onClick={onClose} aria-label="Close course details">
          <X size={19} />
        </button>
        <span className="plannerDetailAccent" aria-hidden="true" />
        <p className="plannerEyebrow">{courseCode(course)} · Section {event.section.sectionNumber}</p>
        <h2 id="planner-detail-title">{course.title}</h2>
        <dl>
          <div><dt>Time</dt><dd>{formatTimeRange(event.meeting)}</dd></div>
          <div><dt>Location</dt><dd>{event.meeting.building ? `${event.meeting.building} ${event.meeting.room ?? ""}` : event.section.modality}</dd></div>
          <div><dt>Instructor</dt><dd>{event.section.instructor || "Instructor TBA"}</dd></div>
          <div><dt>CRN</dt><dd>{event.section.crn} {PLANNER_DATA_MODE === "mock" ? <small>Sample data</small> : null}</dd></div>
        </dl>
        <button type="button" className="plannerDetailRemove" onClick={onRemove}>Remove from schedule</button>
      </motion.section>
    </motion.div>
  );
}

function formatAxisTime(minutes: number): string {
  const rounded = Math.round(minutes / 30) * 30;
  const time = `${String(Math.floor(rounded / 60)).padStart(2, "0")}:${String(rounded % 60).padStart(2, "0")}`;
  return formatTime(time).replace(":00", "");
}

function ConflictPanel({ conflicts, candidate, onClose, onViewWeek }: { conflicts: ScheduleConflict[]; candidate: Section; onClose: () => void; onViewWeek: () => void }) {
  const courses = usePlannerCourses();
  const closeRef = useRef<HTMLButtonElement>(null);
  const dialogRef = useRef<HTMLElement>(null);
  useDialogDismiss(onClose, closeRef, dialogRef);
  const conflict = conflicts[0];
  const candidateCourse = getCourse(courses, candidate.courseId)!;
  const existingCourse = getCourse(courses, conflict.existingCourseId)!;
  return (
    <div className="plannerModalBackdrop" role="presentation">
      <section ref={dialogRef} className="plannerDialog plannerConflictDialog" role="dialog" aria-modal="true" aria-labelledby="conflict-title">
        <button ref={closeRef} className="plannerDialogClose" type="button" onClick={onClose} aria-label="Close conflict details"><X size={19} /></button>
        <span className="plannerDialogIcon"><AlertTriangle size={24} /></span>
        <p className="plannerEyebrow">Schedule conflict</p><h2 id="conflict-title">These sections overlap</h2>
        <div className="plannerConflictComparison">
          <p><strong>{courseCode(candidateCourse)}</strong><span>{formatTime(conflict.candidateStart)}–{formatTime(conflict.candidateEnd)}</span></p>
          <b>overlaps</b>
          <p><strong>{courseCode(existingCourse)}</strong><span>{formatTime(conflict.existingStart)}–{formatTime(conflict.existingEnd)}</span></p>
        </div>
        <p className="plannerOverlap">Overlap: {conflict.overlapMinutes} minutes · {conflict.days.map((day) => DAY_LABELS[day]).join(", ")}</p>
        <div className="plannerDialogActions"><button type="button" onClick={onClose}>Choose another section</button><button type="button" onClick={onViewWeek}>View week</button></div>
      </section>
    </div>
  );
}

function RegistrationSummary({ selected, credits, closeRef, onClose }: { selected: Section[]; credits: number; closeRef: React.RefObject<HTMLButtonElement>; onClose: () => void }) {
  const courses = usePlannerCourses();
  const dialogRef = useRef<HTMLElement>(null);
  useDialogDismiss(onClose, closeRef, dialogRef);
  return (
    <div className="plannerModalBackdrop" onMouseDown={(event) => { if (event.target === event.currentTarget) onClose(); }}>
      <section ref={dialogRef} className="plannerDialog plannerRegistration" role="dialog" aria-modal="true" aria-labelledby="registration-title">
        <button ref={closeRef} className="plannerDialogClose" type="button" onClick={onClose} aria-label="Close registration summary"><X size={19} /></button>
        <p className="plannerEyebrow">{PLANNER_TERM.label}</p><h2 id="registration-title">Registration Summary</h2>
        {PLANNER_DATA_MODE === "mock" ? (
          <p className="plannerRegistrationIntro plannerRegistrationWarning">
            Sample CRNs for interface testing only. Do not enter these values in Banner.
          </p>
        ) : (
          <p className="plannerRegistrationIntro">Review these CRNs in official McNeese registration before submitting.</p>
        )}
        <ul>{selected.map((section) => {
          const course = getCourse(courses, section.courseId)!;
          return <li key={section.id}><span><strong>{courseCode(course)}-{section.sectionNumber}</strong><small>{course.title}</small></span><span><b>CRN {section.crn}</b><small>{course.credits} credits</small></span></li>;
        })}</ul>
        <p className="plannerRegistrationTotal"><span>Total</span><strong>{credits} credits</strong></p>
        <div className="plannerDialogActions">
          <button
            type="button"
            disabled={PLANNER_DATA_MODE === "mock"}
            onClick={() => navigator.clipboard?.writeText(selected.map((section) => section.crn).join(", "))}
          >
            {PLANNER_DATA_MODE === "mock" ? "Copy unavailable for sample data" : "Copy CRNs"}
          </button>
          <button type="button" disabled>Banner handoff requires live data</button>
        </div>
      </section>
    </div>
  );
}
