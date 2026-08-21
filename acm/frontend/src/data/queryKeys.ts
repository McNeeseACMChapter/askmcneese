export const qk = {
  state: ["fixture-state"] as const,
  pulse: ["pulse"] as const,
  projects: ["projects"] as const,
  project: (id: string) => ["project", id] as const,
  approval: (id: string) => ["approval", id] as const,
  work: ["work"] as const,
};
