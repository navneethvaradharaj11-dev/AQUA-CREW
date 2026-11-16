import React from "react";
import { AnalyticsTrends } from "@/services/simulation/types";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/Card";
import { BarChart3, TrendingDown, PieChart, Activity } from "lucide-react";

export interface AnalyticsSectionProps {
  analytics: AnalyticsTrends;
}

export function AnalyticsSection({ analytics }: AnalyticsSectionProps) {
  // Compute max values for SVG scaling
  const maxLoss = Math.max(...analytics.waterLossHourly.map((d) => Math.max(d.lossLph, d.preventedLossLph)), 2500);
  const maxSectorCount = Math.max(...analytics.leakFrequencyBySector.map((d) => d.count), 10);

  // SVG dimensions for Water Loss Chart
  const svgWidth = 500;
  const svgHeight = 160;
  const paddingX = 40;
  const paddingY = 25;

  const pointsLoss = analytics.waterLossHourly.map((d, i) => {
    const x = paddingX + (i / (analytics.waterLossHourly.length - 1)) * (svgWidth - 2 * paddingX);
    const y = svgHeight - paddingY - (d.lossLph / maxLoss) * (svgHeight - 2 * paddingY);
    return `${x},${y}`;
  }).join(" ");

  const pointsPrevented = analytics.waterLossHourly.map((d, i) => {
    const x = paddingX + (i / (analytics.waterLossHourly.length - 1)) * (svgWidth - 2 * paddingX);
    const y = svgHeight - paddingY - (d.preventedLossLph / maxLoss) * (svgHeight - 2 * paddingY);
    return `${x},${y}`;
  }).join(" ");

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between border-b border-slate-800 pb-2">
        <div className="flex items-center gap-2">
          <BarChart3 className="h-5 w-5 text-cyan-400" />
          <h2 className="text-lg font-bold tracking-tight text-white">System Analytics & Telemetry Trends</h2>
          <span className="rounded bg-slate-800 px-2 py-0.5 text-[10px] font-mono text-cyan-400 border border-slate-700">
            [SIMULATED METRICS]
          </span>
        </div>
        <span className="text-xs font-mono text-slate-400">24-Hour Rolling Window</span>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Chart 1: Water Loss vs Mitigated Loss Trend (Area/Line Chart) */}
        <Card variant="default">
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="text-sm">Water Loss vs Mitigated Savings</CardTitle>
                <CardDescription>Litres per hour trend over the last 24h cycle</CardDescription>
              </div>
              <div className="flex items-center gap-3 text-[11px] font-mono">
                <span className="flex items-center gap-1.5 text-rose-400">
                  <span className="h-2 w-2 rounded-full bg-rose-500 inline-block" /> Active Loss
                </span>
                <span className="flex items-center gap-1.5 text-cyan-400">
                  <span className="h-2 w-2 rounded-full bg-cyan-400 inline-block" /> Mitigated
                </span>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <div className="w-full overflow-hidden">
              <svg viewBox={`0 0 ${svgWidth} ${svgHeight}`} className="w-full h-44">
                {/* Horizontal gridlines */}
                {[0.25, 0.5, 0.75].map((pct, idx) => {
                  const y = svgHeight - paddingY - pct * (svgHeight - 2 * paddingY);
                  return (
                    <line
                      key={idx}
                      x1={paddingX}
                      y1={y}
                      x2={svgWidth - paddingX}
                      y2={y}
                      stroke="rgba(100, 116, 139, 0.2)"
                      strokeDasharray="4 4"
                    />
                  );
                })}

                {/* Prevented Loss Line (Cyan) */}
                <polyline
                  fill="none"
                  stroke="#06b6d4"
                  strokeWidth="2.5"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  points={pointsPrevented}
                />

                {/* Active Loss Line (Rose) */}
                <polyline
                  fill="none"
                  stroke="#ef4444"
                  strokeWidth="2.5"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  points={pointsLoss}
                />

                {/* Data points & X-axis labels */}
                {analytics.waterLossHourly.map((d, i) => {
                  const x = paddingX + (i / (analytics.waterLossHourly.length - 1)) * (svgWidth - 2 * paddingX);
                  const yLoss = svgHeight - paddingY - (d.lossLph / maxLoss) * (svgHeight - 2 * paddingY);
                  const yPrevented = svgHeight - paddingY - (d.preventedLossLph / maxLoss) * (svgHeight - 2 * paddingY);
                  return (
                    <g key={i}>
                      <circle cx={x} cy={yLoss} r="3.5" fill="#ef4444" />
                      <circle cx={x} cy={yPrevented} r="3.5" fill="#06b6d4" />
                      <text
                        x={x}
                        y={svgHeight - 6}
                        fill="#94a3b8"
                        fontSize="10"
                        textAnchor="middle"
                        fontFamily="monospace"
                      >
                        {d.time}
                      </text>
                    </g>
                  );
                })}
              </svg>
            </div>
          </CardContent>
        </Card>

        {/* Chart 2: Leak Incidents by Sector (Bar Chart) */}
        <Card variant="default">
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="text-sm">Incident Distribution by Sector</CardTitle>
                <CardDescription>Simulated anomaly frequency across municipal zones</CardDescription>
              </div>
              <span className="font-mono text-xs text-cyan-400">Total: 18 Events</span>
            </div>
          </CardHeader>
          <CardContent className="space-y-3">
            {analytics.leakFrequencyBySector.map((sector) => {
              const widthPct = Math.round((sector.count / maxSectorCount) * 100);
              return (
                <div key={sector.sector} className="space-y-1">
                  <div className="flex items-center justify-between text-xs font-mono">
                    <span className="text-slate-300 font-medium">{sector.sector}</span>
                    <span className="text-slate-400">
                      <strong className="text-cyan-400">{sector.count}</strong> incidents ({sector.volumeLph} L/h)
                    </span>
                  </div>
                  <div className="h-2 w-full overflow-hidden rounded-full bg-slate-800">
                    <div
                      className="h-full rounded-full bg-gradient-to-r from-cyan-500 to-teal-400 transition-all duration-500"
                      style={{ width: `${widthPct}%` }}
                    />
                  </div>
                </div>
              );
            })}
          </CardContent>
        </Card>

        {/* Chart 3: Rover Fleet Operational Utilization */}
        <Card variant="default">
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="text-sm">Rover Fleet Utilization</CardTitle>
                <CardDescription>Time-weighted operational allocation</CardDescription>
              </div>
              <PieChart className="h-4 w-4 text-cyan-400" />
            </div>
          </CardHeader>
          <CardContent>
            {/* Multi-segment stacked progress bar */}
            <div className="h-3 w-full overflow-hidden rounded-full bg-slate-800 flex">
              {analytics.roverUtilization.map((u) => (
                <div
                  key={u.category}
                  style={{ width: `${u.percentage}%`, backgroundColor: u.color }}
                  title={`${u.category}: ${u.percentage}%`}
                />
              ))}
            </div>

            <div className="grid grid-cols-2 gap-3 mt-4 pt-2">
              {analytics.roverUtilization.map((u) => (
                <div key={u.category} className="flex items-center justify-between text-xs font-mono">
                  <span className="flex items-center gap-1.5 text-slate-300">
                    <span className="h-2.5 w-2.5 rounded-sm shrink-0" style={{ backgroundColor: u.color }} />
                    <span className="truncate">{u.category}</span>
                  </span>
                  <span className="font-bold text-white">{u.percentage}%</span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Chart 4: Sensor Connectivity Uptime */}
        <Card variant="default">
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="text-sm">Sensor Network Availability</CardTitle>
                <CardDescription>SLA uptime across 5 diagnostic modalities</CardDescription>
              </div>
              <Activity className="h-4 w-4 text-emerald-400" />
            </div>
          </CardHeader>
          <CardContent className="space-y-3">
            {analytics.sensorConnectivity.map((sc) => (
              <div key={sc.category} className="flex items-center justify-between text-xs font-mono">
                <span className="text-slate-300">{sc.category} Stream</span>
                <div className="flex items-center gap-3">
                  <div className="w-28 h-1.5 rounded-full bg-slate-800 overflow-hidden hidden sm:block">
                    <div
                      className="h-full rounded-full bg-emerald-400"
                      style={{ width: `${sc.uptimePct}%` }}
                    />
                  </div>
                  <span className="text-emerald-400 font-bold w-12 text-right">
                    {sc.uptimePct.toFixed(1)}%
                  </span>
                </div>
              </div>
            ))}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

