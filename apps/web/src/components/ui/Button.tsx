"use client";

import React, { forwardRef } from "react";
import { cn } from "@/lib/utils";
import { Loader2 } from "lucide-react";

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?:
    | "primary"
    | "secondary"
    | "outline"
    | "ghost"
    | "destructive"
    | "industrial";
  size?: "sm" | "md" | "lg";
  isLoading?: boolean;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      className,
      variant = "primary",
      size = "md",
      isLoading = false,
      disabled,
      leftIcon,
      rightIcon,
      children,
      ...props
    },
    ref
  ) => {
    const variantStyles = {
      primary:
        "bg-cyan-500 text-slate-950 font-semibold hover:bg-cyan-400 active:bg-cyan-600 shadow-sm shadow-cyan-500/20 hover:shadow-cyan-500/40",
      secondary:
        "bg-slate-800 text-slate-100 font-medium hover:bg-slate-700 active:bg-slate-800 border border-slate-700/80 hover:border-slate-600",
      outline:
        "bg-transparent text-slate-200 font-medium border border-cyan-500/30 hover:border-cyan-400 hover:bg-cyan-500/10 active:bg-cyan-500/20 text-cyan-300",
      ghost:
        "bg-transparent text-slate-300 font-medium hover:bg-slate-800/60 hover:text-white active:bg-slate-800",
      destructive:
        "bg-rose-600 text-white font-semibold hover:bg-rose-500 active:bg-rose-700 shadow-sm shadow-rose-600/30",
      industrial:
        "bg-slate-900 text-cyan-300 font-mono text-xs uppercase tracking-wider border border-cyan-500/40 hover:border-cyan-300 hover:bg-cyan-950/40 shadow-sm hover:shadow-cyan-glow-sm",
    }[variant];

    const sizeStyles = {
      sm: "h-8 px-3 text-xs gap-1.5 rounded-md",
      md: "h-9 px-4 text-sm gap-2 rounded-lg",
      lg: "h-11 px-6 text-base gap-2.5 rounded-lg",
    }[size];

    return (
      <button
        ref={ref}
        disabled={disabled || isLoading}
        className={cn(
          "inline-flex items-center justify-center font-medium transition-all duration-150 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-cyan-400 focus-visible:ring-offset-2 focus-visible:ring-offset-slate-950 disabled:pointer-events-none disabled:opacity-50 select-none",
          variantStyles,
          sizeStyles,
          className
        )}
        {...props}
      >
        {isLoading ? (
          <Loader2 className="h-4 w-4 animate-spin shrink-0" />
        ) : (
          leftIcon && <span className="shrink-0">{leftIcon}</span>
        )}
        <span>{children}</span>
        {!isLoading && rightIcon && <span className="shrink-0">{rightIcon}</span>}
      </button>
    );
  }
);

Button.displayName = "Button";

