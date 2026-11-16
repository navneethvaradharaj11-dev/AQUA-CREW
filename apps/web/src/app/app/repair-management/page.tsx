import React from "react";
import { AppShell } from "@/components/layout/AppShell";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Intelligent Repair Planning & Management — AQUA CREW",
  description:
    "Evidence-grounded damage assessments, multi-factor repair method ranking, resource and cost estimation, virtual crew dispatch, pre/post digital twin verification, and tamper-evident audit ledger.",
};

export default function RepairManagementPage() {
  return <AppShell initialNav="repair-management" />;
}

