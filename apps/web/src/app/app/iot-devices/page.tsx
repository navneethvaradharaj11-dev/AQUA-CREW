import React from "react";
import { AppShell } from "@/components/layout/AppShell";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "IoT & Hardware Gateway — AQUA CREW",
  description:
    "Secure device ecosystem, real-time sensor telemetry ingestion, ISO-compliant calibration audits, and air-gapped hardware safety gateway.",
};

export default function IotDevicesPage() {
  return <AppShell initialNav="iot-devices" />;
}

