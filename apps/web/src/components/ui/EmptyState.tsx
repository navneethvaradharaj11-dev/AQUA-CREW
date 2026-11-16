import React from "react";
import { cn } from "@/lib/utils";
import { LucideIcon, Layers } from "lucide-react";

export interface EmptyStateProps extends React.HTMLAttributes<HTMLDivElement> {
  title: string;
  description: string;
  icon?: LucideIcon;
  action?: React.ReactNode;
}

export function EmptyState({
  title,
  description,
  icon: Icon = Layers,
  action,
  className,
  ...props
}: EmptyStateProps) {
  return (
    <div
      className={cn(
        "flex flex-col items-center justify-center p-8 sm:p-12 text-center rounded-xl border border-dashed border-slate-800 bg-slate-900/20 backdrop-blur-sm",
        className
      )}
      {...props}
    >
      <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-slate-800/80 border border-slate-700/60 text-slate-400 mb-4 shadow-inner">
        <Icon className="h-6 w-6" />
      </div>

      <h3 className="text-base font-semibold text-white tracking-tight">{title}</h3>
      <p className="mt-1 text-xs sm:text-sm text-slate-400 max-w-sm leading-relaxed">
        {description}
      </p>

      {action && <div className="mt-5">{action}</div>}
    </div>
  );
}

