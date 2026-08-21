import { useCallback, useId, useMemo, useState, type MouseEvent } from "react";

interface SparklineProps {
  values: number[];
  label: string;
  width?: number;
  height?: number;
  /** Optional x-axis labels shown in the hover tooltip */
  categories?: string[];
  formatValue?: (value: number) => string;
}

const defaultFormatValue = (value: number) => String(value);

type Point = { x: number; y: number; value: number; index: number };

/**
 * Interactive sparkline — hover for value tooltips + active point.
 * SVG (not canvas) so dense tables stay light and tests stay stable.
 */
export function Sparkline({
  values,
  label,
  width = 96,
  height = 28,
  categories,
  formatValue = defaultFormatValue,
}: SparklineProps) {
  const tipId = useId();
  const [active, setActive] = useState<number | null>(null);

  const geometry = useMemo(() => {
    if (!values.length) return null;
    const min = Math.min(...values);
    const max = Math.max(...values);
    const span = max - min || 1;
    const padY = 3;
    const points: Point[] = values.map((value, index) => {
      const x = (index / Math.max(values.length - 1, 1)) * width;
      const y = height - ((value - min) / span) * (height - padY * 2) - padY;
      return { x, y, value, index };
    });
    const polyline = points.map((p) => `${p.x},${p.y}`).join(" ");
    const area = `0,${height} ${polyline} ${width},${height}`;
    return { points, polyline, area };
  }, [values, width, height]);

  const categoryAt = useCallback(
    (index: number) => {
      if (categories && categories[index]) return categories[index]!;
      return `Point ${index + 1}`;
    },
    [categories],
  );

  const onMove = useCallback(
    (event: MouseEvent<SVGSVGElement>) => {
      if (!geometry) return;
      const rect = event.currentTarget.getBoundingClientRect();
      const x = ((event.clientX - rect.left) / rect.width) * width;
      let nearest = 0;
      let best = Infinity;
      for (const p of geometry.points) {
        const d = Math.abs(p.x - x);
        if (d < best) {
          best = d;
          nearest = p.index;
        }
      }
      setActive(nearest);
    },
    [geometry, width],
  );

  if (!geometry) {
    return (
      <span className="text-xs text-text-muted" aria-label={`${label}: no data`}>
        —
      </span>
    );
  }

  const activePoint = active !== null ? geometry.points[active] : null;
  const summary = `${label}: ${formatValue(values[0]!)} to ${formatValue(values[values.length - 1]!)}`;

  return (
    <div className="acm-sparkline" style={{ width, height }} title="Hover for values">
      <svg
        width={width}
        height={height}
        viewBox={`0 0 ${width} ${height}`}
        role="img"
        aria-label={summary}
        aria-describedby={activePoint ? tipId : undefined}
        onMouseMove={onMove}
        onMouseLeave={() => setActive(null)}
      >
        <polygon points={geometry.area} fill="rgba(14, 76, 146, 0.12)" />
        <polyline
          fill="none"
          stroke="var(--brand-700, #0e4c92)"
          strokeWidth="1.75"
          strokeLinejoin="round"
          strokeLinecap="round"
          points={geometry.polyline}
        />
        {activePoint ? (
          <>
            <line
              x1={activePoint.x}
              y1={0}
              x2={activePoint.x}
              y2={height}
              stroke="var(--brand-700, #0e4c92)"
              strokeOpacity="0.35"
              strokeWidth="1"
              strokeDasharray="2 2"
            />
            <circle
              cx={activePoint.x}
              cy={activePoint.y}
              r="3.5"
              fill="#f2b134"
              stroke="var(--brand-700, #0e4c92)"
              strokeWidth="1.5"
            />
          </>
        ) : null}
        {/* Invisible hit targets for keyboard/pointer precision */}
        {geometry.points.map((p) => (
          <circle
            key={p.index}
            cx={p.x}
            cy={p.y}
            r="7"
            fill="transparent"
            onMouseEnter={() => setActive(p.index)}
            style={{ cursor: "crosshair" }}
          >
            <title>
              {categoryAt(p.index)}: {formatValue(p.value)}
            </title>
          </circle>
        ))}
      </svg>
      {activePoint ? (
        <div id={tipId} className="acm-sparkline__tip" role="tooltip">
          <span className="acm-sparkline__tip-cat">{categoryAt(activePoint.index)}</span>
          <span className="acm-sparkline__tip-val">
            {label}: {formatValue(activePoint.value)}
          </span>
        </div>
      ) : null}
    </div>
  );
}
