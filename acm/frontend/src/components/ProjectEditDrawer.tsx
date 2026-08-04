import { useEffect, useState, type FormEvent } from "react";
import { Calculator, FileLock2, GitBranch, PencilLine, Save } from "lucide-react";
import { useUpdateProjectMutation } from "../data/hooks";
import type { ProjectHealth, ProjectRecord } from "../data/types";
import { usePrototype } from "../state/PrototypeContext";
import { Button } from "./ui/Button";
import { Drawer } from "./ui/Drawer";
import { useToast } from "./toast/ToastProvider";

interface ProjectEditDrawerProps {
  project: ProjectRecord;
  open: boolean;
  onClose: () => void;
}

const healthOptions: { value: ProjectHealth; label: string }[] = [
  { value: "on_track", label: "On track" },
  { value: "at_risk", label: "At risk" },
  { value: "blocked", label: "Blocked" },
  { value: "completed", label: "Completed" },
];

export function ProjectEditDrawer({ project, open, onClose }: ProjectEditDrawerProps) {
  const { user, roleId } = usePrototype();
  const { push } = useToast();
  const mutation = useUpdateProjectMutation();
  const [scope, setScope] = useState(project.scope);
  const [nextMilestone, setNextMilestone] = useState(project.nextMilestone);
  const [dueDate, setDueDate] = useState(project.dueDate);
  const [progressPercent, setProgressPercent] = useState(project.progressPercent);
  const [health, setHealth] = useState<ProjectHealth>(project.health);
  const [reason, setReason] = useState("");

  useEffect(() => {
    if (!open) return;
    setScope(project.scope);
    setNextMilestone(project.nextMilestone);
    setDueDate(project.dueDate);
    setProgressPercent(project.progressPercent);
    setHealth(project.health);
    setReason("");
  }, [open, project]);

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const changes: Partial<
      Pick<ProjectRecord, "scope" | "nextMilestone" | "dueDate" | "progressPercent" | "health">
    > = {};
    if (scope !== project.scope) changes.scope = scope;
    if (nextMilestone !== project.nextMilestone) changes.nextMilestone = nextMilestone;
    if (dueDate !== project.dueDate) changes.dueDate = dueDate;
    if (progressPercent !== project.progressPercent) changes.progressPercent = progressPercent;
    if (health !== project.health) changes.health = health;

    if (Object.keys(changes).length === 0) {
      push({ title: "No changes to save", tone: "warning" });
      return;
    }

    mutation.mutate(
      {
        id: project.id,
        actor: user.name,
        actorInitials: user.initials,
        roleId,
        reason,
        changes,
      },
      {
        onSuccess: () => {
          push({
            title: "Project updated",
            description: "The durable record and audit history were updated together.",
            tone: "success",
          });
          onClose();
        },
        onError: (error) => {
          push({
            title: "Project update failed",
            description: error instanceof Error ? error.message : "The persistence service rejected the edit.",
            tone: "failure",
          });
        },
      },
    );
  }

  return (
    <Drawer open={open} onClose={onClose} title="Edit managed project fields" variant="side">
      <form className="project-edit-form" onSubmit={submit}>
        <div className="project-edit-boundary" role="note">
          <div>
            <PencilLine size={16} aria-hidden />
            <span><strong>Editable here</strong> Scope, milestone, date, progress, and health.</span>
          </div>
          <div>
            <GitBranch size={16} aria-hidden />
            <span><strong>Workflow-controlled</strong> Completion and archive still require the allowed transition.</span>
          </div>
          <div>
            <FileLock2 size={16} aria-hidden />
            <span><strong>Protected</strong> Owner and approval authority cannot be changed in this form.</span>
          </div>
          <div>
            <Calculator size={16} aria-hidden />
            <span><strong>Calculated</strong> Trends, risk count, and evidence completeness remain read-only.</span>
          </div>
        </div>

        <label className="acm-field">
          <span className="acm-field__label">Scope summary</span>
          <textarea
            className="acm-textarea"
            value={scope}
            onChange={(event) => setScope(event.target.value)}
            minLength={8}
            maxLength={1000}
            rows={4}
            required
          />
        </label>

        <label className="acm-field">
          <span className="acm-field__label">Next committed milestone</span>
          <input
            className="acm-input"
            value={nextMilestone}
            onChange={(event) => setNextMilestone(event.target.value)}
            minLength={3}
            maxLength={180}
            required
          />
        </label>

        <div className="project-edit-form__two">
          <label className="acm-field">
            <span className="acm-field__label">Due date</span>
            <input
              className="acm-input"
              type="date"
              value={dueDate}
              onChange={(event) => setDueDate(event.target.value)}
              required
            />
          </label>
          <label className="acm-field">
            <span className="acm-field__label">Operational health</span>
            <select
              className="acm-select"
              value={health}
              onChange={(event) => setHealth(event.target.value as ProjectHealth)}
            >
              {healthOptions.map((option) => (
                <option key={option.value} value={option.value}>{option.label}</option>
              ))}
            </select>
          </label>
        </div>

        <label className="acm-field">
          <span className="acm-field__label">
            Progress <strong>{progressPercent}%</strong>
          </span>
          <input
            className="project-progress-input"
            type="range"
            min="0"
            max="100"
            step="1"
            value={progressPercent}
            onChange={(event) => setProgressPercent(Number(event.target.value))}
          />
        </label>

        <label className="acm-field">
          <span className="acm-field__label">Change reason · required for audit</span>
          <textarea
            className="acm-textarea"
            value={reason}
            onChange={(event) => setReason(event.target.value)}
            minLength={8}
            maxLength={500}
            rows={3}
            placeholder="What changed, and why is this accurate now?"
            required
          />
          <span className="acm-field__hint">
            This reason travels with the edit and becomes part of the immutable audit event.
          </span>
        </label>

        <div className="project-edit-form__actions">
          <Button type="button" variant="ghost" onClick={onClose}>Cancel</Button>
          <Button type="submit" variant="primary" disabled={mutation.isPending || reason.trim().length < 8}>
            <Save size={16} aria-hidden />
            {mutation.isPending ? "Saving…" : "Save durable record"}
          </Button>
        </div>
      </form>
    </Drawer>
  );
}