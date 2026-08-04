import { Link } from "react-router-dom";
import { PageChrome } from "../components/layout/PageChrome";
import { routeManifest } from "../routes/manifest";
import { usePrototype } from "../state/PrototypeContext";
import { roleOptions } from "../data/seed";
import { Surface } from "../components/ui/Surface";
import type { RoleId } from "../data/types";

const route = routeManifest.find((r) => r.id === "profile")!;

export function ProfilePage() {
  const { user, roleId, setRoleId } = usePrototype();

  return (
    <PageChrome route={route} title="Profile">

      <Surface level="content" className="flex flex-wrap items-center gap-5 p-6">
        <span
          aria-hidden
          className="grid h-16 w-16 place-items-center rounded-full text-lg font-bold"
          style={{ background: "var(--brand-100)", color: "var(--brand-900)" }}
        >
          {user.initials}
        </span>
        <div>
          <p className="text-xl font-semibold text-text-primary" style={{ fontFamily: "var(--font-editorial)" }}>
            {user.name}
          </p>
          <p className="page-lede">
            {user.roleLabel} · {user.termLabel}
          </p>
        </div>
      </Surface>

      <Surface level="content" className="p-5">
        <h2 className="text-lg">Permissions (fixture)</h2>
        <dl className="mt-3 grid gap-3 text-sm sm:grid-cols-2">
          <div>
            <dt className="text-text-muted">Administration</dt>
            <dd className="font-semibold">{user.canViewAdmin ? "Visible" : "Hidden"}</dd>
          </div>
          <div>
            <dt className="text-text-muted">Audit</dt>
            <dd className="font-semibold">{user.canViewAudit ? "Visible" : "Hidden"}</dd>
          </div>
        </dl>
      </Surface>

      <Surface level="content" className="p-5">
        <h2 className="text-lg">Switch fixture role</h2>
        <p className="mt-1 text-sm text-text-secondary">
          Preview Home, My Work, and permission-gated destinations from another chapter role.
        </p>
        <label className="acm-field mt-3 max-w-sm">
          <span className="acm-field__label">Fixture role</span>
          <select
            className="acm-select"
            value={roleId}
            onChange={(e) => setRoleId(e.target.value as RoleId)}
          >
            {roleOptions.map((r) => (
              <option key={r.id} value={r.id}>
                {r.label}
              </option>
            ))}
          </select>
        </label>
        <Link to="/fixtures" className="mt-4 inline-flex text-sm font-semibold">
          Open full fixture gallery →
        </Link>
      </Surface>
    </PageChrome>
  );
}
