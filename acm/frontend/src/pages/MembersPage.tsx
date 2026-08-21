import { useMemo, useState } from "react";
import { PageChrome } from "../components/layout/PageChrome";
import { routeManifest } from "../routes/manifest";
import { useFixtureState } from "../data/hooks";
import { ProgressBar } from "../components/viz/ProgressBar";
import { Sparkline } from "../components/viz/Sparkline";
import { AvatarGroup } from "../components/viz/AvatarGroup";
import { Surface } from "../components/ui/Surface";
import { FilterBar } from "../components/ui/FilterBar";
import { EmptyState } from "../components/ui/EmptyState";

const route = routeManifest.find((r) => r.id === "members")!;

export function MembersPage() {
  const state = useFixtureState();
  const [search, setSearch] = useState("");

  const filtered = useMemo(() => {
    if (!search.trim()) return state.members;
    const q = search.toLowerCase();
    return state.members.filter(
      (m) =>
        m.name.toLowerCase().includes(q) ||
        m.role.toLowerCase().includes(q) ||
        m.skills.some((s) => s.toLowerCase().includes(q)),
    );
  }, [state.members, search]);

  return (
    <PageChrome route={route} title="Members">
      <FilterBar search={search} onSearch={setSearch} />
      {filtered.length === 0 ? (
        <Surface level="content">
          <EmptyState
            title="No matching members"
            body="Adjust search to find chapter members by name, role, or skill."
          />
        </Surface>
      ) : (
        <Surface level="content" className="overflow-hidden">
          <ul className="divide-y divide-[var(--border-subtle)]">
            {filtered.map((member) => (
              <li key={member.id} className="row-hover flex flex-wrap items-center gap-4 px-5 py-4">
                <AvatarGroup people={[{ name: member.name, initials: member.initials }]} />
                <div className="min-w-[200px] flex-1">
                  <p className="text-sm font-semibold text-text-primary">{member.name}</p>
                  <p className="text-xs text-text-muted">
                    {member.role} · {member.term} · Availability {member.availability}
                  </p>
                  <div className="mt-1 flex flex-wrap gap-1">
                    {member.skills.map((skill) => (
                      <span
                        key={skill}
                        className="inline-flex items-center rounded-md bg-surface-subtle px-2 py-0.5 text-xs font-medium text-text-secondary"
                      >
                        {skill}
                      </span>
                    ))}
                  </div>
                </div>
                <div className="min-w-[150px]">
                  <p className="text-xs font-semibold uppercase tracking-wide text-text-muted">
                    Onboarding
                  </p>
                  <div className="mt-1">
                    <ProgressBar value={member.onboardingPercent} label={`${member.name} onboarding`} />
                  </div>
                </div>
                <div>
                  <p className="text-xs font-semibold uppercase tracking-wide text-text-muted">
                    Engagement
                  </p>
                  <div className="mt-1">
                    <Sparkline values={member.engagement} label={`${member.name} engagement`} />
                  </div>
                </div>
                <div className="min-w-[150px] text-xs text-text-muted">
                  {member.projects.length > 0 ? member.projects.join(", ") : "No active project"}
                </div>
              </li>
            ))}
          </ul>
        </Surface>
      )}
    </PageChrome>
  );
}
