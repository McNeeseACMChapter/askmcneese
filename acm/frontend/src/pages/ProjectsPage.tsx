import { useMemo, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import {
  createColumnHelper,
  flexRender,
  getCoreRowModel,
  getSortedRowModel,
  useReactTable,
  type SortingState,
} from "@tanstack/react-table";
import { PageChrome } from "../components/layout/PageChrome";
import { routeManifest } from "../routes/manifest";
import { useFixtureState } from "../data/hooks";
import { HealthStrip } from "../components/viz/HealthStrip";
import { ProgressBar } from "../components/viz/ProgressBar";
import { Sparkline } from "../components/viz/Sparkline";
import { Surface } from "../components/ui/Surface";
import { StatusBadge } from "../components/ui/StatusBadge";
import { EmptyState } from "../components/ui/EmptyState";
import { FilterBar } from "../components/ui/FilterBar";
import type { ProjectHealth, ProjectRecord } from "../data/types";

const route = routeManifest.find((r) => r.id === "projects")!;
const columnHelper = createColumnHelper<ProjectRecord>();

type ViewMode = "table" | "board" | "timeline";
type HealthFilter = "all" | ProjectHealth;

const riskTone = { low: "success", medium: "warning", high: "danger" } as const;
const boardHealths: ProjectHealth[] = ["on_track", "at_risk", "blocked", "completed"];

const columns = [
  columnHelper.accessor("name", {
    header: "Project",
    cell: (info) => (
      <Link
        to={`/projects/${info.row.original.id}`}
        className="acm-data-table__primary no-underline"
      >
        {info.getValue()}
      </Link>
    ),
  }),
  columnHelper.accessor("owner", { header: "Owner" }),
  columnHelper.accessor("health", {
    header: "Health",
    cell: (info) => <HealthStrip health={info.getValue()} />,
  }),
  columnHelper.accessor("progressPercent", {
    header: "Progress",
    cell: (info) => (
      <ProgressBar value={info.getValue()} label={`${info.row.original.name} progress`} />
    ),
  }),
  columnHelper.accessor("trend", {
    header: "Trend",
    enableSorting: false,
    cell: (info) => (
      <Sparkline values={info.getValue()} label={`${info.row.original.name} trend`} />
    ),
  }),
  columnHelper.accessor("riskCount", {
    header: "Risk",
    cell: (info) => {
      const p = info.row.original;
      return p.riskCount === 0 ? (
        <StatusBadge label="No risk" tone="success" />
      ) : (
        <StatusBadge label={`${p.riskCount} open`} tone={riskTone[p.riskSeverity]} />
      );
    },
  }),
  columnHelper.accessor("nextMilestone", { header: "Next milestone" }),
  columnHelper.accessor("dueDate", { header: "Due date" }),
  columnHelper.accessor("updated", {
    header: "Updated",
    cell: (info) => <span className="acm-data-table__meta">{info.getValue()}</span>,
  }),
];

export function ProjectsPage() {
  const state = useFixtureState();
  const [searchParams, setSearchParams] = useSearchParams();
  const [search, setSearch] = useState("");
  const [healthFilter, setHealthFilter] = useState<HealthFilter>("all");
  const [sorting, setSorting] = useState<SortingState>([{ id: "updated", desc: false }]);

  const view: ViewMode =
    searchParams.get("view") === "board" || searchParams.get("view") === "timeline"
      ? (searchParams.get("view") as ViewMode)
      : "table";

  function setView(next: ViewMode) {
    const nextParams = new URLSearchParams(searchParams);
    if (next === "table") nextParams.delete("view");
    else nextParams.set("view", next);
    setSearchParams(nextParams, { replace: true });
  }

  const projects = useMemo(() => state.projects.filter((p) => !p.archived), [state.projects]);

  const filtered = useMemo(() => {
    let rows = projects;
    if (healthFilter !== "all") rows = rows.filter((p) => p.health === healthFilter);
    if (search.trim()) {
      const q = search.toLowerCase();
      rows = rows.filter(
        (p) => p.name.toLowerCase().includes(q) || p.owner.toLowerCase().includes(q),
      );
    }
    return rows;
  }, [projects, healthFilter, search]);

  const table = useReactTable({
    data: filtered,
    columns,
    state: { sorting },
    onSortingChange: setSorting,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
  });

  const byHealth = useMemo(() => {
    const groups: Record<ProjectHealth, ProjectRecord[]> = {
      on_track: [],
      at_risk: [],
      blocked: [],
      completed: [],
      archived: [],
    };
    filtered.forEach((p) => {
      groups[p.health].push(p);
    });
    return groups;
  }, [filtered]);

  const timeline = useMemo(
    () => [...filtered].sort((a, b) => a.dueDate.localeCompare(b.dueDate)),
    [filtered],
  );

  return (
    <PageChrome route={route} title="Projects">
      <FilterBar search={search} onSearch={setSearch}>
        <label className="acm-field">
          <span className="sr-only">Health</span>
          <select
            className="acm-select"
            value={healthFilter}
            onChange={(e) => setHealthFilter(e.target.value as HealthFilter)}
          >
            <option value="all">All health</option>
            <option value="on_track">On track</option>
            <option value="at_risk">At risk</option>
            <option value="blocked">Blocked</option>
            <option value="completed">Completed</option>
          </select>
        </label>
        <div className="segmented" role="tablist" aria-label="Projects view">
          {(["table", "board", "timeline"] as ViewMode[]).map((v) => (
            <button
              key={v}
              type="button"
              role="tab"
              aria-selected={view === v}
              data-active={view === v ? "true" : "false"}
              onClick={() => setView(v)}
            >
              {v[0].toUpperCase() + v.slice(1)}
            </button>
          ))}
        </div>
      </FilterBar>

      {filtered.length === 0 ? (
        <Surface level="content">
          <EmptyState
            title="No matching projects"
            body="Adjust filters or clear search. Empty states use editorial type sparingly."
          />
        </Surface>
      ) : view === "table" ? (
        <Surface level="content" className="overflow-hidden" data-testid="projects-collection">
          <div className="acm-data-table-wrap">
            <table className="acm-data-table">
              <thead>
                {table.getHeaderGroups().map((hg) => (
                  <tr key={hg.id}>
                    {hg.headers.map((header) => {
                      const sortState = header.column.getIsSorted();
                      return (
                        <th key={header.id} scope="col">
                          {header.column.getCanSort() ? (
                            <button
                              type="button"
                              onClick={header.column.getToggleSortingHandler()}
                              className="inline-flex items-center gap-1 border-0 bg-transparent p-0 font-semibold text-text-secondary"
                            >
                              {flexRender(header.column.columnDef.header, header.getContext())}
                              {sortState === "asc" ? " ▲" : sortState === "desc" ? " ▼" : ""}
                            </button>
                          ) : (
                            flexRender(header.column.columnDef.header, header.getContext())
                          )}
                        </th>
                      );
                    })}
                  </tr>
                ))}
              </thead>
              <tbody>
                {table.getRowModel().rows.map((row) => (
                  <tr key={row.id}>
                    {row.getVisibleCells().map((cell) => (
                      <td key={cell.id}>
                        {flexRender(cell.column.columnDef.cell, cell.getContext())}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="acm-mobile-list" data-testid="projects-mobile-list">
            {filtered.map((project) => (
              <Link
                key={project.id}
                to={`/projects/${project.id}`}
                className="acm-mobile-list__item"
              >
                <div className="acm-mobile-list__top">
                  <span className="acm-mobile-list__title">{project.name}</span>
                  <HealthStrip health={project.health} />
                </div>
                <div className="acm-mobile-list__meta">
                  <span>Owner: {project.owner}</span>
                  <span>Due: {project.dueDate}</span>
                  <span>Updated {project.updated}</span>
                </div>
              </Link>
            ))}
          </div>
        </Surface>
      ) : view === "board" ? (
        <div className="board-cols">
          {boardHealths.map((health) => (
            <div key={health} className="board-col">
              <h3>
                {health.replace("_", " ")} ({byHealth[health].length})
              </h3>
              <div className="space-y-2">
                {byHealth[health].length === 0 ? (
                  <p className="text-xs text-text-muted">No projects.</p>
                ) : (
                  byHealth[health].map((p) => (
                    <Surface key={p.id} level="content" className="p-3">
                      <Link
                        to={`/projects/${p.id}`}
                        className="text-sm font-semibold no-underline"
                      >
                        {p.name}
                      </Link>
                      <div className="mt-2">
                        <ProgressBar value={p.progressPercent} label={`${p.name} progress`} />
                      </div>
                      <p className="mt-1 text-xs text-text-muted">
                        Owner {p.owner} · Due {p.dueDate}
                      </p>
                    </Surface>
                  ))
                )}
              </div>
            </div>
          ))}
        </div>
      ) : (
        <Surface level="content" className="p-5">
          <ol className="space-y-4">
            {timeline.map((p) => (
              <li
                key={p.id}
                className="flex flex-wrap items-center gap-4 border-b border-[var(--border-subtle)] pb-4 last:border-0 last:pb-0"
              >
                <div className="w-28 shrink-0 text-sm font-semibold text-text-secondary">
                  {p.dueDate}
                </div>
                <Link to={`/projects/${p.id}`} className="min-w-[160px] text-sm font-semibold no-underline">
                  {p.name}
                </Link>
                <HealthStrip health={p.health} />
                <div className="min-w-[160px] flex-1">
                  <ProgressBar value={p.progressPercent} label={`${p.name} progress`} />
                </div>
                <span className="text-xs text-text-muted">{p.nextMilestone}</span>
              </li>
            ))}
          </ol>
        </Surface>
      )}
    </PageChrome>
  );
}
