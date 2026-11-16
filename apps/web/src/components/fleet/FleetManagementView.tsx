"use client";

import React, { useState, useEffect, useCallback } from "react";
import {
  SimulatedRover,
  RoverOperatingState,
  SimulatedMission,
  RoverStateTransitionRecord,
} from "@/services/simulation/types";
import { roverSimulationEngine } from "@/services/simulation/roverSimulationEngine";
import { roverEventBus } from "@/services/simulation/roverEventBus";
import { SectionHeader } from "@/components/ui/SectionHeader";
import { Button } from "@/components/ui/Button";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { FleetOverviewKpis } from "./FleetOverviewKpis";
import { FleetStatusDistribution } from "./FleetStatusDistribution";
import { FleetSimulationControls } from "./FleetSimulationControls";
import { RoverCardGrid } from "./RoverCardGrid";
import { RoverControlModal, RoverModalMode } from "./RoverControlModal";
import { RoverSelectedPanel } from "./RoverSelectedPanel";
import { FleetEventLog } from "./FleetEventLog";
import { Compass, Bot, ShieldAlert } from "lucide-react";
import { useRouter } from "next/navigation";
import { backendApiClient } from "@/services/api/backendApiClient";

export interface FleetManagementViewProps {
  onNavigateToMap?: (roverId?: string) => void;
}

export function FleetManagementView({ onNavigateToMap }: FleetManagementViewProps) {
  const router = useRouter();
  const [rovers, setRovers] = useState<SimulatedRover[]>([]);
  const [missions, setMissions] = useState<SimulatedMission[]>([]);
  const [transitions, setTransitions] = useState<RoverStateTransitionRecord[]>([]);
  const [selectedRover, setSelectedRover] = useState<SimulatedRover | null>(null);
  const [stateFilter, setStateFilter] = useState<RoverOperatingState | "ALL">("ALL");
  const [isEngineRunning, setIsEngineRunning] = useState<boolean>(false);
  const [tickCount, setTickCount] = useState<number>(0);

  // Modal State
  const [modalMode, setModalMode] = useState<RoverModalMode>(null);
  const [targetRover, setTargetRover] = useState<SimulatedRover | null>(null);

  // Sync state from engine
  const syncStateFromEngine = useCallback(() => {
    const currentRovers = roverSimulationEngine.getRovers();
    setRovers([...currentRovers]);
    setMissions([...roverSimulationEngine.getMissions()]);
    setTransitions([...roverSimulationEngine.getTransitionHistory()]);
    setIsEngineRunning(roverSimulationEngine.isRunning());

    // Update selected rover if open
    setSelectedRover((prev) => {
      if (!prev) return null;
      const updated = currentRovers.find((r) => r.id === prev.id);
      return updated || null;
    });
  }, []);

  // Initial load and event subscriptions
  useEffect(() => {
    syncStateFromEngine();

    // Subscribe to telemetry updates
    const unsubTelemetry = roverEventBus.subscribe("ROVER_TELEMETRY_UPDATED", () => {
      syncStateFromEngine();
    });

    // Subscribe to state change events
    const unsubState = roverEventBus.subscribe("ROVER_STATE_CHANGED", () => {
      syncStateFromEngine();
    });

    // Subscribe to simulation tick
    const unsubTick = roverEventBus.subscribe("SIMULATION_TICK", (ev) => {
      if (ev.type === "SIMULATION_TICK") {
        setTickCount(ev.tickNumber);
        syncStateFromEngine();
      }
    });

    // Subscribe to simulation status
    const unsubStatus = roverEventBus.subscribe("SIMULATION_STATUS_CHANGED", (ev) => {
      if (ev.type === "SIMULATION_STATUS_CHANGED") {
        setIsEngineRunning(ev.isRunning);
      }
    });

    return () => {
      unsubTelemetry();
      unsubState();
      unsubTick();
      unsubStatus();
    };
  }, [syncStateFromEngine]);

  // Simulation Controls Handlers
  const handleTogglePlay = async () => {
    if (roverSimulationEngine.isRunning()) {
      await backendApiClient.pauseSimulation();
    } else {
      await backendApiClient.startSimulation();
    }
    syncStateFromEngine();
  };

  const handleResetEngine = async () => {
    await backendApiClient.resetSimulation();
    setTickCount(0);
    syncStateFromEngine();
  };

  const handleFleetEmergencyStop = () => {
    roverSimulationEngine.emergencyStopFleet("Operator initiated master emergency stop on all rovers");
    rovers.forEach((r) => {
      backendApiClient.commandRover(r.id, "EMERGENCY_STOP", undefined, "Master emergency stop");
    });
    syncStateFromEngine();
  };

  // Rover Individual Actions
  const handlePauseRover = async (rover: SimulatedRover) => {
    await backendApiClient.commandRover(rover.id, "PAUSE", undefined, "Operator manual pause");
    syncStateFromEngine();
  };

  const handleResumeRover = async (rover: SimulatedRover) => {
    await backendApiClient.commandRover(rover.id, "RESUME", undefined, "Operator resumed rover");
    syncStateFromEngine();
  };

  const handleOpenAssignMission = (rover: SimulatedRover) => {
    setTargetRover(rover);
    setModalMode("ASSIGN_MISSION");
  };

  const handleOpenReturnBase = (rover: SimulatedRover) => {
    setTargetRover(rover);
    setModalMode("RETURN_BASE");
  };

  const handleOpenEmergencyStop = (rover: SimulatedRover) => {
    setTargetRover(rover);
    setModalMode("EMERGENCY_STOP");
  };

  const handleOpenResetEStop = (rover: SimulatedRover) => {
    setTargetRover(rover);
    setModalMode("RESET_ESTOP");
  };

  // Modal Confirmations
  const handleConfirmAssignMission = async (roverId: string, missionId: string) => {
    const res = await backendApiClient.assignMission(missionId, roverId);
    if (!res.success && res.message) {
      alert(res.message);
    }
    syncStateFromEngine();
  };

  const handleConfirmEmergencyStop = async (roverId: string, reason: string) => {
    await backendApiClient.commandRover(roverId, "EMERGENCY_STOP", undefined, reason);
    syncStateFromEngine();
  };

  const handleConfirmReturnBase = async (roverId: string) => {
    await backendApiClient.commandRover(roverId, "RETURN_BASE", undefined, "Operator recalled rover");
    syncStateFromEngine();
  };

  const handleConfirmResetEStop = async (roverId: string, notes: string) => {
    await backendApiClient.commandRover(roverId, "RESET_ESTOP", undefined, notes);
    syncStateFromEngine();
  };

  // Navigate to GIS Map
  const handleViewOnMap = (rover: SimulatedRover) => {
    if (onNavigateToMap) {
      onNavigateToMap(rover.id);
    } else {
      router.push(`/app/map`);
    }
  };

  // Filtered rovers
  const filteredRovers = rovers.filter((r) => {
    if (stateFilter === "ALL") return true;
    return r.operatingState === stateFilter;
  });

  // Available scheduled missions for assignment
  const availableMissions = missions.filter(
    (m) => m.status === "Scheduled" || !rovers.some((r) => r.assignedMissionId === m.id)
  );

  return (
    <div className="space-y-6">
      {/* View Header */}
      <SectionHeader
        title="Virtual Autonomous Rover Fleet Management"
        description="Software-only state machine telemetry engine and autonomous pipe navigation testbench."
        badge={
          <StatusBadge
            status={isEngineRunning ? "active" : "online"}
            label={isEngineRunning ? "Simulation Engine Active" : "Simulation Paused"}
            pulse={isEngineRunning}
            size="sm"
          />
        }
        actions={
          <Button
            variant="outline"
            size="sm"
            onClick={() => handleViewOnMap(rovers[0])}
            leftIcon={<Compass className="h-4 w-4 text-cyan-400" />}
          >
            Open Metropolitan GIS Map
          </Button>
        }
      />

      {/* Simulation Controls Bar */}
      <FleetSimulationControls
        isRunning={isEngineRunning}
        tickCount={tickCount}
        onTogglePlay={handleTogglePlay}
        onReset={handleResetEngine}
        onEmergencyStopFleet={handleFleetEmergencyStop}
      />

      {/* Fleet Overview KPIs */}
      <FleetOverviewKpis rovers={rovers} />

      {/* Status Distribution Breakdown */}
      <FleetStatusDistribution
        rovers={rovers}
        selectedFilter={stateFilter}
        onSelectFilter={setStateFilter}
      />

      {/* Main Content Area: Grid + Selected Panel */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 items-start">
        <div className={`${selectedRover ? "lg:col-span-2" : "lg:col-span-3"} space-y-6`}>
          <RoverCardGrid
            rovers={filteredRovers}
            selectedRoverId={selectedRover?.id || null}
            onSelectRover={(r) => setSelectedRover(r)}
            onPauseRover={handlePauseRover}
            onResumeRover={handleResumeRover}
            onReturnBase={handleOpenReturnBase}
            onEmergencyStop={handleOpenEmergencyStop}
            onAssignMission={handleOpenAssignMission}
          />
        </div>

        {/* Selected Rover Detail Inspector Drawer */}
        {selectedRover && (
          <div className="lg:col-span-1 sticky top-6">
            <RoverSelectedPanel
              rover={selectedRover}
              transitions={transitions}
              onClose={() => setSelectedRover(null)}
              onViewOnMap={handleViewOnMap}
              onClearEStop={handleOpenResetEStop}
            />
          </div>
        )}
      </div>

      {/* Event Bus Audit Trail */}
      <FleetEventLog selectedRoverId={selectedRover?.id || null} />

      {/* Control Confirmation Dialog Modal */}
      <RoverControlModal
        rover={targetRover}
        mode={modalMode}
        availableMissions={availableMissions}
        onClose={() => {
          setModalMode(null);
          setTargetRover(null);
        }}
        onConfirmAssignMission={handleConfirmAssignMission}
        onConfirmEmergencyStop={handleConfirmEmergencyStop}
        onConfirmReturnBase={handleConfirmReturnBase}
        onConfirmResetEStop={handleConfirmResetEStop}
      />
    </div>
  );
}
