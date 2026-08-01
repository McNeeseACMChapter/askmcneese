/**
 * ACM Panel runs as its own Vite app on 3100.
 * Ask (5173) owns the member login gate, then hands off here.
 * Do not use 5174 — Windows often reserves that range.
 */
export function getAcmPanelUrl(path = "/home"): string {
  const origin = (import.meta.env.VITE_ACM_PANEL_URL as string | undefined)?.replace(/\/$/, "")
    ?? "http://127.0.0.1:3100";
  const normalized = path.startsWith("/") ? path : `/${path}`;
  return `${origin}${normalized}`;
}
