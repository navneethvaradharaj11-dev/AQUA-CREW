import {
  RoverOperatingState,
  RoverStateTransitionRecord,
  SimulatedRover,
} from "./types";

export type RoverEventType =
  | "ROVER_STATE_CHANGED"
  | "ROVER_TELEMETRY_UPDATED"
  | "ROVER_WAYPOINT_REACHED"
  | "ROVER_MISSION_EVENT"
  | "ROVER_EMERGENCY_STOP"
  | "SIMULATION_TICK"
  | "SIMULATION_STATUS_CHANGED";

export interface BaseRoverEvent {
  id: string;
  type: RoverEventType;
  timestamp: string;
  isSimulated: true;
  provenance: "VIRTUAL_SIMULATION_EVENT_BUS";
}

export interface RoverStateChangedEvent extends BaseRoverEvent {
  type: "ROVER_STATE_CHANGED";
  roverId: string;
  transition: RoverStateTransitionRecord;
}

export interface RoverTelemetryUpdatedEvent extends BaseRoverEvent {
  type: "ROVER_TELEMETRY_UPDATED";
  roverId: string;
  rover: SimulatedRover;
}

export interface RoverWaypointReachedEvent extends BaseRoverEvent {
  type: "ROVER_WAYPOINT_REACHED";
  roverId: string;
  missionId: string;
  waypointIndex: number;
  coordinates: [number, number]; // [lng, lat]
}

export interface RoverMissionEvent extends BaseRoverEvent {
  type: "ROVER_MISSION_EVENT";
  roverId: string;
  missionId: string;
  action: "ASSIGNED" | "STARTED" | "PAUSED" | "RESUMED" | "COMPLETED" | "CANCELLED";
  details: string;
}

export interface RoverEmergencyStopEvent extends BaseRoverEvent {
  type: "ROVER_EMERGENCY_STOP";
  roverId: string;
  reason: string;
  triggeredBy: string;
}

export interface SimulationTickEvent extends BaseRoverEvent {
  type: "SIMULATION_TICK";
  tickNumber: number;
  activeRoverCount: number;
}

export interface SimulationStatusChangedEvent extends BaseRoverEvent {
  type: "SIMULATION_STATUS_CHANGED";
  isRunning: boolean;
  intervalMs: number;
}

export type RoverSimulationEvent =
  | RoverStateChangedEvent
  | RoverTelemetryUpdatedEvent
  | RoverWaypointReachedEvent
  | RoverMissionEvent
  | RoverEmergencyStopEvent
  | SimulationTickEvent
  | SimulationStatusChangedEvent;

export type EventListener<T extends RoverSimulationEvent = RoverSimulationEvent> = (event: T) => void;

class RoverEventBus {
  private listeners: Map<RoverEventType | "*", Set<EventListener<any>>> = new Map();
  private eventHistory: RoverSimulationEvent[] = [];
  private readonly maxHistoryLength = 200;

  /**
   * Subscribe to a specific event type, or '*' for all simulation events.
   * Returns an unsubscribe function to guarantee clean resource teardown.
   */
  public subscribe<T extends RoverSimulationEvent = RoverSimulationEvent>(
    eventType: RoverEventType | "*",
    listener: EventListener<T>
  ): () => void {
    if (!this.listeners.has(eventType)) {
      this.listeners.set(eventType, new Set());
    }
    this.listeners.get(eventType)!.add(listener);

    return () => {
      const set = this.listeners.get(eventType);
      if (set) {
        set.delete(listener);
        if (set.size === 0) {
          this.listeners.delete(eventType);
        }
      }
    };
  }

  /**
   * Dispatches a typed event to all registered listeners and saves to the audit ring-buffer.
   */
  public publish(event: RoverSimulationEvent): void {
    this.eventHistory.unshift(event);
    if (this.eventHistory.length > this.maxHistoryLength) {
      this.eventHistory.pop();
    }

    // Notify specific type listeners
    const specificListeners = this.listeners.get(event.type);
    if (specificListeners) {
      specificListeners.forEach((listener) => {
        try {
          listener(event);
        } catch (err) {
          console.error(`[RoverEventBus] Error in listener for ${event.type}:`, err);
        }
      });
    }

    // Notify wildcard listeners
    const wildcardListeners = this.listeners.get("*");
    if (wildcardListeners) {
      wildcardListeners.forEach((listener) => {
        try {
          listener(event);
        } catch (err) {
          console.error(`[RoverEventBus] Error in wildcard listener:`, err);
        }
      });
    }
  }

  /**
   * Retrieves immutable recent event history for audit logs and UI timelines.
   */
  public getHistory(limit = 50, roverId?: string): RoverSimulationEvent[] {
    let filtered = this.eventHistory;
    if (roverId) {
      filtered = filtered.filter((e) => "roverId" in e && e.roverId === roverId);
    }
    return filtered.slice(0, limit);
  }

  /**
   * Clears event history for test resets.
   */
  public clearHistory(): void {
    this.eventHistory = [];
  }
}

// Global Singleton Event Bus instance
export const roverEventBus = new RoverEventBus();

