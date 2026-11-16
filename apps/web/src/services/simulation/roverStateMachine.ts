import {
  RoverOperatingState,
  RoverOperationalStatus,
  RoverStateTransitionRecord,
} from "./types";

/**
 * Valid state transition matrix for AQUA CREW autonomous rover simulation.
 * Rejects illegal transitions (e.g., CHARGING -> INSPECTING without leaving dock,
 * or EMERGENCY_STOP -> MOVING without administrative safety reset).
 */
export const VALID_ROVER_TRANSITIONS: Record<RoverOperatingState, readonly RoverOperatingState[]> = {
  IDLE: ["MOVING", "INSPECTING", "CHARGING", "OFFLINE", "ERROR", "EMERGENCY_STOP"],
  MOVING: ["INSPECTING", "PAUSED", "RETURNING", "IDLE", "ERROR", "EMERGENCY_STOP", "OFFLINE"],
  INSPECTING: ["PAUSED", "MOVING", "RETURNING", "IDLE", "ERROR", "EMERGENCY_STOP", "OFFLINE"],
  PAUSED: ["MOVING", "INSPECTING", "RETURNING", "IDLE", "EMERGENCY_STOP", "OFFLINE", "ERROR"],
  RETURNING: ["CHARGING", "IDLE", "PAUSED", "EMERGENCY_STOP", "OFFLINE", "ERROR"],
  CHARGING: ["IDLE", "OFFLINE", "ERROR", "EMERGENCY_STOP"],
  OFFLINE: ["IDLE", "CHARGING"],
  ERROR: ["IDLE", "RETURNING", "OFFLINE", "EMERGENCY_STOP"],
  EMERGENCY_STOP: ["IDLE", "ERROR", "OFFLINE"], // Requires explicit safety clear to return to IDLE
};

/**
 * Maps granular operating states to high-level operational status badges for backward-compatibility.
 */
export function mapOperatingStateToStatus(state: RoverOperatingState): RoverOperationalStatus {
  switch (state) {
    case "MOVING":
    case "INSPECTING":
      return "ACTIVE";
    case "IDLE":
    case "CHARGING":
      return "ONLINE";
    case "PAUSED":
      return "IDLE";
    case "RETURNING":
      return "ACTIVE";
    case "ERROR":
    case "EMERGENCY_STOP":
      return "WARNING";
    case "OFFLINE":
      return "OFFLINE";
    default:
      return "ONLINE";
  }
}

/**
 * Verifies if a given transition is valid under the state machine rules.
 */
export function isValidTransition(
  currentState: RoverOperatingState,
  targetState: RoverOperatingState
): boolean {
  if (currentState === targetState) return true;
  const allowed = VALID_ROVER_TRANSITIONS[currentState];
  return allowed ? allowed.includes(targetState) : false;
}

export interface TransitionAttemptResult {
  success: boolean;
  error?: string;
  transition?: RoverStateTransitionRecord;
}

/**
 * Validates and records a state transition.
 */
export function executeTransition(
  roverId: string,
  currentState: RoverOperatingState,
  targetState: RoverOperatingState,
  reason: string,
  triggeredBy: "OPERATOR" | "AUTONOMOUS_CONTROLLER" | "SAFETY_INTERLOCK" | "SIMULATION_ENGINE" = "OPERATOR"
): TransitionAttemptResult {
  if (currentState === targetState) {
    return {
      success: true,
      error: `Rover ${roverId} is already in state ${targetState}.`,
    };
  }

  if (!isValidTransition(currentState, targetState)) {
    return {
      success: false,
      error: `Invalid state transition for rover ${roverId}: Cannot transition from ${currentState} to ${targetState}. Valid transitions are: [${VALID_ROVER_TRANSITIONS[currentState]?.join(", ")}].`,
    };
  }

  const transitionRecord: RoverStateTransitionRecord = {
    id: `TR-${Date.now().toString(36).toUpperCase()}-${Math.random().toString(36).substring(2, 6).toUpperCase()}`,
    roverId,
    previousState: currentState,
    newState: targetState,
    timestamp: new Date().toISOString(),
    reason,
    triggeredBy,
    isSimulated: true,
    source: "VIRTUAL_SIMULATION_ENGINE",
  };

  return {
    success: true,
    transition: transitionRecord,
  };
}

