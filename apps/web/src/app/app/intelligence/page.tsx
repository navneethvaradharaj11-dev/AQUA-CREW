import React from "react";
import { AppShell } from "@/components/layout/AppShell";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "AI Leak Detection & Acoustic Intelligence — AQUA CREW",
  description: "Explainable multi-modal AI leak detection, acoustic frequency decomposition, and risk prioritization",
};

export default function IntelligencePage() {
  return <AppShell initialNav="intelligence" />;
}

