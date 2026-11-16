import React from "react";
import { AppShell } from "@/components/layout/AppShell";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Unified Operational Intelligence & Decision Support — AQUA CREW",
  description:
    "Cross-system decision platform synthesizing AI leak detections, hydraulic digital twin, asset health indices, and autonomous rover resources",
};

export default function OperationalIntelligencePage() {
  return <AppShell initialNav="operational-intelligence" />;
}

