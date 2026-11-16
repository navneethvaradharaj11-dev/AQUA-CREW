import React from "react";
import { AppShell } from "@/components/layout/AppShell";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Network Optimization & Hydraulic Decision Engine — AQUA CREW",
  description:
    "Intelligent water distribution network optimization, Pareto frontier trade-off analysis, pump scheduling, and PRV setpoint modulation with independent EPANET/WNTR hydraulic verification.",
};

export default function OptimizationPage() {
  return <AppShell initialNav="optimization" />;
}

