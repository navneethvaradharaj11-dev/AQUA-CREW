import React from "react";
import { AppShell } from "@/components/layout/AppShell";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Engineering Reports & Regulatory Dossiers — AQUA CREW",
  description: "Publication-grade incident audit reports, hydraulic digital twin certificates, and work orders",
};

export default function ReportsPage() {
  return <AppShell initialNav="reports" />;
}

