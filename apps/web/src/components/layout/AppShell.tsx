"use client";

import React, { useState, useEffect } from "react";
import { Sidebar, NAV_ITEMS } from "@/components/ui/Sidebar";
import { TopNavigation } from "@/components/ui/TopNavigation";
import { SectionHeader } from "@/components/ui/SectionHeader";
import { MetricCard } from "@/components/ui/MetricCard";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { ErrorState } from "@/components/ui/ErrorState";

import {
  fetchCommandCenterData,
  getInitialCommandCenterData,
  CommandCenterDataBundle,
  SimulatedRover,
  SimulatedLeakIncident,
  acknowledgeAlert,
} from "@/services/simulation";

import { CommandCenterHeader } from "@/components/dashboard/CommandCenterHeader";
import { KpiSection } from "@/components/dashboard/KpiSection";
import { WaterNetworkSection } from "@/components/dashboard/WaterNetworkSection";
import { RoverFleetSection } from "@/components/dashboard/RoverFleetSection";
import { LeakIncidentSection } from "@/components/dashboard/LeakIncidentSection";
import { SensorNetworkSection } from "@/components/dashboard/SensorNetworkSection";
import { ActiveMissionsSection } from "@/components/dashboard/ActiveMissionsSection";
import { AnalyticsSection } from "@/components/dashboard/AnalyticsSection";
import { AlertCenterSection } from "@/components/dashboard/AlertCenterSection";
import { RoverDetailModal } from "@/components/dashboard/RoverDetailModal";
import { IncidentDetailModal } from "@/components/dashboard/IncidentDetailModal";
import { MapIntelligenceView } from "@/components/gis/MapIntelligenceView";
import { FleetManagementView } from "@/components/fleet/FleetManagementView";
import { AiIntelligenceView } from "@/components/intelligence/AiIntelligenceView";
import { DispatchCenterView } from "@/components/dispatch/DispatchCenterView";
import { PredictiveMaintenanceView } from "@/components/maintenance/PredictiveMaintenanceView";
import { DigitalTwinView } from "@/components/digital-twin/DigitalTwinView";
import { InfrastructureIntelligenceView } from "@/components/infrastructure-intelligence/InfrastructureIntelligenceView";
import { OperationalIntelligenceView } from "@/components/operational-intelligence/OperationalIntelligenceView";
import { AiAssistantView } from "@/components/ai-assistant/AiAssistantView";
import { NetworkOptimizationView } from "@/components/optimization/NetworkOptimizationView";
import { AutonomousInspectionView } from "@/components/inspection-intelligence/AutonomousInspectionView";
import { RepairManagementView } from "@/components/repair-management/RepairManagementView";
import { IotDevicesView } from "@/components/iot-devices/IotDevicesView";
import { IncidentsView } from "@/components/incidents/IncidentsView";
import { AnalyticsView } from "@/components/analytics/AnalyticsView";
import { ReportsView } from "@/components/reports/ReportsView";
import { SettingsView } from "@/components/settings/SettingsView";
import { SensorMonitoringView } from "@/components/sensors/SensorMonitoringView";

import { ArrowRight, Map } from "lucide-react";

export interface AppShellProps {
  initialNav?: string;
}

export function AppShell({ initialNav = "overview" }: AppShellProps) {
  const [activeNav, setActiveNav] = useState(initialNav);
  const [isCollapsed, setIsCollapsed] = useState(false);
  const [isMobileOpen, setIsMobileOpen] = useState(false);

  // Initialize with typed simulation data to eliminate hydration delay
  const [data, setData] = useState<CommandCenterDataBundle>(getInitialCommandCenterData);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Modal inspection states
  const [selectedRover, setSelectedRover] = useState<SimulatedRover | null>(null);
  const [selectedIncident, setSelectedIncident] = useState<SimulatedLeakIncident | null>(null);

  const loadData = async () => {
    try {
      const bundle = await fetchCommandCenterData();
      setData(bundle);
      setError(null);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to load simulation telemetry");
    } finally {
      setIsRefreshing(false);
    }
  };

  const handleRefresh = async () => {
    setIsRefreshing(true);
    await loadData();
  };

  const handleAcknowledgeAlert = async (id: string) => {
    await acknowledgeAlert(id);
    setData((prev) => ({
      ...prev,
      alerts: prev.alerts.map((a) => (a.id === id ? { ...a, acknowledged: true } : a)),
    }));
  };

  const currentItem = NAV_ITEMS.find((n) => n.id === activeNav) || NAV_ITEMS[0];
  const unacknowledgedCount = data.alerts.filter((a) => !a.acknowledged).length;

  return (
    <div className="flex h-dvh w-full overflow-hidden bg-slate-950 text-slate-100">
      {/* Desktop Collapsible Sidebar */}
      <div className="hidden md:flex">
        <Sidebar
          activeId={activeNav}
          onSelect={(id) => setActiveNav(id)}
          isCollapsed={isCollapsed}
          onToggleCollapse={() => setIsCollapsed(!isCollapsed)}
        />
      </div>

      {/* Mobile Slide-Over Drawer */}
      {isMobileOpen && (
        <div className="fixed inset-0 z-50 flex md:hidden">
          <div
            className="fixed inset-0 bg-slate-950/80 backdrop-blur-sm"
            onClick={() => setIsMobileOpen(false)}
          />
          <div className="relative flex w-72 flex-col bg-slate-950 border-r border-slate-800 z-10 animate-in slide-in-from-left duration-200">
            <Sidebar
              activeId={activeNav}
              onSelect={(id) => {
                setActiveNav(id);
                setIsMobileOpen(false);
              }}
              isCollapsed={false}
              onToggleCollapse={() => setIsMobileOpen(false)}
              className="w-full h-full border-r-0"
            />
          </div>
        </div>
      )}

      {/* Main View Area */}
      <div className="flex flex-1 flex-col overflow-hidden">
        <TopNavigation
          currentViewName={currentItem.name}
          onOpenMobileMenu={() => setIsMobileOpen(true)}
        />

        <main className="flex-1 overflow-y-auto p-4 sm:p-6 lg:p-8 space-y-6">
          {error ? (
            <ErrorState
              title="Simulation Broker Disconnected"
              message={error}
              onRetry={loadData}
              actionText="Re-establish Simulation Stream"
            />
          ) : activeNav === "overview" ? (
            /* ========================================================= */
            /* PRIMARY COMMAND CENTER DASHBOARD (TASK 03 REQUIREMENT)   */
            /* ========================================================= */
            <div className="space-y-6">
              {/* Header (Section A) */}
              <CommandCenterHeader
                lastUpdated={data.timestamp}
                isRefreshing={isRefreshing}
                onRefresh={handleRefresh}
                unacknowledgedAlertsCount={unacknowledgedCount}
              />

              {/* KPI Metrics (Section B) */}
              <KpiSection kpis={data.kpis} />

              {/* Water Network Overview (Section C) */}
              <WaterNetworkSection network={data.network} />

              {/* Rover Fleet Overview (Section D) */}
              <RoverFleetSection
                rovers={data.rovers}
                onSelectRover={(r) => setSelectedRover(r)}
              />

              {/* Leak Incident Overview (Section E) */}
              <LeakIncidentSection
                incidents={data.incidents}
                onSelectIncident={(i) => setSelectedIncident(i)}
              />

              {/* Active Missions (Section G) & Stationary Sensors (Section F) */}
              <div className="space-y-6">
                <ActiveMissionsSection missions={data.missions} />
                <SensorNetworkSection sensors={data.sensors} />
              </div>

              {/* System Analytics & Charts (Section H) */}
              <AnalyticsSection analytics={data.analytics} />

              {/* Alert Center (Section I) */}
              <AlertCenterSection
                alerts={data.alerts}
                onAcknowledgeAlert={handleAcknowledgeAlert}
              />
            </div>
          ) : activeNav === "city-map" ? (
            /* ========================================================= */
            /* INTERACTIVE GIS INTELLIGENCE MAP (TASK 04 REQUIREMENT)    */
            /* ========================================================= */
            <div className="space-y-4">
              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 border-b border-slate-800 pb-3">
                <div>
                  <div className="flex items-center gap-2">
                    <Map className="h-5 w-5 text-cyan-400" />
                    <h2 className="text-lg font-bold tracking-tight text-white">
                      Bengaluru Metropolitan Pipeline GIS Intelligence
                    </h2>
                    <span className="rounded bg-cyan-950/80 px-2 py-0.5 text-[10px] font-mono text-cyan-300 border border-cyan-800/60 font-semibold">
                      [BWSSB SMART WATER GRID]
                    </span>
                  </div>
                  <p className="text-xs text-slate-400">
                    Real-time spatial visualization of underground distribution lines, virtual rovers, leak events & IoT sensor telemetry.
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setActiveNav("overview")}
                  >
                    Return to Overview
                  </Button>
                </div>
              </div>

              <MapIntelligenceView />
            </div>
          ) : activeNav === "rover-fleet" ? (
            /* ========================================================= */
            /* AUTONOMOUS ROVER FLEET MANAGEMENT (TASK 05 REQUIREMENT)   */
            /* ========================================================= */
            <FleetManagementView onNavigateToMap={() => setActiveNav("city-map")} />
          ) : activeNav === "intelligence" || activeNav === "leak-detection" || activeNav === "leak-localization" ? (
            /* ========================================================= */
            /* AI LEAK DETECTION & ACOUSTIC INTELLIGENCE (TASK 07)       */
            /* ========================================================= */
            <AiIntelligenceView />
          ) : activeNav === "sensor-monitoring" ? (
            /* ========================================================= */
            /* STATIONARY SENSOR NETWORK TELEMETRY MONITORING            */
            /* ========================================================= */
            <SensorMonitoringView />
          ) : activeNav === "dispatch" || activeNav === "mission-control" ? (
            /* ========================================================= */
            /* AUTONOMOUS MISSION PLANNING & DISPATCH (TASK 08)          */
            /* ========================================================= */
            <DispatchCenterView />
          ) : activeNav === "maintenance" ? (
            /* ========================================================= */
            /* PREDICTIVE MAINTENANCE & HEALTH INTELLIGENCE (TASK 09)   */
            /* ========================================================= */
            <PredictiveMaintenanceView />
          ) : activeNav === "digital-twin" ? (
            /* ========================================================= */
            /* DIGITAL TWIN & HYDRAULIC SIMULATION PLATFORM (TASK 10)    */
            /* ========================================================= */
            <DigitalTwinView />
          ) : activeNav === "infrastructure-intelligence" ? (
            /* ========================================================= */
            /* INFRASTRUCTURE INTELLIGENCE & GEOSPATIAL RISK (TASK 11)   */
            /* ========================================================= */
            <InfrastructureIntelligenceView />
          ) : activeNav === "operational-intelligence" ? (
            /* ========================================================= */
            /* UNIFIED OPERATIONAL INTELLIGENCE & DECISION (TASK 12)     */
            /* ========================================================= */
            <OperationalIntelligenceView />
          ) : activeNav === "ai-assistant" ? (
            /* ========================================================= */
            /* ADVANCED AI & EVIDENCE-GROUNDED DECISION INTEL (TASK 13)  */
            /* ========================================================= */
            <AiAssistantView />
          ) : activeNav === "optimization" ? (
            /* ========================================================= */
            /* NETWORK OPTIMIZATION & HYDRAULIC DECISION ENGINE (TASK 14)*/
            /* ========================================================= */
            <NetworkOptimizationView />
          ) : activeNav === "inspection-intelligence" ? (
            /* ========================================================= */
            /* AUTONOMOUS INSPECTION INTELLIGENCE & ROVER ORCHESTRATION */
            /* ========================================================= */
            <AutonomousInspectionView />
          ) : activeNav === "repair-management" ? (
            /* ========================================================= */
            /* INTELLIGENT REPAIR PLANNING & MANAGEMENT (TASK 16)        */
            /* ========================================================= */
            <RepairManagementView />
          ) : activeNav === "iot-devices" ? (
            /* ========================================================= */
            /* SECURE IOT DEVICE ECOSYSTEM & HARDWARE GATEWAY (TASK 18)   */
            /* ========================================================= */
            <IotDevicesView />
          ) : activeNav === "incidents" ? (
            /* ========================================================= */
            /* UNIFIED INCIDENT INTELLIGENCE & ACCEPTANCE (TASK 19)      */
            /* ========================================================= */
            <IncidentsView />
          ) : activeNav === "analytics" ? (
            /* ========================================================= */
            /* SYSTEM TELEMETRY & HYDRAULIC ANALYTICS DASHBOARD          */
            /* ========================================================= */
            <AnalyticsView />
          ) : activeNav === "reports" ? (
            /* ========================================================= */
            /* ENGINEERING REPORTS & REGULATORY AUDIT DOSSIERS           */
            /* ========================================================= */
            <ReportsView />
          ) : activeNav === "settings" ? (
            /* ========================================================= */
            /* PLATFORM CONFIGURATION & HARDWARE SAFETY CONTROLS         */
            /* ========================================================= */
            <SettingsView />
          ) : (
            /* ========================================================= */
            /* NAVIGATION DESTINATION PLACEHOLDERS (DESTINATIONS 4-11)   */
            /* ========================================================= */
            <div className="space-y-6">
              <SectionHeader
                title={currentItem.name}
                description={`AQUA CREW System Module destination: ${currentItem.category} tier.`}
                badge={
                  <StatusBadge
                    status="active"
                    label={currentItem.badge || "Planned Module"}
                    pulse
                    size="sm"
                  />
                }
                actions={
                  <Button
                    variant="primary"
                    size="sm"
                    onClick={() => setActiveNav("overview")}
                  >
                    Return to Command Center
                  </Button>
                }
              />

              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                <MetricCard
                  label="Module Scope"
                  value={currentItem.category?.toUpperCase() || "CORE"}
                  unit="LAYER"
                  tone="cyan"
                />
                <MetricCard
                  label="Architectural State"
                  value="PREPARED"
                  unit="TASK 03"
                  tone="emerald"
                />
                <MetricCard
                  label="Simulation Integration"
                  value="READY"
                  unit="Typed Service"
                  tone="slate"
                />
              </div>

              <Card variant="industrial" className="p-8">
                <div className="flex flex-col items-center justify-center text-center space-y-4 max-w-lg mx-auto">
                  <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-cyan-950/60 border border-cyan-800/80 text-cyan-400 shadow-cyan-glow-sm">
                    <currentItem.icon className="h-7 w-7" />
                  </div>
                  <div className="space-y-1">
                    <h2 className="text-xl font-bold tracking-tight text-white">
                      {currentItem.name} Dedicated View
                    </h2>
                    <p className="text-xs sm:text-sm text-slate-400 leading-relaxed">
                      This view destination is configured within the application shell.
                      The centralized Command Center overview is active on the Overview tab.
                    </p>
                  </div>
                  <div className="rounded-lg border border-slate-800 bg-slate-900/60 p-3 text-left w-full text-xs space-y-1 font-mono text-slate-300">
                    <div>ROUTE ID: <code>/app/{currentItem.id}</code></div>
                    <div>RESPONSIBILITY: {currentItem.name} domain orchestration</div>
                    <div>DATA INTERFACE: Ready for API/WebSocket binding</div>
                  </div>
                  <Button
                    variant="primary"
                    size="sm"
                    onClick={() => setActiveNav("overview")}
                    leftIcon={<ArrowRight className="h-3.5 w-3.5 rotate-180" />}
                  >
                    Return to Command Center
                  </Button>
                </div>
              </Card>
            </div>
          )}
        </main>
      </div>

      {/* Rover Detail Modal */}
      <RoverDetailModal
        rover={selectedRover}
        onClose={() => setSelectedRover(null)}
      />

      {/* Incident Detail Modal */}
      <IncidentDetailModal
        incident={selectedIncident}
        onClose={() => setSelectedIncident(null)}
      />
    </div>
  );
}
