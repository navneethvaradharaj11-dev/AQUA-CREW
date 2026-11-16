import React from "react";
import { cn } from "@/lib/utils";
import { AlertTriangle, RotateCcw } from "lucide-react";
import { Button } from "./Button";

export interface ErrorStateProps extends React.HTMLAttributes<HTMLDivElement> {
  title?: string;
  message: string;
  code?: string;
  onRetry?: () => void;
  actionText?: string;
}

export function ErrorState({
  title = "Telemetry Signal Disrupted",
  message,
  code,
  onRetry,
  actionText = "Re-establish Link",
  className,
  ...props
}: ErrorStateProps) {
  return (
    <div
      className={cn(
        "flex flex-col items-center justify-center p-8 sm:p-12 text-center rounded-xl border border-rose-900/40 bg-rose-950/10 backdrop-blur-sm",
        className
      )}
      {...props}
    >
      <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-rose-950/60 border border-rose-800/80 text-rose-400 mb-4 shadow-sm shadow-rose-950">
        <AlertTriangle className="h-6 w-6" />
      </div>

      <h3 className="text-base font-semibold text-rose-200 tracking-tight">{title}</h3>
      <p className="mt-1 text-xs sm:text-sm text-rose-300/80 max-w-md leading-relaxed">
        {message}
      </p>

      {code && (
        <span className="mt-2 rounded bg-rose-950/80 border border-rose-900/60 px-2 py-0.5 font-mono text-[11px] text-rose-400">
          CODE: {code}
        </span>
      )}

      {onRetry && (
        <div className="mt-5">
          <Button
            variant="outline"
            size="sm"
            onClick={onRetry}
            leftIcon={<RotateCcw className="h-3.5 w-3.5" />}
            className="border-rose-800/80 text-rose-300 hover:bg-rose-950/40 hover:text-white"
          >
            {actionText}
          </Button>
        </div>
      )}
    </div>
  );
}

