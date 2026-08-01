import { useEffect } from "react";
import { Navigate } from "react-router-dom";
import { getAcmPanelUrl } from "./panelUrl";
import { readAcmSession } from "./session";

/**
 * Legacy /acm/panel route — send verified members to the ACM Panel app (:5174).
 */
export function AcmPanelPage() {
  const session = readAcmSession();

  useEffect(() => {
    if (!session) return;
    window.location.replace(getAcmPanelUrl("/home"));
  }, [session]);

  if (!session) {
    return <Navigate to="/acm/login" replace />;
  }

  return (
    <main className="acm-panel">
      <div className="acm-panel__shell">
        <p className="acm-panel__lede">Opening ACM Panel…</p>
      </div>
    </main>
  );
}
