"use client";

import React, { useState, useEffect } from "react";
import { Server, RefreshCw, CheckCircle, AlertTriangle } from "lucide-react";
import type { HealthStatusResponse } from "@aqua-crew/contracts";

export function ApiHealthProbe() {
  const [data, setData] = useState<HealthStatusResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [latencyMs, setLatencyMs] = useState<number | null>(null);

  const fetchHealth = async () => {
    setLoading(true);
    setError(null);
    const start = performance.now();
    try {
      const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000/api/v1";
      const res = await fetch(`${baseUrl}/health`, {
        cache: "no-store",
      });
      const duration = Math.round(performance.now() - start);
      setLatencyMs(duration);

      if (!res.ok) {
        throw new Error(`HTTP ${res.status}: ${res.statusText}`);
      }
      const json = await res.json();
      setData(json);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to reach backend");
      setData(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHealth();
  }, []);

  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-5 backdrop-blur-sm">
      <div className="flex items-center justify-between pb-3 border-b border-slate-800">
        <div className="flex items-center gap-2.5">
          <div className="p-2 rounded-lg bg-cyan-950/60 border border-cyan-800/50 text-cyan-400">
            <Server className="h-4 w-4" />
          </div>
          <div>
            <h3 className="text-sm font-semibold text-white">Backend Health Verification</h3>
            <p className="text-xs text-slate-400">GET /api/v1/health</p>
          </div>
        </div>

        <button
          onClick={fetchHealth}
          disabled={loading}
          className="flex items-center gap-1.5 rounded-lg border border-slate-700 bg-slate-800 px-3 py-1.5 text-xs font-medium text-slate-200 transition-colors hover:bg-slate-700 hover:text-white disabled:opacity-50"
        >
          <RefreshCw className={`h-3.5 w-3.5 ${loading ? "animate-spin text-cyan-400" : ""}`} />
          <span>{loading ? "Probing..." : "Test Health"}</span>
        </button>
      </div>

      <div className="mt-4">
        {error ? (
          <div className="flex items-start gap-3 rounded-lg border border-amber-900/50 bg-amber-950/20 p-3 text-xs text-amber-300">
            <AlertTriangle className="h-4 w-4 mt-0.5 text-amber-400 shrink-0" />
            <div>
              <p className="font-semibold">Backend Unreachable or CORS Blocked</p>
              <p className="mt-0.5 text-amber-200/80">
                Ensure the FastAPI backend is running on <code>http://localhost:8000</code>.
              </p>
              <p className="mt-1 font-mono text-[11px] text-amber-400/90">{error}</p>
            </div>
          </div>
        ) : data ? (
          <div className="space-y-3">
            <div className="flex flex-wrap items-center justify-between gap-2 rounded-lg border border-emerald-900/40 bg-emerald-950/20 px-3 py-2 text-xs">
              <div className="flex items-center gap-2 text-emerald-400 font-medium">
                <CheckCircle className="h-4 w-4" />
                <span>Backend Status: {data.status.toUpperCase()}</span>
              </div>
              <div className="flex items-center gap-3 text-slate-400 text-[11px] font-mono">
                <span>Version: {data.version}</span>
                <span>Latency: {latencyMs !== null ? `${latencyMs}ms` : "N/A"}</span>
                <span>Env: {data.environment}</span>
              </div>
            </div>

            <div className="grid grid-cols-3 gap-2 text-center">
              <div className="rounded bg-slate-800/40 border border-slate-800 p-2 text-xs">
                <span className="text-[10px] text-slate-400 uppercase tracking-wide block">Database</span>
                <span className="font-mono text-slate-300 text-[11px]">{data.services.database}</span>
              </div>
              <div className="rounded bg-slate-800/40 border border-slate-800 p-2 text-xs">
                <span className="text-[10px] text-slate-400 uppercase tracking-wide block">Simulation</span>
                <span className="font-mono text-cyan-400 text-[11px]">{data.services.simulation_engine}</span>
              </div>
              <div className="rounded bg-slate-800/40 border border-slate-800 p-2 text-xs">
                <span className="text-[10px] text-slate-400 uppercase tracking-wide block">Hardware HAL</span>
                <span className="font-mono text-cyan-400 text-[11px]">{data.services.hardware_gateway}</span>
              </div>
            </div>
          </div>
        ) : (
          <div className="flex items-center justify-center p-4 text-xs text-slate-500">
            Waiting for health probe response...
          </div>
        )}
      </div>
    </div>
  );
}

