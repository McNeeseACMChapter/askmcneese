import { Link } from "react-router-dom";
import { roleOptions } from "../data/seed";
import type { RoleId } from "../data/types";
import { PageChrome } from "../components/layout/PageChrome";
import { Surface } from "../components/ui/Surface";
import { routeManifest } from "../routes/manifest";
import { usePrototype } from "../state/PrototypeContext";

const route = {
  ...routeManifest.find((r) => r.id === "fixtures")!,
  purpose: "Development index for roles, states, and gated destinations.",
};

const fixtureLinks = [
  { to: "/home", label: "Home (command center)" },
  { to: "/my-work", label: "My Work" },
  { to: "/projects", label: "Projects" },
  { to: "/projects?view=board", label: "Projects board" },
  { to: "/projects/proj-ask-2", label: "Project detail" },
  { to: "/approvals/ap-role-001", label: "Approval (missing evidence)" },
  { to: "/approvals/ap-proj-001", label: "Approval (ready)" },
  { to: "/meetings", label: "Meetings" },
  { to: "/reports", label: "Reports" },
  { to: "/audit", label: "Audit (gated)" },
  { to: "/administration", label: "Administration (gated)" },
  { to: "/fixtures/permission-denied", label: "Permission denied" },
  { to: "/fixtures/empty", label: "Empty state" },
  { to: "/fixtures/archived", label: "Archived record" },
  { to: "/fixtures/offline", label: "Offline" },
  { to: "/fixtures/loading", label: "Loading" },
];

export function FixtureGalleryPage() {
  const { roleId, setRoleId, user } = usePrototype();

  return (
    <PageChrome route={route} title="Fixture gallery">
      <Surface level="content" className="p-5">
        <label className="acm-field max-w-sm">
          <span className="acm-field__label">Fixture role</span>
          <select
            className="acm-select"
            value={roleId}
            onChange={(e) => setRoleId(e.target.value as RoleId)}
            data-testid="fixture-role-switcher"
          >
            {roleOptions.map((r) => (
              <option key={r.id} value={r.id}>
                {r.label}
              </option>
            ))}
          </select>
        </label>
        <p className="mt-3 text-sm text-text-secondary">
          Active: <strong>{user.name}</strong> · {user.roleLabel} · Admin{" "}
          {user.canViewAdmin ? "visible" : "hidden"} · Audit{" "}
          {user.canViewAudit ? "visible" : "hidden"}
        </p>
      </Surface>

      <Surface level="content" className="overflow-hidden">
        <ul className="divide-y divide-[var(--border-subtle)]">
          {fixtureLinks.map((link) => (
            <li key={link.to}>
              <Link
                to={link.to}
                className="row-hover flex min-h-hit items-center px-5 py-3 text-sm font-semibold text-text-primary no-underline"
              >
                {link.label}
              </Link>
            </li>
          ))}
        </ul>
      </Surface>
    </PageChrome>
  );
}
