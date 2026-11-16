import React from "react";
import { AppShell } from "@/components/layout/AppShell";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Operational AI Decision Assistant — AQUA CREW",
  description:
    "Evidence-grounded operational water infrastructure decision intelligence with strict ontological classification, multi-source reasoning, and non-fabricated explainability",
};

export default function AiAssistantPage() {
  return <AppShell initialNav="ai-assistant" />;
}

