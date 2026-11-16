"use client";

import React, { useState } from "react";
import { SimulatedLeakIncident, LeakSeverity, LeakIncidentStatus } from "@/services/simulation/types";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/Card";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { Button } from "@/components/ui/Button";
import { Droplets, Filter, ArrowUpRight, Search } from "lucide-react";

export interface LeakIncidentSectionProps {
  incidents: SimulatedLeakIncident[];
  onSelectIncident: (incident: SimulatedLeakIncident) => void;
}

export function LeakIncidentSection({ incidents, onSelectIncident }: LeakIncidentSectionProps) {
  const [severityFilter, setSeverityFilter] = useState<string>("All");
  const [statusFilter, setStatusFilter] = useState<string>("All");
  const [searchQuery, setSearchQuery] = useState("");

  const filtered = incidents.filter((item) => {
    if (severityFilter !== "All" && item.severity !== severityFilter) return false;
    if (statusFilter !== "All" && item.status !== statusFilter) return false;
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      return (
        item.id.toLowerCase().includes(q) ||
        item.pipelineSegmentId.toLowerCase().includes(q) ||
        item.segmentName.toLowerCase().includes(q) ||
        item.estimatedLocation.zone.toLowerCase().includes(q)
      );
    }
    return true;
  });

  const getSeverityBadge = (severity: LeakSeverity) => {
    switch (severity) {
      case "Critical":
        return <StatusBadge status="critical" label="Critical" pulse size="sm" />;
      case "High":
        return <StatusBadge status="warning" label="High" size="sm" />;
      case "Medium":
        return <StatusBadge status="active" label="Medium" size="sm" />;
      case "Low":
      default:
        return <StatusBadge status="standby" label="Low" size="sm" />;
    }
  };

  const getStatusVariant = (status: LeakIncidentStatus) => {
    switch (status) {
      case "Investigating":
        return "text-cyan-400 bg-cyan-950/60 border-cyan-800/60";
      case "Confirmed":
        return "text-rose-400 bg-rose-950/60 border-rose-800/60";
      case "Repaired":
        return "text-emerald-400 bg-emerald-950/60 border-emerald-800/60";
      case "Suspected":
      default:
        return "text-amber-400 bg-amber-950/60 border-amber-800/60";
    }
  };

  return (
    <Card variant="default">
      <CardHeader>
        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
          <div>
            <div className="flex items-center gap-2">
              <Droplets className="h-5 w-5 text-cyan-400" />
              <CardTitle>Leak Incident Overview</CardTitle>
              <span className="rounded bg-slate-800 px-2 py-0.5 text-[10px] font-mono text-cyan-400 border border-slate-700">
                [SIMULATED INCIDENTS]
              </span>
            </div>
            <CardDescription>
              Acoustic TDOA & pressure drop incidents identified across municipal segments.
            </CardDescription>
          </div>

          {/* Interactive Filters */}
          <div className="flex flex-wrap items-center gap-2 text-xs">
            {/* Search Input */}
            <div className="relative">
              <Search className="h-3.5 w-3.5 absolute left-2.5 top-2.5 text-slate-500" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search segment/ID..."
                className="h-8 pl-8 pr-3 rounded-lg border border-slate-800 bg-slate-900 text-xs text-slate-200 placeholder:text-slate-500 focus:outline-none focus:border-cyan-500"
              />
            </div>

            {/* Severity Filter */}
            <select
              value={severityFilter}
              onChange={(e) => setSeverityFilter(e.target.value)}
              className="h-8 rounded-lg border border-slate-800 bg-slate-900 px-2.5 text-xs text-slate-200 focus:outline-none focus:border-cyan-500 font-mono"
            >
              <option value="All">Severity: All</option>
              <option value="Critical">Critical</option>
              <option value="High">High</option>
              <option value="Medium">Medium</option>
              <option value="Low">Low</option>
            </select>

            {/* Status Filter */}
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="h-8 rounded-lg border border-slate-800 bg-slate-900 px-2.5 text-xs text-slate-200 focus:outline-none focus:border-cyan-500 font-mono"
            >
              <option value="All">Status: All</option>
              <option value="Suspected">Suspected</option>
              <option value="Investigating">Investigating</option>
              <option value="Confirmed">Confirmed</option>
              <option value="Repaired">Repaired</option>
            </select>
          </div>
        </div>
      </CardHeader>

      <CardContent>
        {filtered.length === 0 ? (
          <div className="py-8 text-center text-xs text-slate-500 font-mono">
            No simulated incidents match the selected filter criteria.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="border-b border-slate-800 text-[11px] font-mono uppercase text-slate-400">
                  <th className="py-2.5 px-3">Incident ID</th>
                  <th className="py-2.5 px-3">Pipeline Segment</th>
                  <th className="py-2.5 px-3">Severity</th>
                  <th className="py-2.5 px-3">Status</th>
                  <th className="py-2.5 px-3">Est. Location</th>
                  <th className="py-2.5 px-3">Est. Loss Rate</th>
                  <th className="py-2.5 px-3">Confidence</th>
                  <th className="py-2.5 px-3 text-right">Details</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 font-sans">
                {filtered.map((item) => (
                  <tr
                    key={item.id}
                    onClick={() => onSelectIncident(item)}
                    className="hover:bg-slate-900/80 cursor-pointer transition-colors group"
                  >
                    <td className="py-3 px-3 font-mono font-semibold text-cyan-400">
                      {item.id}
                    </td>
                    <td className="py-3 px-3">
                      <div className="font-medium text-slate-200">{item.segmentName}</div>
                      <div className="text-[10px] font-mono text-slate-500">{item.pipelineSegmentId}</div>
                    </td>
                    <td className="py-3 px-3">{getSeverityBadge(item.severity)}</td>
                    <td className="py-3 px-3">
                      <span
                        className={`inline-flex rounded-full border px-2 py-0.5 text-[10px] font-mono font-medium ${getStatusVariant(
                          item.status
                        )}`}
                      >
                        {item.status}
                      </span>
                    </td>
                    <td className="py-3 px-3">
                      <div className="text-slate-300 text-[11px]">{item.estimatedLocation?.zone || "Central Sector"}</div>
                      <div className="text-[10px] font-mono text-slate-500">
                        {item.estimatedLocation?.latitude != null ? item.estimatedLocation.latitude.toFixed(4) : "—"},{" "}
                        {item.estimatedLocation?.longitude != null ? item.estimatedLocation.longitude.toFixed(4) : "—"}
                      </div>
                    </td>
                    <td className="py-3 px-3 font-mono font-semibold text-white">
                      {item.estimatedLossRateLph} L/h
                    </td>
                    <td className="py-3 px-3 font-mono text-cyan-300">
                      {item.confidenceScorePct}%
                    </td>
                    <td className="py-3 px-3 text-right">
                      <span className="text-cyan-400 group-hover:text-cyan-300 group-hover:underline inline-flex items-center gap-1 font-mono text-[11px]">
                        Inspect <ArrowUpRight className="h-3 w-3" />
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

