import {
  Calculator,
  CheckCircle2,
  Database,
  FileLock2,
  GitBranch,
  PencilLine,
  ServerOff,
} from "lucide-react";
import { Link } from "react-router-dom";
import { PageChrome } from "../components/layout/PageChrome";
import { useAccessContractQuery } from "../data/hooks";
import {
  modeLabels,
  moduleAccessContracts,
  type DataMode,
} from "../data/accessContract";
import { routeManifest } from "../routes/manifest";

const route = routeManifest.find((item) => item.id === "data-access")!;

const modeIcons = {
  managed: PencilLine,
  workflow: GitBranch,
  derived: Calculator,
  immutable: FileLock2,
  restricted: FileLock2,
} satisfies Record<DataMode, typeof PencilLine>;

const flow = [
  {
    label: "1 · Human edit",
    body: "Only fields granted to the signed-in role become form controls.",
  },
  {
    label: "2 · Policy check",
    body: "The API re-checks role, ownership, scope, workflow state, and conflicts.",
  },
  {
    label: "3 · Durable record",
    body: "Structured data persists in the database; files belong in object storage.",
  },
  {
    label: "4 · Audit event",
    body: "Accepted and denied governed changes produce an append-only record.",
  },
];

export function DataAccessPage() {
  const contract = useAccessContractQuery();
  const modules = contract.data?.modules ?? moduleAccessContracts;
  const connected = contract.isSuccess;

  return (
    <PageChrome route={route} title="Data & access">
      <section className="data-access-hero" aria-labelledby="data-access-title">
        <div>
          <p className="data-access-eyebrow">Operational data contract</p>
          <h2 id="data-access-title">Every value has an owner and a boundary.</h2>
          <p>
            A field may be edited directly, changed only through a governed workflow,
            calculated from other records, or preserved permanently.
          </p>
        </div>
        <div
          className={"data-connection " + (connected ? "is-connected" : "is-offline")}
          role="status"
        >
          {connected ? <CheckCircle2 size={19} aria-hidden /> : <ServerOff size={19} aria-hidden />}
          <span>
            <strong>{connected ? "Project persistence connected" : "Persistence API unavailable"}</strong>
            <small>
              {connected
                ? contract.data.currentAdapter + " development adapter · Projects live now · " + contract.data.authoritativeTarget + " target"
                : "Planning contract is visible; managed edits remain disabled until reconnection."}
            </small>
          </span>
        </div>
      </section>

      <section className="data-flow" aria-labelledby="data-flow-title">
        <div className="data-section-heading">
          <p className="data-access-eyebrow">Mutation path</p>
          <h2 id="data-flow-title">Where an edit goes</h2>
        </div>
        <ol>
          {flow.map((step, index) => (
            <li key={step.label}>
              <span aria-hidden>{index + 1}</span>
              <strong>{step.label}</strong>
              <p>{step.body}</p>
            </li>
          ))}
        </ol>
      </section>

      <section className="data-contract" aria-labelledby="module-contract-title">
        <div className="data-section-heading data-section-heading--split">
          <div>
            <p className="data-access-eyebrow">Whole platform</p>
            <h2 id="module-contract-title">Module editability map</h2>
            <p>Direct edits never replace approvals, external evidence, or calculated truth.</p>
          </div>
          <div className="data-mode-legend" aria-label="Data mode legend">
            {(Object.keys(modeLabels) as DataMode[]).map((mode) => {
              const Icon = modeIcons[mode];
              return (
                <span key={mode} data-mode={mode}>
                  <Icon size={13} aria-hidden />
                  {modeLabels[mode]}
                </span>
              );
            })}
          </div>
        </div>

        <div className="data-contract-table" role="table" aria-label="Module data access contract">
          <div className="data-contract-row data-contract-row--header" role="row">
            <span role="columnheader">Module</span>
            <span role="columnheader">Directly editable</span>
            <span role="columnheader">Protected transition</span>
            <span role="columnheader">Calculated / read-only</span>
            <span role="columnheader">Destination</span>
          </div>
          {modules.map((item) => {
            const Icon = modeIcons[item.mode];
            return (
              <div className="data-contract-row" role="row" key={item.module}>
                <div className="data-contract-row__module" role="cell">
                  <span className="data-contract-row__icon" data-mode={item.mode} aria-hidden>
                    <Icon size={16} />
                  </span>
                  <span>
                    <Link to={item.route}>{item.module}</Link>
                    <small data-mode={item.mode}>{modeLabels[item.mode]}</small>
                  </span>
                </div>
                <div role="cell" data-label="Directly editable">{item.editable}</div>
                <div role="cell" data-label="Protected transition">{item.controlled}</div>
                <div role="cell" data-label="Calculated / read-only">{item.derived}</div>
                <div className="data-contract-row__destination" role="cell" data-label="Destination">
                  <Database size={14} aria-hidden />
                  <span>{item.destination}</span>
                </div>
              </div>
            );
          })}
        </div>
      </section>
    </PageChrome>
  );
}