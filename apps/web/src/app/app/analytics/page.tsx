import React from "react";
import { AppShell } from "@/components/layout/AppShell";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Telemetry & Hydraulic Analytics — AQUA CREW",
  description: "Diurnal loss patterns, rover fleet productivity, and sensor reliability",
};

export default function AnalyticsPage() {
  return <AppShell initialNav="analytics" />;
}
