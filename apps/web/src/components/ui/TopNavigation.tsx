"use client";

import React, { useState, useEffect } from "react";
import { cn } from "@/lib/utils";
import {
  Bell,
  Sun,
  Moon,
  Menu,
  Shield,
  Activity,
  Check,
  ExternalLink,
  Wifi,
  WifiOff,
} from "lucide-react";
import { useTheme } from "@/context/ThemeContext";
import { telemetryWsClient, WebSocketConnectionState } from "@/services/api/telemetryWebSocketClient";

export interface TopNavigationProps {
  currentViewName: string;
  onOpenMobileMenu?: () => void;
  className?: string;
}

export function TopNavigation({
  currentViewName,
  onOpenMobileMenu,
  className,
}: TopNavigationProps) {
  const { theme, toggleTheme } = useTheme();
  const [showNotifications, setShowNotifications] = useState(false);
  const [unreadCount, setUnreadCount] = useState(2);
  const [wsState, setWsState] = useState<WebSocketConnectionState>("DISCONNECTED");

  useEffect(() => {
    // Attempt WebSocket connection to FastAPI backend
    telemetryWsClient.connect();
    const unsub = telemetryWsClient.onStatusChange((s) => {
      setWsState(s);
    });

    return () => {
      unsub();
    };
  }, []);

  const notifications = [
    {
      id: "notif-1",
      title: "Virtual Hydrophone Calibration",
      time: "2m ago",
      desc: "Simulated sensor node S-04 baseline established at 42.1 dB.",
      unread: true,
    },
    {
      id: "notif-2",
      title: "Virtual Rover Docking Complete",
      time: "14m ago",
      desc: "Rover AQUA-ROV-01 returned to virtual charging dock at Sector 4.",
      unread: true,
    },
  ];

  const markAllRead = () => {
    setUnreadCount(0);
  };

  return (
    <header
      className={cn(
        "sticky top-0 z-20 flex h-16 w-full items-center justify-between border-b border-slate-800 bg-slate-950/85 px-4 sm:px-6 backdrop-blur-md",
        className
      )}
    >
      {/* Left: Mobile Menu Trigger + Breadcrumb */}
      <div className="flex items-center gap-3">
        {onOpenMobileMenu && (
          <button
            onClick={onOpenMobileMenu}
            className="flex h-9 w-9 items-center justify-center rounded-lg border border-slate-800 bg-slate-900 text-slate-400 hover:text-white md:hidden"
            aria-label="Open navigation menu"
          >
            <Menu className="h-5 w-5" />
          </button>
        )}

        <div className="flex items-center gap-2 text-xs">
          <span className="text-slate-500 font-mono hidden sm:inline">AQUA-CREW /</span>
          <h1 className="font-semibold text-white text-sm sm:text-base tracking-tight">
            {currentViewName}
          </h1>
          <span className="rounded bg-cyan-950/60 border border-cyan-800/40 px-2 py-0.5 text-[10px] font-mono text-cyan-400 hidden md:inline">
            SYSTEM READY
          </span>
        </div>
      </div>

      {/* Right: Telemetry pill, Notification, Theme, Profile */}
      <div className="flex items-center gap-2 sm:gap-3">
        {/* Real-time Backend Connection Status Indicator */}
        <div
          className={cn(
            "hidden sm:flex items-center gap-2 rounded-full border px-3 py-1 text-xs",
            wsState === "CONNECTED"
              ? "border-emerald-900/60 bg-emerald-950/30 text-emerald-400"
              : wsState === "CONNECTING"
              ? "border-amber-900/60 bg-amber-950/30 text-amber-300"
              : "border-slate-800 bg-slate-900/60 text-slate-400"
          )}
        >
          {wsState === "CONNECTED" ? (
            <>
              <Wifi className="h-3.5 w-3.5 text-emerald-400 animate-pulse" />
              <span className="font-mono text-[11px]">BACKEND WS: ONLINE [SIMULATED]</span>
            </>
          ) : wsState === "CONNECTING" ? (
            <>
              <Activity className="h-3.5 w-3.5 text-amber-400 animate-spin" />
              <span className="font-mono text-[11px]">CONNECTING BACKEND...</span>
            </>
          ) : (
            <>
              <WifiOff className="h-3.5 w-3.5 text-slate-500" />
              <span className="font-mono text-[11px]">LOCAL SIMULATION: OFFLINE MODE</span>
            </>
          )}
        </div>

        {/* Notification Area */}
        <div className="relative">
          <button
            onClick={() => setShowNotifications(!showNotifications)}
            className="relative flex h-9 w-9 items-center justify-center rounded-lg border border-slate-800 bg-slate-900/70 text-slate-300 hover:bg-slate-800 hover:text-white transition-colors"
            aria-label="View notifications"
          >
            <Bell className="h-4 w-4" />
            {unreadCount > 0 && (
              <span className="absolute -top-1 -right-1 flex h-4 w-4 items-center justify-center rounded-full bg-cyan-500 text-[10px] font-bold text-slate-950">
                {unreadCount}
              </span>
            )}
          </button>

          {/* Notifications Flyout */}
          {showNotifications && (
            <div className="absolute right-0 mt-2 w-80 rounded-xl border border-slate-800 bg-slate-900/95 p-4 shadow-xl backdrop-blur-md z-50">
              <div className="flex items-center justify-between pb-2 border-b border-slate-800">
                <span className="text-xs font-semibold uppercase tracking-wider text-slate-300">
                  System Alerts
                </span>
                {unreadCount > 0 && (
                  <button
                    onClick={markAllRead}
                    className="text-[11px] text-cyan-400 hover:underline flex items-center gap-1"
                  >
                    <Check className="h-3 w-3" /> Mark read
                  </button>
                )}
              </div>

              <div className="mt-3 space-y-2.5 max-h-60 overflow-y-auto">
                {notifications.map((n) => (
                  <div
                    key={n.id}
                    className="rounded-lg border border-slate-800/80 bg-slate-950/60 p-2.5 text-xs space-y-1 hover:border-slate-700 transition-colors"
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-medium text-slate-200">{n.title}</span>
                      <span className="text-[10px] text-slate-500">{n.time}</span>
                    </div>
                    <p className="text-[11px] text-slate-400">{n.desc}</p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Theme Toggle (Dark / Light) */}
        <button
          onClick={toggleTheme}
          className="flex h-9 w-9 items-center justify-center rounded-lg border border-slate-800 bg-slate-900/70 text-slate-300 hover:bg-slate-800 hover:text-white transition-colors"
          aria-label={theme === "dark" ? "Switch to light mode" : "Switch to dark mode"}
          title={theme === "dark" ? "Switch to light mode" : "Switch to dark mode"}
        >
          {theme === "dark" ? (
            <Sun className="h-4 w-4 text-amber-300" />
          ) : (
            <Moon className="h-4 w-4 text-cyan-500" />
          )}
        </button>

        {/* User Profile Area */}
        <div className="flex items-center gap-2 pl-2 border-l border-slate-800">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-cyan-950 border border-cyan-800/60 font-mono text-xs font-bold text-cyan-400">
            OP
          </div>
          <div className="hidden xl:flex flex-col text-left">
            <span className="text-xs font-medium text-slate-200">Principal Operator</span>
            <span className="text-[10px] font-mono text-slate-400">Command Control</span>
          </div>
        </div>
      </div>
    </header>
  );
}

