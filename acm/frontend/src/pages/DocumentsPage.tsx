import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { FileWarning } from "lucide-react";
import { PageChrome } from "../components/layout/PageChrome";
import { routeManifest } from "../routes/manifest";
import { useFixtureState } from "../data/hooks";
import { Surface } from "../components/ui/Surface";
import { FilterBar } from "../components/ui/FilterBar";
import { StatusBadge, type StatusTone } from "../components/ui/StatusBadge";
import { EmptyState } from "../components/ui/EmptyState";

const route = routeManifest.find((r) => r.id === "documents")!;

const classificationTone: Record<string, StatusTone> = {
  PUBLIC: "success",
  RESTRICTED: "warning",
  OFFICER: "info",
};

export function DocumentsPage() {
  const state = useFixtureState();
  const [search, setSearch] = useState("");

  const filtered = useMemo(() => {
    if (!search.trim()) return state.documents;
    const q = search.toLowerCase();
    return state.documents.filter(
      (d) => d.title.toLowerCase().includes(q) || d.owner.toLowerCase().includes(q),
    );
  }, [state.documents, search]);

  const missing = state.documents.filter((d) => d.version === "—");

  return (
    <PageChrome route={route} title="Documents">
      {missing.length > 0 ? (
        <div className="status-callout status-callout--warning flex items-start gap-3" role="note">
          <FileWarning size={18} strokeWidth={1.75} aria-hidden />
          <div>
            <strong>
              {missing.length} document{missing.length > 1 ? "s" : ""} missing.
            </strong>{" "}
            {missing.map((d) => d.title).join(", ")} — required before related approvals can
            close.
          </div>
        </div>
      ) : null}

      <FilterBar search={search} onSearch={setSearch} />

      {filtered.length === 0 ? (
        <Surface level="content">
          <EmptyState title="No matching documents" body="Adjust search across the evidence library." />
        </Surface>
      ) : (
        <Surface level="content" className="overflow-hidden">
          <div className="acm-data-table-wrap">
            <table className="acm-data-table">
              <thead>
                <tr>
                  <th scope="col">Document</th>
                  <th scope="col">Classification</th>
                  <th scope="col">Owner</th>
                  <th scope="col">Version</th>
                  <th scope="col">Expires</th>
                  <th scope="col">Related</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((doc) => (
                  <tr key={doc.id}>
                    <td className="acm-data-table__primary">{doc.title}</td>
                    <td>
                      <StatusBadge
                        label={doc.classification}
                        tone={classificationTone[doc.classification] ?? "muted"}
                      />
                    </td>
                    <td>{doc.owner}</td>
                    <td>{doc.version}</td>
                    <td className="acm-data-table__meta">{doc.expires ?? "—"}</td>
                    <td>
                      {doc.related.startsWith("ap-") ? (
                        <Link to={`/approvals/${doc.related}`}>{doc.related}</Link>
                      ) : (
                        <span className="text-text-muted">{doc.related}</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Surface>
      )}
    </PageChrome>
  );
}
