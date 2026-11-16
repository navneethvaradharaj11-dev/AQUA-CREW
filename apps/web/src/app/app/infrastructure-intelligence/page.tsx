import React from "react";
import { AppShell } from "@/components/layout/AppShell";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Infrastructure Intelligence & Geospatial Risk Prediction — AQUA CREW",
  description:
    "Autonomous multi-factor vulnerability scoring, DBSCAN spatial incident clustering, temporal deterioration velocity, and intelligent rover inspection queues",
};

export default function InfrastructureIntelligencePage() {
  return <AppShell initialNav="infrastructure-intelligence" />;
}

