import React from "react";
import { AppShell } from "@/components/layout/AppShell";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Autonomous Mission Planning & Rover Dispatch — AQUA CREW",
  description: "Autonomous topological mission planning, battery-constrained rover selection, and operator approval governance",
};

export default function DispatchPage() {
  return <AppShell initialNav="dispatch" />;
}

