"use client";

import React from "react";
import Link from "next/link";
import { useTheme } from "@/context/ThemeContext";
import {
  Droplets,
  Radio,
  Bot,
  Activity,
  Layers,
  Sparkles,
  ArrowRight,
  ShieldCheck,
  Cpu,
  BrainCircuit,
  Map,
  Compass,
  Sun,
  Moon,
  ExternalLink,
} from "lucide-react";
import { Button } from "@/components/ui/Button";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/Card";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { MetricCard } from "@/components/ui/MetricCard";
import { ApiHealthProbe } from "@/components/ApiHealthProbe";
import { ModuleGrid } from "@/components/ModuleGrid";

export default function WelcomePage() {
  const { theme, toggleTheme } = useTheme();

  return (
    <div className="relative flex min-h-dvh flex-col bg-background text-foreground bg-cyber-grid transition-colors duration-200">
      {/* Top Navbar */}
      <header className="sticky top-0 z-40 w-full border-b border-border bg-background/80 backdrop-blur-md">
        <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-cyan-500/10 border border-cyan-500/30 text-cyan-400 shadow-sm shadow-cyan-500/10">
              <Droplets className="h-6 w-6" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-extrabold tracking-wider text-base sm:text-lg">
                  AQUA CREW
                </span>
                <span className="rounded bg-cyan-950 px-2 py-0.5 text-[10px] font-mono font-semibold text-cyan-400 border border-cyan-800/50">
                  v0.1.0
                </span>
              </div>
              <p className="text-[11px] text-muted-foreground hidden sm:block">
                Autonomous Metropolitan Water Infrastructure Management
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2 sm:gap-3">
            <StatusBadge status="online" label="System Initialized" pulse size="sm" />

            <button
              onClick={toggleTheme}
              className="flex h-9 w-9 items-center justify-center rounded-lg border border-border bg-card text-muted-foreground hover:text-foreground transition-colors"
              aria-label={theme === "dark" ? "Switch to light mode" : "Switch to dark mode"}
            >
              {theme === "dark" ? (
                <Sun className="h-4 w-4 text-amber-300" />
              ) : (
                <Moon className="h-4 w-4 text-cyan-600" />
              )}
            </button>

            <Link href="/app">
              <Button
                variant="primary"
                size="sm"
                rightIcon={<ArrowRight className="h-3.5 w-3.5" />}
              >
                Launch Command Center
              </Button>
            </Link>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 px-4 py-8 sm:px-6 lg:px-8 max-w-7xl mx-auto w-full space-y-12">
        {/* Hero Section */}
        <section className="relative overflow-hidden rounded-2xl border border-cyan-500/30 bg-gradient-to-b from-card via-card/70 to-card/40 p-6 sm:p-12 backdrop-blur-xl">
          <div className="absolute top-0 right-0 -mt-12 -mr-12 h-96 w-96 rounded-full bg-cyan-500/10 blur-3xl pointer-events-none" />
          <div className="absolute bottom-0 left-1/4 -mb-12 h-64 w-64 rounded-full bg-teal-500/10 blur-3xl pointer-events-none" />

          <div className="relative z-10 max-w-3xl space-y-6">
            <div className="inline-flex items-center gap-2 rounded-full border border-cyan-500/30 bg-cyan-950/40 px-3 py-1 text-xs font-semibold text-cyan-300">
              <Sparkles className="h-3.5 w-3.5 text-cyan-400" />
              <span>Production Design System & Visual Identity — Task 02</span>
            </div>

            <div className="space-y-2">
              <h1 className="text-3xl font-black tracking-tight sm:text-6xl text-gradient-aqua">
                AQUA CREW
              </h1>
              <p className="text-lg sm:text-xl font-light text-slate-300">
                Autonomous Water Leakage Detection, Localization & Repair Management Platform.
              </p>
            </div>

            <p className="text-sm sm:text-base text-muted-foreground leading-relaxed">
              Designed for metropolitan water distribution utilities. AQUA CREW unifies autonomous
              ground rovers, in-pipe inspection crawlers, acoustic IoT sensor networks, and AI
              anomaly engines into an integrated, real-time command center.
            </p>

            <div className="flex flex-wrap items-center gap-3 pt-2">
              <Link href="/app">
                <Button
                  variant="primary"
                  size="lg"
                  rightIcon={<ArrowRight className="h-4 w-4" />}
                >
                  Enter Command Center Shell
                </Button>
              </Link>
              <Link href="/docs/ARCHITECTURE.md" target="_blank">
                <Button
                  variant="outline"
                  size="lg"
                  rightIcon={<ExternalLink className="h-4 w-4" />}
                >
                  Architecture Docs
                </Button>
              </Link>
            </div>

            <div className="flex flex-wrap items-center gap-3 pt-4 text-xs text-muted-foreground border-t border-border">
              <span className="flex items-center gap-1.5 font-medium">
                <ShieldCheck className="h-4 w-4 text-emerald-400" />
                Strict Software-First Engineering
              </span>
              <span className="flex items-center gap-1.5 font-medium">
                <Radio className="h-4 w-4 text-cyan-400" />
                Hardware Abstraction Layer (HAL)
              </span>
              <span className="flex items-center gap-1.5 font-medium">
                <Cpu className="h-4 w-4 text-teal-400" />
                Multi-Sensor Fusion Architecture
              </span>
            </div>
          </div>
        </section>

        {/* Foundation Metric Cards */}
        <section className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <MetricCard
            label="Visual Identity"
            value="ROBOTICS"
            unit="AQUA & NAVY"
            icon={Bot}
            change={{ value: "Industrial", direction: "up", label: "Cyber-Physical" }}
            tone="cyan"
            progress={100}
          />
          <MetricCard
            label="Design Tokens"
            value="15+"
            unit="COMPONENTS"
            icon={Layers}
            change={{ value: "Dark & Light", direction: "up", label: "Dual Theme" }}
            tone="emerald"
            progress={100}
          />
          <MetricCard
            label="Application Shell"
            value="11"
            unit="NAVIGATION DESTINATIONS"
            icon={Compass}
            change={{ value: "Collapsible", direction: "neutral", label: "Responsive Nav" }}
            tone="cyan"
            progress={100}
          />
          <MetricCard
            label="API Gateway"
            value="REST & WS"
            unit="FASTAPI V1"
            icon={Activity}
            change={{ value: "Verified", direction: "up", label: "Health Live" }}
            tone="emerald"
            progress={100}
          />
        </section>

        {/* Technology Highlights */}
        <section className="space-y-4">
          <div className="border-b border-border pb-3">
            <h2 className="text-xl font-bold tracking-tight">Technology Highlights</h2>
            <p className="text-xs text-muted-foreground">
              Core platform pillars engineered for zero-rewrite physical hardware transition.
            </p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            <Card variant="interactive">
              <CardHeader>
                <div className="flex items-center gap-2.5 text-cyan-400 mb-1">
                  <Bot className="h-5 w-5" />
                  <span className="font-mono text-xs uppercase tracking-wide">Fleet Systems</span>
                </div>
                <CardTitle>Autonomous Ground & Pipe Rovers</CardTitle>
                <CardDescription>
                  Crawler units equipped with acoustic hydrophones, ground-penetrating radar, and sub-meter positioning.
                </CardDescription>
              </CardHeader>
            </Card>

            <Card variant="interactive">
              <CardHeader>
                <div className="flex items-center gap-2.5 text-teal-400 mb-1">
                  <BrainCircuit className="h-5 w-5" />
                  <span className="font-mono text-xs uppercase tracking-wide">Signal Intelligence</span>
                </div>
                <CardTitle>AI Acoustic Anomaly Engine</CardTitle>
                <CardDescription>
                  Continuous FFT wavelet spectral analysis detecting subtle pipe wall friction and burst signatures.
                </CardDescription>
              </CardHeader>
            </Card>

            <Card variant="interactive">
              <CardHeader>
                <div className="flex items-center gap-2.5 text-cyan-400 mb-1">
                  <Map className="h-5 w-5" />
                  <span className="font-mono text-xs uppercase tracking-wide">Geospatial PostGIS</span>
                </div>
                <CardTitle>Metropolitan Pipeline GIS</CardTitle>
                <CardDescription>
                  Underground pipe geometry, pressure zones, isolation valves, and real-time hydraulic transient mapping.
                </CardDescription>
              </CardHeader>
            </Card>
          </div>
        </section>

        {/* Live Backend Connection Verification (Preserved from Task 01) */}
        <section className="space-y-3">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-lg font-semibold tracking-tight">
                Core Service Integration
              </h2>
              <p className="text-xs text-muted-foreground">
                Preserved real-time FastAPI health check integration and latency probe.
              </p>
            </div>
          </div>
          <ApiHealthProbe />
        </section>

        {/* Module Architecture Preview */}
        <section>
          <ModuleGrid />
        </section>
      </main>

      {/* Footer */}
      <footer className="border-t border-border bg-card/60 py-8 mt-12">
        <div className="mx-auto flex max-w-7xl flex-col items-center justify-between gap-4 px-4 sm:flex-row sm:px-6 lg:px-8 text-xs text-muted-foreground">
          <div className="flex items-center gap-2">
            <Droplets className="h-4 w-4 text-cyan-400" />
            <span className="font-bold text-foreground">AQUA CREW</span>
            <span>— Autonomous Municipal Leakage Platform</span>
          </div>
          <div className="flex items-center gap-6">
            <Link href="/app" className="hover:text-cyan-400 transition-colors">
              Command Center
            </Link>
            <Link href="/docs/ARCHITECTURE.md" target="_blank" className="hover:text-cyan-400 transition-colors">
              Architecture Docs
            </Link>
            <span>v0.1.0 • Task 02 Complete</span>
          </div>
        </div>
      </footer>
    </div>
  );
}
