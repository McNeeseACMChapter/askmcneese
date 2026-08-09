# AskMcNeese Class Planner

## Purpose

Class Planner helps students find published McNeese classes, compare sections, detect schedule conflicts, understand weekly timing, and prepare CRNs for official registration. It does not register a student or write to Banner.

> **Beta status:** the feature is complete for the current beta sprint and remains subject to source, production, and usability fixes.

## Supported workflow

```text
Find a course
    -> compare normalized sections
    -> see whether a section fits
    -> preview it on the week
    -> add it locally
    -> review credits, conflicts, and CRNs
```

## Current capabilities

- Fall 2026 term support (`202660`)
- Course code, title, and instructor search
- Open, online, day, and time filtering
- Course-grouped section results
- Lecture/lab and multi-meeting support
- Add, replace section, remove, and undo
- Duplicate-course prevention
- Exact overlap explanations using meeting dates, days, and times
- Browser-local schedule persistence
- Desktop discovery and positioned Monday-Friday calendar
- Phone Find and Week modes backed by the same state
- Candidate ghost preview before Add
- Registration Summary for manual CRN review
- McNeese-local live-time projection during instructional dates
- Loading, refresh, empty, offline, stale, and error states

## Data contract

McNeese public Class Search is the authority. The backend retrieves published term data, parses and normalizes it, validates required fields, runs anomaly gates, and transactionally publishes a SQLite read model. The browser never parses source HTML and never contacts `schedule.mcneese.edu` directly.

A failed synchronization leaves the previous validated dataset active. API responses include source/freshness metadata.

## Frontend modes

`VITE_CLASS_DATA_MODE` controls the adapter:

| Mode | Behavior |
| --- | --- |
| `mock` | Deterministic test/development records |
| `staging` | Backend normalized data with staging provenance |
| `live` | Backend normalized data intended for production operation |

Staging and live never silently fall back to mock records. Enable them only after a validated dataset is published.

## Search and loading behavior

- Query input is debounced by 240 ms before an API request.
- A new request aborts the prior in-flight search.
- Existing results remain visible while filters refresh.
- First-load feedback uses three compact course-shaped skeleton rows.
- Desktop results scroll within the discovery pane and cannot overlap the schedule.
- Native and custom search-clear controls are deduplicated.

## Responsive behavior

### Desktop and tablet

The discovery pane and week calendar are shown together when space permits. Result cards and expanded sections are width-contained. The calendar uses a shared time scale, preserves user scroll, and keeps its summary/header context available.

### Phone

Phones use separate **Week** and **Find** modes without duplicating state. Week keeps all weekdays discoverable, then provides a focused day timeline and event details. Flexible online/time-arranged sections remain present without fabricated meeting positions.

## Deterministic time model

The clock uses `America/Chicago`, aligns updates to minute boundaries, and reconciles after focus/visibility changes. Live state is applied only when:

- today is within the published instructional term;
- the date is not a known no-class date;
- meeting weekday and optional date range match;
- fixed start and end times exist.

Selected day and actual today are independent. Course colors identify classes; green is reserved for current-time state.

## Accessibility

- Semantic buttons, labels, tabs, regions, and dialogs
- Keyboard focus containment and restoration for modal interactions
- Escape dismissal where appropriate
- Minimum touch-target sizing
- Reduced-motion alternatives
- Text explanations for conflicts and schedule state

## Non-goals

This beta does not:

- register or drop classes;
- authenticate to Banner, DegreeWorks, or Canvas;
- guarantee seat availability beyond the published dataset freshness;
- provide seat alerts, calendar export, instructor reviews, or shared schedules;
- persist schedules to a user account;
- use an LLM to decide whether meetings conflict.

## Configuration

```env
VITE_CLASS_DATA_MODE=mock
VITE_CLASS_TERM_ID=202660
CLASS_DATA_MODE=staging
CLASS_PLANNER_DB_PATH=backend/class_planner.sqlite3
CLASS_SYNC_TERM_ID=202660
CLASS_SYNC_ENABLED=false
CLASS_SYNC_INTERVAL_SECONDS=3600
CLASS_SYNC_MIN_SECTIONS=100
```

## API

- `GET /class-planner/terms`
- `GET /class-planner/courses`
- `GET /class-planner/courses/{course_id}`
- `GET /class-planner/sections/{section_id}`
- `GET /class-planner/freshness`

## Verification

The feature is covered by parser/store tests, deterministic planner utility tests, API adapter tests, time-model tests, component tests, mobile navigation tests, TypeScript validation, production bundling, and real browser search/expand/layout checks.

See [`IMPLEMENTATION_RECORD.md`](IMPLEMENTATION_RECORD.md) and [`ARCHITECTURE.md`](ARCHITECTURE.md).
