import React from "react";
import { cn } from "@/lib/utils";

export type StatusVariant =
  | "online"
  | "active"
  | "warning"
  | "critical"
  | "offline"
  | "standby";

export interface StatusBadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  status: StatusVariant;
  label?: string;
  pulse?: boolean;
  size?: "sm" | "md";
}

export function StatusBadge({
  status = "online",
  label,
  pulse = false,
  size = "md",
  className,
  ...props
}: StatusBadgeProps) {
  const statusConfig = {
    online: {
      bg: "bg-emerald-950/40 border-emerald-800/60 text-emerald-400",
      dot: "bg-emerald-400",
      ping: "bg-emerald-400",
      defaultLabel: "Online",
    },
    active: {
      bg: "bg-cyan-950/40 border-cyan-800/60 text-cyan-400",
      dot: "bg-cyan-400",
      ping: "bg-cyan-400",
      defaultLabel: "Active",
    },
    warning: {
      bg: "bg-amber-950/40 border-amber-800/60 text-amber-400",
      dot: "bg-amber-400",
      ping: "bg-amber-400",
      defaultLabel: "Warning",
    },
    critical: {
      bg: "bg-rose-950/40 border-rose-800/60 text-rose-400",
      dot: "bg-rose-400",
      ping: "bg-rose-400",
      defaultLabel: "Critical",
    },
    offline: {
      bg: "bg-slate-900 border-slate-700/80 text-slate-400",
      dot: "bg-slate-400",
      ping: "bg-slate-400",
      defaultLabel: "Offline",
    },
    standby: {
      bg: "bg-indigo-950/40 border-indigo-800/60 text-indigo-400",
      dot: "bg-indigo-400",
      ping: "bg-indigo-400",
      defaultLabel: "Standby",
    },
  }[status];

  const sizeStyles = {
    sm: "px-2 py-0.5 text-[11px] gap-1.5",
    md: "px-2.5 py-1 text-xs gap-2",
  }[size];

  const dotSizes = {
    sm: "h-1.5 w-1.5",
    md: "h-2 w-2",
  }[size];

  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full font-medium border select-none transition-colors",
        statusConfig.bg,
        sizeStyles,
        className
      )}
      {...props}
    >
      <span className={cn("relative flex shrink-0", dotSizes)}>
        {pulse && (
          <span
            className={cn(
              "absolute inline-flex h-full w-full animate-ping rounded-full opacity-75",
              statusConfig.ping
            )}
          />
        )}
        <span
          className={cn("relative inline-flex h-full w-full rounded-full", statusConfig.dot)}
        />
      </span>
      <span>{label || statusConfig.defaultLabel}</span>
    </span>
  );
}

