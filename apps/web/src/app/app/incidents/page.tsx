import React from "react";
import { AppShell } from "@/components/layout/AppShell";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Unified Incident Workspace — AQUA CREW",
  description:
    "Master end-to-end incident lifecycle workspace: IoT telemetry, AI leak detection, hydraulic digital twin, autonomous rover inspection, repair planning, and certified human approval.",
};

export default function IncidentsPage() {
  return <AppShell initialNav="incidents" />;
}

