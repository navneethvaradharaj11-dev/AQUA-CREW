import React from "react";
import { AppShell } from "@/components/layout/AppShell";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Command Center — AQUA CREW",
  description: "Autonomous Water Leakage Detection & Fleet Command Shell",
};

export default function AppPage() {
  return <AppShell />;
}

