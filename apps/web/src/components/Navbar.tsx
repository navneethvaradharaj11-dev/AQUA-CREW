import React from "react";
import { Droplets, ShieldCheck, Cpu } from "lucide-react";

export function Navbar() {
  return (
    <header className="sticky top-0 z-50 w-full border-b border-slate-800/80 bg-slate-950/80 backdrop-blur-md">
      <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-cyan-500/10 border border-cyan-500/30 text-cyan-400">
            <Droplets className="h-6 w-6" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-bold tracking-wider text-white text-lg">AQUA CREW</span>
              <span className="rounded-full bg-cyan-950 px-2 py-0.5 text-[11px] font-semibold text-cyan-400 border border-cyan-800/50">
                v0.1.0
              </span>
            </div>
            <p className="text-xs text-slate-400 hidden sm:block">
              Metropolitan Water Leakage Detection & Fleet Management
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 rounded-full border border-emerald-900/60 bg-emerald-950/40 px-3 py-1 text-xs text-emerald-400">
            <span className="relative flex h-2 w-2">
              <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-75"></span>
              <span className="relative inline-flex h-2 w-2 rounded-full bg-emerald-500"></span>
            </span>
            <span className="font-medium">Phase 01: Initialized</span>
          </div>

          <div className="hidden md:flex items-center gap-1.5 rounded-lg border border-slate-800 bg-slate-900/60 px-3 py-1 text-xs text-slate-300">
            <Cpu className="h-3.5 w-3.5 text-cyan-400" />
            <span>Software-First Architecture</span>
          </div>
        </div>
      </div>
    </header>
  );
}

