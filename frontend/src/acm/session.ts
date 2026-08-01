const KEY = "askmcneese.acm.demoSession";

export type AcmDemoSession = {
  email: string;
  memberId: string;
  role: "admin";
  at: number;
};

export function saveAcmSession(session: AcmDemoSession): void {
  try {
    sessionStorage.setItem(KEY, JSON.stringify(session));
  } catch {
    /* ignore */
  }
}

export function readAcmSession(): AcmDemoSession | null {
  try {
    const raw = sessionStorage.getItem(KEY);
    if (!raw) return null;
    return JSON.parse(raw) as AcmDemoSession;
  } catch {
    return null;
  }
}

export function clearAcmSession(): void {
  try {
    sessionStorage.removeItem(KEY);
  } catch {
    /* ignore */
  }
}
