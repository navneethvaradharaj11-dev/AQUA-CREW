import React from "react";
import { AppShell } from "@/components/layout/AppShell";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Platform Settings & Safety Controls — AQUA CREW",
  description: "Hardware safety interlock, simulation tick rates, audio notifications, and role-based clearance",
};

export default function SettingsPage() {
  return <AppShell initialNav="settings" />;
}

