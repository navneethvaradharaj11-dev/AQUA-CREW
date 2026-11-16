import React from "react";
import { cn } from "@/lib/utils";
import { Loader2, Radio } from "lucide-react";

export interface LoadingStateProps extends React.HTMLAttributes<HTMLDivElement> {
  message?: string;
  subtext?: string;
  variant?: "spinner" | "sonar" | "skeleton";
}

export function LoadingState({
  message = "Acquiring Telemetry Data...",
  subtext = "Calibrating virtual sensor hydrophone streams",
  variant = "sonar",
  className,
  ...props
}: LoadingStateProps) {
  if (variant === "skeleton") {
    return (
      <div
        className={cn("w-full space-y-3 p-6 rounded-xl border border-slate-800 bg-slate-900/30 animate-pulse", className)}
        {...props}
      >
        <div className="h-4 w-1/3 rounded bg-slate-800" />
        <div className="h-8 w-1/2 rounded bg-slate-800/60" />
        <div className="h-2 w-full rounded bg-slate-800/40" />
      </div>
    );
  }

  return (
    <div
      className={cn(
        "flex flex-col items-center justify-center p-8 sm:p-12 text-center rounded-xl border border-slate-800/80 bg-slate-900/20 backdrop-blur-sm",
        className
      )}
      {...props}
    >
      {variant === "sonar" ? (
        <div className="relative flex h-16 w-16 items-center justify-center mb-4">
          <div className="absolute h-full w-full rounded-full border-2 border-cyan-400/40 animate-ping opacity-75" />
          <div className="absolute h-10 w-10 rounded-full border border-cyan-500/60 animate-pulse" />
          <div className="flex h-8 w-8 items-center justify-center rounded-full bg-cyan-950/80 border border-cyan-500 text-cyan-400">
            <Radio className="h-4 w-4" />
          </div>
        </div>
      ) : (
        <Loader2 className="h-8 w-8 animate-spin text-cyan-400 mb-4" />
      )}

      <h3 className="text-sm font-semibold text-white tracking-wide">{message}</h3>
      {subtext && (
        <p className="mt-1 text-xs text-slate-400 font-mono">{subtext}</p>
      )}
    </div>
  );
}

