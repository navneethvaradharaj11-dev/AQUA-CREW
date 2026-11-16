/**
 * AQUA CREW — Task 05 Automated Simulation Engine Test Suite
 * Validates State Machine Transitions, Telemetry Bounds, Movement Geometry,
 * Mission Integration, Safety Interlocks, and Subscription Cleanup.
 */

import {
  isValidTransition,
  executeTransition,
  VALID_ROVER_TRANSITIONS,
  mapOperatingStateToStatus,
} from "../src/services/simulation/roverStateMachine";
import {
  haversineDistanceMeters,
  calculateBearingDeg,
  getRouteProfileForSegment,
  interpolateRoutePosition,
  updateRoverTelemetryTick,
} from "../src/services/simulation/roverMovementEngine";
import {
  RoverSimulationEngine,
} from "../src/services/simulation/roverSimulationEngine";
import {
  roverEventBus,
} from "../src/services/simulation/roverEventBus";
import { SimulatedRover, RoverOperatingState } from "../src/services/simulation/types";

let passedTests = 0;
let failedTests = 0;

function assert(condition: boolean, message: string) {
  if (!condition) {
    console.error(`❌ FAIL: ${message}`);
    failedTests++;
    throw new Error(`Assertion failed: ${message}`);
  } else {
    console.log(`✅ PASS: ${message}`);
    passedTests++;
  }
}

async function runAllTests() {
  console.log("==================================================================");
  console.log("       AQUA CREW TASK 05: SIMULATION TEST RUNNER                 ");
  console.log("==================================================================\n");

  // ========================================================================
  // TEST SUITE 1: ROVER STATE MACHINE TRANSITIONS
  // ========================================================================
  console.log("--- 1. Testing Rover State Machine & Transition Matrix ---");

  // 1.1 Valid Transitions
  assert(isValidTransition("IDLE", "MOVING"), "IDLE can transition to MOVING");
  assert(isValidTransition("MOVING", "INSPECTING"), "MOVING can transition to INSPECTING");
  assert(isValidTransition("INSPECTING", "PAUSED"), "INSPECTING can transition to PAUSED");
  assert(isValidTransition("PAUSED", "MOVING"), "PAUSED can resume to MOVING");
  assert(isValidTransition("MOVING", "RETURNING"), "MOVING can transition to RETURNING");
  assert(isValidTransition("RETURNING", "CHARGING"), "RETURNING can transition to CHARGING at base");
  assert(isValidTransition("CHARGING", "IDLE"), "CHARGING can transition to IDLE when charged");
  assert(isValidTransition("IDLE", "EMERGENCY_STOP"), "IDLE can enter EMERGENCY_STOP");
  assert(isValidTransition("MOVING", "EMERGENCY_STOP"), "MOVING can enter EMERGENCY_STOP");

  // 1.2 Invalid Transitions Rejected
  assert(!isValidTransition("CHARGING", "INSPECTING"), "CHARGING cannot jump to INSPECTING without leaving dock");
  assert(!isValidTransition("EMERGENCY_STOP", "MOVING"), "EMERGENCY_STOP cannot resume directly to MOVING without reset");
  assert(!isValidTransition("OFFLINE", "MOVING"), "OFFLINE cannot transition directly to MOVING");
  assert(!isValidTransition("OFFLINE", "INSPECTING"), "OFFLINE cannot transition directly to INSPECTING");

  // 1.3 Transition Recording
  const trResult = executeTransition(
    "ROV-AQUA-03",
    "IDLE",
    "MOVING",
    "Starting patrol route",
    "OPERATOR"
  );
  assert(trResult.success === true, "executeTransition succeeds for valid transition");
  assert(trResult.transition !== undefined, "executeTransition generates transition record");
  assert(trResult.transition?.previousState === "IDLE", "Record captures previousState");
  assert(trResult.transition?.newState === "MOVING", "Record captures newState");
  assert(trResult.transition?.isSimulated === true, "Record contains simulated provenance flag");

  // 1.4 Status Mapping
  assert(mapOperatingStateToStatus("MOVING") === "ACTIVE", "MOVING maps to status ACTIVE");
  assert(mapOperatingStateToStatus("INSPECTING") === "ACTIVE", "INSPECTING maps to status ACTIVE");
  assert(mapOperatingStateToStatus("IDLE") === "ONLINE", "IDLE maps to status ONLINE");
  assert(mapOperatingStateToStatus("PAUSED") === "IDLE", "PAUSED maps to status IDLE");
  assert(mapOperatingStateToStatus("EMERGENCY_STOP") === "WARNING", "EMERGENCY_STOP maps to status WARNING");
  assert(mapOperatingStateToStatus("OFFLINE") === "OFFLINE", "OFFLINE maps to status OFFLINE");

  // ========================================================================
  // TEST SUITE 2: TELEMETRY ENGINE & BOUNDS VALIDATION
  // ========================================================================
  console.log("\n--- 2. Testing Telemetry Engine & Bounded Ranges ---");

  const mockRover: SimulatedRover = {
    isSimulated: true,
    source: "VIRTUAL_SIMULATION_ENGINE",
    simulatedAt: new Date().toISOString(),
    id: "ROV-TEST-01",
    name: "Test Unit",
    model: "Test Model",
    status: "ACTIVE",
    operatingState: "MOVING",
    connectionStatus: "ONLINE",
    batteryPercentage: 50,
    distanceTravelledKm: 1.0,
    currentMission: "Test",
    currentLocation: {
      stationName: "Test Station",
      latitude: 40.7128,
      longitude: -74.006,
      pipeSegmentId: "PIPE-SEC-4B-92",
    },
    lastCommunication: "1s ago",
    lastHeartbeatTimestamp: new Date().toISOString(),
    kinematics: { velocityMps: 0.5, headingDeg: 90 },
    diagnostics: { internalTempC: 30, motorTempC: 35, motorCurrentAmps: 1.5, signalRssiDbm: -65 },
    payloadSensors: { acousticSplDb: 40, dominantFreqHz: 500, groundMoisturePct: 15 },
  };

  const kinematicState = {
    roverId: "ROV-TEST-01",
    segmentId: "PIPE-SEC-4B-92",
    currentDistanceM: 500,
    direction: 1 as const,
    targetSpeedMps: 0.55,
    totalDistanceTravelledM: 1000,
  };

  const { updatedRover, updatedKinematics } = updateRoverTelemetryTick(mockRover, kinematicState, 1.0);

  // Validate bounds
  assert(updatedRover.batteryPercentage >= 0 && updatedRover.batteryPercentage <= 100, "Battery percentage strictly bounded 0-100%");
  assert(updatedRover.kinematics.velocityMps >= 0 && updatedRover.kinematics.velocityMps <= 1.5, "Velocity strictly bounded 0-1.5 m/s");
  assert(updatedRover.diagnostics.motorTempC >= 20 && updatedRover.diagnostics.motorTempC <= 75, "Motor temp strictly bounded 20-75°C");
  assert(updatedRover.diagnostics.internalTempC >= 20 && updatedRover.diagnostics.internalTempC <= 50, "Internal temp strictly bounded 20-50°C");
  assert(updatedRover.diagnostics.signalRssiDbm >= -115 && updatedRover.diagnostics.signalRssiDbm <= -40, "Signal RSSI bounded -115 to -40 dBm");
  assert(updatedKinematics.totalDistanceTravelledM >= kinematicState.totalDistanceTravelledM, "Distance travelled monotonically increases");

  // Zero velocity when stopped
  const stoppedRover = { ...mockRover, operatingState: "PAUSED" as RoverOperatingState, kinematics: { ...mockRover.kinematics, velocityMps: 0 } };
  const stoppedKinematics = { ...kinematicState, targetSpeedMps: 0 };
  const { updatedRover: resStopped } = updateRoverTelemetryTick(stoppedRover, stoppedKinematics, 1.0);
  assert(resStopped.kinematics.velocityMps === 0, "Velocity is 0 m/s when PAUSED");

  // ========================================================================
  // TEST SUITE 3: MOVEMENT GEOMETRY & BOUNDARY INTERPOLATION
  // ========================================================================
  console.log("\n--- 3. Testing Movement Geometry & Route Interpolation ---");

  const dist = haversineDistanceMeters([-74.0150, 40.7100], [-73.9960, 40.7155]);
  assert(dist > 1000 && dist < 3000, `Haversine distance calculated accurately (${dist.toFixed(1)}m)`);

  const bearing = calculateBearingDeg([-74.0150, 40.7100], [-73.9960, 40.7155]);
  assert(bearing >= 0 && bearing <= 360, `Bearing angle within valid 0-360 deg range (${bearing.toFixed(1)} deg)`);

  const routeProfile = getRouteProfileForSegment("PIPE-SEC-4B-92");
  assert(routeProfile !== null, "Route profile loaded from valid GeoJSON pipeline");
  assert((routeProfile?.coordinates.length || 0) >= 2, "Route profile has at least 2 valid coordinates");

  if (routeProfile) {
    const posStart = interpolateRoutePosition(routeProfile, 0);
    assert(Math.abs(posStart.longitude - routeProfile.coordinates[0][0]) < 0.001, "Start interpolation matches start coordinates");

    const posMid = interpolateRoutePosition(routeProfile, routeProfile.totalLengthM / 2);
    assert(posMid.fractionCompleted >= 0.49 && posMid.fractionCompleted <= 0.51, "Mid interpolation fraction is 50%");

    const posEnd = interpolateRoutePosition(routeProfile, routeProfile.totalLengthM + 500); // Out of bounds clamp test
    assert(posEnd.fractionCompleted === 1.0, "Interpolation clamps strictly at 100% when beyond route bounds");
  }

  // ========================================================================
  // TEST SUITE 4: MISSION INTEGRATION & DUPLICATE ASSIGNMENT GUARDS
  // ========================================================================
  console.log("\n--- 4. Testing Mission Integration & Assignment Rules ---");

  const engine = RoverSimulationEngine.getInstance();
  engine.reset();

  // Test assigning scheduled mission MSN-2026-044 to IDLE rover ROV-AQUA-03
  const assignRes = engine.assignMission("ROV-AQUA-03", "MSN-2026-044");
  assert(assignRes.success === true, "Assign mission to IDLE rover succeeds");

  const r3 = engine.getRoverById("ROV-AQUA-03");
  assert(r3?.operatingState === "INSPECTING", "Rover transitions to INSPECTING on mission start");
  assert(r3?.assignedMissionId === "MSN-2026-044", "Rover stores assignedMissionId");

  // Test duplicate assignment guard: Rover 3 is now busy; attempting to assign another mission must fail
  const dupAssign = engine.assignMission("ROV-AQUA-03", "MSN-2026-042");
  assert(dupAssign.success === false, "Assigning mission to busy rover is rejected");

  // ========================================================================
  // TEST SUITE 5: SAFETY INTERLOCKS & EMERGENCY STOP
  // ========================================================================
  console.log("\n--- 5. Testing Safety Interlocks & Emergency Stop ---");

  // Trigger E-Stop
  const eStopRes = engine.emergencyStopRover("ROV-AQUA-01", "Simulated obstacle detected");
  assert(eStopRes.success === true, "Emergency Stop command executed successfully");

  const r1 = engine.getRoverById("ROV-AQUA-01");
  assert(r1?.operatingState === "EMERGENCY_STOP", "Rover state is EMERGENCY_STOP");
  assert(r1?.kinematics.velocityMps === 0, "Rover velocity is immediately 0.0 m/s");
  assert(r1?.diagnostics.motorCurrentAmps === 0, "Rover motor current is immediately 0.0 A");

  // Direct resume from E-Stop must be rejected
  const illegalResume = engine.commandRoverState("ROV-AQUA-01", "MOVING", "Trying to resume directly");
  assert(illegalResume.success === false, "Direct transition from EMERGENCY_STOP to MOVING is rejected by state machine");

  // Administrative reset clears E-Stop to IDLE
  const resetRes = engine.resetEmergencyStop("ROV-AQUA-01", "Safety perimeter verified clear");
  assert(resetRes.success === true, "Administrative safety clear succeeds");

  const r1Reset = engine.getRoverById("ROV-AQUA-01");
  assert(r1Reset?.operatingState === "IDLE", "Rover returns to IDLE after administrative reset");

  // ========================================================================
  // TEST SUITE 6: EVENT BUS & SUBSCRIPTION CLEANUP
  // ========================================================================
  console.log("\n--- 6. Testing Event Bus & Subscription Teardown ---");

  let receivedTickCount = 0;
  const unsubscribe = roverEventBus.subscribe("SIMULATION_TICK", () => {
    receivedTickCount++;
  });

  // Execute 3 discrete ticks
  engine.executeTick();
  engine.executeTick();
  engine.executeTick();

  assert(receivedTickCount === 3, "Subscriber received exactly 3 tick events");

  // Unsubscribe and verify no more events received
  unsubscribe();
  engine.executeTick();
  assert(receivedTickCount === 3, "No events received after unsubscribe (clean teardown)");

  // Clean up engine
  engine.pause();
  assert(!engine.isRunning(), "Engine timer cleanly stopped");

  console.log("\n==================================================================");
  console.log(` ALL TESTS COMPLETED: ${passedTests} PASSED, ${failedTests} FAILED `);
  console.log("==================================================================");

  if (failedTests > 0) {
    process.exit(1);
  }
}

runAllTests().catch((err) => {
  console.error("Test execution failed:", err);
  process.exit(1);
});

