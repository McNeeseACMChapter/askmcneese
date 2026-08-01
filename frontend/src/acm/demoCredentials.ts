/**
 * Local ACM demo login — mirrors askmcneese/acm/auth/demo-credentials.json.
 * Not production auth.
 */
export const ACM_DEMO = {
  email: "admin",
  emailAliases: ["admin", "admin@mcneese.edu"] as const,
  memberId: "123",
  password: "pass123",
} as const;

export function isAcmDemoLogin(input: {
  email: string;
  memberId: string;
  password: string;
}): boolean {
  const email = input.email.trim().toLowerCase();
  const memberId = input.memberId.trim();
  const password = input.password;
  const emailOk = ACM_DEMO.emailAliases.some((a) => a.toLowerCase() === email);
  return emailOk && memberId === ACM_DEMO.memberId && password === ACM_DEMO.password;
}
