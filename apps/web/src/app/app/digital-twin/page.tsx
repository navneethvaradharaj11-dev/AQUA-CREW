import React from "react";
import { AppShell } from "@/components/layout/AppShell";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Digital Twin & Hydraulic Water Network Simulation — AQUA CREW",
  description: "Virtual hydraulic digital twin simulation, extended-period diurnal demand, Torricelli orifice leaks, booster pumps, and What-If scenario analysis",
};

export default function DigitalTwinPage() {
  return <AppShell initialNav="digital-twin" />;
}

