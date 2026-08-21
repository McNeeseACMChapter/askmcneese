// @vitest-environment node
import path from "node:path";
import { describe, expect, it, vi } from "vitest";
import { canonicalTimelinePlugin } from "../../../vite.config";

function invoke(hook: unknown): (...args: unknown[]) => unknown {
  if (typeof hook === "function") return hook as (...args: unknown[]) => unknown;
  return (hook as { handler: (...args: unknown[]) => unknown }).handler;
}

describe("canonical timeline Vite integration", () => {
  it("watches the source and serves fresh CSV through HMR", async () => {
    const sourcePath = path.resolve(process.cwd(), "../docs/pm/timeline.csv");
    const plugin = canonicalTimelinePlugin(sourcePath);
    const resolvedId = invoke(plugin.resolveId)("virtual:pm-timeline");
    const addWatchFile = vi.fn();

    expect(resolvedId).toBe("\0virtual:pm-timeline");
    const initialModule = invoke(plugin.load).call({ addWatchFile }, resolvedId) as {
      code: string;
    };
    expect(addWatchFile).toHaveBeenCalledWith(sourcePath);
    expect(initialModule.code).toContain("TicketNo,JobDone");

    const timelineModule = {};
    const server = {
      watcher: { add: vi.fn() },
      moduleGraph: { getModuleById: vi.fn().mockReturnValue(timelineModule) },
      ws: { send: vi.fn() },
    };
    invoke(plugin.configureServer)(server);
    expect(server.watcher.add).toHaveBeenCalledWith(sourcePath);

    const result = await invoke(plugin.handleHotUpdate)({
      file: sourcePath,
      read: vi.fn().mockResolvedValue("fresh canonical CSV"),
      server,
    });
    expect(server.moduleGraph.getModuleById).toHaveBeenCalledWith("\0virtual:pm-timeline");
    expect(result).toEqual([timelineModule]);

    const refreshedModule = invoke(plugin.load).call({ addWatchFile }, resolvedId) as {
      code: string;
    };
    expect(refreshedModule.code).toContain("fresh canonical CSV");
  });
});
