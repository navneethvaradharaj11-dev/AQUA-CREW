import React from "react";
import { AppShell } from "@/components/layout/AppShell";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Predictive Maintenance & Infrastructure Health — AQUA CREW",
  description: "AI-powered pipeline health assessment, failure probability forecasting across multi-horizons, and proactive inspection dispatch",
};

export default function MaintenancePage() {
  return <AppShell initialNav="maintenance" />;
}

