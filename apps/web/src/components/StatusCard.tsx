import React from "react";
import { LucideIcon } from "lucide-react";
import { cn } from "@/lib/utils";

interface StatusCardProps {
  title: string;
  value: string;
  subtitle: string;
  icon: LucideIcon;
  badge?: string;
  tone?: "cyan" | "emerald" | "amber" | "slate";
}

export function StatusCard({
  title,
  value,
  subtitle,
  icon: Icon,
  badge,
  tone = "cyan",
}: StatusCardProps) {
  const toneClasses = {
    cyan: "border-cyan-900/40 bg-cyan-950/10 text-cyan-400 group-hover:border-cyan-700/60",
    emerald: "border-emerald-900/40 bg-emerald-950/10 text-emerald-400 group-hover:border-emerald-700/60",
    amber: "border-amber-900/40 bg-amber-950/10 text-amber-400 group-hover:border-amber-700/60",
    slate: "border-slate-800 bg-slate-900/30 text-slate-400 group-hover:border-slate-700",
  }[tone];

  return (
    <div className="group rounded-xl border border-slate-800 bg-slate-900/40 p-5 backdrop-blur-sm transition-all hover:bg-slate-900/70">
      <div className="flex items-center justify-between">
        <span className="text-xs font-medium uppercase tracking-wider text-slate-400">
          {title}
        </span>
        <div className={cn("rounded-lg p-2 transition-colors", toneClasses)}>
          <Icon className="h-5 w-5" />
        </div>
      </div>
      <div className="mt-3 flex items-baseline gap-2">
        <span className="text-2xl font-bold tracking-tight text-white">{value}</span>
        {badge && (
          <span className="rounded bg-slate-800 px-1.5 py-0.5 text-[10px] font-medium text-slate-300">
            {badge}
          </span>
        )}
      </div>
      <p className="mt-1 text-xs text-slate-400">{subtitle}</p>
    </div>
  );
}

