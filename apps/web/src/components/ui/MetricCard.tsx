import React from "react";
import { cn } from "@/lib/utils";
import { LucideIcon, TrendingUp, TrendingDown, Minus } from "lucide-react";

export interface MetricCardProps extends React.HTMLAttributes<HTMLDivElement> {
  label: string;
  value: string | number;
  unit?: string;
  icon?: LucideIcon;
  change?: {
    value: string | number;
    direction: "up" | "down" | "neutral";
    label?: string;
  };
  tone?: "cyan" | "emerald" | "amber" | "rose" | "slate";
  progress?: number; // 0 to 100
}

export function MetricCard({
  label,
  value,
  unit,
  icon: Icon,
  change,
  tone = "cyan",
  progress,
  className,
  ...props
}: MetricCardProps) {
  const toneClasses = {
    cyan: {
      iconBg: "bg-cyan-950/40 text-cyan-400 border-cyan-800/50",
      progress: "bg-cyan-400",
      borderHover: "hover:border-cyan-500/40",
    },
    emerald: {
      iconBg: "bg-emerald-950/40 text-emerald-400 border-emerald-800/50",
      progress: "bg-emerald-400",
      borderHover: "hover:border-emerald-500/40",
    },
    amber: {
      iconBg: "bg-amber-950/40 text-amber-400 border-amber-800/50",
      progress: "bg-amber-400",
      borderHover: "hover:border-amber-500/40",
    },
    rose: {
      iconBg: "bg-rose-950/40 text-rose-400 border-rose-800/50",
      progress: "bg-rose-400",
      borderHover: "hover:border-rose-500/40",
    },
    slate: {
      iconBg: "bg-slate-800/60 text-slate-300 border-slate-700/60",
      progress: "bg-slate-400",
      borderHover: "hover:border-slate-600",
    },
  }[tone];

  return (
    <div
      className={cn(
        "group rounded-xl border border-slate-800 bg-slate-900/40 p-5 backdrop-blur-sm transition-all duration-200 hover:bg-slate-900/70",
        toneClasses.borderHover,
        className
      )}
      {...props}
    >
      <div className="flex items-center justify-between">
        <span className="text-xs font-mono uppercase tracking-wider text-slate-400">
          {label}
        </span>
        {Icon && (
          <div className={cn("rounded-lg border p-2 transition-colors", toneClasses.iconBg)}>
            <Icon className="h-4 w-4" />
          </div>
        )}
      </div>

      <div className="mt-3 flex items-baseline gap-1.5">
        <span className="text-2xl sm:text-3xl font-bold font-mono tracking-tight text-white">
          {value}
        </span>
        {unit && <span className="text-xs text-slate-400 font-mono">{unit}</span>}
      </div>

      {(change || progress !== undefined) && (
        <div className="mt-3 space-y-2 pt-2 border-t border-slate-800/60">
          {change && (
            <div className="flex items-center gap-1.5 text-xs">
              {change.direction === "up" && (
                <TrendingUp className="h-3.5 w-3.5 text-emerald-400" />
              )}
              {change.direction === "down" && (
                <TrendingDown className="h-3.5 w-3.5 text-rose-400" />
              )}
              {change.direction === "neutral" && (
                <Minus className="h-3.5 w-3.5 text-slate-400" />
              )}
              <span
                className={cn(
                  "font-medium font-mono text-[11px]",
                  change.direction === "up" && "text-emerald-400",
                  change.direction === "down" && "text-rose-400",
                  change.direction === "neutral" && "text-slate-400"
                )}
              >
                {change.value}
              </span>
              {change.label && (
                <span className="text-slate-500 text-[11px] truncate">
                  {change.label}
                </span>
              )}
            </div>
          )}

          {progress !== undefined && (
            <div className="h-1.5 w-full overflow-hidden rounded-full bg-slate-800">
              <div
                className={cn("h-full rounded-full transition-all duration-500", toneClasses.progress)}
                style={{ width: `${Math.min(100, Math.max(0, progress))}%` }}
              />
            </div>
          )}
        </div>
      )}
    </div>
  );
}

