"use client";

import React, { useState } from "react";
import { SimulatedAlert, AlertSeverity } from "@/services/simulation/types";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/Card";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { Button } from "@/components/ui/Button";
import { Tabs, TabList, TabTrigger, TabContent } from "@/components/ui/Tabs";
import { ShieldAlert, AlertTriangle, Info, Check, CheckCheck } from "lucide-react";

export interface AlertCenterSectionProps {
  alerts: SimulatedAlert[];
  onAcknowledgeAlert: (id: string) => void;
}

export function AlertCenterSection({ alerts, onAcknowledgeAlert }: AlertCenterSectionProps) {
  const [activeSeverityTab, setActiveSeverityTab] = useState<string>("all");

  const filteredAlerts = alerts.filter((a) => {
    if (activeSeverityTab === "all") return true;
    return a.severity === activeSeverityTab;
  });

  const getAlertIcon = (sev: AlertSeverity) => {
    switch (sev) {
      case "critical":
        return <ShieldAlert className="h-4 w-4 text-rose-400 shrink-0" />;
      case "warning":
        return <AlertTriangle className="h-4 w-4 text-amber-400 shrink-0" />;
      case "informational":
      default:
        return <Info className="h-4 w-4 text-cyan-400 shrink-0" />;
    }
  };

  const getAlertBorder = (sev: AlertSeverity) => {
    switch (sev) {
      case "critical":
        return "border-rose-900/50 bg-rose-950/20";
      case "warning":
        return "border-amber-900/50 bg-amber-950/20";
      case "informational":
      default:
        return "border-cyan-900/50 bg-cyan-950/20";
    }
  };

  const criticalCount = alerts.filter((a) => a.severity === "critical").length;
  const warningCount = alerts.filter((a) => a.severity === "warning").length;
  const infoCount = alerts.filter((a) => a.severity === "informational").length;

  return (
    <Card variant="default">
      <CardHeader>
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
          <div>
            <div className="flex items-center gap-2">
              <ShieldAlert className="h-5 w-5 text-rose-400" />
              <CardTitle>Centralized Alert & Safety Dispatch</CardTitle>
              <span className="rounded bg-slate-800 px-2 py-0.5 text-[10px] font-mono text-cyan-400 border border-slate-700">
                [SIMULATED DISPATCH]
              </span>
            </div>
            <CardDescription>
              Real-time anomaly alerts, failsafe triggers, and maintenance threshold notifications.
            </CardDescription>
          </div>

          <div className="flex items-center gap-2">
            <span className="rounded bg-rose-950 border border-rose-800/60 px-2 py-0.5 text-[11px] font-mono font-bold text-rose-400">
              {criticalCount} Critical
            </span>
            <span className="rounded bg-amber-950 border border-amber-800/60 px-2 py-0.5 text-[11px] font-mono font-bold text-amber-400">
              {warningCount} Warning
            </span>
          </div>
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Severity Tabs */}
        <div className="flex items-center justify-between flex-wrap gap-2">
          <div className="inline-flex h-9 items-center rounded-lg border border-slate-800 bg-slate-900/60 p-1 text-slate-400">
            <button
              onClick={() => setActiveSeverityTab("all")}
              className={`rounded-md px-3 py-1 text-xs font-mono transition-colors ${
                activeSeverityTab === "all" ? "bg-slate-800 text-cyan-300 font-bold" : "hover:text-white"
              }`}
            >
              All ({alerts.length})
            </button>
            <button
              onClick={() => setActiveSeverityTab("critical")}
              className={`rounded-md px-3 py-1 text-xs font-mono transition-colors ${
                activeSeverityTab === "critical" ? "bg-rose-950 text-rose-300 font-bold" : "hover:text-white"
              }`}
            >
              Critical ({criticalCount})
            </button>
            <button
              onClick={() => setActiveSeverityTab("warning")}
              className={`rounded-md px-3 py-1 text-xs font-mono transition-colors ${
                activeSeverityTab === "warning" ? "bg-amber-950 text-amber-300 font-bold" : "hover:text-white"
              }`}
            >
              Warning ({warningCount})
            </button>
            <button
              onClick={() => setActiveSeverityTab("informational")}
              className={`rounded-md px-3 py-1 text-xs font-mono transition-colors ${
                activeSeverityTab === "informational" ? "bg-cyan-950 text-cyan-300 font-bold" : "hover:text-white"
              }`}
            >
              Info ({infoCount})
            </button>
          </div>
        </div>

        {/* Alerts List */}
        <div className="space-y-2.5 max-h-96 overflow-y-auto">
          {filteredAlerts.length === 0 ? (
            <div className="py-8 text-center text-xs text-slate-500 font-mono">
              No simulated alerts in this category.
            </div>
          ) : (
            filteredAlerts.map((alert) => (
              <div
                key={alert.id}
                className={`flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 rounded-xl border p-3.5 transition-colors ${getAlertBorder(
                  alert.severity
                )}`}
              >
                <div className="flex items-start gap-3">
                  <div className="mt-0.5">{getAlertIcon(alert.severity)}</div>
                  <div className="space-y-0.5">
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-xs font-bold text-white">{alert.title}</span>
                      <span className="text-[10px] font-mono text-slate-500 uppercase">{alert.id}</span>
                      {alert.incidentRef && (
                        <span className="rounded bg-slate-800 px-1.5 py-0.2 text-[10px] font-mono text-cyan-400">
                          Ref: {alert.incidentRef}
                        </span>
                      )}
                      {alert.roverRef && (
                        <span className="rounded bg-slate-800 px-1.5 py-0.2 text-[10px] font-mono text-cyan-400">
                          Rover: {alert.roverRef}
                        </span>
                      )}
                    </div>
                    <p className="text-xs text-slate-300 leading-relaxed">{alert.message}</p>
                  </div>
                </div>

                <div className="flex items-center justify-between sm:justify-end gap-3 shrink-0 pt-2 sm:pt-0 border-t sm:border-t-0 border-slate-800/60">
                  <span className="text-[10px] font-mono text-slate-400">{alert.timestamp}</span>
                  {alert.acknowledged ? (
                    <span className="flex items-center gap-1 font-mono text-[10px] text-emerald-400">
                      <CheckCheck className="h-3.5 w-3.5" /> ACKNOWLEDGED
                    </span>
                  ) : (
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => onAcknowledgeAlert(alert.id)}
                      leftIcon={<Check className="h-3 w-3" />}
                    >
                      Acknowledge
                    </Button>
                  )}
                </div>
              </div>
            ))
          )}
        </div>
      </CardContent>
    </Card>
  );
}

