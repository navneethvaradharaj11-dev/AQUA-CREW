import React from "react";
import { AppShell } from "@/components/layout/AppShell";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Autonomous Inspection Intelligence & Rover Orchestration — AQUA CREW",
  description:
    "Unified multi-subsystem inspection priority engine, connected Dijkstra routing, adaptive multi-rover coordination, and evidence-grounded reports.",
};

export default function InspectionIntelligencePage() {
  return <AppShell initialNav="inspection-intelligence" />;
}

