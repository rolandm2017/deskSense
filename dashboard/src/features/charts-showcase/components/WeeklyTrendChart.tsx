import ChartSvg from "../../../components/charts/foundation/ChartSvg";
import {
  buildAreaPath,
  buildPolylinePath,
  scaleLinear,
} from "../../../components/charts/foundation/chartMath";
import { TrendPoint } from "../types";
import ShowcaseSection from "./ShowcaseSection";

interface WeeklyTrendChartProps {
  points: TrendPoint[];
  maxHours?: number;
}

function WeeklyTrendChart({
  points,
  maxHours = 40,
}: WeeklyTrendChartProps) {
  const width = 1000;
  const height = 120;
  const padding = { top: 12, bottom: 4 };

  const chartPoints = points.map((point, index) => ({
    x: scaleLinear(index, 0, points.length - 1, 0, width),
    y: scaleLinear(
      point.hours,
      0,
      maxHours,
      height - padding.bottom,
      padding.top
    ),
  }));

  return (
    <ShowcaseSection
      title="8-Week Trend - Productive Hours"
      delayMs={240}
      className="mb-12 mt-4"
    >
      <div className="relative h-[120px] border-b border-[var(--ds-rule)]">
        <ChartSvg viewBoxWidth={width} viewBoxHeight={height} className="h-full w-full">
          <defs>
            <linearGradient id="showcase-trend-gradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#C7F36B" stopOpacity="0.15" />
              <stop offset="100%" stopColor="#C7F36B" stopOpacity="0.01" />
            </linearGradient>
          </defs>
          <polygon
            points={buildAreaPath(chartPoints, height - padding.bottom)}
            fill="url(#showcase-trend-gradient)"
          />
          <polyline
            points={buildPolylinePath(chartPoints)}
            fill="none"
            stroke="#C7F36B"
            strokeWidth="2"
          />
          {chartPoints.map((point, index) => (
            <g key={points[index].label}>
              <circle cx={point.x} cy={point.y} r="3" fill="#C7F36B" />
              <text
                x={point.x}
                y={point.y - 10}
                textAnchor="middle"
                fill="#8A8478"
                fontFamily="IBM Plex Mono"
                fontSize="11"
              >
                {points[index].hours}h
              </text>
            </g>
          ))}
        </ChartSvg>
      </div>
      <div className="flex justify-between pt-2">
        {points.map((point) => (
          <span
            className="font-mono text-[10px] text-[var(--ds-text-muted)]"
            key={point.label}
          >
            {point.label}
          </span>
        ))}
      </div>
    </ShowcaseSection>
  );
}

export default WeeklyTrendChart;
