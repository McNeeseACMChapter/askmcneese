import { useState } from "react";
import { PageChrome } from "../components/layout/PageChrome";
import { routeManifest } from "../routes/manifest";
import { usePrototype } from "../state/PrototypeContext";
import { fixtureRepo, type FailureMode } from "../data/repository";
import { PermissionNotice } from "../components/ui/PermissionNotice";
import { Surface } from "../components/ui/Surface";
import { Button } from "../components/ui/Button";
import { StatusBadge } from "../components/ui/StatusBadge";
import { useToast } from "../components/toast/ToastProvider";

const route = routeManifest.find((r) => r.id === "administration")!;

const failureModes: { id: FailureMode; label: string; description: string }[] = [
  { id: "none", label: "Healthy", description: "Fixture calls resolve normally." },
  {
    id: "network",
    label: "Network outage",
    description: "Every fixture call rejects with a network error.",
  },
  {
    id: "permission",
    label: "Permission denied",
    description: "Every fixture call rejects as unauthorized.",
  },
  {
    id: "conflict",
    label: "Conflict of interest",
    description: "Every fixture call rejects as a SoD conflict.",
  },
];

export function AdministrationPage() {
  const { user } = usePrototype();
  const { push } = useToast();
  const [mode, setMode] = useState<FailureMode>("none");
  const [delay, setDelay] = useState(450);

  if (!user.canViewAdmin) {
    return (
      <PageChrome route={route} title="Administration">
        <PermissionNotice />
      </PageChrome>
    );
  }

  return (
    <PageChrome route={route} title="Administration">

      <Surface level="content" className="p-5">
        <h2 className="text-lg">Fixture network simulation</h2>
        <p className="mt-1 text-sm text-text-secondary">
          Adjust how the in-memory fixture repository responds to reads and mutations across the
          panel.
        </p>
        <div className="mt-4 grid gap-3 sm:grid-cols-2">
          {failureModes.map((fm) => (
            <button
              key={fm.id}
              type="button"
              className="surface-solid p-4 text-left"
              style={{
                borderColor: mode === fm.id ? "var(--brand-700)" : undefined,
                boxShadow:
                  mode === fm.id
                    ? "0 0 0 2px color-mix(in srgb, var(--brand-700) 25%, transparent)"
                    : undefined,
              }}
              onClick={() => {
                setMode(fm.id);
                fixtureRepo.setFailureMode(fm.id);
                push({
                  title: `Failure mode set to ${fm.label}`,
                  tone: fm.id === "none" ? "success" : "warning",
                });
              }}
            >
              <p className="text-sm font-semibold text-text-primary">{fm.label}</p>
              <p className="mt-1 text-xs text-text-muted">{fm.description}</p>
              {mode === fm.id ? (
                <div className="mt-2">
                  <StatusBadge label="Active" tone="info" />
                </div>
              ) : null}
            </button>
          ))}
        </div>
      </Surface>

      <Surface level="content" className="p-5">
        <h2 className="text-lg">Simulated latency</h2>
        <p className="mt-1 text-sm text-text-secondary">
          Milliseconds of artificial delay before fixture calls resolve.
        </p>
        <div className="mt-3 flex items-center gap-4">
          <input
            type="range"
            min={0}
            max={2000}
            step={50}
            value={delay}
            onChange={(e) => {
              const ms = Number(e.target.value);
              setDelay(ms);
              fixtureRepo.setDelay(ms);
            }}
            className="max-w-sm flex-1"
            aria-label="Simulated latency in milliseconds"
          />
          <span className="w-16 text-sm font-semibold text-text-primary">{delay}ms</span>
        </div>
      </Surface>

      <Surface level="content" className="p-5">
        <h2 className="text-lg">Fixture data</h2>
        <p className="mt-1 text-sm text-text-secondary">
          Reset the in-memory fixture state back to its seed values.
        </p>
        <Button
          variant="danger-outline"
          className="mt-3"
          onClick={() => {
            fixtureRepo.reset();
            setMode("none");
            push({
              title: "Fixture data reset",
              description: "All prototype records restored to seed state.",
              tone: "info",
            });
          }}
        >
          Reset fixture data
        </Button>
      </Surface>

      <Surface level="content" className="p-5">
        <h2 className="text-lg">Build info</h2>
        <dl className="mt-3 grid gap-3 text-sm sm:grid-cols-3">
          <div>
            <dt className="text-text-muted">App</dt>
            <dd className="font-semibold">ACM Panel prototype</dd>
          </div>
          <div>
            <dt className="text-text-muted">Version</dt>
            <dd className="font-semibold">0.1.0-prototype</dd>
          </div>
          <div>
            <dt className="text-text-muted">Mode</dt>
            <dd className="font-semibold">{import.meta.env.MODE}</dd>
          </div>
        </dl>
      </Surface>
    </PageChrome>
  );
}
