import { Navigate } from "react-router-dom";

/**
 * Legacy route retained without simulated authentication.
 */
export function AcmPanelPage() {
  return <Navigate to="/acm/login" replace />;
}
