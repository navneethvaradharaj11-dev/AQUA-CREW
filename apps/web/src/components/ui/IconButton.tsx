"use client";

import React, { forwardRef } from "react";
import { cn } from "@/lib/utils";

export interface IconButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  "aria-label": string;
  variant?: "default" | "outline" | "ghost" | "danger" | "industrial";
  size?: "sm" | "md" | "lg";
  icon: React.ReactNode;
}

export const IconButton = forwardRef<HTMLButtonElement, IconButtonProps>(
  (
    {
      className,
      "aria-label": ariaLabel,
      variant = "ghost",
      size = "md",
      icon,
      disabled,
      ...props
    },
    ref
  ) => {
    const variantStyles = {
      default:
        "bg-slate-800 text-slate-100 border border-slate-700/80 hover:bg-slate-700 active:bg-slate-850",
      outline:
        "bg-transparent text-slate-200 border border-slate-700 hover:border-cyan-400 hover:text-cyan-300 hover:bg-cyan-500/10",
      ghost:
        "bg-transparent text-slate-400 hover:text-slate-100 hover:bg-slate-800/80 active:bg-slate-800",
      danger:
        "bg-transparent text-rose-400 hover:bg-rose-950/40 border border-rose-900/40 hover:border-rose-600",
      industrial:
        "bg-slate-900 text-cyan-400 border border-cyan-800/60 hover:border-cyan-400 hover:bg-cyan-950/50 shadow-sm",
    }[variant];

    const sizeStyles = {
      sm: "h-8 w-8 rounded-md p-1.5",
      md: "h-9 w-9 rounded-lg p-2",
      lg: "h-11 w-11 rounded-lg p-2.5",
    }[size];

    return (
      <button
        ref={ref}
        aria-label={ariaLabel}
        disabled={disabled}
        className={cn(
          "inline-flex items-center justify-center transition-all duration-150 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-cyan-400 focus-visible:ring-offset-2 focus-visible:ring-offset-slate-950 disabled:pointer-events-none disabled:opacity-50 select-none",
          variantStyles,
          sizeStyles,
          className
        )}
        {...props}
      >
        {icon}
      </button>
    );
  }
);

IconButton.displayName = "IconButton";

