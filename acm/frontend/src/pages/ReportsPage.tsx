import { useMemo } from "react";
import { useNavigate } from "react-router-dom";
import ReactECharts from "echarts-for-react";
import type { EChartsOption } from "echarts";
import { PageChrome } from "../components/layout/PageChrome";
import { routeManifest } from "../routes/manifest";
import { useFixtureState, usePulseQuery } from "../data/hooks";
import { CompactMetric } from "../components/viz/CompactMetric";
import { Surface } from "../components/ui/Surface";

const route = routeManifest.find((r) => r.id === "reports")!;

export function ReportsPage() {
  const navigate = useNavigate();
  const state = useFixtureState();
  const { data: pulse } = usePulseQuery();
  const activeProjects = state.projects.filter((p) => !p.archived);
  const avgProgress = Math.round(
    activeProjects.reduce((sum, p) => sum + p.progressPercent, 0) /
      Math.max(activeProjects.length, 1),
  );

  const option = useMemo<EChartsOption>(
    () => ({
      textStyle: { fontFamily: "Source Sans 3, sans-serif" },
      color: ["#0e4c92", "#f2b134"],
      tooltip: {
        trigger: "axis",
        axisPointer: { type: "cross", crossStyle: { color: "#94a3b8" } },
        backgroundColor: "rgba(15, 23, 42, 0.92)",
        borderWidth: 0,
        textStyle: { color: "#f8fafc" },
        formatter: (params) => {
          const list = Array.isArray(params) ? params : [params];
          const title = String((list[0] as { axisValueLabel?: string })?.axisValueLabel ?? "");
          const rows = list
            .map((p) => {
              const item = p as { marker?: string; seriesName?: string; value?: number | string };
              return `${item.marker ?? ""} ${item.seriesName}: <strong>${item.value}%</strong>`;
            })
            .join("<br/>");
          return `<div style="margin-bottom:4px"><strong>${title}</strong></div>${rows}<div style="margin-top:6px;opacity:.75;font-size:11px">Click to open project</div>`;
        },
      },
      legend: {
        data: ["Progress %", "Evidence completeness %"],
        bottom: 0,
        selectedMode: "multiple",
      },
      grid: { left: 48, right: 24, top: 36, bottom: activeProjects.length > 4 ? 88 : 72 },
      dataZoom:
        activeProjects.length > 4
          ? [
              { type: "inside", xAxisIndex: 0, filterMode: "none" },
              { type: "slider", height: 18, bottom: 36, brushSelect: false },
            ]
          : [{ type: "inside", xAxisIndex: 0, filterMode: "none" }],
      xAxis: {
        type: "category",
        data: activeProjects.map((p) => p.name),
        axisLabel: { rotate: activeProjects.length > 3 ? 18 : 0, interval: 10 },
        axisTick: { alignWithLabel: true },
      },
      yAxis: {
        type: "value",
        max: 100,
        axisLabel: { formatter: "{value}%" },
        splitLine: { lineStyle: { type: "dashed", opacity: 0.45 } },
      },
      series: [
        {
          name: "Progress %",
          type: "bar",
          barMaxWidth: 36,
          data: activeProjects.map((p) => ({
            value: p.progressPercent,
            projectId: p.id,
          })),
          emphasis: {
            focus: "series",
            itemStyle: { shadowBlur: 8, shadowColor: "rgba(14, 76, 146, 0.35)" },
          },
        },
        {
          name: "Evidence completeness %",
          type: "line",
          smooth: true,
          symbol: "circle",
          symbolSize: 8,
          data: activeProjects.map((p) => ({
            value: p.evidenceCompleteness,
            projectId: p.id,
          })),
          emphasis: { focus: "series", scale: true },
        },
      ],
    }),
    [activeProjects],
  );

  const onEvents = useMemo(
    () => ({
      click: (params: { data?: { projectId?: string }; dataIndex?: number }) => {
        const id =
          params.data?.projectId ??
          (typeof params.dataIndex === "number"
            ? activeProjects[params.dataIndex]?.id
            : undefined);
        if (id) navigate(`/projects/${id}`);
      },
    }),
    [activeProjects, navigate],
  );

  return (
    <PageChrome route={route} title="Reports">
      <div className="acm-metric-strip">
        <CompactMetric label="Active projects" value={activeProjects.length} />
        <CompactMetric label="Avg. portfolio progress" value={`${avgProgress}%`} />
        <CompactMetric label="Approvals waiting" value={pulse.approvalsWaiting} />
        <CompactMetric label="Projects at risk" value={pulse.projectsAtRisk} />
      </div>

      <Surface level="content" className="p-5">
        <h2 className="text-lg">Progress vs. evidence completeness</h2>
        <p className="mt-1 text-sm text-text-secondary">
          Hover for values, scroll/drag to zoom, click a bar or point to open the project.
        </p>
        <div
          className="mt-4"
          role="img"
          aria-label="Interactive bar and line chart comparing project progress and evidence completeness"
        >
          <ReactECharts
            option={option}
            style={{ height: 320, width: "100%" }}
            opts={{ renderer: "canvas" }}
            onEvents={onEvents}
            notMerge
          />
        </div>
      </Surface>

      <Surface level="content" className="overflow-hidden">
        <div className="border-b border-[var(--border-subtle)] px-5 py-4">
          <h2>Portfolio detail (accessible table)</h2>
          <p className="mt-1 text-sm text-text-secondary">
            Same data as the chart above, in tabular form for assistive technology.
          </p>
        </div>
        <div className="acm-data-table-wrap">
          <table className="acm-data-table">
            <caption className="sr-only">Active project progress, evidence, and risk</caption>
            <thead>
              <tr>
                <th scope="col">Project</th>
                <th scope="col">Progress</th>
                <th scope="col">Evidence completeness</th>
                <th scope="col">Health</th>
                <th scope="col">Risk count</th>
              </tr>
            </thead>
            <tbody>
              {activeProjects.map((p) => (
                <tr key={p.id}>
                  <td className="acm-data-table__primary">{p.name}</td>
                  <td>{p.progressPercent}%</td>
                  <td>{p.evidenceCompleteness}%</td>
                  <td>{p.health.replace("_", " ")}</td>
                  <td>{p.riskCount}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Surface>
    </PageChrome>
  );
}
