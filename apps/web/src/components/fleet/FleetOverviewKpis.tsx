"use client";

import React from "react";
import { SimulatedRover } from "@/services/simulation/types";
import { MetricCard } from "@/components/ui/MetricCard";

export interface FleetOverviewKpisProps {
  rovers: SimulatedRover[];
}

export function FleetOverviewKpis({ rovers }: FleetOverviewKpisProps) {
  const totalRovers = rovers.length;

  const activeCount = rovers.filter(
    (r) => r.operatingState === "MOVING" || r.operatingState === "INSPECTING" || r.operatingState === "RETURNING"
  ).length;

  const standbyCount = rovers.filter(
    (r) => r.operatingState === "IDLE" || r.operatingState === "CHARGING"
  ).length;

  const alertCount = rovers.filter(
    (r) => r.operatingState === "EMERGENCY_STOP" || r.operatingState === "ERROR" || r.status === "WARNING"
  ).length;

  const totalDistanceKm = rovers.reduce((acc, r) => acc + (r.distanceTravelledKm || 0), 0);

  const avgBattery = totalRovers > 0
    ? Math.round(rovers.reduce((acc, r) => acc + r.batteryPercentage, 0) / totalRovers)
    : 0;

  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3 sm:gap-4">
      <MetricCard
        label="Total Fleet Units"
        value={totalRovers}
        unit="ROVERS"
        tone="cyan"
      />
      <MetricCard
        label="Active Missions"
        value={activeCount}
        unit="DEPLOYED"
        tone="emerald"
      />
      <MetricCard
        label="Standby & Docked"
        value={standbyCount}
        unit="READY"
        tone="slate"
      />
      <MetricCard
        label="Critical Alerts / E-Stops"
        value={alertCount}
        unit="INTERLOCKS"
        tone={alertCount > 0 ? "rose" : "emerald"}
      />
      <MetricCard
        label="Inspected Distance"
        value={totalDistanceKm.toFixed(1)}
        unit="KM MONITORED"
        tone="cyan"
      />
      <MetricCard
        label="Average Battery SoC"
        value={`${avgBattery}%`}
        unit="FLEET CHARGE"
        tone={avgBattery < 30 ? "amber" : "emerald"}
      />
    </div>
  );
}

