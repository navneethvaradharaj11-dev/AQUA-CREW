import React from "react";
import { AppShell } from "@/components/layout/AppShell";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Metropolitan Pipeline Map — AQUA CREW",
  description: "Interactive Geospatial Water Distribution Network & Rover Fleet Map",
};

export default function MapPage() {
  return <AppShell initialNav="city-map" />;
}

