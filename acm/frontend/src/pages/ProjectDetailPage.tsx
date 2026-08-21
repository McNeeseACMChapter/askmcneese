import { useState } from "react";
import { PencilLine } from "lucide-react";
import { Link, useParams } from "react-router-dom";
import * as Tabs from "@radix-ui/react-tabs";
import { PageChrome } from "../components/layout/PageChrome";
import { routeManifest } from "../routes/manifest";
import { useFixtureState, useProjectQuery } from "../data/hooks";
import { ProgressBar } from "../components/viz/ProgressBar";
import { ProgressRing } from "../components/viz/ProgressRing";
import { Sparkline } from "../components/viz/Sparkline";
import { LifecycleStepper } from "../components/viz/LifecycleStepper";
import { AvatarGroup } from "../components/viz/AvatarGroup";
import { Surface } from "../components/ui/Surface";
import { Button } from "../components/ui/Button";
import { StatusBadge, healthToTone } from "../components/ui/StatusBadge";
import { Breadcrumbs } from "../components/ui/Breadcrumbs";
import { Timeline } from "../components/ui/Timeline";
import { EvidenceList } from "../components/ui/EvidenceList";
import { ProjectEditDrawer } from "../components/ProjectEditDrawer";
import { usePrototype } from "../state/PrototypeContext";

const route = routeManifest.find((r) => r.id === "project-detail")!;
const severityTone = { low: "success", medium: "warning", high: "danger" } as const;

const tabDefs = [
  { value: "overview", label: "Overview" },
  { value: "activity", label: "Activity" },
  { value: "evidence", label: "Evidence" },
  { value: "decisions", label: "Decisions" },
  { value: "access", label: "Access" },
];

export function ProjectDetailPage() {
  const { projectId } = useParams();
  const { data: project } = useProjectQuery(projectId ?? "");
  const state = useFixtureState();
  const { user, roleId } = usePrototype();
  const [editOpen, setEditOpen] = useState(false);

  if (!project) {
    return (
      <PageChrome route={route} title="Project not found">
        <Surface level="content" className="p-8">
          <h1>Project not found</h1>
          <p className="page-lede">
            This fixture project does not exist.{" "}
            <Link to="/projects">Back to Projects</Link>
          </p>
        </Surface>
      </PageChrome>
    );
  }

  const canEdit =
    (roleId === "project_manager" && project.owner === user.name) ||
    roleId === "president" ||
    roleId === "advisor";
  const tone = healthToTone(project.health);
  const relatedApprovals = state.approvals.filter((a) => a.relatedProjectId === project.id);

  const steps = project.milestones.map((m, i) => ({
    id: m.id,
    label: m.label,
    done: m.done,
    current: !m.done && project.milestones.slice(0, i).every((mm) => mm.done),
  }));

  return (
    <PageChrome
      route={route}
      title={project.name}
      actions={
        canEdit ? (
          <Button variant="secondary" onClick={() => setEditOpen(true)}>
            <PencilLine size={16} aria-hidden />
            Edit project
          </Button>
        ) : undefined
      }
    >
      <Breadcrumbs items={[{ label: "Projects", to: "/projects" }, { label: project.name }]} />

      <div className="record-access-bar" role="note">
        <span className={"record-access-bar__mode" + (canEdit ? "" : " is-view-only")}>
          <PencilLine size={14} aria-hidden />
          {canEdit ? "Managed edit" : "View only"}
        </span>
        <span>
          {canEdit
            ? "You may edit assigned delivery fields. Ownership, approvals, and calculated evidence stay protected."
            : "Your current role can inspect this record but cannot change its managed fields."}
        </span>
        <Link to="/data-access">See field boundaries →</Link>
      </div>

      <div className="flex flex-wrap items-start justify-between gap-4">
        <div className="flex flex-wrap items-center gap-3">
          <h1>{project.name}</h1>
          <StatusBadge label={tone.label} tone={tone.tone} />
        </div>
        <ProgressRing value={project.progressPercent} label="Overall progress" />
      </div>
      <p className="page-lede">
        Owner {project.owner} · Next milestone {project.nextMilestone} · Due {project.dueDate}
      </p>
      <div className="mt-2 flex flex-wrap items-center gap-4">
        <AvatarGroup people={project.team} />
        <Sparkline values={project.trend} label={`${project.name} 7-point trend`} />
      </div>

      <div className="detail-layout mt-6">
        <div className="detail-layout__main">
          <Tabs.Root defaultValue="overview">
            <Tabs.List
              className="flex gap-2 overflow-x-auto border-b border-[var(--border-subtle)] text-sm font-semibold text-text-muted"
              aria-label="Project sections"
            >
              {tabDefs.map((tab) => (
                <Tabs.Trigger
                  key={tab.value}
                  value={tab.value}
                  className="min-h-hit whitespace-nowrap rounded-lg px-3 py-2 data-[state=active]:text-[var(--brand-800)] data-[state=active]:shadow-[inset_0_-2px_0_var(--brand-700)]"
                >
                  {tab.label}
                </Tabs.Trigger>
              ))}
            </Tabs.List>

            <Tabs.Content value="overview" className="space-y-4 pt-4">
              <Surface level="content" className="p-5">
                <h2 className="text-lg">Scope summary</h2>
                <p className="mt-2 text-sm text-text-secondary">{project.scope}</p>
                <div className="mt-3 max-w-sm">
                  <ProgressBar value={project.progressPercent} label="Progress" />
                </div>
              </Surface>
              <Surface level="content" className="p-5">
                <h2 className="text-lg">Milestones</h2>
                <div className="mt-3">
                  <LifecycleStepper steps={steps} label="Milestones" />
                </div>
              </Surface>
              <Surface level="content" className="p-5">
                <h2 className="text-lg">Current risks</h2>
                {project.risks.length === 0 ? (
                  <p className="mt-2 text-sm text-text-muted">No open risks in fixture.</p>
                ) : (
                  <ul className="mt-2 space-y-2">
                    {project.risks.map((r) => (
                      <li key={r.id} className="flex items-center justify-between gap-3 text-sm">
                        <span className="text-text-secondary">{r.label}</span>
                        <StatusBadge label={r.severity} tone={severityTone[r.severity]} />
                      </li>
                    ))}
                  </ul>
                )}
              </Surface>
            </Tabs.Content>

            <Tabs.Content value="activity" className="pt-4">
              <Surface level="content" className="p-5">
                <h2 className="text-lg">Activity</h2>
                <div className="mt-4">
                  <Timeline
                    items={[
                      { id: "updated", title: `Last updated ${project.updated}`, meta: project.owner },
                      ...project.milestones
                        .filter((m) => m.done)
                        .map((m) => ({
                          id: m.id,
                          title: `Milestone complete: ${m.label}`,
                          meta: `Due ${m.due}`,
                        })),
                      ...project.risks.map((r) => ({
                        id: r.id,
                        title: `Risk flagged: ${r.label}`,
                        meta: `Severity ${r.severity}`,
                      })),
                    ]}
                  />
                </div>
              </Surface>
            </Tabs.Content>

            <Tabs.Content value="evidence" className="pt-4">
              <Surface level="content" className="p-5">
                <h2 className="text-lg">Evidence completeness</h2>
                <div className="mt-3 flex items-center gap-4">
                  <ProgressRing value={project.evidenceCompleteness} label="Evidence" />
                  <p className="text-sm text-text-secondary">
                    Milestone artifacts tracked as evidence for this workstream.
                  </p>
                </div>
                <div className="mt-4">
                  <EvidenceList
                    items={project.milestones.map((m) => ({
                      id: m.id,
                      label: m.label,
                      present: m.done,
                    }))}
                  />
                </div>
              </Surface>
            </Tabs.Content>

            <Tabs.Content value="decisions" className="pt-4">
              <Surface level="content" className="p-5">
                <h2 className="text-lg">Related decisions</h2>
                {relatedApprovals.length === 0 ? (
                  <p className="mt-2 text-sm text-text-muted">No linked approvals in fixture.</p>
                ) : (
                  <ul className="mt-2 space-y-2">
                    {relatedApprovals.map((a) => (
                      <li key={a.id} className="flex items-center justify-between gap-3 text-sm">
                        <span className="text-text-secondary">{a.title}</span>
                        <Link to={`/approvals/${a.id}`} className="text-sm font-semibold">
                          Open →
                        </Link>
                      </li>
                    ))}
                  </ul>
                )}
                <p className="mt-4 text-sm text-text-secondary">
                  Keep retrieval eval evidence pack as Phase 2 gate (fixture).
                </p>
              </Surface>
            </Tabs.Content>

            <Tabs.Content value="access" className="pt-4">
              <Surface level="content" className="p-5">
                <h2 className="text-lg">Team &amp; access</h2>
                <ul className="mt-3 space-y-2">
                  {project.team.length === 0 ? (
                    <li className="text-sm text-text-muted">No assigned team in fixture.</li>
                  ) : (
                    project.team.map((t) => (
                      <li key={t.name} className="flex items-center justify-between gap-3 text-sm">
                        <span className="font-semibold text-text-primary">{t.name}</span>
                        <span className="text-text-muted">{t.role}</span>
                      </li>
                    ))
                  )}
                </ul>
                <p className="mt-4 text-xs text-text-muted">
                  Classification: MEMBER (fixture) · workspace visible to assigned team and officers.
                </p>
              </Surface>
            </Tabs.Content>
          </Tabs.Root>
        </div>

        <aside className="detail-layout__aside space-y-4">
          <Surface level="content" className="p-5">
            <h2 className="text-lg">Context</h2>
            <dl className="mt-3 space-y-3 text-sm">
              <div>
                <dt className="text-text-muted">Owner</dt>
                <dd className="font-semibold">{project.owner}</dd>
              </div>
              <div>
                <dt className="text-text-muted">Due</dt>
                <dd className="font-semibold">{project.dueDate}</dd>
              </div>
              <div>
                <dt className="text-text-muted">Updated</dt>
                <dd className="font-semibold">{project.updated}</dd>
              </div>
              <div>
                <dt className="text-text-muted">Risk</dt>
                <dd className="font-semibold">
                  {project.riskCount} open · {project.riskSeverity}
                </dd>
              </div>
            </dl>
          </Surface>
        </aside>
      </div>
      <ProjectEditDrawer project={project} open={editOpen} onClose={() => setEditOpen(false)} />
    </PageChrome>
  );
}
