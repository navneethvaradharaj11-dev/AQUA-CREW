import React from "react";
import { AppShell } from "@/components/layout/AppShell";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Virtual Rover Fleet — AQUA CREW",
  description: "Virtual Autonomous Rover Fleet Management & Telemetry Simulation Engine",
};

export default function FleetPage() {
  return <AppShell initialNav="rover-fleet" />;
}

