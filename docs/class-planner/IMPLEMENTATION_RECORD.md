# Class Planner Implementation Record

## Initial inspection — 2026-08-08

### Inspected architecture

- React 18, TypeScript, Vite, React Router, Vitest, Testing Library, Tailwind utilities, and shared CSS tokens.
- Public routes are declared in `frontend/src/App.tsx` and rendered through `PublicAppShell`.
- Desktop navigation uses `UnifiedSidebar`; phones use `MobileTopNavigation` and its existing hamburger sheet.
- Existing backend course retrieval provides academic-catalog descriptions, not current term sections, CRNs, seats, or meeting records.
- Frontend API helpers target JSON endpoints, but no normalized class-section API currently exists.

### Expected files to create

- `docs/class-planner/README.md`
- `docs/class-planner/ARCHITECTURE.md`
- `docs/class-planner/IMPLEMENTATION_RECORD.md`
- `frontend/src/features/class-planner/ClassPlannerPage.tsx`
- `frontend/src/features/class-planner/plannerData.ts`
- `frontend/src/features/class-planner/plannerTypes.ts`
- `frontend/src/features/class-planner/plannerUtils.ts`
- `frontend/src/features/class-planner/plannerPersistence.ts`
- `frontend/src/features/class-planner/class-planner.css`
- `frontend/src/features/class-planner/plannerUtils.test.ts`
- `frontend/src/features/class-planner/ClassPlannerPage.test.tsx`

### Expected files to modify

- `frontend/src/App.tsx`
- `frontend/src/index.css`
- `frontend/src/components/shell/MobileNavigation.tsx`
- `frontend/src/components/shell/UnifiedSidebar.tsx`
- `frontend/src/components/shell/PublicAppShell.tsx`
- `frontend/src/mobile-top-nav.test.tsx`

### Assumptions

- Fall 2026 is the single MVP term.
- Because no official current-section source or API contract exists, the initial feature uses clearly identified normalized demonstration data.
- Local storage is appropriate behind an adapter until authenticated backend schedule persistence exists.
- Sample CRNs must not be copied to Banner; registration handoff controls remain disabled until a live source exists.

## Decisions

### Compact feature boundary

Used a single compact feature directory rather than introducing repository-wide domain layers.

Reason: matches the current frontend organization and keeps the isolated workspace understandable.

Affected files: `frontend/src/features/class-planner/*`

### No backend pipeline changes

The current catalog retriever cannot supply live section records. The MVP therefore uses normalized demonstration records and documents that limitation instead of presenting catalog descriptions as current availability.

Reason: avoids inaccurate claims and protects unrelated Q&A retrieval.

Affected files: Class Planner data and documentation only.

## Final implementation record

### Files actually created

- `docs/class-planner/README.md`
- `docs/class-planner/ARCHITECTURE.md`
- `docs/class-planner/IMPLEMENTATION_RECORD.md`
- `frontend/src/features/class-planner/ClassPlannerPage.tsx`
- `frontend/src/features/class-planner/class-planner.css`
- `frontend/src/features/class-planner/plannerData.ts`
- `frontend/src/features/class-planner/plannerPersistence.ts`
- `frontend/src/features/class-planner/plannerTypes.ts`
- `frontend/src/features/class-planner/plannerUtils.ts`
- `frontend/src/features/class-planner/ClassPlannerPage.test.tsx`
- `frontend/src/features/class-planner/plannerUtils.test.ts`

### Files actually modified

- `frontend/src/App.tsx`
- `frontend/src/index.css`
- `frontend/src/components/shell/MobileNavigation.tsx`
- `frontend/src/components/shell/PublicAppShell.tsx`
- `frontend/src/components/shell/UnifiedSidebar.tsx`
- `frontend/src/mobile-top-nav.test.tsx`

### Design and implementation decisions

#### Shared state, adaptive composition

One planner state drives phone Find/Week modes, tablet stacking, and the desktop two-pane workspace. Mobile uses a day agenda; desktop uses a 7 AM–9 PM positioned timetable.

Reason: preserves search and schedule context while avoiding a compressed desktop calendar on phones.

#### Deterministic schedule operations

Search, filtering, credits, section grouping, time positioning, and conflicts are pure local operations. Exact time boundaries do not conflict, multi-component meetings are checked, and date ranges are honored when supplied.

Reason: these operations must be predictable, fast, and independent of an LLM.

Local demonstration search runs synchronously without an artificial debounce or skeleton delay. Instructor-only queries return only the matching sections, and day filters compare against the union of lecture and lab meeting days.

#### Conflict-first Add behavior

Valid sections update and persist immediately. A conflicting Add is blocked by an explanatory dialog with class names, meeting ranges, common days, and overlap minutes.

Reason: prevents accidental conflicting plans and removes mental calendar arithmetic.

#### Responsive navigation integration

Class Planner was added to the existing desktop sidebar and existing phone hamburger sheet. About was removed from that sheet and added as a direct phone-header link.

Reason: meets the requested information architecture without introducing new global navigation.

#### Transparent demonstration data

The UI and Registration Summary display sample-data warnings. Copy and Banner handoff controls are disabled. Demonstration records cover open/closed/unknown seats, async online classes, lecture/lab components, long meetings, and conflicts.

Reason: no live normalized section API exists, so presenting sample availability as official would be misleading.

#### One selected section per course

Adding another section of an already selected course replaces the prior section after conflict validation against the other courses.

Reason: prevents duplicate course credits and duplicate CRNs while making section comparison easy.

#### Modal keyboard containment

Conflict and Registration Summary dialogs receive initial focus, trap Tab navigation, close with Escape, and restore focus to the triggering control.

Reason: provides predictable keyboard and screen-reader interaction.

### Tests performed

- Production typecheck and Vite build: passed.
- Planner and navigation regression suite: 22 tests across 5 files passed.
- Full frontend suite: 150 tests passed; one pre-existing `researchPresentation.test.ts` expectation failed outside Class Planner.
- Playwright interaction checks: grouped search, Add, persistence, conflict dialog, 20-minute overlap explanation, Escape dismissal, desktop conflict ghost blocks, mobile menu, mobile Week, and registration summary.
- Automated horizontal-overflow and header-collision checks at 320×568, 360×800, 390×844, 430×932, 768×1024, 1024×768, 1280×800, 1440×900, and 1920×1080: no overflow or mobile header collisions.
- Visual screenshot inspection at phone, tablet, and desktop sizes; generated QA screenshots were removed after inspection.

### Issues discovered and fixed

- The 1024px desktop workspace initially exceeded available width beside the existing sidebar; the intermediate desktop grid was tightened and the summary control made compact.
- The first conflict dialog implementation derived its candidate from transient hover state; it now stores the candidate with the blocking conflict so pointer transitions cannot dismiss or break the dialog.
- Mobile Week initially duplicated the sticky View Week action and crowded the summary heading; the sticky action is now Find-only and the summary uses responsive labels.
- Review found same-course duplicates, section-level search leakage, compound-day filtering, fake local-search latency, incomplete modal focus handling, and a nonfunctional persistence retry; each was corrected and covered by focused tests.

### Limitations

- Course and section records are normalized demonstration data, not live Banner availability.
- Fall 2026 is the only available term and is presented as static text.
- Persistence is local to the browser and device; there is no account synchronization or backend revalidation.
- Sample CRN copy and Banner handoff are disabled until an official current-section source is integrated.
- Weekend columns are not displayed because the demonstration dataset has no weekend meeting.
- The existing application bundle still emits its prior large-chunk warning.

### Future work

Replace the demonstration adapter with an official normalized current-section endpoint while retaining the existing frontend contract and persistence boundary.

## Mobile Week Redesign — 2026-08-08

### Before implementation

The previous phone Week view used weekday tabs followed by independent class cards. It hid four-fifths of the student's week and transformed a spatial schedule into a card list.

Expected files to change:

- `frontend/src/features/class-planner/ClassPlannerPage.tsx`
- `frontend/src/features/class-planner/class-planner.css`
- `frontend/src/features/class-planner/plannerUtils.ts`
- `frontend/src/features/class-planner/plannerUtils.test.ts`
- `frontend/src/features/class-planner/ClassPlannerPage.test.tsx`
- the three existing documents in `docs/class-planner/`

Functionality being preserved:

- normalized Course, Section, and Meeting contracts;
- deterministic conflict detection and credit calculations;
- stable course palette assignment;
- Add, replace-section, Remove, Undo, and local persistence;
- Find filters, fit explanations, desktop ghost previews, and Registration Summary;
- About outside the phone hamburger and Class Planner inside it.

Design approach:

- replace phone day tabs with a five-row Week Surface that positions fixed meetings horizontally;
- keep all Monday–Friday rows visible while a selected day drives a continuous Day Lens timeline;
- integrate asynchronous courses as a compact Flexible section;
- retain the desktop two-pane workspace while removing duplicate title, redundant pane labels, and dominant sample-data chrome;
- keep the presentation compact within the existing page, utility, and stylesheet files.

### After implementation

Files actually changed:

- `frontend/src/features/class-planner/ClassPlannerPage.tsx`
- `frontend/src/features/class-planner/class-planner.css`
- `frontend/src/features/class-planner/plannerUtils.ts`
- `frontend/src/features/class-planner/plannerUtils.test.ts`
- `frontend/src/features/class-planner/ClassPlannerPage.test.tsx`
- `docs/class-planner/README.md`
- `docs/class-planner/ARCHITECTURE.md`
- `docs/class-planner/IMPLEMENTATION_RECORD.md`

Mobile architecture implemented:

- Week Surface keeps five interactive weekday rows visible and projects fixed meetings into a shared horizontal time range.
- The visible time range is derived from selected meetings with academic-hour padding; pure utilities normalize block position and width.
- Tapping a day preserves all weekday context and updates the Day Lens.
- Tapping a course block selects its day, visually focuses the block, and brings the corresponding timeline event into view.
- Day Lens is one continuous time rail with event nodes, course identity, location, time, instructor, explicit conflict copy, and a disclosed action menu.
- Flexible online/time-arranged courses use a compact rail below fixed meetings.
- Course palette variables now carry consistently from Find section surfaces to Week Surface, Day Lens, and the existing desktop calendar.
- Horizontal swipe was intentionally omitted because visible day rows provide a complete, discoverable control without adding gesture complexity.

Desktop cleanup performed:

- removed the duplicate internal desktop Class Planner heading while retaining the phone page title;
- replaced the yellow sample-data banner with a quiet neutral `Demo data` provenance indicator beside the term;
- removed the redundant `My Week` micro-label;
- tightened the term toolbar and pane summary;
- flattened course-group borders and reduced expanded section-card nesting without changing discovery behavior.

Responsive and visual verification:

- inspected screenshots at 320×568, 390×844, 430×932, 768×1024, and 1440×900;
- inspected both Monday and a three-class Tuesday Day Lens at 390×844;
- inspected expanded mobile Find results at 390×844;
- checked overflow and five-row presence at 320×568, 360×800, 390×844, 430×932, 768×1024, 1280×800, 1440×900, and 1920×1080;
- checked a simulated 200% browser zoom with no horizontal document overflow.

Accessibility verification:

- every day row exposes its full weekday name, scheduled-class count, and pressed state;
- every course block exposes course, title, weekday, time range, and conflict state;
- block selection is available by keyboard and does not rely on color;
- event actions use labeled 44px controls and reveal an explicit `Remove from schedule` action;
- existing mobile navigation tests continue to enforce About outside the hamburger and Class Planner inside it;
- reduced-motion behavior is honored for event scrolling and CSS transitions.

Limitations:

- very short meetings across a wide morning-to-evening range may show a truncated visual label; their full accessible label and Day Lens details remain available;
- no swipe navigation was added;
- schedule hydration is synchronous local persistence, so Week Surface loading placeholders are not shown in the current data path;
- tablet continues to use the existing stacked desktop composition.

Final checks:

- `npx vitest run src/features/class-planner src/mobile-top-nav.test.tsx src/routes.visual.test.tsx src/public-shell-header.test.tsx`: 25 tests across 5 files passed;
- `npm run build`: TypeScript and production Vite build passed;
- IDE diagnostics reported no errors in the changed feature and documentation files;
- the existing application-level large-chunk build warning remains unchanged.

## Mobile V3 + Desktop Readability Pass — 2026-08-08

### Before implementation

Visual problems found:

- the mobile Week Surface forced course identity into narrow timetable blocks, producing clipped labels and a bordered white calendar territory;
- the overview lacked explicit per-day counts and useful motion, while day changes and course focus felt disconnected;
- the continuous timeline direction was useful but lacked free-time gaps, direct event details, swipe navigation, and course-color washes;
- the desktop canvas compressed 7 AM–9 PM into one viewport, forcing 50-minute blocks and essential text to remain too small;
- the left-pane starter incorrectly said `Build your week` when a persisted schedule already existed.

Existing components being replaced:

- mobile Week Surface rows and text-bearing temporal blocks;
- mobile overflow-based event actions;
- percentage-height desktop calendar body.

Components and behavior being preserved:

- `ClassPlannerPage`, Find/Week state, Course/Section/Meeting contracts, Add/Remove/Undo, persistence, conflict engine, Registration Summary, ghost preview, stable palette assignment, and navigation placement;
- the mobile continuous-timeline concept and desktop two-pane architecture.

Expected files:

- `frontend/src/features/class-planner/ClassPlannerPage.tsx`
- `frontend/src/features/class-planner/class-planner.css`
- `frontend/src/features/class-planner/plannerUtils.ts`
- `frontend/src/features/class-planner/plannerUtils.test.ts`
- `frontend/src/features/class-planner/ClassPlannerPage.test.tsx`
- the three existing documents in `docs/class-planner/`

Motion system:

Framer Motion is already installed and used by AskMcNeese. It is the sole animation system for this pass. Motion will be limited to weekday selection continuity, directional Focus Day transitions, swipe, event focus/reflow, and the event detail sheet, with `useReducedMotion` fallbacks.

### After implementation

Actual files changed:

- `frontend/src/features/class-planner/ClassPlannerPage.tsx`
- `frontend/src/features/class-planner/class-planner.css`
- `frontend/src/features/class-planner/plannerUtils.ts`
- `frontend/src/features/class-planner/plannerUtils.test.ts`
- `frontend/src/features/class-planner/ClassPlannerPage.test.tsx`
- `docs/class-planner/README.md`
- `docs/class-planner/ARCHITECTURE.md`
- `docs/class-planner/IMPLEMENTATION_RECORD.md`

New interaction model:

- retired the text-bearing mobile timetable and introduced Week Pulse, where five visible rows expose explicit class counts and text-free, actual-time occupancy segments;
- day-row taps, segment taps, and horizontal timeline swipes share `focusedDay`;
- segment taps transition to the relevant day, center the corresponding timeline event, and apply linked focus styling;
- Focus Day reports unique fixed-class count and total scheduled meeting duration;
- the continuous timeline uses course-color washes and nodes, calculates free gaps of at least 30 minutes, and keeps natural page scrolling;
- tapping an event opens an accessible bottom detail sheet with section, time, location, instructor, sample CRN, and Remove;
- flexible meetings are interactive continuation rows, not a separate gray card.

Animation behavior:

- Framer Motion is the only animation library used;
- a shared layout indicator moves between Week Pulse rows;
- Focus Day transitions use direction-aware 200ms slide/fade and optional horizontal drag;
- occupancy segments and timeline events animate meaningful insertion, removal, focus, and reflow;
- the bottom sheet uses a 220ms vertical/opacity transition;
- `useReducedMotion` removes spatial transitions, drag, springs, and smooth event scrolling;
- swipe QA found and fixed an event-sheet activation caused by pointer release after dragging.

Desktop scroll architecture:

- replaced percentage-height positioning with a deterministic 68px/hour scale;
- the weekday header and planner summary remain outside the vertically scrollable calendar body;
- the viewport occupies available planner height and shows readable 13–14px course codes with title, time, and location as height permits;
- initial scroll is calculated once from the earliest fixed class with one hour of context and does not reset user scroll;
- hour lines, day boundaries, time labels, block gutter, hover/focus contrast, and ghost-preview readability were strengthened;
- an existing schedule now produces the compact `Add another class` state instead of the incorrect `Build your week` state.

Visual and interaction checks:

- visually inspected populated planner screenshots at 390×844, 430×932, 768×1024, 1280×800, 1440×900, and 1920×1080;
- separately inspected the settled 390×844 detail sheet;
- confirmed all five Week Pulse rows, weekly counters, selected-day header, timeline start, course-color continuity, free gaps, and Flexible rows;
- confirmed vertical desktop calendar scrolling, persistent weekday header, readable 50-minute events, and contextual discovery state;
- exercised weekday tap, segment/timeline selection, swipe, detail open, Remove, count update, and reduced-motion behavior in a headless browser.

Accessibility checks:

- day rows announce full weekday and unique class count with pressed state;
- occupancy segments announce course, weekday, time, and conflict state;
- timeline events expose full labeled buttons and visible focus;
- the bottom sheet uses modal dialog semantics, initial focus, focus trapping, Escape dismissal, backdrop dismissal, and focus restoration;
- conflicts add iconography and text rather than relying on color;
- reduced motion preserves every interaction outcome.

Verification:

- `npx vitest run src/features/class-planner src/mobile-top-nav.test.tsx src/public-shell-header.test.tsx`: 22 tests across 4 files passed;
- `npm run build`: TypeScript and production Vite build passed;
- IDE diagnostics reported no errors in the changed planner files;
- the existing application-level large-chunk warning remains unchanged.

Remaining limitations:

- data and CRNs remain illustrative, local, and single-term;
- weekend columns and multi-schedule management remain outside MVP scope;
- schedule hydration is synchronous local storage, so calendar skeletons do not appear in the current execution path;
- tablet retains the established stacked planner composition;
- the day-duration counter sums scheduled meetings and does not subtract overlaps.

### Week Pulse Precision + Moving Glass Lens — 2026-08-08

Before implementation:

- preserve the approved Week Pulse rows, segment-to-timeline behavior, Focus Day, and all non-pulse planner UI;
- replace the adaptive pulse range and independently distributed axis labels with one fixed 7 AM–10 PM normalized scale shared by segments, landmarks, and labels;
- make every row and axis use the same CSS Grid day/temporal columns;
- refine proportional segments with a visibility floor while retaining exact start positions and duration differences;
- replace the selected-row border impression with one Framer Motion shared-layout glass lens, plus restrained outgoing-row softening;
- keep backdrop blur constant on the single lens and animate transforms/opacity rather than expensive filters;
- disable traveling blur, spring motion, and smooth scrolling when reduced motion is requested;
- expected files are `ClassPlannerPage.tsx`, `class-planner.css`, `plannerUtils.ts`, related planner tests, and the three existing planner documents.

After implementation:

- Shared time scale: Week Pulse now uses one fixed `{ start: 420, end: 1320 }` range. `getTimeRatio` drives 7 AM, 12 PM, 5 PM, and 10 PM label/landmark positions, while `getTimePosition` and `getTimeWidth` use the same range for meetings. Rows and axis share `--week-pulse-day-column` through one two-column CSS Grid.
- Segment precision: meeting starts remain exact; widths remain duration-proportional with a 12px minimum visibility floor. A restrained vertical tonal gradient and 11px capsule height keep segments legible as time blocks rather than dots.
- Lens implementation: one conditional Framer Motion element with `layoutId="week-pulse-day-lens"` travels between rows using a low-bounce spring. The selected row receives a single translucent lens with constant 10px backdrop blur. Only the departing row softens briefly; incoming content resolves through restrained opacity, saturation, weight, and color transitions.
- Performance: no animated backdrop-filter values, no per-row glass layers, and no animated landmarks or labels. Motion is limited to the shared lens, existing structural transitions, and direct segment feedback.
- Accessibility: row labels now announce `Tuesday, 3 classes. Select Tuesday.`, retain `aria-pressed`, and remain actual buttons. Segment labels and segment-to-timeline behavior are unchanged. Glass and landmarks are decorative.
- Reduced motion: `useReducedMotion` replaces spring travel with an 80ms layout change, suppresses departing-row state and segment tap scaling, and preserves the existing non-smooth event scroll behavior. CSS explicitly removes row blur/transitions.
- Viewports visually inspected: 360×800, 390×844, and 430×932, including Monday and Tuesday final lens states.
- Mathematical browser QA: first/final labels aligned to rail edges within 1.5px; 12 PM and 5 PM aligned to one-third/two-thirds of the rail; 50-, 75-, and 170-minute meetings measured 16px, 24px, and 54.39px respectively at 390px; downward and upward lens travel was measured between row positions.
- Tests: added exact assertions for 7 AM = 0, 2:30 PM = 50%, 10 PM = 100%, duration ordering, rendered axis positions, segment geometry, and one-lens presence.
- Test diagnostics: added the explicit `@testing-library/jest-dom/vitest` type augmentation to `ClassPlannerPage.test.tsx`, clearing the reported matcher diagnostics in that file.

## Live Time Layer — 2026-08-08

### Before implementation

- preserve the approved planner compositions and add one shared live temporal projection to Week Pulse, the selected-day timeline, and the desktop/tablet calendar;
- create one external-store `usePlannerNow` source that derives every update from `Date.now()`, aligns refreshes to minute boundaries, and reconciles immediately on document visibility and window focus;
- use `America/Chicago` through `Intl.DateTimeFormat`, never a fixed UTC offset;
- enrich term metadata only with official Fall 2026 instructional dates and published no-class dates; meeting-level date ranges continue to take precedence when present;
- keep course palette colors as identity while using one dedicated `--planner-live` token for current-time lines, nodes, progress, and textual live state;
- render no live state before August 24, after December 7, on published instructional holidays/breaks, or for a meeting that does not occur on the McNeese-local weekday;
- expected files are the existing planner page, styles, data/types/utilities/tests, one compact shared planner-time module and its test, plus the three existing planner documents.

### After implementation

- Files modified: `plannerTime.ts`, `plannerTime.test.ts`, `plannerData.ts`, `ClassPlannerPage.tsx`, `class-planner.css`, existing planner tests/documents.
- Shared source: `usePlannerNow` is backed by one module-level `useSyncExternalStore`; multiple schedule projections share one timeout and one current snapshot while the page/search surface remains unsubscribed.
- Timezone and dates: all clock parts use `America/Chicago` through `Intl.DateTimeFormat`. Official regular-session classes run August 24–December 7. Labor Day, Fall Break, and Thanksgiving no-class dates from the published McNeese Fall 2026 schedule suppress live state. Optional meeting date ranges further constrain eligibility.
- Tick/wake behavior: the store waits until the next real minute boundary, rebuilds from `Date.now()`, and recursively realigns. Visible-document and window-focus events refresh immediately and reschedule, avoiding stale suspended-tab counters.
- Temporal model: deterministic meeting projection returns inactive/upcoming/current/completed, clamped elapsed progress, minutes until start, and minutes remaining.
- Week Pulse: the current weekday receives one mathematically aligned green marker on the existing 7 AM–10 PM scale. Completed meetings retain course identity at lower saturation/opacity; the current segment retains its course base and receives a green elapsed overlay.
- Timeline: Now is positioned proportionally inside the current meeting or a represented free gap only when the focused day is actual today. The current event shows minutes remaining and a quiet progress edge; only the nearest upcoming event receives Next copy.
- Desktop/tablet: the established 68px/hour scale positions one global horizontal Now line. The time label occupies the time rail, event blocks mask the line to protect text, the current block gets a green progress edge, and the weekday header identifies Today. Initial scroll prefers Now only on first opening during active instructional time.
- Motion: live positions update once per minute; no day-long animation runs. Framer Motion limits interpolation to short structural changes and breathing halos. Reduced motion keeps static markers and discrete position updates with no halo pulse.
- Accessibility: current events include in-progress/minutes-remaining text in their accessible labels, Next is text, Now markers expose a non-live-region current-time label, and green is reinforced by line/node/progress shapes.
- Controlled tests cover 07:00, 08:30, 12:00, 14:25, 18:30, 21:59; before/during/after term; an official excluded date; weekday mismatch; meeting date ranges; upcoming/current/completed; 50% class progress; and America/Chicago date rollover.
- Browser QA used controlled Monday 10:25 AM Central time at 390×844, 768×1024, and 1440×900. It verified mobile current progress, current-event timeline placement, selected Thursday retaining the Monday Week Pulse marker with no Thursday Now line, desktop/tablet alignment, initial Now scrolling, focus/wake reconciliation, pre-term suppression, and reduced-motion marker persistence.
- Limitations: demonstration sections do not identify 7A/7B/online session calendars or one-off make-up meetings, so they inherit the official regular-session instructional calendar unless meeting-level dates are supplied. The timeline intentionally omits a positional Now line before its first and after its last represented interval rather than inventing spatial geometry.

## Real McNeese Data Integration — 2026-08-08

### Source and architecture inspection

- Authoritative public source: `https://schedule.mcneese.edu/`. Coursicle was not accessed.
- The backend is a compact FastAPI application with routers under `backend/app/routers`, services under `backend/app/services`, environment-based configuration, standard-library logging, and `unittest` tests. It had no relational ORM, migration framework, task queue, Redis dependency, or existing scheduler.
- Existing runtime dependencies already include `httpx` and Beautiful Soup. SQLite from the Python standard library was selected rather than adding an ORM, migration package, cache, queue, or scraping framework.
- The React planner already had normalized `Course`/`Section`/multi-`Meeting` types, local ID persistence, deterministic conflict/search utilities, and mock data. The minimum frontend integration is one API data-source module plus orchestration/type/persistence changes; approved visual components and CSS remain unchanged.
- Expected backend files were one compact planner service package, one router, one real-response fixture, one layered test module, and `app/main.py` wiring. Expected frontend files were the data adapter, existing planner page/types/persistence/tests, environment typings, and the three existing documents.

### Verified source request contract

- Term discovery is `GET https://schedule.mcneese.edu/`, returning HTML with `<form method="post" action="index.php">` and `<select name="term_code">`.
- The actual published Fall 2026 option on 2026-08-08 was `<option value="202660">Fall 2026</option>`. This value was read from the source form; it was not inferred from a Banner numbering convention.
- Selecting a term is `POST https://schedule.mcneese.edu/index.php` with form-encoded `term_code=202660`. No hidden anti-CSRF value, redirect, cookie, or session requirement was observed.
- The returned search form posts to the same `/index.php` endpoint. Verified fields are `term_code`, `fps`, `subject`, `course_number`, `title`, `schedule_type`, `credit_hours1`, `credit_hours2`, `course_level`, `part_of_term`, `instructor`, `start_hour`, `start_minute`, `start_ampm`, `end_hour`, `end_minute`, `end_ampm`, weekday checkbox names, `hide_closed`, `only_night`, and `only_web`.
- A verified CSCI request used `POST /index.php`, `term_code=202660`, `fps=0`, `subject=CSCI`, empty text/filter values, and the form's default `00`/`am` time controls. Checked `only_web` submits `only_web=on`.
- An unfiltered empty-`subject` POST uses the same form fields but hangs/times out on the live public Class Search in this environment. Full-term imports therefore iterate the published subject `<select>` and issue one subject POST at a time with a configurable polite delay (`CLASS_SOURCE_SUBJECT_DELAY_SECONDS`, default 1s; source timeout default 180s).
- Responses are server-rendered `text/html; charset=UTF-8`, with no pagination control observed. Results use a repeated two-row section group inside a table. The first row has Status, CRN, combined Course identity, Title, Credits, Level, Capacity, Enrolled, and Available. The next row has Term/part-of-term label, one-or-more locations, one-or-more published instructors plus notes, attributes, and a nested meeting table containing day code, time range, and date range.
- Verified public detail links use `GET /?scr=crse1&term={term}&crn={crn}`; the production importer does not need to follow one link per section.
- McNeese explicitly states enrollment information is real-time and all other information updates hourly from 7:00 AM–4:30 PM. The listing exposes Capacity, Enrolled, and Available independently, so the pipeline stores all three and does not derive one from another.
- Observed CRNs were five numeric digits. Observed day codes use `M T W R F S U`, with `R` normalized internally as Thursday. Fixed times normalize to 24-hour `HH:MM`; `TBA` remains null/time-arranged. Real fixtures include a two-meeting CSCI section, a night CSCI section, and a TBA online ENGL section.
- Assumptions remaining intentionally unverified: no cheap section-only enrollment endpoint or stable source update timestamp was proven. Therefore no public targeted upstream refresh is exposed and no fabricated source timestamp is stored.

### Implemented pipeline and storage

- `McNeeseClassSearchAdapter` owns the fixed source boundary, explicit form contract, timeouts, a clear AskMcNeese user agent, and at most three bounded exponential-backoff attempts.
- The structural parser locates the required result columns, consumes section/detail row pairs, preserves multiple meetings, normalizes source days/times/dates, maps each observed location, and preserves raw day/time/date/status values for diagnosis.
- Validation separates optional missing instructor/room data from invalid identity, CRN, duplicate, negative capacity/enrolled, day, and fixed-time data. Verified Banner `FULL` rows may publish `enrolled > capacity` with blank Available; those over-enrolled sections are accepted as source truth rather than rejected.
- Staging is immutable in-memory normalized records. `ClassPlannerStore.publish` inserts a complete dataset and its normalized terms/courses/sections/meetings/instructors inside one `BEGIN IMMEDIATE` transaction, then switches `terms.active_dataset_id` in the same commit.
- SQLite tables are `datasets`, `terms`, `courses`, `sections`, `meetings`, `instructors`, `section_instructors`, `sync_runs`, and `sync_locks`, with focused lookup indexes. There was no repository migration system to reuse, so idempotent version-one DDL is applied by the store on initialization.
- Failed parsing, validation, anomaly checks, or database publication leave the previous active dataset unchanged. A database-backed per-term lock stores an owner token so abandoned cleanup cannot release a live owner's lock; abandoned locks expire after two hours.
- Anomaly gates include a configurable first-import floor (default 100 sections), at most 5% validation rejection, no greater-than-50% record collapse/removal relative to the baseline, and no systemic greater-than-80% instructor or meeting loss.
- Normalized hashes detect meaningful section changes. Sync runs store parser version, start/finish/status, record and diff counts, duration, and concise failure details without logging source pages.

### API and frontend integration

- Read-only routes are `GET /class-planner/terms`, `/class-planner/courses`, `/class-planner/courses/{courseId}`, `/class-planner/sections/{sectionId}`, and `/class-planner/freshness`.
- Course search supports term, deterministic text, open, online, day, and time-of-day filters against the published database. Responses carry source name, URL, mode, `fetchedAt`, parser version, and section count where appropriate.
- `plannerApi.ts` is the swappable API data source. `VITE_CLASS_DATA_MODE=mock|staging|live` selects it without scattering mock conditionals through visual components. API failure in staging/live is shown honestly and never falls back to `plannerData.ts`.
- Local schedules continue to store canonical section IDs. API mode hydrates those IDs into the latest section records; source changes can therefore flow into conflict detection, Week Pulse, timeline, desktop calendar, credits, CRNs, and the local live-time projection.
- Add re-fetches the normalized AskMcNeese section endpoint and blocks the mutation with an explicit review message if instructor, availability, meeting time, or room changed since search display. It does not trigger an unauthenticated upstream scrape.
- Mobile tab order is now `Week | Find`. A non-empty saved-ID list defaults to Week; an empty schedule defaults to Find. Desktop remains a simultaneous workspace.
- The Demo indicator remains in mock mode. Staging and live modes identify McNeese provenance; live is not enabled by the code change alone.

### Synchronization and current gate

- The idempotent manual entry point is `python -m app.services.class_planner.pipeline --term 202660`.
- Optional automated synchronization reuses the same entry point when `CLASS_SYNC_ENABLED=true`; default cadence is hourly and cannot be configured below 15 minutes. It is disabled by default so a deployment must deliberately choose its database path, term, and scheduler ownership.
- Metadata and availability currently share the full validated snapshot cadence. A 60–120 second targeted seat TTL was not implemented because a cheap, abuse-resistant upstream section refresh contract was not established.
- Current frontend default remains `VITE_CLASS_DATA_MODE=mock`. Backend published mode is `CLASS_DATA_MODE=staging` until an operator explicitly flips production live after the gate below. Production does not silently switch itself to live or fall back to mock.

### After implementation — verified results (2026-08-08)

#### Actual request contract (proven)

- Term discovery: `GET https://schedule.mcneese.edu/` → `<select name="term_code">`.
- Fall 2026 source term ID: `202660` (read from the live form option text/value).
- Section retrieval: `POST https://schedule.mcneese.edu/index.php` with form-encoded fields including `term_code`, `fps=0`, `subject=<code>`, empty filters, default time controls.
- Full-term strategy: 76 published subjects fetched sequentially; empty-subject unfiltered POST is not used for production import because it hangs.
- Response type: HTML tables; CRNs five digits; days `MTWRFSU`; Capacity/Enrolled/Available published independently.

#### Full Fall 2026 import

- Sync run id `4`, dataset id `1`, status `success`.
- Duration: 2032.188 seconds.
- Subjects fetched: 76 (one empty subject `DTSC` allowed).
- Records received/valid/rejected: **1606 / 1606 / 0**.
- Courses: 862. Meetings: 1797.
- Diff vs empty baseline: added 1606, changed 0, removed 0.
- Fetched at: `2026-08-08T16:25:34.140607+00:00`.

#### Representative manual comparison

- Compared 30 freshly re-fetched McNeese sections against the published AskMcNeese dataset across CSCI, MATH, ENGL, BIOL, and ENGL+`only_web`.
- Hard-field match (CRN, subject, number, section, title, credits, instructor, meetings/location/online/TBA): **30/30**.
- Seat counts were intentionally excluded from the hard match because enrollment can move between the import snapshot and the later verification fetch.

#### Fixtures captured

- `backend/tests/fixtures/mcneese_class_search/fall_2026_csci.html` (26 sections)
- `backend/tests/fixtures/mcneese_class_search/fall_2026_engl.html` (132 sections)
- `backend/tests/fixtures/mcneese_class_search/fall_2026_biol.html` (117 sections)
- `backend/tests/fixtures/mcneese_class_search/fall_2026_online.html` (ENGL + only_web, 23 sections)
- Existing `fall_2026_representative.html` remains the compact multi-shape unit fixture.

#### Files changed for this integration pass

- `backend/app/services/class_planner/pipeline.py` — subject-by-subject sync, progress output, over-enrollment acceptance, CLI entry.
- `backend/app/services/class_planner/store.py` — owner-token sync locks.
- `backend/tests/unit/test_class_planner_data.py` — subject parse, empty allow, over-enroll, lock-owner tests.
- `backend/tests/fixtures/mcneese_class_search/*` — live HTML fixtures.
- `.env.example` — timeout/delay/sync knobs.
- Frontend Class Planner API wiring + mobile `Week | Find` (already present; tests confirm).
- Docs: `README.md`, `ARCHITECTURE.md`, this record.

#### Tests actually run

- Backend: `python -m unittest discover -s tests/unit -p "test_class_planner*.py" -v` → **12 passed**.
- Frontend: `vitest run` Class Planner page + utils → **16 passed**.
- Live import + 30/30 hard-field verification as above.
- API smoke against published SQLite: terms/freshness/search/section detail.

#### Current data mode

- Frontend default: **mock** (`VITE_CLASS_DATA_MODE=mock`).
- Local published database: **staging-ready validated real data** for term `202660`.
- Production live gate: **not enabled**. Enable only by explicit env change after operator confirmation.

#### Known limitations

- No cheap public section-only seat refresh endpoint was proven; Add uses AskMcNeese snapshot re-read, not a live upstream scrape.
- Unfiltered full-term POST hangs; subject fan-out is required (~34 minutes for Fall 2026 at 0.5s delay in this run).
- Saved schedules that reference CRNs later removed by McNeese keep the ID association; they are not auto-replaced with another section.
- Building codes are stored/displayed as published; no speculative building-name enrichment.
- Live mode badge/path remains intentionally off until an operator flips `VITE_CLASS_DATA_MODE=live` against a deployed validated database.

## Beta completion layout and loading pass — 2026-08-08

Observed defects:

- Expanded desktop course/section content could grow outside the discovery pane and overlap or clip at the workspace boundary.
- Initial API loading rendered a large field of thin lines that looked like a broken page.
- Every query state discarded visible results while the next request loaded.
- Search could issue requests too eagerly and show both native and custom clear controls.

Corrections:

- Constrained the discovery pane and result rows with explicit `min-height`, intrinsic grid rows, and contained overflow.
- Replaced the striped field with three compact course-shaped skeleton rows.
- Added a 240 ms debounce and abort cleanup for stale requests.
- Kept the prior results visible with a quiet updating indicator during refresh.
- Removed the native WebKit search-cancel control when the custom control is present.
- Added responsive resets below the desktop breakpoint and disabled shimmer under reduced motion.

Verification:

- Real staging search for `CSCI` transitioned from the compact loader to normalized McNeese results.
- Expanded section cards remained inside the desktop discovery pane and scrolled independently.
- TypeScript and production build passed.