import { Link } from "react-router-dom";
import type { AcmRouteDefinition } from "../../routes/manifest";
import type { DataMode } from "../../data/accessContract";
import { modeLabels } from "../../data/accessContract";

const routeModes: Partial<Record<string, DataMode>> = {
  home: "derived",
  "my-work": "derived",
  projects: "managed",
  "project-detail": "managed",
  meetings: "workflow",
  events: "workflow",
  members: "managed",
  governance: "workflow",
  approvals: "workflow",
  sga: "workflow",
  finance: "workflow",
  communications: "workflow",
  documents: "managed",
  reports: "derived",
  notifications: "managed",
  administration: "restricted",
  audit: "immutable",
  profile: "managed",
};

const modeCopy: Record<DataMode, string> = {
  managed: "Some fields can be edited; protected fields still require policy or workflow.",
  workflow: "Changes move through an authorized transition rather than a direct overwrite.",
  derived: "This view is calculated from source records and is not directly editable.",
  immutable: "Records can be inspected and filtered but never overwritten.",
  restricted: "Technical changes require elevated access, a reason, and audit history.",
};

export function DataModeIndicator({ route }: { route: AcmRouteDefinition }) {
  const mode = routeModes[route.id];
  if (!mode) return null;

  return (
    <div className="page-data-mode" data-mode={mode} role="note">
      <span className="page-data-mode__label">{modeLabels[mode]}</span>
      <span>{modeCopy[mode]}</span>
      <Link to="/data-access">View data map</Link>
    </div>
  );
}