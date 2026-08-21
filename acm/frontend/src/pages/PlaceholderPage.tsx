import { Navigate } from "react-router-dom";

/**
 * Deprecated: every module now has a real page component. Kept as a stable
 * redirect in case any stale link still points at a placeholder route.
 */
export function PlaceholderPage() {
  return <Navigate to="/home" replace />;
}
