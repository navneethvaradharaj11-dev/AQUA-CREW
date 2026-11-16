"use client";

import React, { useState } from "react";
import {
  FileText,
  Download,
  Printer,
  ShieldCheck,
  CheckCircle2,
  AlertTriangle,
  Building,
  Droplets,
  Wrench,
  Bot,
  Activity,
  Calendar,
  Layers,
  ArrowUpRight,
  ExternalLink,
} from "lucide-react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { StatusBadge } from "@/components/ui/StatusBadge";

export function ReportsView() {
  const [selectedReportId, setSelectedReportId] = useState<string>("RPT-E2E-2026-003");
  const [downloadSuccess, setDownloadSuccess] = useState<string | null>(null);

  const reportCatalog = [
    {
      id: "RPT-E2E-2026-003",
      title: "Master Incident Lifecycle & Acceptance Audit: INC-2026-003",
      category: "Engineering Acceptance",
      severity: "Critical",
      author: "Principal Operations Lead & AI System Orchestrator",
      date: "2026-11-16",
      complianceCode: "EPA-DWSRF-2026.4",
      status: "APPROVED_FINAL",
      segment: "PIPE-003 (Uptown Main Feeder Line)",
    },
    {
      id: "RPT-HYD-2026-010",
      title: "EPANET Net3 Hydraulic Benchmark & Headloss Recovery Analysis",
      category: "Hydraulic Digital Twin",
      severity: "Low",
      author: "Lead Hydraulic Modeling Engineer",
      date: "2026-11-15",
      complianceCode: "AWWA-M32-HYD",
      status: "CERTIFIED",
      segment: "DMA-METRO-CENTRAL (97 Nodes, 119 Links)",
    },
    {
      id: "RPT-RPR-2026-016",
      title: "Structural Repair Recommendation & Work Order Package: RPR-PLAN-004",
      category: "Repair Management",
      severity: "High",
      author: "Civil Infrastructure & Trenchless Repair Specialist",
      date: "2026-11-14",
      complianceCode: "ASTM-F1216-CIPP",
      status: "EXECUTED",
      segment: "PIPE-SEC-4B-92 (Ductile Iron 400mm)",
    },
    {
      id: "RPT-IOT-2026-018",
      title: "IoT Sensor Gateway Calibration & Telemetry Provenance Audit",
      category: "Hardware Integrity",
      severity: "Low",
      author: "Hardware Systems Security Officer",
      date: "2026-11-13",
      complianceCode: "NIST-SP-800-82-ICS",
      status: "VERIFIED",
      segment: "Network Wide (190 Stations)",
    },
  ];

  const currentReport = reportCatalog.find((r) => r.id === selectedReportId) || reportCatalog[0];

  const handleDownload = (type: "pdf" | "json" | "csv") => {
    const filename = `${currentReport.id}.${type}`;
    const dummyBlob = new Blob(
      [
        `AQUA CREW ENGINEERING AUDIT REPORT\nID: ${currentReport.id}\nTitle: ${currentReport.title}\nStatus: ${currentReport.status}\nDate: ${currentReport.date}\nStandard: ${currentReport.complianceCode}\n\n[SIMULATION CERTIFIED BY TASK 19 UNIFIED ACCEPTANCE SUITE]`
      ],
      { type: type === "json" ? "application/json" : "text/plain" }
    );
    const url = URL.createObjectURL(dummyBlob);
    const link = document.createElement("a");
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);

    setDownloadSuccess(`Report ${filename} generated and saved to your device.`);
    setTimeout(() => setDownloadSuccess(null), 4000);
  };

  return (
    <div className="space-y-6">
      {/* View Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-slate-800 pb-4">
        <div>
          <div className="flex items-center gap-2.5">
            <FileText className="h-6 w-6 text-cyan-400" />
            <h1 className="text-xl sm:text-2xl font-black tracking-tight text-white">
              Engineering Reports & Regulatory Dossiers
            </h1>
            <span className="rounded bg-emerald-950/80 px-2.5 py-0.5 text-xs font-mono text-emerald-300 border border-emerald-800/60 font-semibold">
              OFFICIAL ARCHIVE
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-1 max-w-2xl">
            Audit-grade dossiers compiling physical inspection traces, hydraulic digital twin telemetry, post-repair verifications, and regulatory compliance certificates.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" onClick={() => window.print()} leftIcon={<Printer className="h-3.5 w-3.5" />}>
            Print Dossier
          </Button>
          <Button variant="primary" size="sm" onClick={() => handleDownload("pdf")} leftIcon={<Download className="h-3.5 w-3.5" />}>
            Export Certified PDF
          </Button>
        </div>
      </div>

      {downloadSuccess && (
        <div className="flex items-center gap-2 rounded-lg border border-emerald-500/40 bg-emerald-950/30 px-3.5 py-2 text-xs text-emerald-300 font-mono animate-in fade-in">
          <CheckCircle2 className="h-4 w-4 shrink-0 text-emerald-400" />
          <span>{downloadSuccess}</span>
        </div>
      )}

      {/* Main Grid: Report Selector & Active Dossier Preview */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Report Index List */}
        <div className="lg:col-span-4 space-y-3">
          <div className="flex items-center justify-between pb-1">
            <span className="text-xs font-bold text-white uppercase tracking-wider font-mono">
              Available Engineering Audits
            </span>
            <span className="text-[10px] text-slate-500 font-mono">{reportCatalog.length} Records</span>
          </div>

          <div className="space-y-2.5">
            {reportCatalog.map((r) => (
              <div
                key={r.id}
                onClick={() => setSelectedReportId(r.id)}
                className={`p-3.5 rounded-xl border transition-all cursor-pointer text-xs space-y-1.5 ${
                  selectedReportId === r.id
                    ? "border-cyan-500 bg-cyan-950/20 shadow-cyan-glow-sm"
                    : "border-slate-800/80 bg-slate-900/40 hover:border-slate-700"
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className="font-mono text-[10px] text-cyan-400 font-bold">{r.id}</span>
                  <span className="px-2 py-0.5 rounded text-[9px] font-mono font-bold bg-emerald-950/60 text-emerald-300 border border-emerald-500/30">
                    {r.status}
                  </span>
                </div>
                <h3 className="font-semibold text-white leading-snug line-clamp-2">{r.title}</h3>
                <div className="flex items-center justify-between text-[10px] text-slate-400 font-mono pt-1">
                  <span>{r.category}</span>
                  <span>{r.date}</span>
                </div>
              </div>
            ))}
          </div>

          {/* Standards Notice Card */}
          <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-3.5 text-xs text-slate-400 space-y-1.5">
            <div className="flex items-center gap-1.5 text-amber-300 font-semibold font-mono text-[11px]">
              <ShieldCheck className="h-3.5 w-3.5 text-amber-400" />
              <span>REGULATORY CONFORMANCE</span>
            </div>
            <p className="text-[11px] leading-relaxed">
              All generated dossiers comply with EPA Standard 40 CFR Part 141 and AWWA Water Loss Auditing Manual M36. Telemetry is verified under Task 19 acceptance guidelines.
            </p>
          </div>
        </div>

        {/* Right Column: Publication-Grade Document Preview */}
        <div className="lg:col-span-8">
          <Card variant="industrial" className="p-6 space-y-6">
            {/* Report Header Band */}
            <div className="border-b border-slate-800 pb-5 space-y-3">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <div className="flex items-center gap-2">
                  <span className="rounded bg-slate-800 px-2.5 py-1 text-xs font-mono font-bold text-cyan-400 border border-slate-700">
                    {currentReport.id}
                  </span>
                  <span className="rounded bg-emerald-950/60 px-2 py-0.5 text-xs font-mono text-emerald-300 border border-emerald-800/40">
                    STATUS: {currentReport.status}
                  </span>
                </div>
                <div className="text-xs font-mono text-slate-400">
                  STANDARD: <span className="text-white font-bold">{currentReport.complianceCode}</span>
                </div>
              </div>

              <h2 className="text-lg sm:text-xl font-black tracking-tight text-white leading-snug">
                {currentReport.title}
              </h2>

              <div className="grid grid-cols-2 sm:grid-cols-3 gap-2.5 text-xs font-mono pt-2">
                <div className="rounded border border-slate-800/80 bg-slate-900/60 p-2">
                  <span className="text-[10px] text-slate-500 uppercase block">Affiliated Segment</span>
                  <span className="text-slate-200 font-semibold truncate block">{currentReport.segment}</span>
                </div>
                <div className="rounded border border-slate-800/80 bg-slate-900/60 p-2">
                  <span className="text-[10px] text-slate-500 uppercase block">Certified Date</span>
                  <span className="text-white font-bold block">{currentReport.date}</span>
                </div>
                <div className="rounded border border-slate-800/80 bg-slate-900/60 p-2 col-span-2 sm:col-span-1">
                  <span className="text-[10px] text-slate-500 uppercase block">Lead Certifier</span>
                  <span className="text-cyan-300 font-medium truncate block">{currentReport.author}</span>
                </div>
              </div>
            </div>

            {/* Section 1: Executive Summary */}
            <div className="space-y-2">
              <span className="text-xs font-mono font-bold uppercase text-cyan-400 tracking-wider">
                1.0 Executive Summary & Failure Diagnostics
              </span>
              <p className="text-xs text-slate-300 leading-relaxed font-sans">
                A sudden acoustic burst and pressure transient event was logged on {currentReport.segment}. Initial hydrophone triangulation identified a shear rupture with an estimated water loss of 34.2 L/s. Autonomous dispatch of Triton-1 Crawler (ROV-001) verified a 4.8mm circumferential crack at joint J-14 via HD videometric and hydro-acoustic acoustic imaging.
              </p>
            </div>

            {/* Section 2: Quantitative Telemetry Table */}
            <div className="space-y-2">
              <span className="text-xs font-mono font-bold uppercase text-cyan-400 tracking-wider">
                2.0 Hydraulic & Spectral Telemetry Parameters
              </span>
              <div className="overflow-x-auto rounded-lg border border-slate-800">
                <table className="w-full text-left text-xs font-mono">
                  <thead className="bg-slate-900/80 text-slate-400 border-b border-slate-800">
                    <tr>
                      <th className="py-2 px-3">Parameter Description</th>
                      <th className="py-2 px-3">Pre-Repair Value</th>
                      <th className="py-2 px-3">Post-Repair Standard</th>
                      <th className="py-2 px-3">Delta / Benefit</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60">
                    <tr>
                      <td className="py-2 px-3 text-white font-sans">Hydraulic Head Loss</td>
                      <td className="py-2 px-3 text-rose-400">8.75 meters</td>
                      <td className="py-2 px-3 text-emerald-400">0.42 meters</td>
                      <td className="py-2 px-3 text-cyan-300">-8.33m (-95.2%)</td>
                    </tr>
                    <tr>
                      <td className="py-2 px-3 text-white font-sans">Estimated Water Loss Rate</td>
                      <td className="py-2 px-3 text-rose-400">34.2 L/s</td>
                      <td className="py-2 px-3 text-emerald-400">0.00 L/s</td>
                      <td className="py-2 px-3 text-cyan-300">34.2 L/s Preserved</td>
                    </tr>
                    <tr>
                      <td className="py-2 px-3 text-white font-sans">Acoustic SPL Emission</td>
                      <td className="py-2 px-3 text-rose-400">88.4 dB @ 1.4 kHz</td>
                      <td className="py-2 px-3 text-emerald-400">38.1 dB (Baseline)</td>
                      <td className="py-2 px-3 text-cyan-300">-50.3 dB Restored</td>
                    </tr>
                    <tr>
                      <td className="py-2 px-3 text-white font-sans">Node Pressure Recovery</td>
                      <td className="py-2 px-3 text-rose-400">1.82 bar</td>
                      <td className="py-2 px-3 text-emerald-400">4.45 bar</td>
                      <td className="py-2 px-3 text-cyan-300">+2.63 bar Gain</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>

            {/* Section 3: Engineering Sign-off & Stamp */}
            <div className="space-y-3 pt-3 border-t border-slate-800">
              <span className="text-xs font-mono font-bold uppercase text-cyan-400 tracking-wider">
                3.0 Official Certification & Engineering Seal
              </span>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4 space-y-2">
                  <span className="text-[10px] font-mono text-slate-500 uppercase block">Digital Audit Signature</span>
                  <div className="font-mono text-xs text-emerald-400 font-bold break-all">
                    SHA256: 4a9f81d3b5e709a826421387d890cfb120ea93b3
                  </div>
                  <div className="text-[10px] text-slate-400 font-mono">
                    Signed by: SYSTEM_AI_ACCEPTANCE_ENGINE @ 2026-11-16T16:30:00Z
                  </div>
                </div>

                <div className="rounded-xl border border-emerald-900/40 bg-emerald-950/20 p-4 space-y-1.5 flex flex-col justify-center">
                  <div className="flex items-center gap-2 text-emerald-400 font-bold text-xs">
                    <ShieldCheck className="h-4 w-4" />
                    <span>OPERATIONAL ENGINEERING SIGN-OFF</span>
                  </div>
                  <p className="text-[11px] text-slate-300 font-sans">
                    Certified compliant under EPANET WNTR digital twin criteria. Zero hydraulic violations detected in 24h simulation loop.
                  </p>
                </div>
              </div>
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
}
