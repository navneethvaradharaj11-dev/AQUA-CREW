"use client";

import React, { useState } from "react";
import { Modal } from "@/components/ui/Modal";
import { Button } from "@/components/ui/Button";
import { SimulatedRover, SimulatedMission } from "@/services/simulation/types";
import { AlertOctagon, RotateCcw, ClipboardList, ShieldAlert, CheckCircle2 } from "lucide-react";

export type RoverModalMode = "ASSIGN_MISSION" | "EMERGENCY_STOP" | "RETURN_BASE" | "RESET_ESTOP" | null;

export interface RoverControlModalProps {
  rover: SimulatedRover | null;
  mode: RoverModalMode;
  availableMissions: SimulatedMission[];
  onClose: () => void;
  onConfirmAssignMission: (roverId: string, missionId: string) => void;
  onConfirmEmergencyStop: (roverId: string, reason: string) => void;
  onConfirmReturnBase: (roverId: string) => void;
  onConfirmResetEStop: (roverId: string, notes: string) => void;
}

export function RoverControlModal({
  rover,
  mode,
  availableMissions,
  onClose,
  onConfirmAssignMission,
  onConfirmEmergencyStop,
  onConfirmReturnBase,
  onConfirmResetEStop,
}: RoverControlModalProps) {
  const [selectedMissionId, setSelectedMissionId] = useState<string>("");
  const [eStopReason, setEStopReason] = useState<string>("Operator precautionary emergency stop");
  const [resetNotes, setResetNotes] = useState<string>("Simulated safety perimeter verified clear");

  if (!rover || !mode) return null;

  const handleConfirm = () => {
    if (mode === "ASSIGN_MISSION" && selectedMissionId) {
      onConfirmAssignMission(rover.id, selectedMissionId);
    } else if (mode === "EMERGENCY_STOP") {
      onConfirmEmergencyStop(rover.id, eStopReason);
    } else if (mode === "RETURN_BASE") {
      onConfirmReturnBase(rover.id);
    } else if (mode === "RESET_ESTOP") {
      onConfirmResetEStop(rover.id, resetNotes);
    }
    onClose();
  };

  return (
    <Modal
      isOpen={!!mode}
      onClose={onClose}
      title={
        mode === "ASSIGN_MISSION"
          ? `Assign Mission to ${rover.name}`
          : mode === "EMERGENCY_STOP"
          ? `Emergency Stop: ${rover.name} (${rover.id})`
          : mode === "RETURN_BASE"
          ? `Recall ${rover.name} to Base Station`
          : `Clear Emergency Stop: ${rover.name}`
      }
      description="Simulation command confirmation and state interlock verification."
      size="md"
      footer={
        <div className="flex items-center justify-end gap-2 w-full">
          <Button variant="secondary" size="sm" onClick={onClose}>
            Cancel
          </Button>
          <Button
            variant={mode === "EMERGENCY_STOP" ? "destructive" : "primary"}
            size="sm"
            onClick={handleConfirm}
            disabled={mode === "ASSIGN_MISSION" && !selectedMissionId}
          >
            {mode === "ASSIGN_MISSION"
              ? "Confirm & Dispatch Mission"
              : mode === "EMERGENCY_STOP"
              ? "Trigger Emergency Stop"
              : mode === "RETURN_BASE"
              ? "Confirm Recall"
              : "Clear Safety Interlock"}
          </Button>
        </div>
      }
    >
      <div className="space-y-4 text-xs font-mono">
        {/* Simulation Notice */}
        <div className="flex items-center gap-2 p-2.5 rounded-lg border border-amber-900/40 bg-amber-950/20 text-amber-300">
          <ShieldAlert className="h-4 w-4 shrink-0 text-amber-400" />
          <span>SIMULATED COMMAND ONLY • Virtual Rover State Interlock</span>
        </div>

        {/* Mode: ASSIGN MISSION */}
        {mode === "ASSIGN_MISSION" && (
          <div className="space-y-3 font-sans">
            <p className="text-slate-300 text-xs">
              Select an available scheduled inspection mission for <strong className="text-white font-mono">{rover.name}</strong> ({rover.id}). Rover state will transition to <strong className="text-cyan-400 font-mono">INSPECTING</strong>.
            </p>

            <div className="space-y-2">
              <label className="text-[11px] font-mono uppercase text-slate-400 block">
                Scheduled Inspection Missions
              </label>
              <select
                value={selectedMissionId}
                onChange={(e) => setSelectedMissionId(e.target.value)}
                className="w-full bg-slate-900 border border-slate-700 rounded-lg p-2.5 text-xs text-white focus:outline-none focus:border-cyan-500 font-mono"
              >
                <option value="">-- Choose a scheduled mission --</option>
                {availableMissions.map((m) => (
                  <option key={m.id} value={m.id}>
                    {m.id} — {m.missionType} [{m.targetSegmentId}] ({m.waypointCount} waypoints)
                  </option>
                ))}
              </select>
            </div>
          </div>
        )}

        {/* Mode: EMERGENCY STOP */}
        {mode === "EMERGENCY_STOP" && (
          <div className="space-y-3 font-sans">
            <div className="p-3 rounded-lg border border-red-900/50 bg-red-950/20 space-y-1.5 text-red-300 text-xs">
              <div className="flex items-center gap-2 font-bold text-red-200">
                <AlertOctagon className="h-4 w-4 text-red-400" />
                <span>Simulated Emergency Stop Execution</span>
              </div>
              <p className="text-[11px] text-red-300/90 leading-relaxed">
                This action will immediately set velocity to 0.0 m/s, cut motor current to 0.0 A, and transition the rover state to <strong>EMERGENCY_STOP</strong>. The unit cannot resume until explicitly cleared.
              </p>
            </div>

            <div className="space-y-1.5">
              <label className="text-[11px] font-mono uppercase text-slate-400 block">
                Operator Incident Reason
              </label>
              <input
                type="text"
                value={eStopReason}
                onChange={(e) => setEStopReason(e.target.value)}
                className="w-full bg-slate-900 border border-slate-700 rounded-lg p-2.5 text-xs text-white focus:outline-none focus:border-red-500 font-mono"
              />
            </div>
          </div>
        )}

        {/* Mode: RETURN BASE */}
        {mode === "RETURN_BASE" && (
          <div className="space-y-3 font-sans">
            <p className="text-slate-300 text-xs leading-relaxed">
              Confirm recalling <strong className="text-white font-mono">{rover.name}</strong> to its starting docking cradle. The kinematics engine will reverse velocity heading along pipeline <strong className="text-cyan-400 font-mono">{rover.currentLocation.pipeSegmentId}</strong> until Station 0m is reached.
            </p>
          </div>
        )}

        {/* Mode: RESET ESTOP */}
        {mode === "RESET_ESTOP" && (
          <div className="space-y-3 font-sans">
            <p className="text-slate-300 text-xs leading-relaxed">
              Administrative safety clear for <strong className="text-white font-mono">{rover.name}</strong>. This clears the safety interlock and transitions the rover to <strong className="text-emerald-400 font-mono">IDLE</strong>.
            </p>

            <div className="space-y-1.5">
              <label className="text-[11px] font-mono uppercase text-slate-400 block">
                Safety Verification Notes
              </label>
              <input
                type="text"
                value={resetNotes}
                onChange={(e) => setResetNotes(e.target.value)}
                className="w-full bg-slate-900 border border-slate-700 rounded-lg p-2.5 text-xs text-white focus:outline-none focus:border-cyan-500 font-mono"
              />
            </div>
          </div>
        )}
      </div>
    </Modal>
  );
}
