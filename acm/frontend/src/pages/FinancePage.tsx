import { useMemo } from "react";
import ReactECharts from "echarts-for-react";
import type { EChartsOption } from "echarts";
import { PageChrome } from "../components/layout/PageChrome";
import { routeManifest } from "../routes/manifest";
import { useFixtureState } from "../data/hooks";
import { CompactMetric } from "../components/viz/CompactMetric";
import { ProgressRing } from "../components/viz/ProgressRing";
import { Sparkline } from "../components/viz/Sparkline";
import { Surface } from "../components/ui/Surface";
import { StatusBadge } from "../components/ui/StatusBadge";

const route = routeManifest.find((r) => r.id === "finance")!;

const MONTH_LABELS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

function currency(value: number) {
  return `$${value.toLocaleString()}`;
}

export function FinancePage() {
  const state = useFixtureState();
  const { finance } = state;

  const categoryOption = useMemo<EChartsOption>(
    () => ({
      textStyle: { fontFamily: "Source Sans 3, sans-serif" },
      color: ["#0e4c92", "#f2b134"],
      tooltip: {
        trigger: "axis",
        axisPointer: { type: "shadow" },
        backgroundColor: "rgba(15, 23, 42, 0.92)",
        borderWidth: 0,
        textStyle: { color: "#f8fafc" },
        formatter: (params) => {
          const list = Array.isArray(params) ? params : [params];
          const title = String((list[0] as { axisValueLabel?: string })?.axisValueLabel ?? "");
          const rows = list
            .map((p) => {
              const item = p as { marker?: string; seriesName?: string; value?: number | string };
              return `${item.marker ?? ""} ${item.seriesName}: <strong>${currency(Number(item.value ?? 0))}</strong>`;
            })
            .join("<br/>");
          return `<strong>${title}</strong><br/>${rows}`;
        },
      },
      legend: { data: ["Budget", "Actual"], bottom: 0 },
      grid: { left: 52, right: 16, top: 24, bottom: 48 },
      xAxis: {
        type: "category",
        data: finance.categories.map((c) => c.name),
        axisLabel: { interval: 0, rotate: finance.categories.length > 3 ? 16 : 0 },
      },
      yAxis: {
        type: "value",
        axisLabel: { formatter: (v: number) => `$${v}` },
        splitLine: { lineStyle: { type: "dashed", opacity: 0.45 } },
      },
      series: [
        {
          name: "Budget",
          type: "bar",
          barMaxWidth: 28,
          data: finance.categories.map((c) => c.budget),
          emphasis: { focus: "series" },
        },
        {
          name: "Actual",
          type: "bar",
          barMaxWidth: 28,
          data: finance.categories.map((c) => c.actual),
          emphasis: { focus: "series" },
        },
      ],
    }),
    [finance.categories],
  );

  const monthCats = finance.monthly.map((_, i) => MONTH_LABELS[i] ?? `M${i + 1}`);

  return (
    <PageChrome route={route} title="Finance">
      <div className="acm-metric-strip">
        <CompactMetric
          label="Chapter budget"
          value={currency(finance.budget)}
          hint="Academic year (fixture)"
        />
        <CompactMetric label="Actual spend" value={currency(finance.actual)} deltaTone="down" />
        <CompactMetric label="Remaining" value={currency(finance.remaining)} deltaTone="up" />
        <CompactMetric
          label="Pending approvals"
          value={finance.pendingApprovals}
          hint={`${finance.missingReceipts} missing receipt(s)`}
        />
      </div>

      <div className="home-grid">
        <Surface level="content" className="p-5">
          <h2 className="text-lg">Category variance</h2>
          <p className="mt-1 text-sm text-text-secondary">
            Hover bars for budget vs. actual. Toggle series in the legend.
          </p>
          <div className="mt-3" role="img" aria-label="Interactive budget versus actual by category">
            <ReactECharts
              option={categoryOption}
              style={{ height: 280, width: "100%" }}
              opts={{ renderer: "canvas" }}
              notMerge
            />
          </div>
        </Surface>

        <div className="space-y-4">
          <Surface level="content" className="p-5">
            <h2 className="text-lg">Monthly trend</h2>
            <p className="mt-1 text-sm text-text-secondary">Hover the line for each month’s spend.</p>
            <div className="mt-3 flex items-center gap-4">
              <Sparkline
                values={finance.monthly}
                label="Monthly spend"
                width={220}
                height={72}
                categories={monthCats}
                formatValue={currency}
              />
              <p className="text-sm text-text-secondary">
                Latest month {currency(finance.monthly.at(-1) ?? 0)} (fixture).
              </p>
            </div>
          </Surface>
          <Surface level="content" className="flex items-center gap-4 p-5">
            <ProgressRing value={finance.reconciledPercent} label="Reconciled" />
            <div className="text-sm text-text-secondary">
              <p>Reimbursement age: {finance.reimbursementAgeDays} days average.</p>
              <p className="mt-1">Missing receipts: {finance.missingReceipts}</p>
            </div>
          </Surface>
        </div>
      </div>

      <Surface level="content" className="p-5">
        <h2 className="text-lg">Funding sources</h2>
        <ul className="mt-3 space-y-2">
          {finance.fundingSources.map((s) => (
            <li key={s.name} className="flex items-center justify-between text-sm">
              <span className="text-text-secondary">{s.name}</span>
              <span className="font-semibold text-text-primary">{currency(s.amount)}</span>
            </li>
          ))}
        </ul>
        {finance.missingReceipts > 0 ? (
          <div className="status-callout status-callout--warning mt-4 flex items-center gap-2" role="note">
            <StatusBadge label="Action needed" tone="warning" />
            <span>{finance.missingReceipts} reimbursement(s) missing receipts.</span>
          </div>
        ) : null}
      </Surface>
    </PageChrome>
  );
}
