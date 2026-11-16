import {
  SimulatedRover,
  RoverOperatingState,
  SimulatedMission,
  RoverStateTransitionRecord,
} from "./types";
import {
  executeTransition,
  mapOperatingStateToStatus,
  isValidTransition,
} from "./roverStateMachine";
import {
  RoverKinematicState,
  updateRoverTelemetryTick,
  getRouteProfileForSegment,
} from "./roverMovementEngine";
import {
  roverEventBus,
  RoverSimulationEvent,
} from "./roverEventBus";

// Initial baseline simulated rovers from Task 03
const INITIAL_ROVERS: SimulatedRover[] = [
  {
    isSimulated: true,
    source: "VIRTUAL_SIMULATION_ENGINE",
    simulatedAt: new Date().toISOString(),
    id: "ROV-AQUA-01",
    name: "Triton-1 Crawler",
    model: "In-Pipe Acoustic Crawler MK-IV",
    status: "ACTIVE",
    operatingState: "INSPECTING",
    connectionStatus: "ONLINE",
    batteryPercentage: 86,
    distanceTravelledKm: 14.8,
    currentMission: "Acoustic Survey Segment NY-402",
    assignedMissionId: "MSN-2026-042",
    currentLocation: {
      stationName: "Sector 4 — Station 1200m",
      latitude: 40.7128,
      longitude: -74.006,
      pipeSegmentId: "PIPE-SEC-4B-92",
      routeProgressPct: 65,
    },
    lastCommunication: "1s ago",
    lastHeartbeatTimestamp: new Date().toISOString(),
    kinematics: {
      velocityMps: 0.28,
      headingDeg: 178.4,
      targetSpeedMps: 0.28,
    },
    diagnostics: {
      internalTempC: 31.4,
      motorTempC: 38.5,
      motorCurrentAmps: 1.85,
      signalRssiDbm: -64,
    },
    payloadSensors: {
      acousticSplDb: 46.2,
      dominantFreqHz: 1240,
      groundMoisturePct: 18.5,
    },
  },
  {
    isSimulated: true,
    source: "VIRTUAL_SIMULATION_ENGINE",
    simulatedAt: new Date().toISOString(),
    id: "ROV-AQUA-02",
    name: "Nautilus Ground Scout",
    model: "Autonomous Ground Rover G-200",
    status: "ACTIVE",
    operatingState: "MOVING",
    connectionStatus: "ONLINE",
    batteryPercentage: 92,
    distanceTravelledKm: 8.4,
    currentMission: "Manhole Surface Acoustic Grid Scan",
    assignedMissionId: "MSN-2026-043",
    currentLocation: {
      stationName: "East Avenue — Valve Box 12",
      latitude: 40.7145,
      longitude: -74.0021,
      pipeSegmentId: "PIPE-IND-1A-04",
      routeProgressPct: 42,
    },
    lastCommunication: "1s ago",
    lastHeartbeatTimestamp: new Date().toISOString(),
    kinematics: {
      velocityMps: 0.55,
      headingDeg: 92.1,
      targetSpeedMps: 0.55,
    },
    diagnostics: {
      internalTempC: 28.9,
      motorTempC: 34.2,
      motorCurrentAmps: 2.1,
      signalRssiDbm: -58,
    },
    payloadSensors: {
      acousticSplDb: 38.1,
      dominantFreqHz: 420,
      groundMoisturePct: 12.0,
    },
  },
  {
    isSimulated: true,
    source: "VIRTUAL_SIMULATION_ENGINE",
    simulatedAt: new Date().toISOString(),
    id: "ROV-AQUA-03",
    name: "Hydra Pipe Probe",
    model: "Micro-Submersible Sewer & Pipe Sonar",
    status: "ONLINE",
    operatingState: "IDLE",
    connectionStatus: "ONLINE",
    batteryPercentage: 74,
    distanceTravelledKm: 5.1,
    currentMission: "Standby Patrol Patrol Route 3",
    assignedMissionId: null,
    currentLocation: {
      stationName: "Northern Gate Pump Station",
      latitude: 40.7198,
      longitude: -74.0089,
      pipeSegmentId: "PIPE-RES-3C-11",
      routeProgressPct: 0,
    },
    lastCommunication: "5s ago",
    lastHeartbeatTimestamp: new Date().toISOString(),
    kinematics: {
      velocityMps: 0.0,
      headingDeg: 0.0,
      targetSpeedMps: 0.0,
    },
    diagnostics: {
      internalTempC: 26.5,
      motorTempC: 24.8,
      motorCurrentAmps: 0.4,
      signalRssiDbm: -72,
    },
    payloadSensors: {
      acousticSplDb: 34.0,
      dominantFreqHz: 180,
      groundMoisturePct: 10.4,
    },
  },
  {
    isSimulated: true,
    source: "VIRTUAL_SIMULATION_ENGINE",
    simulatedAt: new Date().toISOString(),
    id: "ROV-AQUA-04",
    name: "Aquila Surface Drone",
    model: "Overhead Thermal Leak Mapper",
    status: "ACTIVE",
    operatingState: "RETURNING",
    connectionStatus: "DEGRADED",
    batteryPercentage: 24,
    distanceTravelledKm: 19.3,
    currentMission: "Returning to Docking Cradle B",
    assignedMissionId: null,
    currentLocation: {
      stationName: "Harbor Transit Line B",
      latitude: 40.7091,
      longitude: -74.0115,
      pipeSegmentId: "PIPE-HRB-02-19",
      routeProgressPct: 70,
    },
    lastCommunication: "2s ago",
    lastHeartbeatTimestamp: new Date().toISOString(),
    kinematics: {
      velocityMps: 0.85,
      headingDeg: 270.0,
      targetSpeedMps: 0.85,
    },
    diagnostics: {
      internalTempC: 39.8,
      motorTempC: 45.1,
      motorCurrentAmps: 3.4,
      signalRssiDbm: -82,
    },
    payloadSensors: {
      acousticSplDb: 40.5,
      dominantFreqHz: 850,
      groundMoisturePct: 22.1,
    },
  },
  {
    isSimulated: true,
    source: "VIRTUAL_SIMULATION_ENGINE",
    simulatedAt: new Date().toISOString(),
    id: "ROV-AQUA-05",
    name: "Scylla Depth Unit",
    model: "Heavy Deep-Trunk Crawler",
    status: "OFFLINE",
    operatingState: "OFFLINE",
    connectionStatus: "OFFLINE",
    batteryPercentage: 0,
    distanceTravelledKm: 2.2,
    currentMission: "Scheduled Depot Maintenance",
    assignedMissionId: null,
    currentLocation: {
      stationName: "Central Maintenance Facility Bay 3",
      latitude: 40.7040,
      longitude: -74.0060,
      pipeSegmentId: "PIPE-SEC-4A-10",
      routeProgressPct: 0,
    },
    lastCommunication: "2h ago",
    lastHeartbeatTimestamp: new Date().toISOString(),
    kinematics: {
      velocityMps: 0.0,
      headingDeg: 0.0,
      targetSpeedMps: 0.0,
    },
    diagnostics: {
      internalTempC: 22.0,
      motorTempC: 22.0,
      motorCurrentAmps: 0.0,
      signalRssiDbm: -110,
    },
    payloadSensors: {
      acousticSplDb: 0.0,
      dominantFreqHz: 0,
      groundMoisturePct: 0.0,
    },
  },
];

const INITIAL_MISSIONS: SimulatedMission[] = [
  {
    isSimulated: true,
    source: "VIRTUAL_SIMULATION_ENGINE",
    simulatedAt: new Date().toISOString(),
    id: "MSN-2026-042",
    assignedRoverId: "ROV-AQUA-01",
    assignedRoverName: "Triton-1 Crawler",
    missionType: "Acoustic Pipe Survey",
    progressPercentage: 68,
    status: "In Progress",
    startTime: "14:15 UTC (1h 25m elapsed)",
    estimatedCompletionTime: "16:00 UTC (~20m remaining)",
    targetSegmentId: "PIPE-SEC-4B-92",
    waypointCount: 24,
    completedWaypoints: 16,
  },
  {
    isSimulated: true,
    source: "VIRTUAL_SIMULATION_ENGINE",
    simulatedAt: new Date().toISOString(),
    id: "MSN-2026-043",
    assignedRoverId: "ROV-AQUA-02",
    assignedRoverName: "Nautilus Ground Scout",
    missionType: "Emergency Intercept",
    progressPercentage: 42,
    status: "In Progress",
    startTime: "15:00 UTC (40m elapsed)",
    estimatedCompletionTime: "16:30 UTC (~50m remaining)",
    targetSegmentId: "PIPE-IND-1A-04",
    waypointCount: 12,
    completedWaypoints: 5,
  },
  {
    isSimulated: true,
    source: "VIRTUAL_SIMULATION_ENGINE",
    simulatedAt: new Date().toISOString(),
    id: "MSN-2026-044",
    assignedRoverId: "ROV-AQUA-03",
    assignedRoverName: "Hydra Pipe Probe",
    missionType: "Pressure Transient Test",
    progressPercentage: 0,
    status: "Scheduled",
    startTime: "17:00 UTC (in 1h 20m)",
    estimatedCompletionTime: "18:45 UTC",
    targetSegmentId: "PIPE-RES-3C-11",
    waypointCount: 18,
    completedWaypoints: 0,
  },
];

export class RoverSimulationEngine {
  private static instance: RoverSimulationEngine | null = null;

  private rovers: Map<string, SimulatedRover> = new Map();
  private kinematicStates: Map<string, RoverKinematicState> = new Map();
  private missions: Map<string, SimulatedMission> = new Map();
  private transitionHistory: RoverStateTransitionRecord[] = [];

  private timerId: NodeJS.Timeout | null = null;
  private isEngineRunning = false;
  private tickIntervalMs = 1000;
  private tickCount = 0;

  private constructor() {
    this.reset();
  }

  public static getInstance(): RoverSimulationEngine {
    if (!RoverSimulationEngine.instance) {
      RoverSimulationEngine.instance = new RoverSimulationEngine();
    }
    return RoverSimulationEngine.instance;
  }

  /**
   * Resets entire simulation state to pristine default values.
   */
  public reset(): void {
    this.pause();
    this.rovers.clear();
    this.kinematicStates.clear();
    this.missions.clear();
    this.transitionHistory = [];
    this.tickCount = 0;

    // Load initial rovers
    INITIAL_ROVERS.forEach((r) => {
      this.rovers.set(r.id, JSON.parse(JSON.stringify(r)));
    });

    // Initialize kinematic states
    this.kinematicStates.set("ROV-AQUA-01", {
      roverId: "ROV-AQUA-01",
      segmentId: "PIPE-SEC-4B-92",
      currentDistanceM: 1200,
      direction: 1,
      targetSpeedMps: 0.28,
      totalDistanceTravelledM: 14800,
    });
    this.kinematicStates.set("ROV-AQUA-02", {
      roverId: "ROV-AQUA-02",
      segmentId: "PIPE-IND-1A-04",
      currentDistanceM: 350,
      direction: 1,
      targetSpeedMps: 0.55,
      totalDistanceTravelledM: 8400,
    });
    this.kinematicStates.set("ROV-AQUA-03", {
      roverId: "ROV-AQUA-03",
      segmentId: "PIPE-RES-3C-11",
      currentDistanceM: 0,
      direction: 1,
      targetSpeedMps: 0,
      totalDistanceTravelledM: 5100,
    });
    this.kinematicStates.set("ROV-AQUA-04", {
      roverId: "ROV-AQUA-04",
      segmentId: "PIPE-HRB-02-19",
      currentDistanceM: 540,
      direction: -1,
      targetSpeedMps: 0.85,
      totalDistanceTravelledM: 19300,
    });
    this.kinematicStates.set("ROV-AQUA-05", {
      roverId: "ROV-AQUA-05",
      segmentId: "PIPE-SEC-4A-10",
      currentDistanceM: 0,
      direction: 1,
      targetSpeedMps: 0,
      totalDistanceTravelledM: 2200,
    });

    // Load initial missions
    INITIAL_MISSIONS.forEach((m) => {
      this.missions.set(m.id, JSON.parse(JSON.stringify(m)));
    });

    roverEventBus.publish({
      id: `SIM-RESET-${Date.now()}`,
      type: "SIMULATION_STATUS_CHANGED",
      isRunning: false,
      intervalMs: this.tickIntervalMs,
      timestamp: new Date().toISOString(),
      isSimulated: true,
      provenance: "VIRTUAL_SIMULATION_EVENT_BUS",
    });
  }

  /**
   * Starts or resumes the periodic simulation tick loop.
   */
  public start(): void {
    if (this.isEngineRunning) return;
    this.isEngineRunning = true;

    this.timerId = setInterval(() => {
      this.executeTick();
    }, this.tickIntervalMs);

    roverEventBus.publish({
      id: `SIM-START-${Date.now()}`,
      type: "SIMULATION_STATUS_CHANGED",
      isRunning: true,
      intervalMs: this.tickIntervalMs,
      timestamp: new Date().toISOString(),
      isSimulated: true,
      provenance: "VIRTUAL_SIMULATION_EVENT_BUS",
    });
  }

  /**
   * Pauses simulation tick loop.
   */
  public pause(): void {
    if (!this.isEngineRunning) return;
    this.isEngineRunning = false;
    if (this.timerId) {
      clearInterval(this.timerId);
      this.timerId = null;
    }

    roverEventBus.publish({
      id: `SIM-PAUSE-${Date.now()}`,
      type: "SIMULATION_STATUS_CHANGED",
      isRunning: false,
      intervalMs: this.tickIntervalMs,
      timestamp: new Date().toISOString(),
      isSimulated: true,
      provenance: "VIRTUAL_SIMULATION_EVENT_BUS",
    });
  }

  public isRunning(): boolean {
    return this.isEngineRunning;
  }

  /**
   * Single discrete simulation step.
   */
  public executeTick(): void {
    this.tickCount++;
    const deltaSeconds = this.tickIntervalMs / 1000;
    let activeCount = 0;

    this.rovers.forEach((rover, roverId) => {
      const kinematic = this.kinematicStates.get(roverId);
      if (!kinematic) return;

      if (rover.operatingState === "MOVING" || rover.operatingState === "INSPECTING" || rover.operatingState === "RETURNING") {
        activeCount++;
      }

      // Safety Interlocks
      // 1. Low battery safety return-to-base interlock
      if (rover.batteryPercentage <= 12 && (rover.operatingState === "MOVING" || rover.operatingState === "INSPECTING")) {
        this.commandRoverState(
          roverId,
          "RETURNING",
          "Low battery safety interlock triggered (<12%). Returning to base charging cradle.",
          "SAFETY_INTERLOCK"
        );
      }

      // 2. High motor temperature protection interlock
      if (rover.diagnostics.motorTempC >= 58.0 && rover.operatingState !== "PAUSED" && rover.operatingState !== "EMERGENCY_STOP") {
        this.commandRoverState(
          roverId,
          "PAUSED",
          `High motor temperature safety cut-off (${rover.diagnostics.motorTempC}°C >= 58°C). Pausing for cool-down.`,
          "SAFETY_INTERLOCK"
        );
      }

      const { updatedRover, updatedKinematics, eventOccurred } = updateRoverTelemetryTick(
        rover,
        kinematic,
        deltaSeconds
      );

      this.rovers.set(roverId, updatedRover);
      this.kinematicStates.set(roverId, updatedKinematics);

      // Handle Route Completion / Base Return
      if (eventOccurred === "ROUTE_END_REACHED") {
        if (updatedRover.operatingState === "MOVING" || updatedRover.operatingState === "INSPECTING") {
          // If on a mission, complete mission and initiate return
          if (updatedRover.assignedMissionId) {
            this.completeMission(updatedRover.assignedMissionId);
          }
          this.commandRoverState(
            roverId,
            "RETURNING",
            "Pipeline endpoint reached. Automatic return to base initiated.",
            "AUTONOMOUS_CONTROLLER"
          );
        }
      } else if (eventOccurred === "BASE_REACHED") {
        if (updatedRover.operatingState === "RETURNING") {
          this.commandRoverState(
            roverId,
            "CHARGING",
            "Arrived at pipeline access station docking port. Charging sequence initiated.",
            "AUTONOMOUS_CONTROLLER"
          );
        }
      }

      // Synchronize mission progress if rover is on an active mission
      if (updatedRover.assignedMissionId && this.missions.has(updatedRover.assignedMissionId)) {
        const mission = this.missions.get(updatedRover.assignedMissionId)!;
        if (mission.status === "In Progress") {
          const route = getRouteProfileForSegment(updatedKinematics.segmentId);
          if (route) {
            const fraction = Math.min(1, Math.max(0, updatedKinematics.currentDistanceM / route.totalLengthM));
            mission.progressPercentage = Math.round(fraction * 100);
            mission.completedWaypoints = Math.round(fraction * mission.waypointCount);
            this.missions.set(mission.id, mission);
          }
        }
      }

      // Publish live telemetry update
      roverEventBus.publish({
        id: `TEL-${roverId}-${Date.now()}`,
        type: "ROVER_TELEMETRY_UPDATED",
        roverId,
        rover: updatedRover,
        timestamp: new Date().toISOString(),
        isSimulated: true,
        provenance: "VIRTUAL_SIMULATION_EVENT_BUS",
      });
    });

    // Publish tick pulse
    roverEventBus.publish({
      id: `TICK-${this.tickCount}-${Date.now()}`,
      type: "SIMULATION_TICK",
      tickNumber: this.tickCount,
      activeRoverCount: activeCount,
      timestamp: new Date().toISOString(),
      isSimulated: true,
      provenance: "VIRTUAL_SIMULATION_EVENT_BUS",
    });
  }

  /**
   * Commands a rover state transition with strict validation, event logging, and status mapping.
   */
  public commandRoverState(
    roverId: string,
    targetState: RoverOperatingState,
    reason: string,
    triggeredBy: "OPERATOR" | "AUTONOMOUS_CONTROLLER" | "SAFETY_INTERLOCK" | "SIMULATION_ENGINE" = "OPERATOR"
  ): { success: boolean; error?: string } {
    const rover = this.rovers.get(roverId);
    if (!rover) {
      return { success: false, error: `Rover ${roverId} not found.` };
    }

    const result = executeTransition(roverId, rover.operatingState, targetState, reason, triggeredBy);
    if (!result.success || !result.transition) {
      return { success: false, error: result.error };
    }

    // Apply state change
    rover.operatingState = targetState;
    rover.status = mapOperatingStateToStatus(targetState);

    // If stopping or returning, adjust kinematic target
    const kinematic = this.kinematicStates.get(roverId);
    if (kinematic) {
      if (targetState === "RETURNING") {
        kinematic.direction = -1;
      } else if (targetState === "MOVING" || targetState === "INSPECTING") {
        kinematic.direction = 1;
      }
    }

    if (targetState === "EMERGENCY_STOP" || targetState === "ERROR" || targetState === "OFFLINE" || targetState === "IDLE") {
      rover.kinematics.velocityMps = 0;
      rover.kinematics.targetSpeedMps = 0;
      rover.diagnostics.motorCurrentAmps = 0;
    }

    this.rovers.set(roverId, rover);
    this.transitionHistory.unshift(result.transition);

    // Publish event
    roverEventBus.publish({
      id: `EV-TR-${Date.now()}`,
      type: "ROVER_STATE_CHANGED",
      roverId,
      transition: result.transition,
      timestamp: new Date().toISOString(),
      isSimulated: true,
      provenance: "VIRTUAL_SIMULATION_EVENT_BUS",
    });

    if (targetState === "EMERGENCY_STOP") {
      roverEventBus.publish({
        id: `ESTOP-${roverId}-${Date.now()}`,
        type: "ROVER_EMERGENCY_STOP",
        roverId,
        reason,
        triggeredBy,
        timestamp: new Date().toISOString(),
        isSimulated: true,
        provenance: "VIRTUAL_SIMULATION_EVENT_BUS",
      });
    }

    return { success: true };
  }

  /**
   * Pauses individual rover.
   */
  public pauseRover(roverId: string, reason = "Operator requested manual pause"): { success: boolean; error?: string } {
    return this.commandRoverState(roverId, "PAUSED", reason, "OPERATOR");
  }

  /**
   * Resumes individual rover from pause.
   */
  public resumeRover(roverId: string, reason = "Operator resumed operation"): { success: boolean; error?: string } {
    const rover = this.rovers.get(roverId);
    if (!rover) return { success: false, error: "Rover not found" };

    const targetState: RoverOperatingState = rover.assignedMissionId ? "INSPECTING" : "MOVING";
    return this.commandRoverState(roverId, targetState, reason, "OPERATOR");
  }

  /**
   * Commands rover to return to base.
   */
  public returnRoverToBase(roverId: string, reason = "Operator recalled rover to base cradle"): { success: boolean; error?: string } {
    return this.commandRoverState(roverId, "RETURNING", reason, "OPERATOR");
  }

  /**
   * Emergency Stop for an individual rover.
   */
  public emergencyStopRover(roverId: string, reason = "Immediate emergency stop triggered"): { success: boolean; error?: string } {
    return this.commandRoverState(roverId, "EMERGENCY_STOP", reason, "SAFETY_INTERLOCK");
  }

  /**
   * Fleet-wide Emergency Stop.
   */
  public emergencyStopFleet(reason = "Fleet-wide master emergency stop triggered"): void {
    this.rovers.forEach((_, id) => {
      this.commandRoverState(id, "EMERGENCY_STOP", reason, "SAFETY_INTERLOCK");
    });
  }

  /**
   * Clears emergency stop and resets rover to IDLE state.
   */
  public resetEmergencyStop(roverId: string, operatorNotes = "Safety interlocks verified cleared"): { success: boolean; error?: string } {
    const rover = this.rovers.get(roverId);
    if (!rover) return { success: false, error: "Rover not found" };
    if (rover.operatingState !== "EMERGENCY_STOP") {
      return { success: false, error: `Rover is not in EMERGENCY_STOP (current: ${rover.operatingState}).` };
    }

    return this.commandRoverState(roverId, "IDLE", `Administrative safety reset: ${operatorNotes}`, "OPERATOR");
  }

  /**
   * Assigns an available idle rover to a scheduled mission.
   */
  public assignMission(
    roverId: string,
    missionId: string
  ): { success: boolean; error?: string } {
    const rover = this.rovers.get(roverId);
    if (!rover) return { success: false, error: `Rover ${roverId} not found.` };

    if (rover.operatingState !== "IDLE") {
      return {
        success: false,
        error: `Cannot assign mission to rover ${roverId}: Rover must be in IDLE state (current: ${rover.operatingState}).`,
      };
    }

    const mission = this.missions.get(missionId);
    if (!mission) {
      return { success: false, error: `Mission ${missionId} not found.` };
    }

    // Check duplicate assignment
    let alreadyAssigned = false;
    this.rovers.forEach((r) => {
      if (r.assignedMissionId === missionId && r.id !== roverId && r.operatingState !== "IDLE") {
        alreadyAssigned = true;
      }
    });

    if (alreadyAssigned) {
      return {
        success: false,
        error: `Mission ${missionId} is already actively assigned to another rover.`,
      };
    }

    // Connect rover and mission
    rover.assignedMissionId = missionId;
    rover.currentMission = `${mission.missionType} (${mission.id})`;
    rover.currentLocation.pipeSegmentId = mission.targetSegmentId;

    mission.assignedRoverId = rover.id;
    mission.assignedRoverName = rover.name;
    mission.status = "In Progress";
    mission.startTime = `${new Date().toISOString().substring(11, 16)} UTC (Just started)`;

    // Update kinematic segment
    const kinematic = this.kinematicStates.get(roverId);
    if (kinematic) {
      kinematic.segmentId = mission.targetSegmentId;
      kinematic.currentDistanceM = 0;
      kinematic.direction = 1;
    }

    this.missions.set(missionId, mission);
    this.rovers.set(roverId, rover);

    // Transition rover to INSPECTING
    this.commandRoverState(
      roverId,
      "INSPECTING",
      `Mission ${missionId} assigned: ${mission.missionType}`,
      "OPERATOR"
    );

    roverEventBus.publish({
      id: `MSN-EV-${Date.now()}`,
      type: "ROVER_MISSION_EVENT",
      roverId,
      missionId,
      action: "ASSIGNED",
      details: `Rover ${rover.name} assigned to mission ${mission.missionType} on segment ${mission.targetSegmentId}.`,
      timestamp: new Date().toISOString(),
      isSimulated: true,
      provenance: "VIRTUAL_SIMULATION_EVENT_BUS",
    });

    return { success: true };
  }

  /**
   * Completes mission.
   */
  public completeMission(missionId: string): void {
    const mission = this.missions.get(missionId);
    if (!mission) return;

    mission.status = "Completed";
    mission.progressPercentage = 100;
    mission.completedWaypoints = mission.waypointCount;
    this.missions.set(missionId, mission);

    roverEventBus.publish({
      id: `MSN-COMP-${Date.now()}`,
      type: "ROVER_MISSION_EVENT",
      roverId: mission.assignedRoverId,
      missionId,
      action: "COMPLETED",
      details: `Mission ${missionId} (${mission.missionType}) successfully completed 100% of pipeline waypoints.`,
      timestamp: new Date().toISOString(),
      isSimulated: true,
      provenance: "VIRTUAL_SIMULATION_EVENT_BUS",
    });
  }

  /**
   * Cancels mission.
   */
  public cancelMission(missionId: string, reason = "Operator cancelled mission"): { success: boolean; error?: string } {
    const mission = this.missions.get(missionId);
    if (!mission) return { success: false, error: "Mission not found" };

    mission.status = "Cancelled";
    this.missions.set(missionId, mission);

    if (mission.assignedRoverId) {
      const rover = this.rovers.get(mission.assignedRoverId);
      if (rover && rover.assignedMissionId === missionId) {
        rover.assignedMissionId = null;
        rover.currentMission = "Standby (Mission Cancelled)";
        this.rovers.set(rover.id, rover);
        this.commandRoverState(rover.id, "IDLE", reason, "OPERATOR");
      }
    }

    roverEventBus.publish({
      id: `MSN-CANC-${Date.now()}`,
      type: "ROVER_MISSION_EVENT",
      roverId: mission.assignedRoverId || "UNASSIGNED",
      missionId,
      action: "CANCELLED",
      details: `Mission ${missionId} cancelled: ${reason}`,
      timestamp: new Date().toISOString(),
      isSimulated: true,
      provenance: "VIRTUAL_SIMULATION_EVENT_BUS",
    });

    return { success: true };
  }

  /**
   * Getters (Single Source of Truth)
   */
  public getRovers(): SimulatedRover[] {
    return Array.from(this.rovers.values());
  }

  public getRoverById(id: string): SimulatedRover | null {
    return this.rovers.get(id) || null;
  }

  public getMissions(): SimulatedMission[] {
    return Array.from(this.missions.values());
  }

  public getTransitionHistory(roverId?: string, limit = 50): RoverStateTransitionRecord[] {
    let list = this.transitionHistory;
    if (roverId) {
      list = list.filter((t) => t.roverId === roverId);
    }
    return list.slice(0, limit);
  }
}

// Global Singleton Engine Instance
export const roverSimulationEngine = RoverSimulationEngine.getInstance();

