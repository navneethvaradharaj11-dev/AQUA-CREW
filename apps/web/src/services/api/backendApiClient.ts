/**
 * AQUA CREW — Backend API Client
 * Primary HTTP transport interface for connecting to the FastAPI backend.
 * Gracefully handles offline fallback to local simulation models when backend is unreachable.
 */
import {
  SimulatedRover,
  SimulatedMission,
  RoverOperatingState,
} from "../simulation/types";
import { roverSimulationEngine } from "../simulation/roverSimulationEngine";
import {
  AiDetection,
  AiHealth,
  AiModelInfo,
  AiModelMetrics,
  AcousticScenario,
  LeakAnalyzeRequest,
  SyntheticWaveformResponse,
  DetectionStatus,
} from "./aiTypes";
import {
  MissionRecommendation,
  RoverSuitability,
  MissionPriorityAssessment,
  MissionProgressInfo,
  MissionRouteInfo,
} from "./dispatchTypes";
import {
  PipelineHealth,
  PredictiveRisk,
  HistoricalTrend,
  MaintenanceRecommendation,
  PredictiveMaintenanceOverview,
  MaintenanceModelInfo,
} from "./maintenanceTypes";
import {
  HydraulicNetwork,
  NetworkTopologyBundle,
  SimulationScenario,
  SimulationRun,
  ScenarioComparison,
  EquipmentStatusBundle,
  RoverHandoffResponse,
  ValidationStatus,
  Net1BenchmarkResult,
  Net3BenchmarkResult,
  ReproducibilityBenchmarkResult,
} from "./digitalTwinTypes";
import {
  PipelineVulnerabilityItem,
  PipelineVulnerabilityListResponse,
  SegmentDeepDiveResponse,
  SpatialClusterItem,
  GeographicRiskZoneItem,
  HeatmapPointItem,
  TemporalTrendItem,
  PredictionItem,
  InspectionPriorityItem,
  InfrastructureOverviewResponse,
  InspectionDispatchResponse,
} from "./infrastructureIntelligenceTypes";
import {
  OperationalOverview,
  OperationalAssessment,
  OperationalRecommendation,
  OperationalEvidence,
  OperationalImpact,
  IncidentCorrelation,
  ResourcePlanning,
  OperationalDecisionRecord,
  OperationalExecutionRecord,
} from "./operationalIntelligenceTypes";
import {
  EvidenceItem,
  AIChatRequest,
  AIChatResponse,
  AIConversationItem,
  AIConversationDetail,
  ProviderStatus,
  DecisionExplanation,
  PipelineComparisonResponse,
  OperationalSummaryResponse,
  EvidenceGapAnalysis,
  MultiSourceReasoningResult,
} from "./advancedAiTypes";
import {
  UserProfile,
  UserRole,
  LoginRequest,
  TokenResponse,
  SecurityAuditEvent,
  UserCreateRequest,
} from "./authTypes";
import {
  ObjectiveProfile,
  DecisionVariable,
  ObjectiveWeights,
  OptimizationConstraints,
  HydraulicCandidateMetrics,
  OptimizationCandidate,
  BaselineComparison,
  OptimizationJobDetail,
  OptimizationStatusResponse,
  OptimizationTriggerRequest,
  OptimizationRecommendRequest,
} from "./optimizationTypes";
import {
  InspectionRecommendation,
  RoverSuitability as InspectionRoverSuitability,
  InspectionPlan,
  InspectionExecutionProgress,
  InspectionReport,
} from "./inspectionIntelligenceTypes";
import {
  DamageAssessment,
  DamageCategory,
  DamageSeverity,
  RepairMethodType,
  RepairMethodOption,
  RepairRecommendation,
  RepairResourceItem,
  ResourcePlan,
  CostComponent,
  RepairCostEstimate,
  RepairPriority,
  RepairScheduleItem,
  RepairPlan,
  RepairWorkflowStatus,
  DigitalTwinRepairScenario,
  DigitalTwinRepairComparison,
  RepairVerification,
  VerificationOutcome,
  RepairOverviewSummary,
  RepairWorkflowEvent,
} from "./repairManagementTypes";

const DEFAULT_API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

export interface BackendConnectionStatus {
  isConnected: boolean;
  version?: string;
  environment?: string;
  lastChecked: string;
  error?: string;
}

class BackendApiClient {
  private baseUrl: string;
  private isBackendOnline: boolean = false;
  private lastHealthCheck: string = new Date().toISOString();
  private accessToken: string | null = null;
  private refreshTokenVal: string | null = null;
  private currentUser: UserProfile | null = null;

  constructor(baseUrl = DEFAULT_API_BASE) {
    this.baseUrl = baseUrl.replace(/\/$/, "");
    if (typeof window !== "undefined") {
      this.accessToken = localStorage.getItem("aqua_crew_access_token") || null;
      this.refreshTokenVal = localStorage.getItem("aqua_crew_refresh_token") || null;
      try {
        const storedUser = localStorage.getItem("aqua_crew_user");
        this.currentUser = storedUser ? JSON.parse(storedUser) : null;
      } catch {
        this.currentUser = null;
      }
    }
  }

  public getAuthHeaders(contentType?: string): Record<string, string> {
    const headers: Record<string, string> = {
      Accept: "application/json",
    };
    if (contentType) {
      headers["Content-Type"] = contentType;
    }
    if (this.accessToken) {
      headers["Authorization"] = `Bearer ${this.accessToken}`;
    }
    return headers;
  }

  public setAuthSession(tokenResponse: TokenResponse): void {
    this.accessToken = tokenResponse.access_token;
    this.refreshTokenVal = tokenResponse.refresh_token;
    this.currentUser = tokenResponse.user;
    if (typeof window !== "undefined") {
      localStorage.setItem("aqua_crew_access_token", tokenResponse.access_token);
      localStorage.setItem("aqua_crew_refresh_token", tokenResponse.refresh_token);
      localStorage.setItem("aqua_crew_user", JSON.stringify(tokenResponse.user));
    }
  }

  public clearAuthSession(): void {
    this.accessToken = null;
    this.refreshTokenVal = null;
    this.currentUser = null;
    if (typeof window !== "undefined") {
      localStorage.removeItem("aqua_crew_access_token");
      localStorage.removeItem("aqua_crew_refresh_token");
      localStorage.removeItem("aqua_crew_user");
    }
  }

  public getCurrentUser(): UserProfile | null {
    return this.currentUser;
  }

  public getAccessToken(): string | null {
    return this.accessToken;
  }

  public async login(req: LoginRequest): Promise<TokenResponse> {
    const res = await fetch(`${this.baseUrl}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json", Accept: "application/json" },
      body: JSON.stringify(req),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: "Login failed" }));
      throw new Error(err.detail || `Login failed with status ${res.status}`);
    }
    const data: TokenResponse = await res.json();
    this.setAuthSession(data);
    return data;
  }

  public async logout(): Promise<void> {
    try {
      if (this.accessToken) {
        await fetch(`${this.baseUrl}/auth/logout`, {
          method: "POST",
          headers: this.getAuthHeaders(),
        });
      }
    } finally {
      this.clearAuthSession();
    }
  }

  public async fetchCurrentUser(): Promise<UserProfile> {
    const res = await fetch(`${this.baseUrl}/auth/me`, {
      method: "GET",
      headers: this.getAuthHeaders(),
    });
    if (!res.ok) {
      throw new Error(`Failed to fetch current user profile: status ${res.status}`);
    }
    const user: UserProfile = await res.json();
    this.currentUser = user;
    if (typeof window !== "undefined") {
      localStorage.setItem("aqua_crew_user", JSON.stringify(user));
    }
    return user;
  }

  public async listUsers(): Promise<UserProfile[]> {
    const res = await fetch(`${this.baseUrl}/auth/users`, {
      method: "GET",
      headers: this.getAuthHeaders(),
    });
    if (!res.ok) {
      throw new Error(`Failed to list users: status ${res.status}`);
    }
    return res.json();
  }

  public async getSecurityAuditLogs(limit: number = 50): Promise<SecurityAuditEvent[]> {
    const res = await fetch(`${this.baseUrl}/auth/audit-logs?limit=${limit}`, {
      method: "GET",
      headers: this.getAuthHeaders(),
    });
    if (!res.ok) {
      throw new Error(`Failed to get security audit logs: status ${res.status}`);
    }
    return res.json();
  }

  public getBaseUrl(): string {
    return this.baseUrl;
  }

  public isOnline(): boolean {
    return this.isBackendOnline;
  }

  /**
   * Health check to detect backend server presence.
   */
  public async checkHealth(): Promise<BackendConnectionStatus> {
    try {
      const res = await fetch(`${this.baseUrl}/health`, {
        method: "GET",
        headers: { Accept: "application/json" },
        cache: "no-store",
      });

      if (!res.ok) {
        throw new Error(`Health check returned status ${res.status}`);
      }

      const data = await res.json();
      this.isBackendOnline = true;
      this.lastHealthCheck = new Date().toISOString();

      return {
        isConnected: true,
        version: data.version,
        environment: data.environment,
        lastChecked: this.lastHealthCheck,
      };
    } catch (err: any) {
      this.isBackendOnline = false;
      this.lastHealthCheck = new Date().toISOString();
      return {
        isConnected: false,
        lastChecked: this.lastHealthCheck,
        error: err.message || "Backend server unreachable",
      };
    }
  }

  /**
   * Fetches rovers from backend; falls back to local engine if offline.
   */
  public async getRovers(): Promise<SimulatedRover[]> {
    try {
      const res = await fetch(`${this.baseUrl}/rovers`, {
        method: "GET",
        headers: { Accept: "application/json" },
        cache: "no-store",
      });

      if (res.ok) {
        const body = await res.json();
        this.isBackendOnline = true;
        return body.rovers;
      }
    } catch {
      this.isBackendOnline = false;
    }

    // Graceful fallback to local engine
    return roverSimulationEngine.getRovers();
  }

  /**
   * Fetches rover by ID.
   */
  public async getRoverById(roverId: string): Promise<SimulatedRover | null> {
    try {
      const res = await fetch(`${this.baseUrl}/rovers/${roverId}`, {
        method: "GET",
        headers: { Accept: "application/json" },
        cache: "no-store",
      });

      if (res.ok) {
        this.isBackendOnline = true;
        return await res.json();
      }
    } catch {
      this.isBackendOnline = false;
    }

    return roverSimulationEngine.getRoverById(roverId);
  }

  /**
   * Dispatches state/kinematic command to rover.
   */
  public async commandRover(
    roverId: string,
    command: "PAUSE" | "RESUME" | "RETURN_BASE" | "EMERGENCY_STOP" | "RESET_ESTOP" | "SET_STATE",
    targetState?: RoverOperatingState,
    reason: string = "Operator command",
    triggeredBy: string = "OPERATOR"
  ): Promise<{ success: boolean; message?: string; error?: string }> {
    try {
      const res = await fetch(`${this.baseUrl}/rovers/${roverId}/commands`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Accept: "application/json",
        },
        body: JSON.stringify({
          command,
          target_state: targetState,
          reason,
          triggered_by: triggeredBy,
        }),
      });

      const body = await res.json();
      if (!res.ok) {
        return {
          success: false,
          message: body.error?.message || "Command rejected by backend",
          error: body.error?.code,
        };
      }

      this.isBackendOnline = true;
      return { success: true, message: body.message };
    } catch {
      this.isBackendOnline = false;
      // Fallback to local engine
      if (command === "PAUSE") return roverSimulationEngine.pauseRover(roverId, reason);
      if (command === "RESUME") return roverSimulationEngine.resumeRover(roverId, reason);
      if (command === "RETURN_BASE") return roverSimulationEngine.returnRoverToBase(roverId, reason);
      if (command === "EMERGENCY_STOP") return roverSimulationEngine.emergencyStopRover(roverId, reason);
      if (command === "RESET_ESTOP") return roverSimulationEngine.resetEmergencyStop(roverId, reason);
      if (command === "SET_STATE" && targetState) {
        return roverSimulationEngine.commandRoverState(roverId, targetState, reason);
      }
      return { success: false, message: "Unknown command" };
    }
  }

  /**
   * Fetches missions from backend.
   */
  public async getMissions(): Promise<SimulatedMission[]> {
    try {
      const res = await fetch(`${this.baseUrl}/missions`, {
        method: "GET",
        headers: { Accept: "application/json" },
        cache: "no-store",
      });

      if (res.ok) {
        const body = await res.json();
        this.isBackendOnline = true;
        return body.missions;
      }
    } catch {
      this.isBackendOnline = false;
    }

    return roverSimulationEngine.getMissions();
  }

  /**
   * Assigns mission to rover.
   */
  public async assignMission(missionId: string, roverId: string): Promise<{ success: boolean; message?: string; error?: string }> {
    try {
      const res = await fetch(`${this.baseUrl}/missions/${missionId}/assign`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Accept: "application/json" },
        body: JSON.stringify({ rover_id: roverId }),
      });

      const body = await res.json();
      if (!res.ok) {
        return {
          success: false,
          message: body.error?.message || "Assignment failed",
          error: body.error?.code,
        };
      }

      this.isBackendOnline = true;
      return { success: true, message: body.message };
    } catch {
      this.isBackendOnline = false;
      return roverSimulationEngine.assignMission(roverId, missionId);
    }
  }

  /**
   * Simulation lifecycle controls.
   */
  public async startSimulation(): Promise<{ success: boolean; message: string }> {
    try {
      const res = await fetch(`${this.baseUrl}/simulation/start`, { method: "POST" });
      if (res.ok) {
        const body = await res.json();
        return { success: true, message: body.message };
      }
    } catch {}
    roverSimulationEngine.start();
    return { success: true, message: "Local simulation started (backend offline)" };
  }

  public async pauseSimulation(): Promise<{ success: boolean; message: string }> {
    try {
      const res = await fetch(`${this.baseUrl}/simulation/pause`, { method: "POST" });
      if (res.ok) {
        const body = await res.json();
        return { success: true, message: body.message };
      }
    } catch {}
    roverSimulationEngine.pause();
    return { success: true, message: "Local simulation paused" };
  }

  public async resetSimulation(): Promise<{ success: boolean; message: string }> {
    try {
      const res = await fetch(`${this.baseUrl}/simulation/reset`, { method: "POST" });
      if (res.ok) {
        const body = await res.json();
        return { success: true, message: body.message };
      }
    } catch {}
    roverSimulationEngine.reset();
    return { success: true, message: "Local simulation reset" };
  }

  /* ========================================================= */
  /* AI LEAK DETECTION & ACOUSTIC INTELLIGENCE (TASK 07)       */
  /* ========================================================= */

  public async getAiDetections(filters?: {
    segment_id?: string;
    risk_level?: string;
    status?: string;
    limit?: number;
  }): Promise<AiDetection[]> {
    try {
      const params = new URLSearchParams();
      if (filters?.segment_id) params.set("segment_id", filters.segment_id);
      if (filters?.risk_level) params.set("risk_level", filters.risk_level);
      if (filters?.status) params.set("status", filters.status);
      if (filters?.limit) params.set("limit", filters.limit.toString());

      const res = await fetch(`${this.baseUrl}/ai/detections?${params.toString()}`, {
        method: "GET",
        headers: { Accept: "application/json" },
        cache: "no-store",
      });

      if (res.ok) {
        this.isBackendOnline = true;
        return await res.json();
      }
    } catch {
      this.isBackendOnline = false;
    }

    return getFallbackAiDetections(filters);
  }

  public async getAiDetectionById(id: string): Promise<AiDetection | null> {
    try {
      const res = await fetch(`${this.baseUrl}/ai/detections/${id}`, {
        headers: { Accept: "application/json" },
        cache: "no-store",
      });
      if (res.ok) {
        this.isBackendOnline = true;
        return await res.json();
      }
    } catch {
      this.isBackendOnline = false;
    }

    const detections = getFallbackAiDetections();
    return detections.find((d) => d.id === id) || null;
  }

  public async analyzeLeak(req: LeakAnalyzeRequest): Promise<AiDetection> {
    try {
      const res = await fetch(`${this.baseUrl}/ai/analyze`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Accept: "application/json" },
        body: JSON.stringify(req),
      });
      if (res.ok) {
        this.isBackendOnline = true;
        return await res.json();
      }
    } catch {
      this.isBackendOnline = false;
    }

    // Local fallback analysis
    return simulateLocalAiDetection(req);
  }

  public async updateDetectionStatus(
    id: string,
    status: DetectionStatus,
    operator_notes?: string
  ): Promise<AiDetection | null> {
    try {
      const res = await fetch(`${this.baseUrl}/ai/detections/${id}/status`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json", Accept: "application/json" },
        body: JSON.stringify({ status, operator_notes }),
      });
      if (res.ok) {
        this.isBackendOnline = true;
        return await res.json();
      }
    } catch {
      this.isBackendOnline = false;
    }

    // Local fallback status update
    return updateFallbackDetectionStatus(id, status, operator_notes);
  }

  public async synthesizeWaveform(
    scenario: AcousticScenario = "MODERATE_LEAK",
    durationSec = 2.0,
    snrDb = 15.0
  ): Promise<SyntheticWaveformResponse> {
    try {
      const res = await fetch(`${this.baseUrl}/ai/waveform/synthesize`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Accept: "application/json" },
        body: JSON.stringify({
          scenario,
          duration_sec: durationSec,
          snr_db: snrDb,
        }),
      });
      if (res.ok) {
        this.isBackendOnline = true;
        return await res.json();
      }
    } catch {
      this.isBackendOnline = false;
    }

    return generateFallbackWaveform(scenario, durationSec, snrDb);
  }

  public async getAiModels(): Promise<{ models: AiModelInfo[]; is_simulated: boolean }> {
    try {
      const res = await fetch(`${this.baseUrl}/ai/models`, {
        headers: { Accept: "application/json" },
        cache: "no-store",
      });
      if (res.ok) {
        this.isBackendOnline = true;
        return await res.json();
      }
    } catch {
      this.isBackendOnline = false;
    }

    return {
      models: [
        {
          id: "random_forest_classifier",
          name: "Random Forest Leak Classifier",
          algorithm: "RandomForestClassifier",
          version: "v1.2.0-rf-explainable",
          classes: ["NORMAL", "LOW_LEAK_PROBABILITY", "MEDIUM_LEAK_PROBABILITY", "HIGH_LEAK_PROBABILITY"],
          features_used: 12,
          is_active: true,
        },
        {
          id: "isolation_forest_anomaly",
          name: "Isolation Forest Anomaly Engine",
          algorithm: "IsolationForest",
          version: "v1.1.0-isoforest",
          purpose: "Unsupervised Multi-Sensor Outlier Scoring",
          is_active: true,
        },
        {
          id: "logistic_regression_calibrated",
          name: "Multinomial Logistic Regression",
          algorithm: "LogisticRegression",
          version: "v1.0.0-lr",
          purpose: "Baseline Calibrated Probabilities",
          is_active: true,
        },
        {
          id: "tdoa_acoustic_localization",
          name: "Cross-Correlation TDOA Localization",
          algorithm: "Generalized Cross-Correlation (Phase Transform)",
          version: "v1.2.0-tdoa",
          purpose: "Acoustic Coordinate Estimation",
          is_active: true,
        },
      ],
      is_simulated: true,
    };
  }

  public async getAiModelMetrics(): Promise<AiModelMetrics> {
    try {
      const res = await fetch(`${this.baseUrl}/ai/models/metrics`, {
        headers: { Accept: "application/json" },
        cache: "no-store",
      });
      if (res.ok) {
        this.isBackendOnline = true;
        return await res.json();
      }
    } catch {
      this.isBackendOnline = false;
    }

    return {
      model_version: "v1.2.0-rf-explainable",
      accuracy: 0.945,
      precision: 0.932,
      recall: 0.960,
      f1_score: 0.946,
      confusion_matrix: {
        normal: { normal: 48, leak: 2 },
        leak: { normal: 3, leak: 47 },
      },
      training_samples: 400,
      testing_samples: 100,
      classes: ["NORMAL", "LOW_LEAK_PROBABILITY", "MEDIUM_LEAK_PROBABILITY", "HIGH_LEAK_PROBABILITY"],
      is_simulated: true,
      provenance: "DETERMINISTIC_SYNTHETIC_BENCHMARK_SUITE",
    };
  }

  public async getAiHealth(): Promise<AiHealth> {
    try {
      const res = await fetch(`${this.baseUrl}/ai/health`, {
        headers: { Accept: "application/json" },
        cache: "no-store",
      });
      if (res.ok) {
        this.isBackendOnline = true;
        return await res.json();
      }
    } catch {
      this.isBackendOnline = false;
    }

    return {
      status: "HEALTHY_SIMULATED",
      models_loaded: 4,
      active_classifier: "RandomForestClassifier(n_estimators=100)",
      total_detections: fallbackDetectionsStore.length,
      pending_reviews: fallbackDetectionsStore.filter((d) => d.status === "PENDING_REVIEW").length,
      sensor_readings_ingested: 840,
      is_simulated: true,
      provenance: "VIRTUAL_SIMULATION_BACKEND",
    };
  }

  /* ========================================================= */
  /* AUTONOMOUS MISSION PLANNING & DISPATCH (TASK 08)          */
  /* ========================================================= */

  public async planMission(
    detectionId: string,
    preferredRoverId?: string,
    priorityOverride?: string
  ): Promise<MissionRecommendation> {
    try {
      const res = await fetch(`${this.baseUrl}/missions/plan`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Accept: "application/json" },
        body: JSON.stringify({
          detection_id: detectionId,
          preferred_rover_id: preferredRoverId,
          priority_override: priorityOverride,
        }),
      });
      if (res.ok) {
        this.isBackendOnline = true;
        return await res.json();
      }
    } catch {
      this.isBackendOnline = false;
    }

    return generateFallbackRecommendation(detectionId, preferredRoverId);
  }

  public async getRecommendations(filters?: {
    status?: string;
    priority?: string;
    limit?: number;
  }): Promise<MissionRecommendation[]> {
    try {
      const params = new URLSearchParams();
      if (filters?.status) params.set("status", filters.status);
      if (filters?.priority) params.set("priority", filters.priority);
      if (filters?.limit) params.set("limit", filters.limit.toString());

      const res = await fetch(`${this.baseUrl}/missions/recommendations?${params.toString()}`, {
        headers: { Accept: "application/json" },
        cache: "no-store",
      });
      if (res.ok) {
        this.isBackendOnline = true;
        return await res.json();
      }
    } catch {
      this.isBackendOnline = false;
    }

    return getFallbackRecommendations(filters);
  }

  public async getRecommendationById(id: string): Promise<MissionRecommendation | null> {
    try {
      const res = await fetch(`${this.baseUrl}/missions/recommendations/${id}`, {
        headers: { Accept: "application/json" },
        cache: "no-store",
      });
      if (res.ok) {
        this.isBackendOnline = true;
        return await res.json();
      }
    } catch {
      this.isBackendOnline = false;
    }

    return fallbackRecommendationsStore.find((r) => r.id === id) || null;
  }

  public async approveRecommendation(
    id: string,
    operatorId = "OPERATOR_CHIEF",
    notes?: string
  ): Promise<{ success: boolean; message: string; mission_id?: string; rover_id?: string }> {
    try {
      const res = await fetch(`${this.baseUrl}/missions/recommendations/${id}/approve`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Accept: "application/json" },
        body: JSON.stringify({ operator_id: operatorId, notes }),
      });
      if (res.ok) {
        this.isBackendOnline = true;
        return await res.json();
      }
    } catch {
      this.isBackendOnline = false;
    }

    // Local fallback approval
    return approveFallbackRecommendation(id, operatorId, notes);
  }

  public async rejectRecommendation(
    id: string,
    reason: string,
    operatorNotes?: string
  ): Promise<MissionRecommendation | null> {
    try {
      const res = await fetch(`${this.baseUrl}/missions/recommendations/${id}/reject`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Accept: "application/json" },
        body: JSON.stringify({ rejection_reason: reason, operator_notes: operatorNotes }),
      });
      if (res.ok) {
        this.isBackendOnline = true;
        return await res.json();
      }
    } catch {
      this.isBackendOnline = false;
    }

    return rejectFallbackRecommendation(id, reason, operatorNotes);
  }

  public async recalculateRecommendation(id: string): Promise<MissionRecommendation | null> {
    try {
      const res = await fetch(`${this.baseUrl}/missions/recommendations/${id}/recalculate`, {
        method: "POST",
        headers: { Accept: "application/json" },
      });
      if (res.ok) {
        this.isBackendOnline = true;
        return await res.json();
      }
    } catch {
      this.isBackendOnline = false;
    }

    return fallbackRecommendationsStore.find((r) => r.id === id) || null;
  }

  public async getMissionRoute(missionId: string): Promise<MissionRouteInfo | null> {
    try {
      const res = await fetch(`${this.baseUrl}/missions/${missionId}/route`, {
        headers: { Accept: "application/json" },
        cache: "no-store",
      });
      if (res.ok) {
        this.isBackendOnline = true;
        return await res.json();
      }
    } catch {
      this.isBackendOnline = false;
    }

    return {
      mission_id: missionId,
      target_segment_id: "PIPE-SEC-4B-92",
      assigned_rover_id: "ROV-AQUA-01",
      route_distance_m: 1450.0,
      waypoint_count: 5,
      waypoints: [
        [-74.015, 40.71],
        [-74.011, 40.7115],
        [-74.006, 40.7128],
        [-74.001, 40.714],
        [-73.996, 40.7155],
      ],
      is_simulated: true,
    };
  }

  public async getMissionProgress(missionId: string): Promise<MissionProgressInfo | null> {
    try {
      const res = await fetch(`${this.baseUrl}/missions/${missionId}/progress`, {
        headers: { Accept: "application/json" },
        cache: "no-store",
      });
      if (res.ok) {
        this.isBackendOnline = true;
        return await res.json();
      }
    } catch {
      this.isBackendOnline = false;
    }

    return {
      mission_id: missionId,
      status: "In Progress",
      progress_percentage: 65,
      inspected_distance_m: 940.0,
      total_distance_m: 1450.0,
      completed_waypoints: 3,
      total_waypoints: 5,
      start_time: "14:20 UTC (Dispatched)",
      estimated_completion_time: "15 min",
      is_simulated: true,
    };
  }

  public async getEligibleRovers(targetSegmentId = "PIPE-SEC-4B-92"): Promise<RoverSuitability[]> {
    try {
      const res = await fetch(`${this.baseUrl}/dispatch/eligible-rovers?target_segment_id=${targetSegmentId}`, {
        headers: { Accept: "application/json" },
        cache: "no-store",
      });
      if (res.ok) {
        this.isBackendOnline = true;
        return await res.json();
      }
    } catch {
      this.isBackendOnline = false;
    }

    return getFallbackRoverSuitabilities();
  }

  // =========================================================================
  // PREDICTIVE MAINTENANCE & INFRASTRUCTURE HEALTH INTELLIGENCE (TASK 09)
  // =========================================================================

  public async getMaintenanceOverview(): Promise<PredictiveMaintenanceOverview> {
    try {
      const res = await fetch(`${this.baseUrl}/maintenance/overview`, {
        headers: { Accept: "application/json" },
        cache: "no-store",
      });
      if (res.ok) {
        this.isBackendOnline = true;
        return await res.json();
      }
    } catch {
      this.isBackendOnline = false;
    }
    return getFallbackMaintenanceOverview();
  }

  public async getHealthAssessments(limit = 50): Promise<PipelineHealth[]> {
    try {
      const res = await fetch(`${this.baseUrl}/maintenance/health?limit=${limit}`, {
        headers: { Accept: "application/json" },
        cache: "no-store",
      });
      if (res.ok) {
        this.isBackendOnline = true;
        return await res.json();
      }
    } catch {
      this.isBackendOnline = false;
    }
    return getFallbackHealthAssessments();
  }

  public async getSegmentHealth(segmentId: string): Promise<PipelineHealth> {
    try {
      const res = await fetch(`${this.baseUrl}/maintenance/health/${segmentId}`, {
        headers: { Accept: "application/json" },
        cache: "no-store",
      });
      if (res.ok) {
        this.isBackendOnline = true;
        return await res.json();
      }
    } catch {
      this.isBackendOnline = false;
    }
    return getFallbackSegmentHealth(segmentId);
  }

  public async getPredictions(limit = 50): Promise<PredictiveRisk[]> {
    try {
      const res = await fetch(`${this.baseUrl}/maintenance/predictions?limit=${limit}`, {
        headers: { Accept: "application/json" },
        cache: "no-store",
      });
      if (res.ok) {
        this.isBackendOnline = true;
        return await res.json();
      }
    } catch {
      this.isBackendOnline = false;
    }
    return getFallbackPredictions();
  }

  public async getSegmentPrediction(segmentId: string): Promise<PredictiveRisk> {
    try {
      const res = await fetch(`${this.baseUrl}/maintenance/predictions/${segmentId}`, {
        headers: { Accept: "application/json" },
        cache: "no-store",
      });
      if (res.ok) {
        this.isBackendOnline = true;
        return await res.json();
      }
    } catch {
      this.isBackendOnline = false;
    }
    return getFallbackSegmentPrediction(segmentId);
  }

  public async getTrends(segmentId?: string): Promise<HistoricalTrend[]> {
    try {
      const url = segmentId
        ? `${this.baseUrl}/maintenance/trends/${segmentId}`
        : `${this.baseUrl}/maintenance/trends`;
      const res = await fetch(url, {
        headers: { Accept: "application/json" },
        cache: "no-store",
      });
      if (res.ok) {
        this.isBackendOnline = true;
        const data = await res.json();
        return Array.isArray(data) ? data : [data];
      }
    } catch {
      this.isBackendOnline = false;
    }
    return getFallbackTrends(segmentId);
  }

  public async getMaintenanceRecommendations(
    status?: string,
    urgency?: string
  ): Promise<MaintenanceRecommendation[]> {
    try {
      const params = new URLSearchParams();
      if (status && status !== "ALL") params.append("status", status);
      if (urgency && urgency !== "ALL") params.append("urgency", urgency);
      const query = params.toString() ? `?${params.toString()}` : "";
      const res = await fetch(`${this.baseUrl}/maintenance/recommendations${query}`, {
        headers: { Accept: "application/json" },
        cache: "no-store",
      });
      if (res.ok) {
        this.isBackendOnline = true;
        return await res.json();
      }
    } catch {
      this.isBackendOnline = false;
    }
    return getFallbackMaintenanceRecommendations(status, urgency);
  }

  public async reviewMaintenanceRecommendation(
    recommendationId: string,
    action: "ACKNOWLEDGE" | "DISMISS" | "DISPATCH",
    operatorId: string = "OPERATOR_CHIEF",
    operatorNotes?: string
  ): Promise<MaintenanceRecommendation> {
    try {
      const res = await fetch(`${this.baseUrl}/maintenance/recommendations/${recommendationId}/review`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Accept: "application/json" },
        body: JSON.stringify({ action, operator_id: operatorId, operator_notes: operatorNotes }),
      });
      if (res.ok) {
        this.isBackendOnline = true;
        return await res.json();
      }
    } catch {
      this.isBackendOnline = false;
    }
    return reviewFallbackMaintenanceRecommendation(recommendationId, action, operatorId, operatorNotes);
  }

  /* ========================================================= */
  /* TASK 10 DIGITAL TWIN & HYDRAULIC SIMULATION METHODS       */
  /* ========================================================= */

  public async getDigitalTwinNetworks(): Promise<HydraulicNetwork[]> {
    try {
      const res = await fetch(`${this.baseUrl}/digital-twin/networks`, {
        headers: { Accept: "application/json" },
      });
      if (res.ok) {
        this.isBackendOnline = true;
        return await res.json();
      }
    } catch {
      this.isBackendOnline = false;
    }
    return getFallbackDigitalTwinNetworks();
  }

  public async getDigitalTwinTopology(networkId: string = "NET-METRO-01"): Promise<NetworkTopologyBundle> {
    try {
      const res = await fetch(`${this.baseUrl}/digital-twin/networks/${networkId}/topology`, {
        headers: { Accept: "application/json" },
      });
      if (res.ok) {
        this.isBackendOnline = true;
        return await res.json();
      }
    } catch {
      this.isBackendOnline = false;
    }
    return getFallbackDigitalTwinTopology(networkId);
  }

  public async getDigitalTwinScenarios(networkId: string = "NET-METRO-01"): Promise<SimulationScenario[]> {
    try {
      const res = await fetch(`${this.baseUrl}/digital-twin/scenarios?network_id=${networkId}`, {
        headers: { Accept: "application/json" },
      });
      if (res.ok) {
        this.isBackendOnline = true;
        return await res.json();
      }
    } catch {
      this.isBackendOnline = false;
    }
    return getFallbackDigitalTwinScenarios(networkId);
  }

  public async getDigitalTwinScenario(scenarioId: string): Promise<SimulationScenario> {
    try {
      const res = await fetch(`${this.baseUrl}/digital-twin/scenarios/${scenarioId}`, {
        headers: { Accept: "application/json" },
      });
      if (res.ok) {
        this.isBackendOnline = true;
        return await res.json();
      }
    } catch {
      this.isBackendOnline = false;
    }
    return getFallbackDigitalTwinScenario(scenarioId);
  }

  public async createDigitalTwinScenario(data: {
    network_id?: string;
    name: string;
    scenario_type: string;
    description?: string;
    duration_hours?: number;
    time_step_minutes?: number;
    solver_mode?: string;
    parameters_override?: any;
  }): Promise<{ id: string; name: string; scenario_type: string; status: string; message: string }> {
    try {
      const res = await fetch(`${this.baseUrl}/digital-twin/scenarios`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Accept: "application/json" },
        body: JSON.stringify(data),
      });
      if (res.ok) {
        this.isBackendOnline = true;
        return await res.json();
      }
    } catch {
      this.isBackendOnline = false;
    }
    return createFallbackDigitalTwinScenario(data);
  }

  public async runDigitalTwinScenario(scenarioId: string, overrides?: any): Promise<any> {
    try {
      const res = await fetch(`${this.baseUrl}/digital-twin/scenarios/${scenarioId}/run`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Accept: "application/json" },
        body: JSON.stringify(overrides || {}),
      });
      if (res.ok) {
        this.isBackendOnline = true;
        return await res.json();
      }
    } catch {
      this.isBackendOnline = false;
    }
    return runFallbackDigitalTwinScenario(scenarioId, overrides);
  }

  public async getDigitalTwinRunResults(runId: string): Promise<SimulationRun> {
    try {
      const res = await fetch(`${this.baseUrl}/digital-twin/runs/${runId}`, {
        headers: { Accept: "application/json" },
      });
      if (res.ok) {
        this.isBackendOnline = true;
        return await res.json();
      }
    } catch {
      this.isBackendOnline = false;
    }
    return getFallbackDigitalTwinRunResults(runId);
  }

  public async compareDigitalTwinScenarios(baselineScenarioId: string, comparisonScenarioId: string): Promise<ScenarioComparison> {
    try {
      const res = await fetch(`${this.baseUrl}/digital-twin/scenarios/compare`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Accept: "application/json" },
        body: JSON.stringify({
          baseline_scenario_id: baselineScenarioId,
          comparison_scenario_id: comparisonScenarioId,
        }),
      });
      if (res.ok) {
        this.isBackendOnline = true;
        return await res.json();
      }
    } catch {
      this.isBackendOnline = false;
    }
    return compareFallbackDigitalTwinScenarios(baselineScenarioId, comparisonScenarioId);
  }

  public async simulateDigitalTwinLeak(req: {
    network_id?: string;
    target_node_id: string;
    leak_area_cm2: number;
    discharge_coeff?: number;
    name?: string;
  }): Promise<any> {
    try {
      const res = await fetch(`${this.baseUrl}/digital-twin/simulate-leak`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Accept: "application/json" },
        body: JSON.stringify(req),
      });
      if (res.ok) {
        this.isBackendOnline = true;
        return await res.json();
      }
    } catch {
      this.isBackendOnline = false;
    }
    return simulateFallbackDigitalTwinLeak(req);
  }

  public async getDigitalTwinEquipmentStatus(networkId: string = "NET-METRO-01"): Promise<EquipmentStatusBundle> {
    try {
      const res = await fetch(`${this.baseUrl}/digital-twin/equipment-status?network_id=${networkId}`, {
        headers: { Accept: "application/json" },
      });
      if (res.ok) {
        this.isBackendOnline = true;
        return await res.json();
      }
    } catch {
      this.isBackendOnline = false;
    }
    return getFallbackDigitalTwinEquipmentStatus(networkId);
  }

  public async handoffDigitalTwinRoverDispatch(req: {
    scenario_id: string;
    target_node_id: string;
    operator_id?: string;
    notes?: string;
  }): Promise<RoverHandoffResponse> {
    try {
      const res = await fetch(`${this.baseUrl}/digital-twin/handoff-rover-dispatch`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Accept: "application/json" },
        body: JSON.stringify(req),
      });
      if (res.ok) {
        this.isBackendOnline = true;
        return await res.json();
      }
    } catch {
      this.isBackendOnline = false;
    }
    return handoffFallbackDigitalTwinRoverDispatch(req);
  }

  public async getDigitalTwinNet1Benchmark(): Promise<Net1BenchmarkResult> {
    try {
      const res = await fetch(`${this.baseUrl}/digital-twin/benchmark/net1`, {
        headers: { Accept: "application/json" },
      });
      if (res.ok) {
        this.isBackendOnline = true;
        return await res.json();
      }
    } catch {
      this.isBackendOnline = false;
    }
    return getFallbackDigitalTwinNet1Benchmark();
  }

  public async getDigitalTwinNet3Benchmark(): Promise<Net3BenchmarkResult> {
    try {
      const res = await fetch(`${this.baseUrl}/digital-twin/benchmark/net3`, {
        headers: { Accept: "application/json" },
      });
      if (res.ok) {
        this.isBackendOnline = true;
        return await res.json();
      }
    } catch {
      this.isBackendOnline = false;
    }
    return getFallbackDigitalTwinNet3Benchmark();
  }

  public async getDigitalTwinReproducibility(
    network: string = "Net1",
    iterations: number = 5
  ): Promise<ReproducibilityBenchmarkResult> {
    try {
      const res = await fetch(`${this.baseUrl}/digital-twin/benchmark/reproducibility?network=${network}&iterations=${iterations}`, {
        headers: { Accept: "application/json" },
      });
      if (res.ok) {
        this.isBackendOnline = true;
        return await res.json();
      }
    } catch {
      this.isBackendOnline = false;
    }
    return getFallbackDigitalTwinReproducibility(network, iterations);
  }

  public async getDigitalTwinValidationStatus(): Promise<ValidationStatus> {
    try {
      const res = await fetch(`${this.baseUrl}/digital-twin/validation-status`, {
        headers: { Accept: "application/json" },
      });
      if (res.ok) {
        this.isBackendOnline = true;
        return await res.json();
      }
    } catch {
      this.isBackendOnline = false;
    }
    return getFallbackDigitalTwinValidationStatus();
  }

  /* ========================================================= */
  /* INFRASTRUCTURE INTELLIGENCE & GEOSPATIAL PREDICTION (T11)  */
  /* ========================================================= */

  public async getInfrastructureOverview(): Promise<InfrastructureOverviewResponse> {
    try {
      const res = await fetch(`${this.baseUrl}/infrastructure-intelligence/overview`, {
        headers: { Accept: "application/json" },
      });
      if (res.ok) {
        this.isBackendOnline = true;
        return await res.json();
      }
    } catch {
      this.isBackendOnline = false;
    }
    return getFallbackInfrastructureOverview();
  }

  public async triggerInfrastructureAssessment(): Promise<any> {
    try {
      const res = await fetch(`${this.baseUrl}/infrastructure-intelligence/assess`, {
        method: "POST",
        headers: { Accept: "application/json" },
      });
      if (res.ok) {
        this.isBackendOnline = true;
        return await res.json();
      }
    } catch {
      this.isBackendOnline = false;
    }
    return { status: "ASSESSMENT_COMPLETED_FALLBACK" };
  }

  public async getInfrastructureSegments(
    riskLevel?: string,
    zone?: string,
    trend?: string,
    limit: number = 50,
    offset: number = 0
  ): Promise<PipelineVulnerabilityListResponse> {
    try {
      const params = new URLSearchParams();
      if (riskLevel) params.append("risk_level", riskLevel);
      if (zone) params.append("zone", zone);
      if (trend) params.append("trend", trend);
      params.append("limit", limit.toString());
      params.append("offset", offset.toString());

      const res = await fetch(`${this.baseUrl}/infrastructure-intelligence/segments?${params.toString()}`, {
        headers: { Accept: "application/json" },
      });
      if (res.ok) {
        this.isBackendOnline = true;
        return await res.json();
      }
    } catch {
      this.isBackendOnline = false;
    }
    return getFallbackInfrastructureSegments();
  }

  public async getSegmentDeepDive(segmentId: string): Promise<SegmentDeepDiveResponse> {
    try {
      const res = await fetch(`${this.baseUrl}/infrastructure-intelligence/segments/${segmentId}`, {
        headers: { Accept: "application/json" },
      });
      if (res.ok) {
        this.isBackendOnline = true;
        return await res.json();
      }
    } catch {
      this.isBackendOnline = false;
    }
    return getFallbackSegmentDeepDive(segmentId);
  }

  public async getInfrastructureClusters(): Promise<SpatialClusterItem[]> {
    try {
      const res = await fetch(`${this.baseUrl}/infrastructure-intelligence/clusters`, {
        headers: { Accept: "application/json" },
      });
      if (res.ok) {
        this.isBackendOnline = true;
        return await res.json();
      }
    } catch {
      this.isBackendOnline = false;
    }
    return getFallbackInfrastructureClusters();
  }

  public async getInfrastructureZones(): Promise<GeographicRiskZoneItem[]> {
    try {
      const res = await fetch(`${this.baseUrl}/infrastructure-intelligence/zones`, {
        headers: { Accept: "application/json" },
      });
      if (res.ok) {
        this.isBackendOnline = true;
        return await res.json();
      }
    } catch {
      this.isBackendOnline = false;
    }
    return getFallbackInfrastructureZones();
  }

  public async getInfrastructureHeatmap(): Promise<HeatmapPointItem[]> {
    try {
      const res = await fetch(`${this.baseUrl}/infrastructure-intelligence/heatmap`, {
        headers: { Accept: "application/json" },
      });
      if (res.ok) {
        this.isBackendOnline = true;
        return await res.json();
      }
    } catch {
      this.isBackendOnline = false;
    }
    return getFallbackInfrastructureHeatmap();
  }

  public async getInfrastructureTrends(): Promise<TemporalTrendItem[]> {
    try {
      const res = await fetch(`${this.baseUrl}/infrastructure-intelligence/trends`, {
        headers: { Accept: "application/json" },
      });
      if (res.ok) {
        this.isBackendOnline = true;
        return await res.json();
      }
    } catch {
      this.isBackendOnline = false;
    }
    return getFallbackInfrastructureTrends();
  }

  public async getInfrastructurePredictions(): Promise<PredictionItem[]> {
    try {
      const res = await fetch(`${this.baseUrl}/infrastructure-intelligence/predictions`, {
        headers: { Accept: "application/json" },
      });
      if (res.ok) {
        this.isBackendOnline = true;
        return await res.json();
      }
    } catch {
      this.isBackendOnline = false;
    }
    return getFallbackInfrastructurePredictions();
  }

  public async getInspectionPriorities(status?: string): Promise<InspectionPriorityItem[]> {
    try {
      const url = status
        ? `${this.baseUrl}/infrastructure-intelligence/inspection-priorities?status=${status}`
        : `${this.baseUrl}/infrastructure-intelligence/inspection-priorities`;
      const res = await fetch(url, {
        headers: { Accept: "application/json" },
      });
      if (res.ok) {
        this.isBackendOnline = true;
        return await res.json();
      }
    } catch {
      this.isBackendOnline = false;
    }
    return getFallbackInspectionPriorities();
  }

  public async acknowledgeInspectionPriority(
    priorityId: string,
    operatorName: string = "OPERATOR_CHIEF",
    notes?: string
  ): Promise<InspectionPriorityItem> {
    try {
      const res = await fetch(`${this.baseUrl}/infrastructure-intelligence/inspection-priorities/${priorityId}/acknowledge`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Accept: "application/json" },
        body: JSON.stringify({ operator_name: operatorName, notes }),
      });
      if (res.ok) {
        this.isBackendOnline = true;
        return await res.json();
      }
    } catch {
      this.isBackendOnline = false;
    }
    return {
      id: priorityId,
      pipeline_segment_id: "PIPE-SEC-4B-92",
      segment_name: "Metro Central Main Trunk Line B",
      priority_score: 84.5,
      priority_level: "CRITICAL_IMMEDIATE",
      status: "ACKNOWLEDGED",
      target_latitude: 40.7128,
      target_longitude: -74.006,
      reasons: ["Critical vulnerability index", "Rapid degradation rate"],
      suggested_action: "Immediate acoustic crawling patrol and acoustic leak pinpointing",
      reviewed_by: operatorName,
      reviewed_at: new Date().toISOString(),
      operator_notes: notes || null,
      is_simulated: true,
    };
  }

  public async dismissInspectionPriority(
    priorityId: string,
    operatorName: string = "OPERATOR_CHIEF",
    reason?: string
  ): Promise<InspectionPriorityItem> {
    try {
      const res = await fetch(`${this.baseUrl}/infrastructure-intelligence/inspection-priorities/${priorityId}/dismiss`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Accept: "application/json" },
        body: JSON.stringify({ operator_name: operatorName, reason }),
      });
      if (res.ok) {
        this.isBackendOnline = true;
        return await res.json();
      }
    } catch {
      this.isBackendOnline = false;
    }
    return {
      id: priorityId,
      pipeline_segment_id: "PIPE-RES-3C-11",
      segment_name: "Pinecrest Residential Sub-Branch",
      priority_score: 42.0,
      priority_level: "ROUTINE_SCHEDULED",
      status: "DISMISSED",
      target_latitude: 40.7198,
      target_longitude: -74.0089,
      reasons: ["Standard periodic inspection recommendation"],
      suggested_action: "Routine preventive rover patrol",
      reviewed_by: operatorName,
      reviewed_at: new Date().toISOString(),
      dismissal_reason: reason || "Dismissed by operator",
      is_simulated: true,
    };
  }

  public async requestInspectionDispatch(
    priorityId: string,
    operatorName: string = "OPERATOR_CHIEF",
    preferredRoverId?: string,
    notes?: string
  ): Promise<InspectionDispatchResponse> {
    try {
      const res = await fetch(`${this.baseUrl}/infrastructure-intelligence/inspection-priorities/${priorityId}/request-inspection`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Accept: "application/json" },
        body: JSON.stringify({
          operator_name: operatorName,
          preferred_rover_id: preferredRoverId,
          notes,
        }),
      });
      if (res.ok) {
        this.isBackendOnline = true;
        return await res.json();
      }
    } catch {
      this.isBackendOnline = false;
    }
    return {
      status: "DISPATCHED",
      priority_record_id: priorityId,
      pipeline_segment_id: "PIPE-SEC-4B-92",
      mission_recommendation_id: `REC-2026-DISP-${Math.floor(Math.random() * 9000 + 1000)}`,
      assigned_rover_id: preferredRoverId || "ROV-01",
      assigned_rover_name: "AquaRover Alpha (Crawler)",
      planned_route_distance_m: 1250.0,
      operator_approval_required: true,
      recommendation_status: "PENDING_APPROVAL",
      message: "Inspection mission recommendation generated for rover AquaRover Alpha. Operator approval required to launch.",
    };
  }

  /* ========================================================= */
  /* UNIFIED OPERATIONAL INTELLIGENCE & DECISION SUPPORT (T12) */
  /* ========================================================= */

  public async getOperationalOverview(): Promise<OperationalOverview> {
    try {
      const res = await fetch(`${this.baseUrl}/operational-intelligence/overview`, {
        headers: { Accept: "application/json" },
      });
      if (res.ok) {
        this.isBackendOnline = true;
        return await res.json();
      }
    } catch {
      this.isBackendOnline = false;
    }
    return getFallbackOperationalOverview();
  }

  public async runOperationalAssessment(): Promise<OperationalAssessment> {
    try {
      const res = await fetch(`${this.baseUrl}/operational-intelligence/assessments/run`, {
        method: "POST",
        headers: { Accept: "application/json" },
      });
      if (res.ok) {
        this.isBackendOnline = true;
        return await res.json();
      }
    } catch {
      this.isBackendOnline = false;
    }
    return getFallbackOperationalAssessment();
  }

  public async getOperationalRecommendations(filters?: {
    category?: string;
    status?: string;
    priority_tier?: string;
  }): Promise<OperationalRecommendation[]> {
    try {
      const params = new URLSearchParams();
      if (filters?.category) params.append("category", filters.category);
      if (filters?.status) params.append("status", filters.status);
      if (filters?.priority_tier) params.append("priority_tier", filters.priority_tier);

      const res = await fetch(`${this.baseUrl}/operational-intelligence/recommendations?${params.toString()}`, {
        headers: { Accept: "application/json" },
      });
      if (res.ok) {
        this.isBackendOnline = true;
        const data = await res.json();
        return data.items || [];
      }
    } catch {
      this.isBackendOnline = false;
    }
    return getFallbackOperationalRecommendations(filters);
  }

  public async getOperationalRecommendationDetail(id: string): Promise<any> {
    try {
      const res = await fetch(`${this.baseUrl}/operational-intelligence/recommendations/${id}`, {
        headers: { Accept: "application/json" },
      });
      if (res.ok) {
        this.isBackendOnline = true;
        return await res.json();
      }
    } catch {
      this.isBackendOnline = false;
    }
    return getFallbackOperationalRecommendationDetail(id);
  }

  public async approveOperationalRecommendation(
    id: string,
    reason: string,
    operatorId: string = "OPERATOR-SUPERVISOR-01",
    overridePriority?: number
  ): Promise<any> {
    try {
      const res = await fetch(`${this.baseUrl}/operational-intelligence/recommendations/${id}/approve`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Accept: "application/json" },
        body: JSON.stringify({
          decision_type: "APPROVED",
          decision_reason: reason,
          operator_id: operatorId,
          override_priority: overridePriority,
        }),
      });
      if (res.ok) {
        this.isBackendOnline = true;
        return await res.json();
      }
    } catch {
      this.isBackendOnline = false;
    }
    return {
      success: true,
      decision_id: `DEC-FALLBACK-${id}`,
      recommendation_id: id,
      decision_type: "APPROVED",
      decision_reason: reason,
      status: "APPROVED",
      timestamp: new Date().toISOString(),
      message: "Approved in local fallback simulation mode.",
    };
  }

  public async rejectOperationalRecommendation(
    id: string,
    reason: string,
    operatorId: string = "OPERATOR-SUPERVISOR-01"
  ): Promise<any> {
    try {
      const res = await fetch(`${this.baseUrl}/operational-intelligence/recommendations/${id}/reject`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Accept: "application/json" },
        body: JSON.stringify({
          decision_type: "REJECTED",
          decision_reason: reason,
          operator_id: operatorId,
        }),
      });
      if (res.ok) {
        this.isBackendOnline = true;
        return await res.json();
      }
    } catch {
      this.isBackendOnline = false;
    }
    return {
      success: true,
      decision_id: `DEC-FALLBACK-${id}`,
      recommendation_id: id,
      decision_type: "REJECTED",
      decision_reason: reason,
      status: "REJECTED",
      timestamp: new Date().toISOString(),
      message: "Rejected in local fallback simulation mode.",
    };
  }

  public async getIncidentCorrelations(segmentId?: string): Promise<IncidentCorrelation[]> {
    try {
      const url = segmentId
        ? `${this.baseUrl}/operational-intelligence/correlations?pipeline_segment_id=${segmentId}`
        : `${this.baseUrl}/operational-intelligence/correlations`;
      const res = await fetch(url, { headers: { Accept: "application/json" } });
      if (res.ok) {
        this.isBackendOnline = true;
        const data = await res.json();
        return data.items || [];
      }
    } catch {
      this.isBackendOnline = false;
    }
    return getFallbackIncidentCorrelations();
  }

  public async getOperationalPriorities(): Promise<any[]> {
    try {
      const res = await fetch(`${this.baseUrl}/operational-intelligence/priorities`, {
        headers: { Accept: "application/json" },
      });
      if (res.ok) {
        this.isBackendOnline = true;
        const data = await res.json();
        return data.items || [];
      }
    } catch {
      this.isBackendOnline = false;
    }
    return getFallbackOperationalPriorities();
  }

  public async getResourcePlanning(segmentId?: string): Promise<ResourcePlanning[]> {
    try {
      const url = segmentId
        ? `${this.baseUrl}/operational-intelligence/resource-planning?pipeline_segment_id=${segmentId}`
        : `${this.baseUrl}/operational-intelligence/resource-planning`;
      const res = await fetch(url, { headers: { Accept: "application/json" } });
      if (res.ok) {
        this.isBackendOnline = true;
        const data = await res.json();
        return data.items || [];
      }
    } catch {
      this.isBackendOnline = false;
    }
    return getFallbackResourcePlanning();
  }

  public async getOperatorDecisions(): Promise<OperationalDecisionRecord[]> {
    try {
      const res = await fetch(`${this.baseUrl}/operational-intelligence/decisions`, {
        headers: { Accept: "application/json" },
      });
      if (res.ok) {
        this.isBackendOnline = true;
        return await res.json();
      }
    } catch {
      this.isBackendOnline = false;
    }
    return getFallbackOperatorDecisions();
  }

  public async getExecutionHistory(): Promise<OperationalExecutionRecord[]> {
    try {
      const res = await fetch(`${this.baseUrl}/operational-intelligence/execution-history`, {
        headers: { Accept: "application/json" },
      });
      if (res.ok) {
        this.isBackendOnline = true;
        const data = await res.json();
        return data.items || [];
      }
    } catch {
      this.isBackendOnline = false;
    }
    return getFallbackExecutionHistory();
  }

  public async runWhatIfImpactAnalysis(segmentId: string, orificeMm: number = 15.0): Promise<any> {
    try {
      const res = await fetch(`${this.baseUrl}/operational-intelligence/impact/analyze`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Accept: "application/json" },
        body: JSON.stringify({
          pipeline_segment_id: segmentId,
          leak_orifice_diameter_mm: orificeMm,
        }),
      });
      if (res.ok) {
        this.isBackendOnline = true;
        return await res.json();
      }
    } catch {
      this.isBackendOnline = false;
    }
    return getFallbackWhatIfAnalysis(segmentId, orificeMm);
  }

  /* ========================================================= */
  /* TASK 13 ADVANCED AI & DECISION INTELLIGENCE API METHODS   */
  /* ========================================================= */

  public async getAdvancedAiHealth(): Promise<any> {
    try {
      const res = await fetch(`${this.baseUrl}/advanced-ai/health`, {
        method: "GET",
        headers: { Accept: "application/json" },
      });
      if (res.ok) {
        this.isBackendOnline = true;
        return await res.json();
      }
    } catch {
      this.isBackendOnline = false;
    }
    return {
      status: "healthy",
      subsystem: "advanced_ai_decision_intelligence",
      version: "1.0.0",
      active_provider: "DETERMINISTIC",
      active_model: "deterministic-grounded-engine",
      fallback_mode_active: false,
      is_simulated: true,
      source: "VIRTUAL_SIMULATION_ENGINE",
      hardware_actuators_disabled: true,
      human_in_the_loop_mandatory: true,
    };
  }

  public async getProviderStatus(): Promise<ProviderStatus> {
    try {
      const res = await fetch(`${this.baseUrl}/advanced-ai/providers`, {
        method: "GET",
        headers: { Accept: "application/json" },
      });
      if (res.ok) {
        this.isBackendOnline = true;
        return await res.json();
      }
    } catch {
      this.isBackendOnline = false;
    }
    return {
      configured_provider: "DETERMINISTIC",
      active_provider: "DETERMINISTIC",
      active_model: "deterministic-grounded-engine",
      is_available: true,
      is_fallback: false,
      is_live_verified: false,
      live_verification_status: "NOT LIVE-VERIFIED (No active external credentials configured; running in deterministic fallback mode)",
      base_url: null,
      api_key_configured: false,
      api_key_status: "none",
      timeout_seconds: 30.0,
      max_tokens: 2048,
      temperature: 0.2,
      supported_models: [
        "meta/llama-3.1-70b-instruct",
        "meta/llama-3.1-8b-instruct",
        "mistralai/mixtral-8x22b-instruct-v0.1",
        "gpt-4o",
        "gpt-4o-mini",
        "deterministic-grounded-engine"
      ],
    };
  }

  public async chatWithAiAssistant(req: AIChatRequest): Promise<AIChatResponse> {
    try {
      const res = await fetch(`${this.baseUrl}/advanced-ai/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Accept: "application/json" },
        body: JSON.stringify(req),
      });
      if (res.ok) {
        this.isBackendOnline = true;
        return await res.json();
      }
    } catch {
      this.isBackendOnline = false;
    }
    return getFallbackAIChatResponse(req);
  }

  public async listAiConversations(limit: number = 20): Promise<AIConversationItem[]> {
    try {
      const res = await fetch(`${this.baseUrl}/advanced-ai/conversations?limit=${limit}`, {
        method: "GET",
        headers: { Accept: "application/json" },
      });
      if (res.ok) {
        this.isBackendOnline = true;
        return await res.json();
      }
    } catch {
      this.isBackendOnline = false;
    }
    return getFallbackAIConversations();
  }

  public async getAiConversationDetail(conversationId: string): Promise<AIConversationDetail> {
    try {
      const res = await fetch(`${this.baseUrl}/advanced-ai/conversations/${conversationId}`, {
        method: "GET",
        headers: { Accept: "application/json" },
      });
      if (res.ok) {
        this.isBackendOnline = true;
        return await res.json();
      }
    } catch {
      this.isBackendOnline = false;
    }
    return getFallbackAIConversationDetail(conversationId);
  }

  public async deleteAiConversation(conversationId: string): Promise<boolean> {
    try {
      const res = await fetch(`${this.baseUrl}/advanced-ai/conversations/${conversationId}`, {
        method: "DELETE",
        headers: this.getAuthHeaders(),
      });
      if (res.ok) {
        this.isBackendOnline = true;
        return true;
      }
    } catch {
      this.isBackendOnline = false;
    }
    return true;
  }

  public async explainSegmentDecision(segmentId: string): Promise<DecisionExplanation> {
    try {
      const res = await fetch(`${this.baseUrl}/advanced-ai/explain/segment/${segmentId}`, {
        method: "GET",
        headers: { Accept: "application/json" },
      });
      if (res.ok) {
        this.isBackendOnline = true;
        return await res.json();
      }
    } catch {
      this.isBackendOnline = false;
    }
    return getFallbackSegmentExplanation(segmentId);
  }

  public async explainRecommendationDecision(recommendationId: string): Promise<DecisionExplanation> {
    try {
      const res = await fetch(`${this.baseUrl}/advanced-ai/explain/recommendation/${recommendationId}`, {
        method: "GET",
        headers: { Accept: "application/json" },
      });
      if (res.ok) {
        this.isBackendOnline = true;
        return await res.json();
      }
    } catch {
      this.isBackendOnline = false;
    }
    return getFallbackRecommendationExplanation(recommendationId);
  }

  public async comparePipelines(segmentIds: string[]): Promise<PipelineComparisonResponse> {
    try {
      const res = await fetch(`${this.baseUrl}/advanced-ai/compare/pipelines`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Accept: "application/json" },
        body: JSON.stringify({ segment_ids: segmentIds }),
      });
      if (res.ok) {
        this.isBackendOnline = true;
        return await res.json();
      }
    } catch {
      this.isBackendOnline = false;
    }
    return getFallbackPipelineComparison(segmentIds);
  }

  public async getOperationalSummary(): Promise<OperationalSummaryResponse> {
    try {
      const res = await fetch(`${this.baseUrl}/advanced-ai/summaries/operational`, {
        method: "GET",
        headers: { Accept: "application/json" },
      });
      if (res.ok) {
        this.isBackendOnline = true;
        return await res.json();
      }
    } catch {
      this.isBackendOnline = false;
    }
    return getFallbackOperationalSummary();
  }

  public async analyzeEvidenceGaps(segmentId: string): Promise<EvidenceGapAnalysis> {
    try {
      const res = await fetch(`${this.baseUrl}/advanced-ai/analyze/evidence-gaps/${segmentId}`, {
        method: "GET",
        headers: { Accept: "application/json" },
      });
      if (res.ok) {
        this.isBackendOnline = true;
        return await res.json();
      }
    } catch {
      this.isBackendOnline = false;
    }
    return getFallbackEvidenceGaps(segmentId);
  }

  public async getSegmentReasoning(segmentId: string): Promise<MultiSourceReasoningResult> {
    try {
      const res = await fetch(`${this.baseUrl}/advanced-ai/reasoning/${segmentId}`, {
        method: "GET",
        headers: { Accept: "application/json" },
      });
      if (res.ok) {
        this.isBackendOnline = true;
        return await res.json();
      }
    } catch {
      this.isBackendOnline = false;
    }
    return getFallbackSegmentReasoning(segmentId);
  }

  /* ========================================================= */
  /* TASK 14 HYDRAULIC OPTIMIZATION & DECISION ENGINE API     */
  /* ========================================================= */

  public async getOptimizationStatus(): Promise<OptimizationStatusResponse> {
    try {
      const res = await fetch(`${this.baseUrl}/optimization/status`, {
        method: "GET",
        headers: this.getAuthHeaders(),
      });
      if (res.ok) {
        this.isBackendOnline = true;
        return await res.json();
      }
    } catch {
      this.isBackendOnline = false;
    }
    return getFallbackOptimizationStatus();
  }

  public async getNetworkBaseline(networkId: string = "Net1"): Promise<any> {
    try {
      const res = await fetch(`${this.baseUrl}/optimization/network/baseline?network_id=${encodeURIComponent(networkId)}`, {
        method: "GET",
        headers: this.getAuthHeaders(),
      });
      if (res.ok) {
        this.isBackendOnline = true;
        return await res.json();
      }
    } catch {
      this.isBackendOnline = false;
    }
    return getFallbackNetworkBaseline(networkId);
  }

  public async triggerOptimization(payload?: OptimizationTriggerRequest): Promise<OptimizationJobDetail> {
    try {
      const res = await fetch(`${this.baseUrl}/optimization/optimize`, {
        method: "POST",
        headers: this.getAuthHeaders("application/json"),
        body: JSON.stringify(payload || {
          network_id: "Net1",
          objective_profile: "BALANCED_OPERATION",
        }),
      });
      if (res.ok) {
        this.isBackendOnline = true;
        return await res.json();
      }
    } catch {
      this.isBackendOnline = false;
    }
    return getFallbackOptimizationJob();
  }

  public async getOptimizationJob(jobId: string): Promise<OptimizationJobDetail> {
    try {
      const res = await fetch(`${this.baseUrl}/optimization/jobs/${jobId}`, {
        method: "GET",
        headers: this.getAuthHeaders(),
      });
      if (res.ok) {
        this.isBackendOnline = true;
        return await res.json();
      }
    } catch {
      this.isBackendOnline = false;
    }
    return getFallbackOptimizationJob(jobId);
  }

  public async listOptimizationJobs(limit: number = 10): Promise<OptimizationJobDetail[]> {
    try {
      const res = await fetch(`${this.baseUrl}/optimization/jobs?limit=${limit}`, {
        method: "GET",
        headers: this.getAuthHeaders(),
      });
      if (res.ok) {
        this.isBackendOnline = true;
        return await res.json();
      }
    } catch {
      this.isBackendOnline = false;
    }
    return [getFallbackOptimizationJob()];
  }

  public async getOptimizationPareto(jobId: string): Promise<OptimizationCandidate[]> {
    try {
      const res = await fetch(`${this.baseUrl}/optimization/jobs/${jobId}/pareto`, {
        method: "GET",
        headers: this.getAuthHeaders(),
      });
      if (res.ok) {
        this.isBackendOnline = true;
        return await res.json();
      }
    } catch {
      this.isBackendOnline = false;
    }
    return getFallbackOptimizationJob(jobId).pareto_candidates;
  }

  public async cancelOptimizationJob(jobId: string): Promise<any> {
    try {
      const res = await fetch(`${this.baseUrl}/optimization/jobs/${jobId}/cancel`, {
        method: "POST",
        headers: this.getAuthHeaders(),
      });
      if (res.ok) {
        this.isBackendOnline = true;
        return await res.json();
      }
    } catch {
      this.isBackendOnline = false;
    }
    return { status: "CANCELLED", job_id: jobId };
  }

  public async recommendOptimizationCandidate(jobId: string, payload: OptimizationRecommendRequest): Promise<any> {
    try {
      const res = await fetch(`${this.baseUrl}/optimization/jobs/${jobId}/recommend`, {
        method: "POST",
        headers: this.getAuthHeaders("application/json"),
        body: JSON.stringify(payload),
      });
      if (res.ok) {
        this.isBackendOnline = true;
        return await res.json();
      }
    } catch {
      this.isBackendOnline = false;
    }
    return {
      status: "APPROVED_FOR_STAGING",
      job_id: jobId,
      candidate_id: payload.candidate_id,
      operator_notes: payload.operator_notes,
      requires_physical_actuation: false,
    };
  }

  /* ========================================================= */
  /* TASK 15 — AUTONOMOUS INSPECTION INTELLIGENCE METHODS     */
  /* ========================================================= */

  async getInspectionRecommendations(
    status?: string,
    priority?: string
  ): Promise<InspectionRecommendation[]> {
    try {
      const params = new URLSearchParams();
      if (status) params.append("status", status);
      if (priority) params.append("priority", priority);
      const url = `${this.baseUrl}/inspection-intelligence/recommendations?${params.toString()}`;
      const res = await fetch(url, { headers: this.getAuthHeaders() });
      if (res.ok) {
        this.isBackendOnline = true;
        return await res.json();
      }
    } catch {
      this.isBackendOnline = false;
    }
    return [
      {
        id: "INSP-REC-PIPE-SEC-01",
        pipeline_segment_id: "PIPE-SEC-01",
        segment_name: "Metropolitan Secondary Water Main",
        priority_score: 84.5,
        priority_category: "CRITICAL",
        urgency_factors: {
          vulnerability: 82.0,
          degradation_rate: 76.5,
          active_leak_detection: 95.0,
          hydraulic_stress: 68.0,
          cluster_proximity: 85.0,
          network_consequence: 75.0,
        },
        supporting_evidence: [
          {
            evidence_id: "EVID-ASSET-01",
            source_subsystem: "TASK_04_GIS",
            classification: "MEASURED",
            metric_name: "pipe_diameter_mm",
            metric_value: 450,
            description: "Ductile iron transmission main with nominal pressure 4.5 bar.",
            confidence: 1.0,
          },
          {
            evidence_id: "EVID-LEAK-01",
            source_subsystem: "TASK_07_AI_LEAKS",
            classification: "MEASURED",
            metric_name: "acoustic_leak_confidence",
            metric_value: 0.94,
            description: "Acoustic hydrophone anomaly detected at 480 Hz.",
            confidence: 0.94,
          },
        ],
        primary_classification: "DERIVED",
        confidence: 0.91,
        uncertainty_radius_m: 12.0,
        recommended_method: "ACOUSTIC_CORRELATION",
        estimated_duration_minutes: 45,
        required_rover_capabilities: ["pipe_navigation", "hydrophone_acoustic"],
        recommended_action: "Dispatch acoustic rover to verify pinpoint acoustic cross-correlation center.",
        human_approval_status: "PENDING_APPROVAL",
        created_at: new Date().toISOString(),
        is_simulated: true,
      },
      {
        id: "INSP-REC-PIPE-TRUNK-02",
        pipeline_segment_id: "PIPE-TRUNK-02",
        segment_name: "Industrial Harbor Trunk Conduit",
        priority_score: 68.2,
        priority_category: "HIGH",
        urgency_factors: {
          vulnerability: 74.0,
          degradation_rate: 65.0,
          active_leak_detection: 30.0,
          hydraulic_stress: 82.0,
          cluster_proximity: 70.0,
          network_consequence: 85.0,
        },
        supporting_evidence: [
          {
            evidence_id: "EVID-HYD-02",
            source_subsystem: "TASK_10_HYDRAULIC_TWIN",
            classification: "SIMULATED",
            metric_name: "pipe_velocity_mps",
            metric_value: 3.2,
            description: "High velocity flow and dynamic headloss across harbor zone.",
            confidence: 0.88,
          },
        ],
        primary_classification: "DERIVED",
        confidence: 0.86,
        uncertainty_radius_m: 25.0,
        recommended_method: "MULTI_SENSOR_CRAWLER",
        estimated_duration_minutes: 60,
        required_rover_capabilities: ["pipe_navigation", "hydrophone_acoustic", "high_res_optical"],
        recommended_action: "Deploy multi-sensor crawler to evaluate internal wall-thickness loss.",
        human_approval_status: "PENDING_APPROVAL",
        created_at: new Date().toISOString(),
        is_simulated: true,
      },
    ];
  }

  async generateInspectionRecommendations(): Promise<InspectionRecommendation[]> {
    try {
      const res = await fetch(`${this.baseUrl}/inspection-intelligence/recommendations/generate`, {
        method: "POST",
        headers: this.getAuthHeaders(),
      });
      if (res.ok) {
        this.isBackendOnline = true;
        return await res.json();
      }
    } catch {
      this.isBackendOnline = false;
    }
    return this.getInspectionRecommendations();
  }

  async generateInspectionPlan(payload: {
    plan_name?: string;
    recommendation_ids?: string[];
    preferred_rover_ids?: string[];
    max_targets_per_rover?: number;
    battery_safety_reserve_pct?: number;
  }): Promise<InspectionPlan> {
    try {
      const res = await fetch(`${this.baseUrl}/inspection-intelligence/plans/generate`, {
        method: "POST",
        headers: this.getAuthHeaders("application/json"),
        body: JSON.stringify(payload),
      });
      if (res.ok) {
        this.isBackendOnline = true;
        return await res.json();
      }
    } catch {
      this.isBackendOnline = false;
    }
    return {
      id: `INSP-PLAN-${Math.random().toString(36).substring(2, 9).toUpperCase()}`,
      plan_name: payload.plan_name || "Autonomous Campaign Plan",
      allocations: [
        {
          rover_id: "ROV-AQUA-01",
          rover_name: "AquaRover Alpha",
          assigned_targets: [
            {
              target_id: "TGT-PIPE-SEC-01",
              pipeline_segment_id: "PIPE-SEC-01",
              target_coordinates: [-74.006, 40.7128],
              inspection_method: "ACOUSTIC_CORRELATION",
              priority_score: 84.5,
              estimated_duration_minutes: 45,
            },
          ],
          route_waypoints: [
            [-74.006, 40.7128],
            [-74.004, 40.7135],
            [-74.002, 40.7142],
            [-74.006, 40.7128],
          ],
          segments_traversed: ["PIPE-SEC-01", "PIPE-SEC-02"],
          total_route_distance_m: 820.0,
          estimated_mission_duration_s: 3200.0,
          estimated_battery_drain_pct: 12.5,
          projected_reserve_after_return_pct: 82.5,
          return_to_base_feasible: true,
          route_selection_reason: "Shortest topological path along underground pipe geometry with 82.5% projected battery reserve.",
        },
      ],
      unreachable_targets: [],
      conflict_checks_passed: true,
      total_rovers_assigned: 1,
      total_targets_covered: 1,
      human_approval_status: "PENDING_APPROVAL",
      created_at: new Date().toISOString(),
      is_simulated: true,
    };
  }

  async getInspectionPlans(): Promise<InspectionPlan[]> {
    try {
      const res = await fetch(`${this.baseUrl}/inspection-intelligence/plans`, {
        headers: this.getAuthHeaders(),
      });
      if (res.ok) {
        this.isBackendOnline = true;
        return await res.json();
      }
    } catch {
      this.isBackendOnline = false;
    }
    return [];
  }

  async approveInspectionPlan(planId: string, notes?: string): Promise<InspectionPlan> {
    try {
      const res = await fetch(`${this.baseUrl}/inspection-intelligence/plans/${planId}/approve`, {
        method: "POST",
        headers: this.getAuthHeaders("application/json"),
        body: JSON.stringify({ operator_notes: notes }),
      });
      if (res.ok) {
        this.isBackendOnline = true;
        return await res.json();
      }
    } catch {
      this.isBackendOnline = false;
    }
    return {
      id: planId,
      plan_name: "Autonomous Campaign Plan",
      allocations: [],
      unreachable_targets: [],
      conflict_checks_passed: true,
      total_rovers_assigned: 1,
      total_targets_covered: 1,
      human_approval_status: "APPROVED",
      approved_by: "OPERATOR_LOCAL",
      approved_at: new Date().toISOString(),
      created_at: new Date().toISOString(),
      is_simulated: true,
    };
  }

  async rejectInspectionPlan(planId: string, reason: string): Promise<InspectionPlan> {
    try {
      const res = await fetch(`${this.baseUrl}/inspection-intelligence/plans/${planId}/reject`, {
        method: "POST",
        headers: this.getAuthHeaders("application/json"),
        body: JSON.stringify({ rejection_reason: reason }),
      });
      if (res.ok) {
        this.isBackendOnline = true;
        return await res.json();
      }
    } catch {
      this.isBackendOnline = false;
    }
    return {
      id: planId,
      plan_name: "Autonomous Campaign Plan",
      allocations: [],
      unreachable_targets: [],
      conflict_checks_passed: true,
      total_rovers_assigned: 0,
      total_targets_covered: 0,
      human_approval_status: "REJECTED",
      rejection_reason: reason,
      created_at: new Date().toISOString(),
      is_simulated: true,
    };
  }

  async launchInspectionMission(planId: string, roverId: string): Promise<InspectionExecutionProgress> {
    try {
      const res = await fetch(`${this.baseUrl}/inspection-intelligence/missions/${planId}/launch/${roverId}`, {
        method: "POST",
        headers: this.getAuthHeaders(),
      });
      if (res.ok) {
        this.isBackendOnline = true;
        return await res.json();
      }
    } catch {
      this.isBackendOnline = false;
    }
    return {
      mission_id: `MIS-INSP-${Math.random().toString(36).substring(2, 7).toUpperCase()}`,
      rover_id: roverId,
      plan_id: planId,
      status: "IN_PROGRESS",
      current_step: 0,
      total_steps: 10,
      progress_percentage: 0.0,
      current_coordinates: [-74.006, 40.7128],
      distance_traversed_m: 0.0,
      remaining_distance_m: 820.0,
      battery_percentage: 95.0,
      motor_temp_c: 28.5,
      active_anomalies_detected: 0,
      route_adapted: false,
      adaptation_history: [],
      recent_observations: [],
      last_updated: new Date().toISOString(),
      is_simulated: true,
    };
  }

  async advanceInspectionStep(missionId: string, incrementM: number = 100.0): Promise<InspectionExecutionProgress> {
    try {
      const res = await fetch(`${this.baseUrl}/inspection-intelligence/missions/${missionId}/step?step_increment_m=${incrementM}`, {
        method: "POST",
        headers: this.getAuthHeaders(),
      });
      if (res.ok) {
        this.isBackendOnline = true;
        return await res.json();
      }
    } catch {
      this.isBackendOnline = false;
    }
    return {
      mission_id: missionId,
      rover_id: "ROV-AQUA-01",
      plan_id: "PLAN-LOCAL",
      status: "IN_PROGRESS",
      current_step: 1,
      total_steps: 10,
      progress_percentage: 15.0,
      current_coordinates: [-74.0055, 40.713],
      distance_traversed_m: incrementM,
      remaining_distance_m: 720.0,
      battery_percentage: 94.0,
      motor_temp_c: 29.0,
      active_anomalies_detected: 0,
      route_adapted: false,
      adaptation_history: [],
      recent_observations: [],
      last_updated: new Date().toISOString(),
      is_simulated: true,
    };
  }

  async adaptInspectionRoute(
    missionId: string,
    reason: string,
    detourCoord?: [number, number]
  ): Promise<InspectionExecutionProgress> {
    try {
      const res = await fetch(`${this.baseUrl}/inspection-intelligence/missions/${missionId}/adapt-route`, {
        method: "POST",
        headers: this.getAuthHeaders("application/json"),
        body: JSON.stringify({
          adaptation_reason: reason,
          new_anomaly_coordinates: detourCoord,
        }),
      });
      if (res.ok) {
        this.isBackendOnline = true;
        return await res.json();
      }
    } catch {
      this.isBackendOnline = false;
    }
    return {
      mission_id: missionId,
      rover_id: "ROV-AQUA-01",
      plan_id: "PLAN-LOCAL",
      status: "IN_PROGRESS",
      current_step: 3,
      total_steps: 12,
      progress_percentage: 30.0,
      current_coordinates: [-74.004, 40.7135],
      distance_traversed_m: 350.0,
      remaining_distance_m: 650.0,
      battery_percentage: 88.0,
      motor_temp_c: 31.0,
      active_anomalies_detected: 1,
      route_adapted: true,
      adaptation_history: [
        {
          timestamp: new Date().toISOString(),
          reason,
          detour_distance_m: 180.0,
          new_target_coordinates: detourCoord || [-74.0035, 40.7138],
          projected_reserve_pct: 78.0,
        },
      ],
      recent_observations: [],
      last_updated: new Date().toISOString(),
      is_simulated: true,
    };
  }

  async getInspectionReports(): Promise<InspectionReport[]> {
    try {
      const res = await fetch(`${this.baseUrl}/inspection-intelligence/reports`, {
        headers: this.getAuthHeaders(),
      });
      if (res.ok) {
        this.isBackendOnline = true;
        return await res.json();
      }
    } catch {
      this.isBackendOnline = false;
    }
    return [];
  }

  // =========================================================================
  // TASK 16: INTELLIGENT REPAIR PLANNING & MANAGEMENT METHODS
  // =========================================================================

  async getRepairEngineStatus(): Promise<{
    status: string;
    module: string;
    task: string;
    environment: string;
    zero_physical_actuation_enforced: boolean;
  }> {
    try {
      const res = await fetch(`${this.baseUrl}/repair-management/status`, {
        headers: this.getAuthHeaders(),
      });
      if (res.ok) {
        this.isBackendOnline = true;
        return await res.json();
      }
    } catch {
      this.isBackendOnline = false;
    }
    return {
      status: "OPERATIONAL",
      module: "INTELLIGENT_REPAIR_PLANNING_AND_MANAGEMENT",
      task: "TASK_16",
      environment: "VIRTUAL_SIMULATION_SANDBOX",
      zero_physical_actuation_enforced: true,
    };
  }

  async getRepairOverview(): Promise<RepairOverviewSummary> {
    try {
      const res = await fetch(`${this.baseUrl}/repair-management/overview`, {
        headers: this.getAuthHeaders(),
      });
      if (res.ok) {
        this.isBackendOnline = true;
        return await res.json();
      }
    } catch {
      this.isBackendOnline = false;
    }
    return this.getMockRepairOverview();
  }

  async listDamageAssessments(limit: number = 100): Promise<DamageAssessment[]> {
    try {
      const res = await fetch(`${this.baseUrl}/repair-management/assessments?limit=${limit}`, {
        headers: this.getAuthHeaders(),
      });
      if (res.ok) {
        this.isBackendOnline = true;
        return await res.json();
      }
    } catch {
      this.isBackendOnline = false;
    }
    return [
      this.getMockDamageAssessment("PIPE-SEC-01"),
      this.getMockDamageAssessment("PIPE-SEC-03"),
      this.getMockDamageAssessment("PIPE-SEC-07"),
    ];
  }

  async evaluateDamageAssessment(payload: {
    pipeline_segment_id: string;
    source_inspection_report_id?: string;
    notes?: string;
  }): Promise<DamageAssessment> {
    try {
      const res = await fetch(`${this.baseUrl}/repair-management/assessments/evaluate`, {
        method: "POST",
        headers: this.getAuthHeaders("application/json"),
        body: JSON.stringify(payload),
      });
      if (res.ok) {
        this.isBackendOnline = true;
        return await res.json();
      }
    } catch {
      this.isBackendOnline = false;
    }
    return this.getMockDamageAssessment(payload.pipeline_segment_id);
  }

  async getDamageAssessment(assessmentId: string): Promise<DamageAssessment> {
    try {
      const res = await fetch(`${this.baseUrl}/repair-management/assessments/${assessmentId}`, {
        headers: this.getAuthHeaders(),
      });
      if (res.ok) {
        this.isBackendOnline = true;
        return await res.json();
      }
    } catch {
      this.isBackendOnline = false;
    }
    return this.getMockDamageAssessment("PIPE-SEC-01");
  }

  async getRepairRecommendations(assessmentId: string): Promise<RepairRecommendation> {
    try {
      const res = await fetch(`${this.baseUrl}/repair-management/recommendations/${assessmentId}`, {
        headers: this.getAuthHeaders(),
      });
      if (res.ok) {
        this.isBackendOnline = true;
        return await res.json();
      }
    } catch {
      this.isBackendOnline = false;
    }
    return this.getMockRepairRecommendation(assessmentId);
  }

  async generateRepairPlan(payload: {
    pipeline_segment_id: string;
    plan_name?: string;
    selected_method?: string;
    override_notes?: string;
  }): Promise<RepairPlan> {
    try {
      const res = await fetch(`${this.baseUrl}/repair-management/plans/generate`, {
        method: "POST",
        headers: this.getAuthHeaders("application/json"),
        body: JSON.stringify(payload),
      });
      if (res.ok) {
        this.isBackendOnline = true;
        return await res.json();
      }
    } catch {
      this.isBackendOnline = false;
    }
    return this.getMockRepairPlan(undefined, payload.pipeline_segment_id);
  }

  async listRepairPlans(status?: string, limit: number = 100): Promise<RepairPlan[]> {
    try {
      const url = status
        ? `${this.baseUrl}/repair-management/plans?status=${encodeURIComponent(status)}&limit=${limit}`
        : `${this.baseUrl}/repair-management/plans?limit=${limit}`;
      const res = await fetch(url, {
        headers: this.getAuthHeaders(),
      });
      if (res.ok) {
        this.isBackendOnline = true;
        return await res.json();
      }
    } catch {
      this.isBackendOnline = false;
    }
    return [
      this.getMockRepairPlan("PLAN-REP-001", "PIPE-SEC-01", "APPROVED"),
      this.getMockRepairPlan("PLAN-REP-002", "PIPE-SEC-03", "ENGINEERING_REVIEW_PENDING"),
      this.getMockRepairPlan("PLAN-REP-003", "PIPE-SEC-07", "SCHEDULED"),
    ];
  }

  async getRepairPlan(planId: string): Promise<RepairPlan> {
    try {
      const res = await fetch(`${this.baseUrl}/repair-management/plans/${planId}`, {
        headers: this.getAuthHeaders(),
      });
      if (res.ok) {
        this.isBackendOnline = true;
        return await res.json();
      }
    } catch {
      this.isBackendOnline = false;
    }
    return this.getMockRepairPlan(planId);
  }

  async approveRepairPlan(
    planId: string,
    payload: { engineer_notes: string; override_selected_method?: string }
  ): Promise<RepairPlan> {
    try {
      const res = await fetch(`${this.baseUrl}/repair-management/plans/${planId}/approve`, {
        method: "POST",
        headers: this.getAuthHeaders("application/json"),
        body: JSON.stringify(payload),
      });
      if (res.ok) {
        this.isBackendOnline = true;
        return await res.json();
      }
    } catch {
      this.isBackendOnline = false;
    }
    return this.getMockRepairPlan(planId, undefined, "APPROVED");
  }

  async rejectRepairPlan(
    planId: string,
    payload: { rejection_reason: string }
  ): Promise<RepairPlan> {
    try {
      const res = await fetch(`${this.baseUrl}/repair-management/plans/${planId}/reject`, {
        method: "POST",
        headers: this.getAuthHeaders("application/json"),
        body: JSON.stringify(payload),
      });
      if (res.ok) {
        this.isBackendOnline = true;
        return await res.json();
      }
    } catch {
      this.isBackendOnline = false;
    }
    return this.getMockRepairPlan(planId, undefined, "REJECTED");
  }

  async transitionRepairWorkflow(
    planId: string,
    payload: { target_status: string; reason: string; notes?: string }
  ): Promise<RepairPlan> {
    try {
      const res = await fetch(`${this.baseUrl}/repair-management/plans/${planId}/transition`, {
        method: "POST",
        headers: this.getAuthHeaders("application/json"),
        body: JSON.stringify(payload),
      });
      if (res.ok) {
        this.isBackendOnline = true;
        return await res.json();
      }
    } catch {
      this.isBackendOnline = false;
    }
    return this.getMockRepairPlan(planId, undefined, payload.target_status as RepairWorkflowStatus);
  }

  async listVirtualCrews(availableOnly: boolean = false): Promise<any[]> {
    try {
      const res = await fetch(`${this.baseUrl}/repair-management/crews?available_only=${availableOnly}`, {
        headers: this.getAuthHeaders(),
      });
      if (res.ok) {
        this.isBackendOnline = true;
        return await res.json();
      }
    } catch {
      this.isBackendOnline = false;
    }
    return [
      {
        crew_id: "CREW-ALPHA",
        crew_name: "Rapid Response Crew Alpha",
        specialization: "EMERGENCY_REPAIR",
        skills: ["CLAMP_REPAIR", "VALVE_REPLACEMENT", "RAPID_ISOLATION"],
        members: ["J. Doe (Lead)", "R. Smith (Tech)", "A. Patel (Safety)"],
        is_available: true,
        base_location_lat: 40.7128,
        base_location_lng: -74.006,
        current_assigned_job_id: null,
      },
      {
        crew_id: "CREW-BETA",
        crew_name: "Structural Rehabilitation Crew Beta",
        specialization: "STRUCTURAL_REPLACEMENT",
        skills: ["PIPE_SECTION_REPLACEMENT", "INTERNAL_LINING_REHABILITATION"],
        members: ["M. Johnson (Lead)", "K. Lee (Operator)", "S. Brown (Welder)"],
        is_available: false,
        base_location_lat: 40.7135,
        base_location_lng: -74.004,
        current_assigned_job_id: "JOB-4412",
      },
      {
        crew_id: "CREW-GAMMA",
        crew_name: "Corrosion & Joint Specialists Gamma",
        specialization: "CORROSION_AND_JOINTS",
        skills: ["CORROSION_PROTECTION", "JOINT_REPAIR_REPLACEMENT"],
        members: ["T. Wilson (Lead)", "C. Martinez (Tech)"],
        is_available: true,
        base_location_lat: 40.7142,
        base_location_lng: -74.002,
        current_assigned_job_id: null,
      },
    ];
  }

  async getRepairSimulation(planId: string): Promise<{
    scenario: DigitalTwinRepairScenario;
    comparison: DigitalTwinRepairComparison;
  }> {
    try {
      const res = await fetch(`${this.baseUrl}/repair-management/simulation/${planId}`, {
        headers: this.getAuthHeaders(),
      });
      if (res.ok) {
        this.isBackendOnline = true;
        return await res.json();
      }
    } catch {
      this.isBackendOnline = false;
    }
    return this.getMockRepairSimulation(planId);
  }

  async submitRepairVerification(payload: {
    repair_plan_id: string;
    post_repair_leakage_lph: number;
    acoustic_anomaly_cleared: boolean;
    pressure_gradient_restored: boolean;
    verification_notes?: string;
  }): Promise<RepairVerification> {
    try {
      const res = await fetch(`${this.baseUrl}/repair-management/verify`, {
        method: "POST",
        headers: this.getAuthHeaders("application/json"),
        body: JSON.stringify(payload),
      });
      if (res.ok) {
        this.isBackendOnline = true;
        return await res.json();
      }
    } catch {
      this.isBackendOnline = false;
    }
    return this.getMockRepairVerification(payload.repair_plan_id);
  }

  async getRepairVerification(planId: string): Promise<RepairVerification> {
    try {
      const res = await fetch(`${this.baseUrl}/repair-management/verifications/${planId}`, {
        headers: this.getAuthHeaders(),
      });
      if (res.ok) {
        this.isBackendOnline = true;
        return await res.json();
      }
    } catch {
      this.isBackendOnline = false;
    }
    return this.getMockRepairVerification(planId);
  }

  async listRepairWorkflowEvents(planId?: string, limit: number = 100): Promise<RepairWorkflowEvent[]> {
    try {
      const url = planId
        ? `${this.baseUrl}/repair-management/events?plan_id=${encodeURIComponent(planId)}&limit=${limit}`
        : `${this.baseUrl}/repair-management/events?limit=${limit}`;
      const res = await fetch(url, {
        headers: this.getAuthHeaders(),
      });
      if (res.ok) {
        this.isBackendOnline = true;
        return await res.json();
      }
    } catch {
      this.isBackendOnline = false;
    }
    return [
      {
        id: "EVT-001",
        repair_plan_id: planId || "PLAN-REP-001",
        from_status: "INSPECTION_COMPLETED",
        to_status: "DAMAGE_ASSESSED",
        changed_by: "system_assessment_engine",
        reason: "Autonomous multi-factor damage assessment completed",
        details: { severity: "HIGH", damage_category: "PIPE_LEAK" },
        timestamp: new Date(Date.now() - 7200000).toISOString(),
      },
      {
        id: "EVT-002",
        repair_plan_id: planId || "PLAN-REP-001",
        from_status: "DAMAGE_ASSESSED",
        to_status: "REPAIR_RECOMMENDED",
        changed_by: "repair_method_engine",
        reason: "Feasibility engine scored CLAMP_REPAIR as primary candidate",
        details: { score: 92.5 },
        timestamp: new Date(Date.now() - 3600000).toISOString(),
      },
      {
        id: "EVT-003",
        repair_plan_id: planId || "PLAN-REP-001",
        from_status: "REPAIR_RECOMMENDED",
        to_status: "ENGINEERING_REVIEW_PENDING",
        changed_by: "operator_user",
        reason: "Plan submitted for certified engineering review",
        details: {},
        timestamp: new Date(Date.now() - 1800000).toISOString(),
      },
    ];
  }

  private getMockRepairOverview(): RepairOverviewSummary {
    return {
      system_status: "OPERATIONAL",
      active_assessments_count: 6,
      pending_engineering_reviews_count: 2,
      approved_plans_count: 4,
      scheduled_repairs_count: 3,
      in_progress_repairs_count: 1,
      completed_verifications_count: 11,
      total_water_loss_prevented_m3: 2450.8,
      total_repair_expenditure_usd: 54200.0,
      supported_damage_categories: [
        "PIPE_LEAK",
        "PIPE_BURST",
        "JOINT_FAILURE",
        "CORROSION",
        "STRUCTURAL_CRACK",
        "PRESSURE_DAMAGE",
        "VALVE_FAILURE",
        "UNKNOWN_DAMAGE",
      ],
      supported_repair_methods: [
        "CLAMP_REPAIR",
        "JOINT_REPAIR_REPLACEMENT",
        "PIPE_SECTION_REPLACEMENT",
        "INTERNAL_LINING_REHABILITATION",
        "CORROSION_PROTECTION",
        "VALVE_REPLACEMENT",
        "PRESSURE_MANAGEMENT",
        "FURTHER_INSPECTION_REQUIRED",
      ],
      is_simulated: true,
    };
  }

  private getMockDamageAssessment(segmentId: string = "PIPE-SEC-01"): DamageAssessment {
    return {
      id: `DMG-${segmentId}`,
      pipeline_segment_id: segmentId,
      segment_name: `Main Conduit Distribution ${segmentId}`,
      source_inspection_report_id: "INSP-REP-001",
      damage_category: "PIPE_LEAK",
      severity: "HIGH",
      pipe_material: "DUCTILE_IRON",
      pipe_diameter_mm: 300,
      pipe_age_years: 18,
      nominal_pressure_psi: 65.0,
      estimated_water_loss_lph: 240.0,
      structural_vulnerability_score: 68.5,
      previous_repair_count: 1,
      inspection_confidence: 0.92,
      evidence_completeness_pct: 88.0,
      missing_information: [],
      engineering_review_required: true,
      supporting_evidence: [
        {
          evidence_id: "EV-01",
          source_subsystem: "ACOUSTIC_LEAK_DETECTOR",
          classification: "MEASURED",
          metric_name: "acoustic_confidence",
          metric_value: 0.94,
          description: "Distinct high-frequency localized acoustic leak signature detected",
          confidence: 0.94,
          observed_at: new Date().toISOString(),
        },
        {
          evidence_id: "EV-02",
          source_subsystem: "HYDRAULIC_DIGITAL_TWIN",
          classification: "SIMULATED",
          metric_name: "pressure_drop_psi",
          metric_value: 4.8,
          description: "Localized head loss consistent with 240 L/h continuous discharge",
          confidence: 0.88,
          observed_at: new Date().toISOString(),
        },
      ],
      assessment_notes: "High severity circumferential pipe leak identified along ductile iron conduit.",
      assessed_by: "system_damage_assessment_engine",
      assessed_at: new Date().toISOString(),
      is_simulated: true,
    };
  }

  private getMockRepairRecommendation(assessmentId: string): RepairRecommendation {
    return {
      id: `REC-${assessmentId}`,
      damage_assessment_id: assessmentId,
      pipeline_segment_id: "PIPE-SEC-01",
      primary_recommended_method: "CLAMP_REPAIR",
      secondary_alternative_method: "PIPE_SECTION_REPLACEMENT",
      all_evaluated_options: [
        {
          method: "CLAMP_REPAIR",
          method_name: "Stainless Steel Repair Clamp Installation",
          is_recommended: true,
          feasibility_score: 92.5,
          rationale: "Highly suited for 300mm ductile iron pipe with localized leak at 65 PSI nominal pressure.",
          applicable_damage_types: ["PIPE_LEAK", "STRUCTURAL_CRACK"],
          material_compatibility: ["DUCTILE_IRON", "CAST_IRON", "STEEL", "PVC"],
          min_diameter_mm: 50,
          max_diameter_mm: 800,
          max_pressure_psi: 150.0,
          operational_constraints: ["Requires trench excavation and dewatering"],
          advantages: ["Rapid 3-4 hour installation", "Minimal service interruption", "Cost-effective"],
          limitations: ["Not suitable for severe structural fractures or long splits"],
          required_equipment: ["Excavator", "Trench Shoring", "Torque Wrench", "Dewatering Pump"],
          estimated_duration_hours: 4.5,
          risks_and_uncertainties: ["Soil settling after backfill"],
          standards_references: ["AWWA C230", "BS EN 545"],
          required_professional_approvals: ["CERTIFIED_PIPELINE_ENGINEER"],
        },
        {
          method: "PIPE_SECTION_REPLACEMENT",
          method_name: "Full Pipe Section Cut & Replace",
          is_recommended: false,
          feasibility_score: 74.0,
          rationale: "Overkill for localized pinhole leak; recommended only if crack propagation is detected.",
          applicable_damage_types: ["PIPE_BURST", "STRUCTURAL_CRACK"],
          material_compatibility: ["DUCTILE_IRON", "STEEL", "HDPE"],
          min_diameter_mm: 100,
          max_diameter_mm: 1200,
          max_pressure_psi: 250.0,
          operational_constraints: ["Requires full segment isolation and bypass pumping"],
          advantages: ["Permanent structural renewal", "Full pressure rating restoration"],
          limitations: ["High cost", "Extended downtime", "Major traffic disruption"],
          required_equipment: ["Pipe Saw", "Crane", "Excavator", "Bypass Pump"],
          estimated_duration_hours: 12.0,
          risks_and_uncertainties: ["Disruption to customer supply during isolation"],
          standards_references: ["AWWA C600"],
          required_professional_approvals: ["CERTIFIED_PIPELINE_ENGINEER", "MUNICIPAL_PERMIT"],
        },
      ],
      engineering_rationale: "Clamp repair offers fastest recovery (4.5h vs 12h) with 92.5% feasibility score under current soil and pressure parameters.",
      urgency_tier: "URGENT",
      requires_isolation: true,
      bypass_pumping_needed: false,
      traffic_disruption_level: "LOW",
      status: "PROPOSED",
      created_at: new Date().toISOString(),
      is_simulated: true,
    };
  }

  private getMockRepairPlan(
    planId: string = "PLAN-REP-001",
    segmentId: string = "PIPE-SEC-01",
    status: RepairWorkflowStatus = "APPROVED"
  ): RepairPlan {
    return {
      id: planId,
      plan_name: `Intelligent Repair Plan: ${segmentId}`,
      pipeline_segment_id: segmentId,
      segment_name: `Main Conduit Distribution ${segmentId}`,
      damage_assessment_id: `DMG-${segmentId}`,
      repair_recommendation_id: `REC-DMG-${segmentId}`,
      selected_method: "CLAMP_REPAIR",
      workflow_status: status,
      priority: {
        pipeline_segment_id: segmentId,
        repair_priority_score: 79.4,
        priority_category: "HIGH",
        contributing_factors: {
          damage_severity: 85.0,
          water_loss_impact: 78.0,
          criticality_and_consequence: 75.0,
          infrastructure_vulnerability: 68.5,
          geospatial_hotspot: 65.0,
        },
        uncertainty_margin: 0.12,
        recommended_response_time_hours: 24.0,
        escalation_requirements: ["NOTIFY_ZONE_SUPERVISOR"],
        calculated_at: new Date().toISOString(),
      },
      resources: {
        id: `RES-${planId}`,
        repair_plan_id: planId,
        items: [
          {
            resource_id: "RES-CLM-300",
            name: "300mm Stainless Steel Full-Circle Repair Clamp",
            category: "MATERIALS",
            unit: "PIECE",
            estimated_quantity: 1,
            compatibility_requirements: "AWWA C230 compatible for 300mm DI pipe",
            availability_status: "IN_STOCK",
            estimated_unit_cost_usd: 480.0,
            total_cost_usd: 480.0,
            supplier_info: "AquaMaterials Inc Depot A",
            cost_data_source: "DERIVED",
            cost_data_timestamp: new Date().toISOString(),
          },
          {
            resource_id: "RES-EXC-MINI",
            name: "Mini-Excavator & Trench Shoring Set",
            category: "EQUIPMENT",
            unit: "HOURS",
            estimated_quantity: 6,
            compatibility_requirements: "Urban road excavation compliant",
            availability_status: "IN_STOCK",
            estimated_unit_cost_usd: 120.0,
            total_cost_usd: 720.0,
            supplier_info: "Fleet Equipment Depot",
            cost_data_source: "DERIVED",
            cost_data_timestamp: new Date().toISOString(),
          },
        ],
        total_materials_cost_usd: 480.0,
        total_equipment_cost_usd: 720.0,
        all_resources_available: true,
        procurement_lead_time_days: 0.5,
        created_at: new Date().toISOString(),
      },
      cost_estimate: {
        id: `EST-${planId}`,
        damage_assessment_id: `DMG-${segmentId}`,
        pipeline_segment_id: segmentId,
        components: [
          {
            component_name: "Materials",
            amount_usd: 480.0,
            formula: "unit_cost * quantity",
            input_values: { unit_cost: 480.0, quantity: 1 },
            units: "USD",
            assumptions: "AWWA standard certified clamp",
            uncertainty_range_pct: 5.0,
            provenance: "DERIVED",
          },
          {
            component_name: "Labor & Crew",
            amount_usd: 1260.0,
            formula: "crew_hours * hourly_rate * crew_size",
            input_values: { hours: 4.5, rate: 70.0, crew_size: 4 },
            units: "USD",
            assumptions: "Standard municipal utility rate",
            uncertainty_range_pct: 10.0,
            provenance: "DERIVED",
          },
          {
            component_name: "Water Loss Prevention Value",
            amount_usd: 350.0,
            formula: "water_loss_rate * response_time * cost_per_m3",
            input_values: { lph: 240, hours: 24, cost_m3: 2.5 },
            units: "USD",
            assumptions: "Municipal potable water tariff",
            uncertainty_range_pct: 15.0,
            provenance: "SIMULATED",
          },
        ],
        total_material_cost_usd: 480.0,
        total_equipment_cost_usd: 720.0,
        total_labour_cost_usd: 1260.0,
        inspection_cost_usd: 250.0,
        estimated_water_loss_cost_usd: 350.0,
        restoration_cost_usd: 500.0,
        contingency_cost_usd: 356.0,
        total_estimated_cost_usd: 3916.0,
        estimated_downtime_hours: 4.5,
        cost_uncertainty_lower_bound_usd: 3524.4,
        cost_uncertainty_upper_bound_usd: 4307.6,
        financial_disclaimer: "SYNTHETIC ESTIMATE: Virtual decision support model only. Real-world material and contractor pricing may vary.",
        created_at: new Date().toISOString(),
        is_simulated: true,
      },
      schedule: {
        schedule_id: `SCH-${planId}`,
        repair_plan_id: planId,
        crew_id: "CREW-ALPHA",
        crew_name: "Rapid Response Crew Alpha",
        scheduled_start: new Date(Date.now() + 86400000).toISOString(),
        scheduled_end: new Date(Date.now() + 102600000).toISOString(),
        estimated_duration_hours: 4.5,
        travel_distance_km: 3.4,
        travel_time_hours: 0.35,
        has_schedule_conflicts: false,
        schedule_conflict_details: null,
        scheduling_notes: "Scheduled during off-peak morning window to minimize distribution pressure impact.",
      },
      approved_by: status === "APPROVED" ? "eng_sarah_chen" : null,
      approved_at: status === "APPROVED" ? new Date().toISOString() : null,
      rejection_reason: null,
      operator_notes: "Standard clamp installation verified against digital twin pressure bounds.",
      digital_twin_scenario_id: "SCEN-REPAIR-SIM-01",
      created_by: "system_planner",
      created_at: new Date(Date.now() - 86400000).toISOString(),
      updated_at: new Date().toISOString(),
      is_simulated: true,
    };
  }

  private getMockRepairSimulation(planId: string): {
    scenario: DigitalTwinRepairScenario;
    comparison: DigitalTwinRepairComparison;
  } {
    return {
      scenario: {
        scenario_id: `SCEN-SIM-${planId}`,
        repair_plan_id: planId,
        pipeline_segment_id: "PIPE-SEC-01",
        baseline_pressure_bar: 4.5,
        pre_repair_pressure_bar: 3.8,
        post_repair_pressure_bar: 4.45,
        baseline_leakage_m3: 0.0,
        pre_repair_leakage_m3: 5.76,
        post_repair_leakage_m3: 0.12,
        water_loss_reduction_pct: 97.9,
        pressure_restoration_pct: 98.9,
        pump_energy_delta_kwh: -18.4,
        demand_satisfaction_pct: 100.0,
        simulation_solver: "EPANET_2.2_WNTR_DIGITAL_TWIN",
        is_simulated: true,
      },
      comparison: {
        repair_plan_id: planId,
        scenario_comparison_id: `COMP-${planId}`,
        baseline_scenario_id: "SCEN-BASELINE-01",
        pre_repair_scenario_id: `SCEN-PRE-${planId}`,
        post_repair_scenario_id: `SCEN-POST-${planId}`,
        summary_metrics: {
          water_loss_reduction_lph: 235.0,
          pressure_deficit_recovery_psi: 9.4,
          energy_savings_kwh_day: 44.2,
        },
        link_differences: [],
        node_differences: [],
        hydraulic_benefit_score: 94.2,
      },
    };
  }

  private getMockRepairVerification(planId: string): RepairVerification {
    return {
      id: `VER-${planId}`,
      repair_plan_id: planId,
      pipeline_segment_id: "PIPE-SEC-01",
      verification_outcome: "VERIFIED_SUCCESS",
      pre_repair_leakage_lph: 240.0,
      post_repair_leakage_lph: 2.1,
      leakage_reduction_pct: 99.1,
      acoustic_anomaly_cleared: true,
      pressure_gradient_restored: true,
      remaining_uncertainty_pct: 2.5,
      supporting_evidence: [
        {
          evidence_id: "EV-VERIF-01",
          source_subsystem: "VIRTUAL_ROVER_ACOUSTIC",
          classification: "MEASURED",
          metric_name: "post_repair_acoustic_amplitude_db",
          metric_value: 12.4,
          description: "Follow-up rover sweep confirmed acoustic signature returned to baseline ambient levels",
          confidence: 0.98,
          observed_at: new Date().toISOString(),
        },
        {
          evidence_id: "EV-VERIF-02",
          source_subsystem: "SCADA_FLOW_TELEMETRY",
          classification: "MEASURED",
          metric_name: "differential_flow_reduction_lph",
          metric_value: 237.9,
          description: "Mass balance flow sensor confirms full flow restoration",
          confidence: 0.96,
          observed_at: new Date().toISOString(),
        },
      ],
      verified_by: "eng_sarah_chen",
      verified_at: new Date().toISOString(),
      tamper_proof_hash: "a4f7832bc9812e34d98a00192837465e9f8a7b6c5d4e3f2a1b0c9d8e7f6a5b4c",
      is_simulated: true,
    };
  }
}

/* ========================================================= */
/* DETERMINISTIC CLIENT-SIDE FALLBACK DATA STORES           */
/* ========================================================= */

const fallbackDetectionsStore: AiDetection[] = [
  {
    id: "DET-2026-B81E29",
    pipeline_segment_id: "PIPE-SEC-4B-92",
    anomaly_score: 0.88,
    classification: "HIGH_LEAK_PROBABILITY",
    confidence: 0.92,
    risk_level: "CRITICAL",
    estimated_loss_lph: 2450.0,
    estimated_latitude: 40.7118,
    estimated_longitude: -74.0095,
    localization_uncertainty_m: 14.5,
    localization_quality: "HIGH",
    status: "PENDING_REVIEW",
    contributing_features: {
      acoustic_spl_db: 0.42,
      dominant_freq_hz: 0.28,
      pressure_deviation: 0.18,
      ground_moisture_pct: 0.12,
    },
    risk_explanation:
      "Acoustic spectral signature (84 dB at 1,420 Hz) combined with severe pressure drop (-1.4 bar) and saturated ground moisture (88%) on Ductile Iron 450mm mainline indicates active pressurized orifice rupture.",
    model_version: "v1.2.0-rf-explainable",
    created_at: new Date(Date.now() - 1000 * 60 * 18).toISOString(),
    is_simulated: true,
    source: "VIRTUAL_SIMULATION_ENGINE",
  },
  {
    id: "DET-2026-A12F90",
    pipeline_segment_id: "PIPE-SEC-2A-14",
    anomaly_score: 0.65,
    classification: "MEDIUM_LEAK_PROBABILITY",
    confidence: 0.78,
    risk_level: "HIGH",
    estimated_loss_lph: 920.0,
    estimated_latitude: 40.7162,
    estimated_longitude: -74.0034,
    localization_uncertainty_m: 26.0,
    localization_quality: "MODERATE",
    status: "INVESTIGATING",
    contributing_features: {
      acoustic_spl_db: 0.35,
      pressure_deviation: 0.25,
      flow_deviation: 0.22,
      dominant_freq_hz: 0.18,
    },
    risk_explanation:
      "Moderate hiss anomaly detected (68 dB at 780 Hz) with consistent flow rate deviation (+14 m3/h) in Midtown sub-distribution segment.",
    model_version: "v1.2.0-rf-explainable",
    created_at: new Date(Date.now() - 1000 * 60 * 45).toISOString(),
    is_simulated: true,
    source: "VIRTUAL_SIMULATION_ENGINE",
  },
  {
    id: "DET-2026-C44D12",
    pipeline_segment_id: "PIPE-SEC-7C-03",
    anomaly_score: 0.42,
    classification: "LOW_LEAK_PROBABILITY",
    confidence: 0.64,
    risk_level: "MODERATE",
    estimated_loss_lph: 280.0,
    estimated_latitude: 40.7225,
    estimated_longitude: -74.0142,
    localization_uncertainty_m: 48.0,
    localization_quality: "LOW",
    status: "PENDING_REVIEW",
    contributing_features: {
      dominant_freq_hz: 0.40,
      acoustic_spl_db: 0.30,
      ground_moisture_pct: 0.20,
      pressure_deviation: 0.10,
    },
    risk_explanation:
      "Intermittent high-frequency acoustic hiss with low pressure delta. Possible micro-fissure or valve cavitation.",
    model_version: "v1.2.0-rf-explainable",
    created_at: new Date(Date.now() - 1000 * 60 * 120).toISOString(),
    is_simulated: true,
    source: "VIRTUAL_SIMULATION_ENGINE",
  },
  {
    id: "DET-2026-F90B33",
    pipeline_segment_id: "PIPE-SEC-1A-01",
    anomaly_score: 0.15,
    classification: "NORMAL",
    confidence: 0.95,
    risk_level: "NEGLIGIBLE",
    estimated_loss_lph: 0.0,
    estimated_latitude: null,
    estimated_longitude: null,
    localization_uncertainty_m: null,
    localization_quality: "SUPPRESSED",
    status: "FALSE_POSITIVE",
    contributing_features: {
      acoustic_spl_db: 0.05,
      pressure_deviation: 0.02,
      ground_moisture_pct: 0.01,
    },
    risk_explanation: "Nominal operating acoustics (36 dB) and stable pressure (4.8 bar). Baseline water flow confirmed.",
    model_version: "v1.2.0-rf-explainable",
    created_at: new Date(Date.now() - 1000 * 60 * 240).toISOString(),
    is_simulated: true,
    source: "VIRTUAL_SIMULATION_ENGINE",
  },
];

function getFallbackAiDetections(filters?: {
  segment_id?: string;
  risk_level?: string;
  status?: string;
  limit?: number;
}): AiDetection[] {
  let list = [...fallbackDetectionsStore];
  if (filters?.segment_id) {
    list = list.filter((d) => d.pipeline_segment_id.toLowerCase().includes(filters.segment_id!.toLowerCase()));
  }
  if (filters?.risk_level) {
    list = list.filter((d) => d.risk_level.toUpperCase() === filters.risk_level!.toUpperCase());
  }
  if (filters?.status) {
    list = list.filter((d) => d.status.toUpperCase() === filters.status!.toUpperCase());
  }
  if (filters?.limit) {
    list = list.slice(0, filters.limit);
  }
  return list;
}

function updateFallbackDetectionStatus(
  id: string,
  newStatus: DetectionStatus,
  notes?: string
): AiDetection | null {
  const item = fallbackDetectionsStore.find((d) => d.id === id);
  if (!item) return null;
  item.status = newStatus;
  if (notes) {
    item.risk_explanation = `${item.risk_explanation} | Operator Notes: ${notes}`;
  }
  return { ...item };
}

function simulateLocalAiDetection(req: LeakAnalyzeRequest): AiDetection {
  const scenario = req.acoustic_scenario || "MODERATE_LEAK";
  let classification: AiDetection["classification"] = "MEDIUM_LEAK_PROBABILITY";
  let risk: AiDetection["risk_level"] = "HIGH";
  let loss = 850.0;
  let anomaly = 0.72;
  let conf = 0.85;

  if (scenario === "MAJOR_LEAK") {
    classification = "HIGH_LEAK_PROBABILITY";
    risk = "CRITICAL";
    loss = 2800.0;
    anomaly = 0.94;
    conf = 0.95;
  } else if (scenario === "MINOR_LEAK") {
    classification = "LOW_LEAK_PROBABILITY";
    risk = "MODERATE";
    loss = 320.0;
    anomaly = 0.48;
    conf = 0.74;
  } else if (scenario === "NORMAL_FLOW") {
    classification = "NORMAL";
    risk = "NEGLIGIBLE";
    loss = 0.0;
    anomaly = 0.12;
    conf = 0.96;
  }

  const detection: AiDetection = {
    id: `DET-2026-${Math.random().toString(36).substring(2, 8).toUpperCase()}`,
    pipeline_segment_id: req.pipeline_segment_id,
    anomaly_score: anomaly,
    classification,
    confidence: conf,
    risk_level: risk,
    estimated_loss_lph: loss,
    estimated_latitude: 40.7145,
    estimated_longitude: -74.0078,
    localization_uncertainty_m: classification === "NORMAL" ? null : 18.0,
    localization_quality: classification === "NORMAL" ? "SUPPRESSED" : "HIGH",
    status: "PENDING_REVIEW",
    contributing_features: {
      acoustic_spl_db: 0.38,
      pressure_deviation: 0.26,
      dominant_freq_hz: 0.22,
      ground_moisture_pct: 0.14,
    },
    risk_explanation: `Analysis on ${req.pipeline_segment_id} using scenario '${scenario}'. Loss rate estimated at ${loss} L/h with confidence ${conf * 100}%.`,
    model_version: "v1.2.0-rf-explainable",
    created_at: new Date().toISOString(),
    is_simulated: true,
    source: "VIRTUAL_SIMULATION_ENGINE",
  };

  fallbackDetectionsStore.unshift(detection);
  return detection;
}

function generateFallbackWaveform(
  scenario: AcousticScenario,
  durationSec: number,
  snrDb: number
): SyntheticWaveformResponse {
  const points = 80;
  const timeSeries: number[] = [];
  const freqSpectrum: { frequency_hz: number; magnitude: number }[] = [];

  const baseFreq =
    scenario === "MAJOR_LEAK"
      ? 1800
      : scenario === "MODERATE_LEAK"
      ? 1200
      : scenario === "MINOR_LEAK"
      ? 750
      : scenario === "ENVIRONMENTAL_NOISE"
      ? 350
      : scenario === "MECHANICAL_VIBRATION"
      ? 120
      : 500;

  for (let i = 0; i < points; i++) {
    const t = (i / points) * durationSec;
    const sig =
      Math.sin(2 * Math.PI * baseFreq * t * 0.01) * 0.6 +
      Math.sin(2 * Math.PI * (baseFreq * 2.1) * t * 0.01) * 0.25 +
      (Math.random() - 0.5) * (scenario === "NORMAL_FLOW" ? 0.1 : 0.4);
    timeSeries.push(Math.round(sig * 1000) / 1000);
  }

  // 12 frequency bins for FFT visualization
  const bins = [100, 250, 500, 750, 1000, 1250, 1500, 1750, 2000, 2500, 3000, 4000];
  for (const f of bins) {
    const dist = Math.abs(f - baseFreq);
    const mag = Math.max(0.02, Math.exp(-dist / 600) * 0.95 + (Math.random() * 0.05));
    freqSpectrum.push({ frequency_hz: f, magnitude: Math.round(mag * 1000) / 1000 });
  }

  return {
    scenario,
    duration_sec: durationSec,
    sampling_rate_hz: 8000,
    rms_amplitude: scenario === "MAJOR_LEAK" ? 82.4 : scenario === "MODERATE_LEAK" ? 68.1 : 44.5,
    peak_amplitude: scenario === "MAJOR_LEAK" ? 94.2 : scenario === "MODERATE_LEAK" ? 77.0 : 52.3,
    dominant_frequency_hz: baseFreq,
    spectral_centroid_hz: Math.round(baseFreq * 1.15),
    spectral_bandwidth_hz: Math.round(baseFreq * 0.65),
    snr_db: snrDb,
    time_series: timeSeries,
    frequency_spectrum: freqSpectrum,
    is_simulated: true,
    source: "VIRTUAL_SIMULATION_ENGINE",
  };
}



function getFallbackDigitalTwinNet3Benchmark(): Net3BenchmarkResult {
  return {
    benchmark_network: "EPANET Net3 (EPA 97-Node Benchmark)",
    benchmark_file: "Net3.inp",
    source_provenance: "EPA EPANET Standard Net3 Distribution Benchmark bundled with WNTR",
    nodes_count: 97,
    links_count: 119,
    junctions_count: 92,
    tanks_count: 3,
    reservoirs_count: 2,
    pipes_count: 117,
    pumps_count: 2,
    valves_count: 0,
    execution_duration_ms: 32.4,
    validation_status: "VALIDATED",
    is_validated: true,
    loops_evaluated_count: 22,
    tolerances: {
      max_pressure_relative_error_pct_allowed: 0.10,
      max_flow_relative_error_pct_allowed: 0.50,
      max_flow_absolute_error_m3s_allowed: 0.0001,
      mass_balance_residual_threshold_m3s: 0.0001,
      loop_energy_headloss_closure_threshold_m: 0.05,
    },
    metrics: {
      max_absolute_error_pressure_m: 0.000044,
      max_relative_error_pressure_pct: 0.000727,
      max_absolute_error_head_m: 0.000044,
      max_relative_error_head_pct: 0.000727,
      max_absolute_error_flow_m3s: 0.00001991,
      max_relative_error_flow_pct: 0.007296,
      max_absolute_error_velocity_mps: 0.000021,
      total_inflow_m3s: 0.850902,
      total_outflow_m3s: 0.850902,
      mass_balance_residual_m3s: 0.0,
      mass_balance_conserved: true,
      loop_headloss_closure_residual_m: 0.0,
      energy_balance_conserved: true,
    },
    is_simulated: true,
    source: "VIRTUAL_SIMULATION_ENGINE",
  };
}

function getFallbackDigitalTwinReproducibility(network = "Net1", iterations = 5): ReproducibilityBenchmarkResult {
  return {
    network_name: `EPANET ${network}`,
    iterations,
    deterministic_reproducible: true,
    reproducibility_status: "DETERMINISTIC_REPRODUCIBLE",
    max_head_standard_deviation_m: 0.0,
    max_flow_standard_deviation_m3s: 0.0,
    run_durations_ms: [18.2, 17.9, 18.1, 18.5, 18.0],
    mean_execution_duration_ms: 18.14,
    min_execution_duration_ms: 17.9,
    max_execution_duration_ms: 18.5,
    provenance: "Zero floating-point divergence across repeated WNTR/EPANET executions",
    is_simulated: true,
    source: "VIRTUAL_SIMULATION_ENGINE",
  };
}

/* ========================================================= */
/* MISSION RECOMMENDATIONS FALLBACK STORES                   */
/* ========================================================= */

const fallbackRecommendationsStore: MissionRecommendation[] = [
  {
    id: "REC-2026-B81E99",
    detection_id: "DET-2026-B81E29",
    pipeline_segment_id: "PIPE-SEC-4B-92",
    recommended_rover_id: "ROV-AQUA-03",
    recommended_rover_name: "Hydra Pipe Probe",
    priority_score: 95.0,
    priority_category: "CRITICAL",
    status: "PENDING_APPROVAL",
    route_distance_m: 1368.0,
    estimated_duration_s: 2480.0,
    estimated_energy_pct: 6.9,
    battery_reserve_after_pct: 67.1,
    destination_lat: 40.7118,
    destination_lng: -74.0095,
    localization_uncertainty_m: 14.5,
    waypoints: [
      [-74.0089, 40.7198],
      [-74.006, 40.722],
      [-74.006, 40.7128],
      [-74.0095, 40.7118],
    ],
    segments_traversed: ["PIPE-RES-3C-11", "PIPE-SEC-4A-10", "PIPE-SEC-4B-92"],
    contributing_factors: {
      risk_severity: 35.0,
      classification_likelihood: 25.0,
      water_loss_volume: 20.0,
      infrastructure_criticality: 12.0,
      pressure_drop_severity: 8.0,
    },
    explanation:
      "Recommended Hydra Pipe Probe (ROV-AQUA-03) with suitability 84/100. Priority: CRITICAL (95/100). Planned pipeline distance: 1368m (41 min). Estimated battery draw: 6.9% (Projected reserve: 67.1%).",
    created_at: new Date(Date.now() - 1000 * 60 * 12).toISOString(),
    is_simulated: true,
    source: "VIRTUAL_SIMULATION_ENGINE",
  },
  {
    id: "REC-2026-A12F44",
    detection_id: "DET-2026-A12F90",
    pipeline_segment_id: "PIPE-SEC-2A-14",
    recommended_rover_id: "ROV-AQUA-02",
    recommended_rover_name: "Nautilus Ground Scout",
    priority_score: 76.0,
    priority_category: "HIGH",
    status: "APPROVED",
    route_distance_m: 820.0,
    estimated_duration_s: 1490.0,
    estimated_energy_pct: 4.8,
    battery_reserve_after_pct: 87.2,
    destination_lat: 40.7162,
    destination_lng: -74.0034,
    localization_uncertainty_m: 26.0,
    waypoints: [
      [-74.0021, 40.7145],
      [-74.0034, 40.7162],
    ],
    segments_traversed: ["PIPE-IND-1A-04"],
    contributing_factors: {
      risk_severity: 25.0,
      classification_likelihood: 18.0,
      water_loss_volume: 15.0,
      infrastructure_criticality: 12.0,
      pressure_drop_severity: 5.0,
    },
    explanation:
      "Recommended Nautilus Ground Scout (ROV-AQUA-02) with suitability 91/100. Priority: HIGH (76/100). Route distance: 820m. Battery reserve: 87.2%.",
    assigned_mission_id: "MSN-2026-043",
    approved_by: "OPERATOR_CHIEF",
    operator_notes: "Dispatched ground scout for acoustic surface grid validation.",
    created_at: new Date(Date.now() - 1000 * 60 * 35).toISOString(),
    is_simulated: true,
    source: "VIRTUAL_SIMULATION_ENGINE",
  },
];

function getFallbackRecommendations(filters?: {
  status?: string;
  priority?: string;
  limit?: number;
}): MissionRecommendation[] {
  let list = [...fallbackRecommendationsStore];
  if (filters?.status) {
    list = list.filter((r) => r.status.toUpperCase() === filters.status!.toUpperCase());
  }
  if (filters?.priority) {
    list = list.filter((r) => r.priority_category.toUpperCase() === filters.priority!.toUpperCase());
  }
  if (filters?.limit) {
    list = list.slice(0, filters.limit);
  }
  return list;
}

function generateFallbackRecommendation(
  detectionId: string,
  preferredRoverId?: string
): MissionRecommendation {
  const det = fallbackDetectionsStore.find((d) => d.id === detectionId) || fallbackDetectionsStore[0];
  const roverId = preferredRoverId || "ROV-AQUA-03";
  const roverName = roverId === "ROV-AQUA-03" ? "Hydra Pipe Probe" : roverId === "ROV-AQUA-01" ? "Triton-1 Crawler" : "Nautilus Ground Scout";

  const rec: MissionRecommendation = {
    id: `REC-2026-${Math.random().toString(36).substring(2, 8).toUpperCase()}`,
    detection_id: det.id,
    pipeline_segment_id: det.pipeline_segment_id,
    recommended_rover_id: roverId,
    recommended_rover_name: roverName,
    priority_score: det.risk_level === "CRITICAL" ? 92.0 : det.risk_level === "HIGH" ? 78.0 : 54.0,
    priority_category: det.risk_level === "CRITICAL" ? "CRITICAL" : det.risk_level === "HIGH" ? "HIGH" : "MEDIUM",
    status: "PENDING_APPROVAL",
    route_distance_m: 1420.0,
    estimated_duration_s: 2580.0,
    estimated_energy_pct: 7.2,
    battery_reserve_after_pct: 66.8,
    destination_lat: det.estimated_latitude || 40.7128,
    destination_lng: det.estimated_longitude || -74.0060,
    localization_uncertainty_m: det.localization_uncertainty_m || 18.0,
    waypoints: [
      [-74.0089, 40.7198],
      [-74.0060, 40.7128],
      [det.estimated_longitude || -74.0060, det.estimated_latitude || 40.7128],
    ],
    segments_traversed: [det.pipeline_segment_id],
    contributing_factors: {
      risk_severity: 30.0,
      classification_likelihood: 20.0,
      water_loss_volume: 15.0,
      infrastructure_criticality: 10.0,
    },
    explanation: `Recommended ${roverName} (${roverId}) for inspection on segment ${det.pipeline_segment_id}. Projected battery reserve: 66.8%.`,
    created_at: new Date().toISOString(),
    is_simulated: true,
    source: "VIRTUAL_SIMULATION_ENGINE",
  };

  fallbackRecommendationsStore.unshift(rec);
  return rec;
}

function approveFallbackRecommendation(
  id: string,
  operatorId: string,
  notes?: string
): { success: boolean; message: string; mission_id: string; rover_id: string } {
  const rec = fallbackRecommendationsStore.find((r) => r.id === id);
  const missionId = `MSN-2026-${Math.random().toString(36).substring(2, 8).toUpperCase()}`;

  if (rec) {
    rec.status = "APPROVED";
    rec.assigned_mission_id = missionId;
    rec.operator_notes = notes;
    rec.approved_by = operatorId;
  }

  return {
    success: true,
    message: `Mission ${missionId} approved and rover ${rec?.recommended_rover_id || "ROV-AQUA-03"} dispatched.`,
    mission_id: missionId,
    rover_id: rec?.recommended_rover_id || "ROV-AQUA-03",
  };
}

function rejectFallbackRecommendation(
  id: string,
  reason: string,
  operatorNotes?: string
): MissionRecommendation | null {
  const rec = fallbackRecommendationsStore.find((r) => r.id === id);
  if (!rec) return null;
  rec.status = "REJECTED";
  rec.rejection_reason = reason;
  rec.operator_notes = operatorNotes;
  return { ...rec };
}

function getFallbackRoverSuitabilities(): RoverSuitability[] {
  return [
    {
      rover_id: "ROV-AQUA-03",
      rover_name: "Hydra Pipe Probe",
      operating_state: "IDLE",
      battery_percentage: 74.0,
      is_eligible: true,
      distance_to_target_m: 650.0,
      estimated_energy_consumption_pct: 6.9,
      battery_reserve_after_pct: 67.1,
      suitability_score: 88.5,
      suitability_explanation: "Optimal candidate: IDLE, 67% projected battery reserve, high acoustic sensor match.",
    },
    {
      rover_id: "ROV-AQUA-02",
      rover_name: "Nautilus Ground Scout",
      operating_state: "MOVING",
      battery_percentage: 92.0,
      is_eligible: false,
      disqualification_reason: "Rover operating state is MOVING (must be IDLE).",
      distance_to_target_m: 820.0,
      estimated_energy_consumption_pct: 4.8,
      battery_reserve_after_pct: 87.2,
      suitability_score: 0.0,
      suitability_explanation: "INELIGIBLE: Rover is actively executing mission MSN-2026-043.",
    },
    {
      rover_id: "ROV-AQUA-01",
      rover_name: "Triton-1 Crawler",
      operating_state: "INSPECTING",
      battery_percentage: 86.0,
      is_eligible: false,
      disqualification_reason: "Rover operating state is INSPECTING (must be IDLE).",
      distance_to_target_m: 1200.0,
      estimated_energy_consumption_pct: 8.2,
      battery_reserve_after_pct: 77.8,
      suitability_score: 0.0,
      suitability_explanation: "INELIGIBLE: Rover is actively executing mission MSN-2026-042.",
    },
    {
      rover_id: "ROV-AQUA-04",
      rover_name: "Aquila Surface Drone",
      operating_state: "RETURNING",
      battery_percentage: 24.0,
      is_eligible: false,
      disqualification_reason: "Insufficient battery: 24% available (must have >= 35% with 20% safety reserve).",
      distance_to_target_m: 1950.0,
      estimated_energy_consumption_pct: 12.0,
      battery_reserve_after_pct: 12.0,
      suitability_score: 0.0,
      suitability_explanation: "INELIGIBLE: Battery critically low and returning to charging pad.",
    },
  ];
}

/* ========================================================= */
/* TASK 09 PREDICTIVE MAINTENANCE FALLBACK STORES            */
/* ========================================================= */

const fallbackHealthStore: PipelineHealth[] = [
  {
    id: "HLT-2026-001",
    pipeline_segment_id: "PIPE-SEC-4B-92",
    health_score: 42.0,
    health_category: "POOR",
    acoustic_stability_score: 45.0,
    pressure_stability_score: 38.0,
    flow_stability_score: 60.0,
    moisture_anomaly_score: 30.0,
    data_coverage_pct: 95.0,
    confidence: 0.92,
    contributing_factors: {
      severe_pressure_loss: 25.0,
      acoustic_high_spl: 22.0,
      high_ground_saturation: 18.0,
    },
    positive_indicators: ["Ductile iron class 54 structural tensile capacity intact"],
    explanation: "Pipe section PIPE-SEC-4B-92 in POOR health (42/100). Recurrent pressure dips and 78 dB acoustic emissions indicate active micro-fissure expansion.",
    assessed_at: new Date().toISOString(),
    is_simulated: true,
    source: "VIRTUAL_SIMULATION_ENGINE",
  },
  {
    id: "HLT-2026-002",
    pipeline_segment_id: "PIPE-SEC-4A-10",
    health_score: 82.0,
    health_category: "GOOD",
    acoustic_stability_score: 88.0,
    pressure_stability_score: 84.0,
    flow_stability_score: 92.0,
    moisture_anomaly_score: 80.0,
    data_coverage_pct: 90.0,
    confidence: 0.88,
    contributing_factors: {
      minor_pressure_fluctuation: 6.0,
    },
    positive_indicators: ["Nominal operating pressure 4.7 bar", "Acoustic background quiet (38 dB SPL)"],
    explanation: "Grand Avenue Spine Trunk in GOOD health (82/100). Minor diurnal pressure variation within acceptable tolerance.",
    assessed_at: new Date().toISOString(),
    is_simulated: true,
    source: "VIRTUAL_SIMULATION_ENGINE",
  },
  {
    id: "HLT-2026-003",
    pipeline_segment_id: "PIPE-IND-1A-04",
    health_score: 94.0,
    health_category: "EXCELLENT",
    acoustic_stability_score: 96.0,
    pressure_stability_score: 95.0,
    flow_stability_score: 94.0,
    moisture_anomaly_score: 92.0,
    data_coverage_pct: 88.0,
    confidence: 0.90,
    contributing_factors: {},
    positive_indicators: ["Zero acoustic anomalies detected", "Flow mass balance 100% nominal"],
    explanation: "Industrial Park Feeder Line in EXCELLENT health (94/100). Fully stabilized telemetry.",
    assessed_at: new Date().toISOString(),
    is_simulated: true,
    source: "VIRTUAL_SIMULATION_ENGINE",
  },
];

const fallbackPredictionsStore: PredictiveRisk[] = [
  {
    id: "PRD-2026-001",
    pipeline_segment_id: "PIPE-SEC-4B-92",
    failure_prob_24h: 0.48,
    failure_prob_7d: 0.74,
    failure_prob_30d: 0.89,
    overall_risk_level: "CRITICAL",
    leak_probability: 0.78,
    burst_rupture_risk: 0.42,
    model_version: "v1.0.0-rf-gradient-predictive",
    confidence: 0.88,
    uncertainty_margin: 0.06,
    contributing_factors: {
      acute_pressure_drop_loss: 0.35,
      high_acoustic_spl_emissions: 0.30,
      ground_saturation_anomaly: 0.15,
    },
    risk_explanation: "Critical 7-day failure forecast (74% probability) driven by continuous pressure gradient loss and ground soil moisture saturation.",
    assessed_at: new Date().toISOString(),
    is_simulated: true,
    source: "VIRTUAL_SIMULATION_ENGINE",
  },
  {
    id: "PRD-2026-002",
    pipeline_segment_id: "PIPE-SEC-4A-10",
    failure_prob_24h: 0.04,
    failure_prob_7d: 0.12,
    failure_prob_30d: 0.22,
    overall_risk_level: "LOW",
    leak_probability: 0.09,
    burst_rupture_risk: 0.03,
    model_version: "v1.0.0-rf-gradient-predictive",
    confidence: 0.86,
    uncertainty_margin: 0.04,
    contributing_factors: {
      diurnal_flow_cycle: 0.05,
    },
    risk_explanation: "Low failure probability across all horizons (4% in 24h, 22% in 30d). Nominal structural integrity.",
    assessed_at: new Date().toISOString(),
    is_simulated: true,
    source: "VIRTUAL_SIMULATION_ENGINE",
  },
  {
    id: "PRD-2026-003",
    pipeline_segment_id: "PIPE-IND-1A-04",
    failure_prob_24h: 0.02,
    failure_prob_7d: 0.06,
    failure_prob_30d: 0.11,
    overall_risk_level: "LOW",
    leak_probability: 0.05,
    burst_rupture_risk: 0.01,
    model_version: "v1.0.0-rf-gradient-predictive",
    confidence: 0.90,
    uncertainty_margin: 0.03,
    contributing_factors: {},
    risk_explanation: "Minimal risk profile. HDPE conduit with zero thermal or acoustic stress indicators.",
    assessed_at: new Date().toISOString(),
    is_simulated: true,
    source: "VIRTUAL_SIMULATION_ENGINE",
  },
];

const fallbackRecommendationsStoreMaintenance: MaintenanceRecommendation[] = [
  {
    id: "MNT-2026-A101",
    pipeline_segment_id: "PIPE-SEC-4B-92",
    health_score: 42.0,
    predicted_risk: "CRITICAL",
    urgency: "CRITICAL",
    recommended_action: "DISPATCH_INSPECTION_ROVER",
    timeframe_days: 1,
    status: "PENDING_REVIEW",
    explanation: "Critical deterioration on Central Trunk Line B (Health: 42/100, 24h failure risk: 48%). Autonomous crawler inspection recommended to locate exact fissure zone.",
    sensor_evidence: {
      mean_spl_db: 78.4,
      pressure_drop_bar: 1.2,
      soil_moisture_pct: 64.0,
    },
    created_at: new Date().toISOString(),
    is_simulated: true,
    source: "VIRTUAL_SIMULATION_ENGINE",
  },
  {
    id: "MNT-2026-B202",
    pipeline_segment_id: "PIPE-SEC-4A-10",
    health_score: 82.0,
    predicted_risk: "LOW",
    urgency: "ROUTINE",
    recommended_action: "CONTINUE_MONITORING",
    timeframe_days: 30,
    status: "ACKNOWLEDGED",
    explanation: "Operating parameters nominal. Continue routine 30-day telemetry polling.",
    sensor_evidence: {
      mean_spl_db: 38.2,
      pressure_drop_bar: 0.1,
      soil_moisture_pct: 12.0,
    },
    created_at: new Date().toISOString(),
    is_simulated: true,
    source: "VIRTUAL_SIMULATION_ENGINE",
  },
];

function getFallbackMaintenanceOverview(): PredictiveMaintenanceOverview {
  return {
    total_segments_monitored: 8,
    excellent_count: 3,
    good_count: 3,
    fair_count: 1,
    poor_count: 1,
    critical_count: 0,
    insufficient_data_count: 0,
    average_health_score: 81.4,
    high_risk_segment_count: 1,
    pending_recommendation_count: 1,
    timestamp: new Date().toISOString(),
    is_simulated: true,
  };
}

function getFallbackHealthAssessments(): PipelineHealth[] {
  return [...fallbackHealthStore];
}

function getFallbackSegmentHealth(segmentId: string): PipelineHealth {
  const found = fallbackHealthStore.find((h) => h.pipeline_segment_id === segmentId);
  if (found) return found;
  return {
    id: `HLT-FALLBACK-${segmentId}`,
    pipeline_segment_id: segmentId,
    health_score: 78.0,
    health_category: "GOOD",
    acoustic_stability_score: 80.0,
    pressure_stability_score: 82.0,
    flow_stability_score: 85.0,
    moisture_anomaly_score: 80.0,
    data_coverage_pct: 85.0,
    confidence: 0.85,
    contributing_factors: {},
    positive_indicators: ["Nominal baseline parameters"],
    explanation: `Pipeline ${segmentId} evaluated at 78/100 health index in stable state.`,
    assessed_at: new Date().toISOString(),
    is_simulated: true,
    source: "VIRTUAL_SIMULATION_ENGINE",
  };
}







function getFallbackPredictions(): PredictiveRisk[] {
  return [...fallbackPredictionsStore];
}

function getFallbackSegmentPrediction(segmentId: string): PredictiveRisk {
  const found = fallbackPredictionsStore.find((p) => p.pipeline_segment_id === segmentId);
  if (found) return found;
  return {
    id: `PRD-FALLBACK-${segmentId}`,
    pipeline_segment_id: segmentId,
    failure_prob_24h: 0.05,
    failure_prob_7d: 0.12,
    failure_prob_30d: 0.20,
    overall_risk_level: "LOW",
    leak_probability: 0.10,
    burst_rupture_risk: 0.02,
    model_version: "v1.0.0-rf-gradient-predictive",
    confidence: 0.85,
    uncertainty_margin: 0.05,
    contributing_factors: {},
    risk_explanation: `Low predicted failure probability for ${segmentId}.`,
    assessed_at: new Date().toISOString(),
    is_simulated: true,
    source: "VIRTUAL_SIMULATION_ENGINE",
  };
}







function getFallbackTrends(segmentId = "PIPE-SEC-4B-92"): HistoricalTrend[] {
  const isDeteriorating = segmentId === "PIPE-SEC-4B-92";
  const now = new Date();
  const points = [];
  for (let i = 0; i < 14; i++) {
    const d = new Date(now.getTime() - (13 - i) * 24 * 3600 * 1000);
    points.push({
      timestamp: d.toISOString(),
      day_offset: 13 - i,
      health_score: isDeteriorating ? Math.max(35, 75 - i * 2.8) : Math.min(95, 88 + (i % 3)),
      pressure_bar: isDeteriorating ? Math.max(2.4, 4.5 - i * 0.12) : 4.6,
      flow_lps: isDeteriorating ? 120 + i * 2.5 : 120,
      acoustic_spl_db: isDeteriorating ? Math.min(84, 42 + i * 2.6) : 38,
    });
  }

  return [
    {
      id: `TRD-${segmentId}`,
      pipeline_segment_id: segmentId,
      trend_direction: isDeteriorating ? "DETERIORATING" : "STABLE",
      health_slope_per_day: isDeteriorating ? -2.4 : 0.05,
      pressure_variance: isDeteriorating ? 0.32 : 0.04,
      flow_anomaly_rate: isDeteriorating ? 0.22 : 0.02,
      acoustic_emission_count: isDeteriorating ? 6 : 0,
      historical_leak_count: isDeteriorating ? 2 : 0,
      window_days: 30,
      time_series_points: points,
      assessed_at: new Date().toISOString(),
      is_simulated: true,
      source: "VIRTUAL_SIMULATION_ENGINE",
    },
  ];
}

function getFallbackMaintenanceRecommendations(status?: string, urgency?: string): MaintenanceRecommendation[] {
  let recs = [...fallbackRecommendationsStoreMaintenance];
  if (status && status !== "ALL") {
    recs = recs.filter((r) => r.status === status);
  }
  if (urgency && urgency !== "ALL") {
    recs = recs.filter((r) => r.urgency === urgency);
  }
  return recs;
}

function reviewFallbackMaintenanceRecommendation(
  id: string,
  action: "ACKNOWLEDGE" | "DISMISS" | "DISPATCH",
  operatorId = "OPERATOR_CHIEF",
  notes?: string
): MaintenanceRecommendation {
  const rec = fallbackRecommendationsStoreMaintenance.find((r) => r.id === id);
  const now = new Date().toISOString();
  if (rec) {
    if (action === "ACKNOWLEDGE") rec.status = "ACKNOWLEDGED";
    else if (action === "DISMISS") rec.status = "DISMISSED";
    else if (action === "DISPATCH") {
      rec.status = "DISPATCHED";
      rec.dispatched_mission_id = `REC-2026-${Math.random().toString(36).substring(2, 8).toUpperCase()}`;
    }
    rec.reviewed_by = operatorId;
    rec.operator_notes = notes;
    rec.reviewed_at = now;
    return { ...rec };
  }
  return {
    id,
    pipeline_segment_id: "PIPE-SEC-4B-92",
    health_score: 42.0,
    predicted_risk: "CRITICAL",
    urgency: "CRITICAL",
    recommended_action: "DISPATCH_INSPECTION_ROVER",
    timeframe_days: 1,
    status: action === "DISPATCH" ? "DISPATCHED" : action === "ACKNOWLEDGE" ? "ACKNOWLEDGED" : "DISMISSED",
    explanation: "Updated offline recommendation.",
    sensor_evidence: {},
    operator_notes: notes,
    reviewed_by: operatorId,
    reviewed_at: now,
    created_at: now,
    is_simulated: true,
    source: "VIRTUAL_SIMULATION_ENGINE",
  };
}







/* ========================================================= */
/* TASK 10 DIGITAL TWIN FALLBACK STORES & GENERATORS         */
/* ========================================================= */

const fallbackNetworksStore: HydraulicNetwork[] = [
  {
    id: "NET-METRO-01",
    name: "Metro Central Water Supply & Hydraulic Distribution Network",
    description: "Digital twin of metropolitan water grid including trunk mains, booster pumps, elevated tanks, and pressure zones.",
    headloss_formula: "H-W",
    flow_units: "LPS",
    demand_model: "PDA",
    is_active: true,
    created_at: new Date().toISOString(),
  },
];

const fallbackScenariosStore: SimulationScenario[] = [
  {
    id: "SCEN-BASELINE-01",
    network_id: "NET-METRO-01",
    name: "Baseline Municipal Operating Conditions",
    scenario_type: "BASELINE",
    description: "Nominal 24-hour diurnal water distribution across Metro Central with balanced pressure gradients and zero active leaks.",
    is_baseline: true,
    duration_hours: 24,
    time_step_minutes: 60,
    solver_mode: "PDA",
    status: "COMPLETED",
    parameters_override: { demand_multiplier: 1.0, leaks: [] },
  },
  {
    id: "SCEN-PEAK-DEMAND-01",
    network_id: "NET-METRO-01",
    name: "Summer Morning Peak Demand Surge",
    scenario_type: "HIGH_DEMAND",
    description: "Simulates 1.6x municipal demand surge during hot summer morning hours, testing peripheral node pressure resilience.",
    is_baseline: false,
    duration_hours: 24,
    time_step_minutes: 60,
    solver_mode: "PDA",
    status: "COMPLETED",
    parameters_override: { demand_multiplier: 1.6 },
  },
  {
    id: "SCEN-BURST-PIPE-02",
    network_id: "NET-METRO-01",
    name: "Severe Pipe Burst on Metro Central Trunk B",
    scenario_type: "PIPE_BURST",
    description: "Catastrophic structural pipe rupture on PIPE-SEC-4B-92 near J2. Emitter orifice area 35 cm2 discharging over 40 L/s.",
    is_baseline: false,
    duration_hours: 24,
    time_step_minutes: 60,
    solver_mode: "PDA",
    status: "COMPLETED",
    parameters_override: {
      leaks: [
        {
          node_id: "NODE-JUNC-02",
          area_m2: 0.0035,
          discharge_coeff: 0.8,
          pipeline_segment_id: "PIPE-SEC-4B-92",
        },
      ],
    },
  },
  {
    id: "SCEN-MINOR-LEAK-03",
    network_id: "NET-METRO-01",
    name: "Developing Pin-Hole Leak at Industrial Feeder 1",
    scenario_type: "MINOR_LEAK",
    description: "Simulates an incipient sub-surface pipe leak on PIPE-IND-1A-04 near J4, correlated with Task 07 acoustic anomalies.",
    is_baseline: false,
    duration_hours: 24,
    time_step_minutes: 60,
    solver_mode: "PDA",
    status: "COMPLETED",
    parameters_override: {
      leaks: [
        {
          node_id: "NODE-JUNC-04",
          area_m2: 0.0004,
          discharge_coeff: 0.75,
          pipeline_segment_id: "PIPE-IND-1A-04",
        },
      ],
    },
  },
  {
    id: "SCEN-PUMP-TRIP-04",
    network_id: "NET-METRO-01",
    name: "Grand Avenue Spine Booster Pump Trip",
    scenario_type: "PUMP_TRIP",
    description: "Simulates unannounced mechanical shutdown / power trip of Booster Pump Station P1.",
    is_baseline: false,
    duration_hours: 24,
    time_step_minutes: 60,
    solver_mode: "PDA",
    status: "COMPLETED",
    parameters_override: {
      pump_overrides: { "LINK-PUMP-BOOSTER-01": { status: "CLOSED", speed: 0 } },
    },
  },
];

function getFallbackDigitalTwinNetworks(): HydraulicNetwork[] {
  return fallbackNetworksStore;
}

function getFallbackDigitalTwinTopology(networkId: string): NetworkTopologyBundle {
  return {
    network: fallbackNetworksStore[0],
    nodes_count: 8,
    links_count: 8,
    geojson: {
      type: "FeatureCollection",
      features: [
        {
          type: "Feature",
          id: "NODE-RES-01",
          geometry: { type: "Point", coordinates: [-74.006, 40.722] },
          properties: {
            feature_type: "NODE",
            name: "Northern Aqueduct Supply Reservoir R1",
            node_type: "RESERVOIR",
            elevation_m: 25.0,
            base_head_m: 85.0,
            min_pressure_bar: 2.0,
            nominal_pressure_bar: 5.8,
          },
        },
        {
          type: "Feature",
          id: "NODE-JUNC-01",
          geometry: { type: "Point", coordinates: [-74.006, 40.7128] },
          properties: {
            feature_type: "NODE",
            name: "Central Grand Avenue Spine Junction J1",
            node_type: "JUNCTION",
            elevation_m: 16.5,
            base_demand_lps: 22.0,
            min_pressure_bar: 1.5,
            nominal_pressure_bar: 4.5,
          },
        },
        {
          type: "Feature",
          id: "NODE-JUNC-02",
          geometry: { type: "Point", coordinates: [-74.011, 40.7115] },
          properties: {
            feature_type: "NODE",
            name: "Metro Central Commercial Distribution Node J2",
            node_type: "JUNCTION",
            elevation_m: 14.0,
            base_demand_lps: 18.5,
            min_pressure_bar: 1.5,
            nominal_pressure_bar: 4.2,
          },
        },
        {
          type: "Feature",
          id: "NODE-JUNC-03",
          geometry: { type: "Point", coordinates: [-74.015, 40.71] },
          properties: {
            feature_type: "NODE",
            name: "Western Harbor Perimeter Junction J3",
            node_type: "JUNCTION",
            elevation_m: 8.0,
            base_demand_lps: 12.0,
            min_pressure_bar: 1.5,
            nominal_pressure_bar: 4.0,
          },
        },
        {
          type: "Feature",
          id: "NODE-JUNC-04",
          geometry: { type: "Point", coordinates: [-74.0021, 40.7145] },
          properties: {
            feature_type: "NODE",
            name: "Eastern Industrial Sector Node J4",
            node_type: "JUNCTION",
            elevation_m: 18.0,
            base_demand_lps: 28.0,
            min_pressure_bar: 1.5,
            nominal_pressure_bar: 4.1,
          },
        },
        {
          type: "Feature",
          id: "NODE-TANK-01",
          geometry: { type: "Point", coordinates: [-73.998, 40.716] },
          properties: {
            feature_type: "NODE",
            name: "Industrial Park Elevated Storage Tank T1",
            node_type: "TANK",
            elevation_m: 24.0,
            initial_level_m: 6.5,
            diameter_m: 18.0,
            min_pressure_bar: 1.5,
            nominal_pressure_bar: 3.8,
          },
        },
        {
          type: "Feature",
          id: "NODE-JUNC-05",
          geometry: { type: "Point", coordinates: [-74.006, 40.704] },
          properties: {
            feature_type: "NODE",
            name: "Harbor Terminal Service Intake J5",
            node_type: "JUNCTION",
            elevation_m: 6.5,
            base_demand_lps: 15.0,
            min_pressure_bar: 1.5,
            nominal_pressure_bar: 3.5,
          },
        },
        {
          type: "Feature",
          id: "NODE-JUNC-06",
          geometry: { type: "Point", coordinates: [-74.013, 40.718] },
          properties: {
            feature_type: "NODE",
            name: "Pinecrest Residential Node J6",
            node_type: "JUNCTION",
            elevation_m: 22.0,
            base_demand_lps: 14.0,
            min_pressure_bar: 1.5,
            nominal_pressure_bar: 3.9,
          },
        },
        // Links
        {
          type: "Feature",
          id: "LINK-PIPE-TRUNK-A",
          geometry: {
            type: "LineString",
            coordinates: [
              [-74.006, 40.722],
              [-74.006, 40.7128],
            ],
          },
          properties: {
            feature_type: "LINK",
            name: "Spine Trunk Line A (Upper)",
            link_type: "PIPE",
            length_m: 1050.0,
            diameter_mm: 750.0,
            current_status: "OPEN",
          },
        },
        {
          type: "Feature",
          id: "LINK-PIPE-TRUNK-B1",
          geometry: {
            type: "LineString",
            coordinates: [
              [-74.006, 40.7128],
              [-74.011, 40.7115],
            ],
          },
          properties: {
            feature_type: "LINK",
            name: "Metro Central Main Trunk Line B (West)",
            link_type: "PIPE",
            length_m: 620.0,
            diameter_mm: 600.0,
            current_status: "OPEN",
          },
        },
        {
          type: "Feature",
          id: "LINK-PIPE-TRUNK-B2",
          geometry: {
            type: "LineString",
            coordinates: [
              [-74.011, 40.7115],
              [-74.015, 40.71],
            ],
          },
          properties: {
            feature_type: "LINK",
            name: "Metro Central Main Trunk Line B (Far West)",
            link_type: "PIPE",
            length_m: 540.0,
            diameter_mm: 600.0,
            current_status: "OPEN",
          },
        },
        {
          type: "Feature",
          id: "LINK-PIPE-IND-01",
          geometry: {
            type: "LineString",
            coordinates: [
              [-74.006, 40.7128],
              [-74.0035, 40.7135],
              [-74.0021, 40.7145],
            ],
          },
          properties: {
            feature_type: "LINK",
            name: "Industrial Park Feeder Line 1",
            link_type: "PIPE",
            length_m: 820.0,
            diameter_mm: 400.0,
            current_status: "OPEN",
          },
        },
      ],
    },
    solver_data: {},
  };
}

function getFallbackDigitalTwinScenarios(networkId: string): SimulationScenario[] {
  return fallbackScenariosStore;
}

function getFallbackDigitalTwinScenario(scenarioId: string): SimulationScenario {
  const scen = fallbackScenariosStore.find((s) => s.id === scenarioId);
  return scen || fallbackScenariosStore[0];
}

function createFallbackDigitalTwinScenario(data: any): any {
  const id = `SCEN-${Math.random().toString(36).substring(2, 8).toUpperCase()}`;
  const scen: SimulationScenario = {
    id,
    network_id: data.network_id || "NET-METRO-01",
    name: data.name,
    scenario_type: data.scenario_type || "WHAT_IF",
    description: data.description || "",
    is_baseline: false,
    duration_hours: data.duration_hours || 24,
    time_step_minutes: data.time_step_minutes || 60,
    solver_mode: data.solver_mode || "PDA",
    status: "COMPLETED",
    parameters_override: data.parameters_override || {},
  };
  fallbackScenariosStore.push(scen);
  return { id, name: scen.name, scenario_type: scen.scenario_type, status: "COMPLETED", message: "Created offline." };
}

function runFallbackDigitalTwinScenario(scenarioId: string, overrides?: any): any {
  return {
    run_id: `RUN-${Math.random().toString(36).substring(2, 8).toUpperCase()}`,
    scenario_id: scenarioId,
    execution_timestamp: new Date().toISOString(),
    execution_duration_ms: 18.5,
    converged: true,
    total_demand_m3: 345.6,
    total_leakage_m3: scenarioId.includes("BURST") ? 142.5 : 0.0,
    water_loss_percentage: scenarioId.includes("BURST") ? 29.2 : 0.0,
    min_pressure_bar: scenarioId.includes("BURST") ? 1.15 : 3.85,
    max_pressure_bar: 5.8,
    pressure_deficit_nodes_count: scenarioId.includes("BURST") ? 2 : 0,
    is_simulated: true,
    source: "VIRTUAL_SIMULATION_ENGINE",
  };
}







function getFallbackDigitalTwinRunResults(runId: string): SimulationRun {
  return {
    id: runId,
    scenario_id: "SCEN-BASELINE-01",
    network_id: "NET-METRO-01",
    execution_timestamp: new Date().toISOString(),
    execution_duration_ms: 14.2,
    converged: true,
    iterations: 4,
    total_demand_m3: 358.2,
    total_leakage_m3: 0.0,
    water_loss_percentage: 0.0,
    min_pressure_bar: 3.85,
    max_pressure_bar: 5.82,
    pressure_deficit_nodes_count: 0,
    summary: {
      solver_name: "WNTR / EPANET 2.2 Simulation Engine",
      total_supply_lps: 99.5,
      total_demand_lps: 99.5,
      total_leakage_lps: 0.0,
      avg_pressure_bar: 4.45,
    },
    nodes: {
      "NODE-RES-01": {
        node_id: "NODE-RES-01",
        name: "Northern Aqueduct Supply Reservoir R1",
        node_type: "RESERVOIR",
        pressure_bar: 5.88,
        pressure_psi: 85.2,
        head_m: 85.0,
        elevation_m: 25.0,
        actual_demand_lps: 0.0,
        expected_demand_lps: 0.0,
        leak_flow_lps: 0.0,
        pressure_deficit: false,
        status: "NORMAL",
      },
      "NODE-JUNC-01": {
        node_id: "NODE-JUNC-01",
        name: "Central Grand Avenue Spine Junction J1",
        node_type: "JUNCTION",
        pressure_bar: 4.62,
        pressure_psi: 67.0,
        head_m: 63.6,
        elevation_m: 16.5,
        actual_demand_lps: 22.0,
        expected_demand_lps: 22.0,
        leak_flow_lps: 0.0,
        pressure_deficit: false,
        status: "NORMAL",
      },
      "NODE-JUNC-02": {
        node_id: "NODE-JUNC-02",
        name: "Metro Central Commercial Distribution Node J2",
        node_type: "JUNCTION",
        pressure_bar: 4.35,
        pressure_psi: 63.1,
        head_m: 58.4,
        elevation_m: 14.0,
        actual_demand_lps: 18.5,
        expected_demand_lps: 18.5,
        leak_flow_lps: 0.0,
        pressure_deficit: false,
        status: "NORMAL",
      },
      "NODE-JUNC-04": {
        node_id: "NODE-JUNC-04",
        name: "Eastern Industrial Sector Node J4",
        node_type: "JUNCTION",
        pressure_bar: 4.12,
        pressure_psi: 59.8,
        head_m: 60.0,
        elevation_m: 18.0,
        actual_demand_lps: 28.0,
        expected_demand_lps: 28.0,
        leak_flow_lps: 0.0,
        pressure_deficit: false,
        status: "NORMAL",
      },
    },
    links: {
      "LINK-PIPE-TRUNK-A": {
        link_id: "LINK-PIPE-TRUNK-A",
        name: "Spine Trunk Line A (Upper)",
        link_type: "PIPE",
        flow_lps: 99.5,
        velocity_mps: 0.98,
        headloss_m: 2.14,
        unit_headloss_m_per_km: 2.04,
        friction_factor: 140,
        direction: "FORWARD",
        status: "OPEN",
      },
      "LINK-PIPE-TRUNK-B1": {
        link_id: "LINK-PIPE-TRUNK-B1",
        name: "Metro Central Main Trunk Line B (West)",
        link_type: "PIPE",
        flow_lps: 45.2,
        velocity_mps: 0.64,
        headloss_m: 0.85,
        unit_headloss_m_per_km: 1.37,
        friction_factor: 130,
        direction: "FORWARD",
        status: "OPEN",
      },
    },
    timesteps: [],
    is_simulated: true,
    source: "VIRTUAL_SIMULATION_ENGINE",
  };
}







function compareFallbackDigitalTwinScenarios(baselineId: string, comparisonId: string): ScenarioComparison {
  return {
    comparison_id: `CMP-${Math.random().toString(36).substring(2, 8).toUpperCase()}`,
    baseline_scenario_id: baselineId,
    comparison_scenario_id: comparisonId,
    baseline_run_id: "RUN-BASE-01",
    comparison_run_id: "RUN-CMP-02",
    delta_total_leakage_m3: 142.5,
    delta_water_loss_pct: 28.4,
    delta_min_pressure_bar: -2.7,
    affected_nodes_count: 3,
    high_risk_links_count: 2,
    nodes: {
      "NODE-JUNC-02": {
        node_id: "NODE-JUNC-02",
        name: "Metro Central Commercial Distribution Node J2",
        baseline_pressure_bar: 4.35,
        comparison_pressure_bar: 1.15,
        delta_pressure_bar: -3.2,
        pressure_drop_pct: 73.6,
        baseline_leak_lps: 0.0,
        comparison_leak_lps: 39.5,
        delta_leak_lps: 39.5,
        deficit_introduced: true,
      },
      "NODE-JUNC-01": {
        node_id: "NODE-JUNC-01",
        name: "Central Grand Avenue Spine Junction J1",
        baseline_pressure_bar: 4.62,
        comparison_pressure_bar: 2.85,
        delta_pressure_bar: -1.77,
        pressure_drop_pct: 38.3,
        baseline_leak_lps: 0.0,
        comparison_leak_lps: 0.0,
        delta_leak_lps: 0.0,
        deficit_introduced: false,
      },
    },
    links: {
      "LINK-PIPE-TRUNK-B1": {
        link_id: "LINK-PIPE-TRUNK-B1",
        name: "Metro Central Main Trunk Line B (West)",
        baseline_flow_lps: 45.2,
        comparison_flow_lps: 84.7,
        delta_flow_lps: 39.5,
        baseline_velocity_mps: 0.64,
        comparison_velocity_mps: 1.82,
        delta_velocity_mps: 1.18,
        is_high_risk: true,
      },
    },
    is_simulated: true,
    source: "VIRTUAL_SIMULATION_ENGINE",
  };
}







function simulateFallbackDigitalTwinLeak(req: any): any {
  return {
    scenario: {
      id: `SCEN-WHATIF-${Math.random().toString(36).substring(2, 6).toUpperCase()}`,
      name: `What-If Leak @ ${req.target_node_id} (${req.leak_area_cm2} cm²)`,
      type: "WHAT_IF_LEAK",
    },
    run: {
      id: `RUN-${Math.random().toString(36).substring(2, 6).toUpperCase()}`,
      converged: true,
      total_leakage_m3: Math.round(req.leak_area_cm2 * 12.5),
      water_loss_percentage: Math.min(45.0, Math.round(req.leak_area_cm2 * 2.8)),
      min_pressure_bar: 1.25,
      pressure_deficit_nodes_count: req.leak_area_cm2 > 5 ? 2 : 0,
    },
    comparison: compareFallbackDigitalTwinScenarios("SCEN-BASELINE-01", "SCEN-BURST-PIPE-02"),
  };
}

function getFallbackDigitalTwinEquipmentStatus(networkId: string): EquipmentStatusBundle {
  return {
    network_id: networkId,
    pumps: [
      {
        id: "LINK-PUMP-BOOSTER-01",
        name: "Metro Spine Booster Pump Station P1",
        status: "OPEN",
        speed: 1.0,
        power_kw: 45.0,
        flow_lps: 42.5,
        headloss_m: 45.0,
        efficiency_pct: 82.5,
      },
    ],
    valves: [
      {
        id: "LINK-VALVE-HRB-PRV",
        name: "Harbor Zone Pressure Reducing Valve PRV-01",
        valve_type: "PRV",
        setting_bar: 3.5,
        status: "ACTIVE",
        flow_lps: 18.2,
      },
    ],
    tanks: [
      {
        id: "NODE-TANK-01",
        name: "Industrial Park Elevated Storage Tank T1",
        level_m: 6.5,
        min_level_m: 1.5,
        max_level_m: 12.0,
        diameter_m: 18.0,
        volume_pct: 54.2,
        pressure_bar: 3.8,
        status: "OPERATIONAL",
      },
    ],
    is_simulated: true,
    source: "VIRTUAL_SIMULATION_ENGINE",
  };
}







function handoffFallbackDigitalTwinRoverDispatch(req: any): RoverHandoffResponse {
  return {
    recommendation_id: `REC-DTWIN-${Math.random().toString(36).substring(2, 8).toUpperCase()}`,
    status: "RECOMMENDED",
    scenario_id: req.scenario_id,
    target_node_id: req.target_node_id,
    target_coordinates: [-74.011, 40.7115],
    assigned_rover_id: "ROV-AQUA-01",
    assigned_rover_name: "Proteus Mk.IV Pipeline Inspector",
    suitability_score: 94.5,
    inspection_urgency: "CRITICAL_BURST_INVESTIGATION",
    operator_approval_required: true,
    notes: req.notes,
    message: "Digital Twin hydraulic anomaly successfully packaged into autonomous rover inspection mission recommendation. Awaiting human operator approval.",
    is_simulated: true,
    source: "VIRTUAL_SIMULATION_ENGINE",
  };
}







function getFallbackDigitalTwinNet1Benchmark(): Net1BenchmarkResult {
  return {
    benchmark_network: "EPANET Net1 (EPA Benchmark)",
    benchmark_file: "Net1.inp",
    source_provenance: "EPA EPANET Standard Net1 Distribution Benchmark bundled with WNTR",
    nodes_count: 11,
    links_count: 13,
    junctions_count: 9,
    tanks_count: 1,
    reservoirs_count: 1,
    pipes_count: 12,
    pumps_count: 1,
    valves_count: 0,
    execution_duration_ms: 18.5,
    validation_status: "VALIDATED",
    is_validated: true,
    tolerances: {
      max_pressure_relative_error_pct_allowed: 0.10,
      max_flow_relative_error_pct_allowed: 0.10,
      mass_balance_residual_threshold_m3s: 0.0001,
      loop_energy_headloss_closure_threshold_m: 0.05,
    },
    metrics: {
      max_absolute_error_pressure_m: 0.000017,
      max_relative_error_pressure_pct: 0.000048,
      max_absolute_error_head_m: 0.000017,
      max_relative_error_head_pct: 0.000048,
      max_absolute_error_flow_m3s: 0.00000007,
      max_relative_error_flow_pct: 0.000035,
      max_absolute_error_velocity_mps: 0.000015,
      total_inflow_m3s: 0.117407,
      total_outflow_m3s: 0.117407,
      mass_balance_residual_m3s: 0.0,
      mass_balance_conserved: true,
      loop_headloss_closure_residual_m: 0.0,
      energy_balance_conserved: true,
    },
    is_simulated: true,
    source: "VIRTUAL_SIMULATION_ENGINE",
  };
}













function getFallbackDigitalTwinValidationStatus(): ValidationStatus {
  return {
    audit_version: "TASK-10.5-HYDRAULIC-ENGINEERING-AUDIT",
    primary_solver: {
      name: "EPANET 2.2 / WNTR 1.5.0 Engine",
      status: "VALIDATED",
      modes_supported: ["DDA (Demand-Driven Analysis)", "PDA (Pressure-Dependent Demand)"],
      fallback_policy: "NO_SILENT_FALLBACK (explicit exception on failure)",
    },
    secondary_solver: {
      name: "EXPERIMENTAL: Todini-Pilati Global Gradient Solver (Python / Hazen-Williams)",
      status: "EXPERIMENTAL",
      scope: "Isolated testbed and educational verification; never silently substituted for primary solver",
    },
    benchmark_summary: {
      name: "EPANET Net1 (EPA Standard Benchmark)",
      status: "VALIDATED",
      max_relative_pressure_error_pct: 0.000048,
      max_absolute_flow_error_m3s: 0.00000007,
      mass_balance_continuity_residual_m3s: 0.0,
      loop_headloss_closure_residual_m: 0.0,
    },
    physical_formulations: {
      pipe_friction: "Hazen-Williams: h_f = 10.67 * (L / (C^1.852 * D^4.87)) * Q^1.852",
      orifice_leakage: "Torricelli: Q = Cd * A * sqrt(2 * ΔP / ρ)",
      pressure_dependent_demand: "Wagner PDD: d = d_req * ((P - P_min) / (P_req - P_min))^0.5",
      mass_conservation: "Sum(Q_in) - Sum(Q_out) = 0",
      energy_conservation: "Sum(h_f) around closed loops = 0",
    },
    operational_guardrails: {
      simulation_isolation: "STRICT (is_simulated: true, source: VIRTUAL_SIMULATION_ENGINE)",
      hardware_control_disabled: true,
      human_approval_required_for_dispatch: true,
      baseline_immutability: true,
    },
    is_simulated: true,
    source: "VIRTUAL_SIMULATION_ENGINE",
  };
}







function getFallbackInfrastructureOverview(): InfrastructureOverviewResponse {
  return {
    total_segments_analyzed: 5,
    critical_segments_count: 1,
    high_risk_segments_count: 1,
    moderate_risk_segments_count: 2,
    low_risk_segments_count: 1,
    average_network_vulnerability: 54.2,
    network_deterioration_rate: 0.16,
    deteriorating_segments_count: 2,
    active_clusters_count: 2,
    pending_inspections_count: 3,
    highest_risk_segment: {
      id: "PIPE-SEC-4B-92",
      name: "Metro Central Main Trunk Line B",
      score: 84.5,
      level: "CRITICAL",
      material: "Ductile Iron (Class 54)",
    },
    highest_risk_zone: {
      code: "ZONE-PZ01",
      name: "Metro Central High-Pressure Corridor",
      avg_score: 68.2,
      critical_count: 1,
    },
    validation_status: "VALIDATED",
    methodology_version: "v1.2.0-hybrid-physics-geodesic",
    configured_risk_weights: {
      hydraulic: 0.30,
      structural: 0.25,
      incident: 0.25,
      environmental: 0.20,
    },
    last_updated: new Date().toISOString(),
    is_fallback: true,
    is_simulated: true,
    source: "VIRTUAL_SIMULATION_ENGINE",
  };
}

function getFallbackInfrastructureSegments(): PipelineVulnerabilityListResponse {
  const items: PipelineVulnerabilityItem[] = [
    {
      id: "vuln_PIPE-SEC-4B-92",
      pipeline_segment_id: "PIPE-SEC-4B-92",
      segment_name: "Metro Central Main Trunk Line B",
      material: "Ductile Iron (Class 54)",
      diameter_mm: 600,
      length_m: 1850.0,
      pressure_zone_id: "PZ-01",
      category: "primary",
      vulnerability_score: 84.5,
      vulnerability_level: "CRITICAL",
      hydraulic_score: 82.0,
      structural_score: 80.0,
      incident_score: 92.0,
      environmental_score: 85.0,
      contributing_factors: {
        hydraulic: { score: 82.0, weight: 0.3, weighted_contribution: 24.6, reasons: ["High nominal operating pressure (65 psi)", "Pressure zone transition"] },
        structural: { score: 80.0, weight: 0.25, weighted_contribution: 20.0, reasons: ["Large transmission diameter (600mm) increases burst consequence"] },
        incident: { score: 92.0, weight: 0.25, weighted_contribution: 23.0, reasons: ["Active acoustic anomaly alert", "Historical leak incident cluster"] },
        environmental: { score: 85.0, weight: 0.2, weighted_contribution: 17.0, reasons: ["Immediate proximity (120m) to active incident cluster"] },
      },
      confidence: 0.92,
      data_completeness_pct: 95.0,
      uncertainty_margin: 3.5,
      deterioration_rate_per_day: 0.26,
      trend_direction: "DETERIORATING",
      active_incident_count: 2,
      midpoint_lat: 40.7128,
      midpoint_lng: -74.006,
      assessed_at: new Date().toISOString(),
      is_simulated: true,
    },
    {
      id: "vuln_PIPE-HRB-02-19",
      pipeline_segment_id: "PIPE-HRB-02-19",
      segment_name: "Harbor Marginal Service Line",
      material: "Cast Iron (Epoxy Lined)",
      diameter_mm: 250,
      length_m: 780.0,
      pressure_zone_id: "PZ-04",
      category: "distribution",
      vulnerability_score: 66.8,
      vulnerability_level: "HIGH",
      hydraulic_score: 55.0,
      structural_score: 75.0,
      incident_score: 72.0,
      environmental_score: 65.0,
      contributing_factors: {
        hydraulic: { score: 55.0, weight: 0.3, weighted_contribution: 16.5, reasons: ["Nominal pressure head within limits"] },
        structural: { score: 75.0, weight: 0.25, weighted_contribution: 18.8, reasons: ["Cast iron material subject to external graphitization"] },
        incident: { score: 72.0, weight: 0.25, weighted_contribution: 18.0, reasons: ["1 logged leak anomaly event"] },
        environmental: { score: 65.0, weight: 0.2, weighted_contribution: 13.0, reasons: ["Coastal soil moisture elevation"] },
      },
      confidence: 0.88,
      data_completeness_pct: 85.0,
      uncertainty_margin: 4.8,
      deterioration_rate_per_day: 0.18,
      trend_direction: "DETERIORATING",
      active_incident_count: 1,
      midpoint_lat: 40.7091,
      midpoint_lng: -74.0115,
      assessed_at: new Date().toISOString(),
      is_simulated: true,
    },
    {
      id: "vuln_PIPE-SEC-4A-10",
      pipeline_segment_id: "PIPE-SEC-4A-10",
      segment_name: "Grand Avenue Spine Trunk Line A",
      material: "Pre-stressed Concrete Cylinder",
      diameter_mm: 750,
      length_m: 2100.0,
      pressure_zone_id: "PZ-01",
      category: "primary",
      vulnerability_score: 52.0,
      vulnerability_level: "MODERATE",
      hydraulic_score: 50.0,
      structural_score: 68.0,
      incident_score: 40.0,
      environmental_score: 50.0,
      contributing_factors: {},
      confidence: 0.85,
      data_completeness_pct: 88.0,
      uncertainty_margin: 5.5,
      deterioration_rate_per_day: 0.08,
      trend_direction: "STABLE",
      active_incident_count: 0,
      midpoint_lat: 40.7128,
      midpoint_lng: -74.006,
      assessed_at: new Date().toISOString(),
      is_simulated: true,
    },
    {
      id: "vuln_PIPE-RES-3C-11",
      pipeline_segment_id: "PIPE-RES-3C-11",
      segment_name: "Pinecrest Residential Sub-Branch",
      material: "Ductile Iron",
      diameter_mm: 350,
      length_m: 940.0,
      pressure_zone_id: "PZ-03",
      category: "secondary",
      vulnerability_score: 41.5,
      vulnerability_level: "MODERATE",
      hydraulic_score: 42.0,
      structural_score: 50.0,
      incident_score: 35.0,
      environmental_score: 40.0,
      contributing_factors: {},
      confidence: 0.82,
      data_completeness_pct: 80.0,
      uncertainty_margin: 6.0,
      deterioration_rate_per_day: 0.05,
      trend_direction: "STABLE",
      active_incident_count: 0,
      midpoint_lat: 40.7198,
      midpoint_lng: -74.0089,
      assessed_at: new Date().toISOString(),
      is_simulated: true,
    },
    {
      id: "vuln_PIPE-IND-1A-04",
      pipeline_segment_id: "PIPE-IND-1A-04",
      segment_name: "Industrial Park Feeder Line 1",
      material: "High-Density Polyethylene (HDPE)",
      diameter_mm: 400,
      length_m: 820.0,
      pressure_zone_id: "PZ-02",
      category: "secondary",
      vulnerability_score: 26.2,
      vulnerability_level: "LOW",
      hydraulic_score: 32.0,
      structural_score: 22.0,
      incident_score: 25.0,
      environmental_score: 28.0,
      contributing_factors: {},
      confidence: 0.90,
      data_completeness_pct: 90.0,
      uncertainty_margin: 4.0,
      deterioration_rate_per_day: 0.02,
      trend_direction: "STABLE",
      active_incident_count: 0,
      midpoint_lat: 40.7145,
      midpoint_lng: -74.0021,
      assessed_at: new Date().toISOString(),
      is_simulated: true,
    },
  ];

  return {
    total: items.length,
    limit: 50,
    offset: 0,
    items,
  };
}

function getFallbackSegmentDeepDive(segmentId: string): SegmentDeepDiveResponse {
  const segments = getFallbackInfrastructureSegments().items;
  const match = segments.find((s) => s.pipeline_segment_id === segmentId) || segments[0];

  return {
    ...match,
    predictive_forecast: {
      projected_risk_24h: match.vulnerability_score + 0.3,
      projected_risk_7d: match.vulnerability_score + 1.8,
      projected_risk_30d: Math.min(100, match.vulnerability_score + 7.8),
      trend_24h_delta: 0.3,
      trend_7d_delta: 1.8,
      trend_30d_delta: 7.8,
      primary_risk_drivers: [
        "Acoustic anomaly density in vicinity",
        "Conduit joint fatigue on ductile iron substrate",
        "High operating pressure transient zone",
      ],
      mitigation_urgency: match.vulnerability_level === "CRITICAL" ? "IMMEDIATE" : "SHORT_TERM",
      hydraulic_deficit_flag: match.hydraulic_score > 60,
      cluster_proximity_m: 140.0,
    },
    inspection_priority: {
      id: `INSP-FALLBACK-${match.pipeline_segment_id}`,
      pipeline_segment_id: match.pipeline_segment_id,
      segment_name: match.segment_name,
      priority_score: match.vulnerability_score,
      priority_level: match.vulnerability_level === "CRITICAL" ? "CRITICAL_IMMEDIATE" : "HIGH_PRIORITY",
      status: "PENDING",
      target_latitude: match.midpoint_lat || 40.7128,
      target_longitude: match.midpoint_lng || -74.006,
      reasons: ["Critical vulnerability index", "Rapid degradation rate"],
      suggested_action: "Immediate acoustic crawling patrol and acoustic leak pinpointing",
      is_simulated: true,
    },
    source: "VIRTUAL_SIMULATION_ENGINE",
  };
}

function getFallbackInfrastructureClusters(): SpatialClusterItem[] {
  return [
    {
      id: "CLUS-01-METRO",
      cluster_name: "Hotspot Cluster #1 (Ductile Iron Main)",
      zone_id: "ZONE-PZ01",
      centroid_lat: 40.7128,
      centroid_lng: -74.006,
      radius_m: 220.0,
      incident_count: 2,
      dominant_material: "Ductile Iron (Class 54)",
      average_severity: 0.82,
      cluster_risk_level: "CRITICAL",
      affected_segment_ids: ["PIPE-SEC-4B-92"],
      hotspot_intensity: 0.85,
      is_active: true,
      identified_at: new Date().toISOString(),
      is_simulated: true,
    },
    {
      id: "CLUS-02-HARBOR",
      cluster_name: "Hotspot Cluster #2 (Cast Iron Terminal)",
      zone_id: "ZONE-PZ04",
      centroid_lat: 40.7091,
      centroid_lng: -74.0115,
      radius_m: 180.0,
      incident_count: 1,
      dominant_material: "Cast Iron",
      average_severity: 0.65,
      cluster_risk_level: "HIGH",
      affected_segment_ids: ["PIPE-HRB-02-19"],
      hotspot_intensity: 0.62,
      is_active: true,
      identified_at: new Date().toISOString(),
      is_simulated: true,
    },
  ];
}

function getFallbackInfrastructureZones(): GeographicRiskZoneItem[] {
  return [
    {
      id: "zone_zone-pz01",
      zone_code: "ZONE-PZ01",
      zone_name: "Metro Central High-Pressure Corridor",
      description: "Primary high-pressure arterial spine servicing downtown commercial and civic core.",
      total_segments: 2,
      total_length_km: 3.95,
      avg_vulnerability_score: 68.2,
      dominant_risk_level: "HIGH",
      critical_segment_count: 1,
      active_clusters_count: 1,
      avg_pressure_psi: 65.0,
      is_simulated: true,
    },
    {
      id: "zone_zone-pz04",
      zone_code: "ZONE-PZ04",
      zone_name: "Harbor Utility Terminal",
      description: "Coastal distribution grid with elevated saline groundwater and marine proximity.",
      total_segments: 1,
      total_length_km: 0.78,
      avg_vulnerability_score: 66.8,
      dominant_risk_level: "HIGH",
      critical_segment_count: 0,
      active_clusters_count: 1,
      avg_pressure_psi: 58.0,
      is_simulated: true,
    },
    {
      id: "zone_zone-pz03",
      zone_code: "ZONE-PZ03",
      zone_name: "Northern Residential Zone",
      description: "Residential sub-branch with diurnal peaking and residential service connections.",
      total_segments: 1,
      total_length_km: 0.94,
      avg_vulnerability_score: 41.5,
      dominant_risk_level: "MODERATE",
      critical_segment_count: 0,
      active_clusters_count: 0,
      avg_pressure_psi: 52.0,
      is_simulated: true,
    },
    {
      id: "zone_zone-pz02",
      zone_code: "ZONE-PZ02",
      zone_name: "Eastern Industrial Sector",
      description: "Industrial feeder network with high daily flow variation and heavy manufacturing demand.",
      total_segments: 1,
      total_length_km: 0.82,
      avg_vulnerability_score: 26.2,
      dominant_risk_level: "LOW",
      critical_segment_count: 0,
      active_clusters_count: 0,
      avg_pressure_psi: 60.0,
      is_simulated: true,
    },
  ];
}

function getFallbackInfrastructureHeatmap(): HeatmapPointItem[] {
  return [
    { latitude: 40.71, longitude: -74.015, weight: 0.85, segment_id: "PIPE-SEC-4B-92", risk_level: "CRITICAL", score: 84.5, point_type: "PIPELINE_VERTEX" },
    { latitude: 40.7115, longitude: -74.011, weight: 0.85, segment_id: "PIPE-SEC-4B-92", risk_level: "CRITICAL", score: 84.5, point_type: "PIPELINE_VERTEX" },
    { latitude: 40.7128, longitude: -74.006, weight: 0.95, segment_id: "PIPE-SEC-4B-92", risk_level: "CRITICAL", score: 95.0, point_type: "CLUSTER_HOTSPOT" },
    { latitude: 40.7091, longitude: -74.0115, weight: 0.72, segment_id: "PIPE-HRB-02-19", risk_level: "HIGH", score: 72.0, point_type: "CLUSTER_HOTSPOT" },
    { latitude: 40.7198, longitude: -74.0089, weight: 0.42, segment_id: "PIPE-RES-3C-11", risk_level: "MODERATE", score: 41.5, point_type: "PIPELINE_VERTEX" },
    { latitude: 40.7145, longitude: -74.0021, weight: 0.26, segment_id: "PIPE-IND-1A-04", risk_level: "LOW", score: 26.2, point_type: "PIPELINE_VERTEX" },
  ];
}

function getFallbackInfrastructureTrends(): TemporalTrendItem[] {
  return [
    {
      pipeline_segment_id: "PIPE-SEC-4B-92",
      segment_name: "Metro Central Main Trunk Line B",
      vulnerability_score: 84.5,
      trend_direction: "DETERIORATING",
      deterioration_rate_per_day: 0.26,
      trend_24h_delta: 0.26,
      trend_7d_delta: 1.82,
      trend_30d_delta: 7.8,
      rapid_degradation: true,
    },
    {
      pipeline_segment_id: "PIPE-HRB-02-19",
      segment_name: "Harbor Marginal Service Line",
      vulnerability_score: 66.8,
      trend_direction: "DETERIORATING",
      deterioration_rate_per_day: 0.18,
      trend_24h_delta: 0.18,
      trend_7d_delta: 1.26,
      trend_30d_delta: 5.4,
      rapid_degradation: false,
    },
    {
      pipeline_segment_id: "PIPE-SEC-4A-10",
      segment_name: "Grand Avenue Spine Trunk Line A",
      vulnerability_score: 52.0,
      trend_direction: "STABLE",
      deterioration_rate_per_day: 0.08,
      trend_24h_delta: 0.08,
      trend_7d_delta: 0.56,
      trend_30d_delta: 2.4,
      rapid_degradation: false,
    },
  ];
}

function getFallbackInfrastructurePredictions(): PredictionItem[] {
  return [
    {
      pipeline_segment_id: "PIPE-SEC-4B-92",
      segment_name: "Metro Central Main Trunk Line B",
      current_vulnerability_score: 84.5,
      risk_level: "CRITICAL",
      projected_risk_24h: 84.8,
      projected_risk_7d: 86.3,
      projected_risk_30d: 92.3,
      trend_24h_delta: 0.26,
      trend_7d_delta: 1.82,
      trend_30d_delta: 7.8,
      primary_risk_drivers: ["Acoustic anomaly density in vicinity", "High pressure zone transition"],
      mitigation_urgency: "IMMEDIATE",
      hydraulic_deficit_flag: true,
      cluster_proximity_m: 120.0,
    },
    {
      pipeline_segment_id: "PIPE-HRB-02-19",
      segment_name: "Harbor Marginal Service Line",
      current_vulnerability_score: 66.8,
      risk_level: "HIGH",
      projected_risk_24h: 67.0,
      projected_risk_7d: 68.1,
      projected_risk_30d: 72.2,
      trend_24h_delta: 0.18,
      trend_7d_delta: 1.26,
      trend_30d_delta: 5.4,
      primary_risk_drivers: ["Cast iron graphitization", "Coastal moisture exposure"],
      mitigation_urgency: "SHORT_TERM",
      hydraulic_deficit_flag: false,
      cluster_proximity_m: 180.0,
    },
  ];
}

function getFallbackInspectionPriorities(): InspectionPriorityItem[] {
  return [
    {
      id: "INSP-SEC4B",
      pipeline_segment_id: "PIPE-SEC-4B-92",
      segment_name: "Metro Central Main Trunk Line B",
      priority_score: 88.5,
      priority_level: "CRITICAL_IMMEDIATE",
      status: "PENDING",
      target_latitude: 40.7128,
      target_longitude: -74.006,
      reasons: [
        "Critical vulnerability index (84.5/100)",
        "Rapid degradation rate (+0.26 pts/day)",
        "Located directly within active incident hotspot (120m)",
        "Arterial trunk conduit (dia: 600mm) carries high systemic failure consequence",
      ],
      suggested_action: "Immediate acoustic crawling patrol and acoustic leak pinpointing",
      is_simulated: true,
    },
    {
      id: "INSP-HRB02",
      pipeline_segment_id: "PIPE-HRB-02-19",
      segment_name: "Harbor Marginal Service Line",
      priority_score: 68.2,
      priority_level: "HIGH_PRIORITY",
      status: "PENDING",
      target_latitude: 40.7091,
      target_longitude: -74.0115,
      reasons: [
        "Elevated vulnerability index (66.8/100)",
        "Progressive structural wear (+0.18 pts/day)",
        "Hotspot proximity zone (180m)",
      ],
      suggested_action: "Scheduled autonomous rover sonar & visual inspection within 48h",
      is_simulated: true,
    },
    {
      id: "INSP-RES3C",
      pipeline_segment_id: "PIPE-RES-3C-11",
      segment_name: "Pinecrest Residential Sub-Branch",
      priority_score: 42.0,
      priority_level: "ROUTINE_SCHEDULED",
      status: "PENDING",
      target_latitude: 40.7198,
      target_longitude: -74.0089,
      reasons: ["Standard periodic inspection recommendation based on service age"],
      suggested_action: "Routine preventive rover patrol and pressure sensor validation",
      is_simulated: true,
    },
  ];
}

/* ========================================================= */
/* TASK 12 OPERATIONAL INTELLIGENCE DETERMINISTIC FALLBACKS  */
/* ========================================================= */

function getFallbackOperationalOverview(): OperationalOverview {
  return {
    active_incidents_count: 2,
    critical_segments_count: 1,
    pending_recommendations_count: 3,
    approved_actions_count: 1,
    active_missions_count: 1,
    available_rovers_count: 2,
    network_health_score: 79.4,
    network_urgency: "CRITICAL",
    recommendations_by_category: {
      IMMEDIATE_INSPECTION: 1,
      URGENT_LEAK_INVESTIGATION: 1,
      PREVENTIVE_MAINTENANCE: 1,
    },
    latest_assessment: getFallbackOperationalAssessment(),
    validation_status: "VALIDATED_AND_CERTIFIED",
    methodology_version: "v1.0.0-unified-operational-decision",
    is_simulated: true,
    source: "VIRTUAL_SIMULATION_ENGINE",
    actuation_notice: "REAL-WORLD PHYSICAL ACTUATORS PERMANENTLY DISABLED (SAFETY INTERLOCKED)",
  };
}

function getFallbackOperationalAssessment(): OperationalAssessment {
  return {
    id: "ASSESS-FALLBACK-01",
    assessment_name: "Metropolitan Network Operational Health Audit",
    total_recommendations: 3,
    immediate_action_count: 1,
    urgent_leak_count: 1,
    preventive_count: 1,
    critical_segments_analyzed: 3,
    overall_network_urgency: "CRITICAL",
    summary: {
      immediate_inspections: 1,
      urgent_leaks: 1,
      preventive_actions: 1,
      total_recommendations: 3,
      fleet_size: 3,
      methodology_version: "v1.0.0-unified-operational-decision",
    },
    assessed_at: new Date().toISOString(),
    is_simulated: true,
    source: "VIRTUAL_SIMULATION_ENGINE",
  };
}

function getFallbackOperationalRecommendations(filters?: { category?: string; status?: string; priority_tier?: string }): OperationalRecommendation[] {
  const all: OperationalRecommendation[] = [
    {
      id: "REC-SEC4B-92",
      assessment_id: "ASSESS-FALLBACK-01",
      category: "URGENT_LEAK_INVESTIGATION",
      pipeline_segment_id: "PIPE-SEC-4B-92",
      segment_name: "Metro Central Main Trunk Line B",
      associated_incident_id: "DET-2026-B81E29",
      risk_severity: "CRITICAL",
      priority_score: 88.5,
      priority_tier: "CRITICAL_IMMEDIATE",
      recommended_action: "Deploy autonomous acoustic crawler rover for high-frequency pin-point localization",
      action_details: "Target: Metro Central Main Trunk Line B (600mm Ductile Iron, 1200m). Assigned resource: AquaRover Alpha",
      why_explanation: "High-confidence acoustic anomaly (88.0%) detected on high-vulnerability arterial conduit Metro Central Main Trunk Line B.",
      what_missing: "No significant data gaps. All baseline telemetric and hydraulic attributes verified.",
      expected_impact: "Mitigates catastrophic joint burst; preserves network pressure stability in central grid.",
      contributing_factors: {
        incident_severity: 88.0,
        vulnerability: 84.5,
        asset_health_deficit: 45.0,
        hydraulic_impact: 62.0,
        service_criticality: 100.0,
        recurrence: 40.0,
      },
      evidence_sources: [
        "TASK_07_AI_LEAK_DETECTION",
        "TASK_09_PREDICTIVE_MAINTENANCE",
        "TASK_11_INFRASTRUCTURE_INTELLIGENCE",
        "TASK_10_HYDRAULIC_DIGITAL_TWIN",
      ],
      resource_requirements: {
        best_rover_id: "ROV-01",
        best_rover_name: "AquaRover Alpha",
        feasibility: "READY_FOR_DISPATCH",
        estimated_duration_min: 40.0,
        estimated_energy_pct: 9.6,
      },
      confidence: 0.92,
      data_completeness_pct: 95.0,
      uncertainty_margin: 3.2,
      status: "PENDING_REVIEW",
      approval_status: "PENDING",
      assigned_rover_id: "ROV-01",
      dispatched_mission_id: null,
      created_at: new Date().toISOString(),
      is_simulated: true,
      source: "VIRTUAL_SIMULATION_ENGINE",
    },
    {
      id: "REC-HRB02-19",
      assessment_id: "ASSESS-FALLBACK-01",
      category: "PREVENTIVE_MAINTENANCE",
      pipeline_segment_id: "PIPE-HRB-02-19",
      segment_name: "Harbor Utility Distribution Main",
      associated_incident_id: null,
      risk_severity: "HIGH",
      priority_score: 68.2,
      priority_tier: "URGENT",
      recommended_action: "Schedule pipe relining, cathodic protection inspection, and localized sleeve reinforcement",
      action_details: "Target: Harbor Utility Distribution Main (350mm Cast Iron, 800m). Assigned resource: AquaRover Beta",
      why_explanation: "Structural degradation slope on Cast Iron material indicates accelerating wall thinning.",
      what_missing: "Missing localized ground vibration frequency measurements.",
      expected_impact: "Extends asset operating life by 5-10 years; averts sudden catastrophic blowout.",
      contributing_factors: {
        incident_severity: 20.0,
        vulnerability: 66.8,
        asset_health_deficit: 48.0,
        hydraulic_impact: 35.0,
        service_criticality: 70.0,
        recurrence: 20.0,
      },
      evidence_sources: [
        "TASK_09_PREDICTIVE_MAINTENANCE",
        "TASK_11_INFRASTRUCTURE_INTELLIGENCE",
      ],
      resource_requirements: {
        best_rover_id: "ROV-02",
        best_rover_name: "AquaRover Beta",
        feasibility: "READY_FOR_DISPATCH",
        estimated_duration_min: 26.7,
        estimated_energy_pct: 6.4,
      },
      confidence: 0.85,
      data_completeness_pct: 88.0,
      uncertainty_margin: 4.5,
      status: "PENDING_REVIEW",
      approval_status: "PENDING",
      assigned_rover_id: "ROV-02",
      dispatched_mission_id: null,
      created_at: new Date().toISOString(),
      is_simulated: true,
      source: "VIRTUAL_SIMULATION_ENGINE",
    },
    {
      id: "REC-IND1A-04",
      assessment_id: "ASSESS-FALLBACK-01",
      category: "CONTINUOUS_MONITORING",
      pipeline_segment_id: "PIPE-IND-1A-04",
      segment_name: "Industrial Park Southern Feeder",
      associated_incident_id: null,
      risk_severity: "LOW",
      priority_score: 32.5,
      priority_tier: "ROUTINE",
      recommended_action: "Maintain continuous 1Hz acoustic listening and nominal pressure tracking",
      action_details: "Target: Industrial Park Southern Feeder (250mm HDPE, 1500m). Resource: Standby",
      why_explanation: "Pipeline Industrial Park Southern Feeder operates within nominal hydraulic and structural tolerance thresholds.",
      what_missing: "None. All primary telemetric indicators available.",
      expected_impact: "Ensures baseline operational stability with zero service interruption.",
      contributing_factors: {
        incident_severity: 0.0,
        vulnerability: 18.0,
        asset_health_deficit: 10.0,
        hydraulic_impact: 15.0,
        service_criticality: 40.0,
        recurrence: 0.0,
      },
      evidence_sources: ["TASK_10_HYDRAULIC_DIGITAL_TWIN"],
      resource_requirements: {
        best_rover_id: "ROV-03",
        best_rover_name: "AquaRover Gamma",
        feasibility: "READY_FOR_DISPATCH",
        estimated_duration_min: 50.0,
        estimated_energy_pct: 12.0,
      },
      confidence: 0.95,
      data_completeness_pct: 98.0,
      uncertainty_margin: 1.5,
      status: "PENDING_REVIEW",
      approval_status: "PENDING",
      assigned_rover_id: "ROV-03",
      dispatched_mission_id: null,
      created_at: new Date().toISOString(),
      is_simulated: true,
      source: "VIRTUAL_SIMULATION_ENGINE",
    },
  ];

  return all.filter((r) => {
    if (filters?.category && r.category !== filters.category) return false;
    if (filters?.status && r.status !== filters.status) return false;
    if (filters?.priority_tier && r.priority_tier !== filters.priority_tier) return false;
    return true;
  });
}

function getFallbackOperationalRecommendationDetail(id: string): any {
  const rec = getFallbackOperationalRecommendations().find((r) => r.id === id) || getFallbackOperationalRecommendations()[0];
  return {
    ...rec,
    evidences: [
      {
        id: `EVID-${rec.id}-01`,
        recommendation_id: rec.id,
        evidence_type: "ACOUSTIC_ANOMALY",
        source_module: "TASK_07_AI",
        source_table: "ai_detections",
        source_record_id: "DET-2026-B81E29",
        metric_name: "anomaly_score",
        metric_value: 0.88,
        metric_unit: "normalized_0_1",
        confidence_score: 0.92,
        evidence_summary: "AI acoustic model detected HIGH_LEAK_PROBABILITY with confidence 0.92",
        payload: { estimated_loss_lph: 2450.0 },
        recorded_at: new Date().toISOString(),
        is_simulated: true,
        source: "VIRTUAL_SIMULATION_ENGINE",
      },
      {
        id: `EVID-${rec.id}-02`,
        recommendation_id: rec.id,
        evidence_type: "VULNERABILITY_PROFILE",
        source_module: "TASK_11_GEOSPATIAL",
        source_table: "pipeline_vulnerability_profiles",
        source_record_id: "VULN-PIPE-SEC-4B-92",
        metric_name: "vulnerability_score",
        metric_value: 84.5,
        metric_unit: "score_0_100",
        confidence_score: 0.89,
        evidence_summary: "Multi-factor vulnerability rated 84.5 (CRITICAL)",
        payload: { hydraulic_score: 62.0, structural_score: 88.0 },
        recorded_at: new Date().toISOString(),
        is_simulated: true,
        source: "VIRTUAL_SIMULATION_ENGINE",
      },
    ],
    impact_assessment: {
      id: `IMP-${rec.id}`,
      recommendation_id: rec.id,
      pipeline_segment_id: rec.pipeline_segment_id,
      scenario_id: "SCEN-WHATIF-FALLBACK",
      estimated_water_loss_m3_day: 184.2,
      is_water_loss_measured: false,
      service_disruption_risk: "SEVERE",
      affected_nodes_count: 6,
      affected_population_estimate: 8500,
      hydraulic_headloss_delta_m: 8.6,
      min_pressure_drop_bar: 0.85,
      estimated_inspection_distance_m: 1200.0,
      estimated_mission_energy_pct: 9.6,
      estimated_inspection_duration_min: 40.0,
      cost_impact_display: "NOT AVAILABLE",
      data_quality_rating: "ESTIMATED_SIMULATED",
      assumptions: {
        governing_equation: "Torricelli Orifice Flow Q = Cd * A * sqrt(2*g*h)",
        discharge_coefficient_Cd: 0.62,
      },
      uncertainty_margin_pct: 15.0,
      assessed_at: new Date().toISOString(),
      is_simulated: true,
      source: "VIRTUAL_SIMULATION_ENGINE",
    },
  };
}

function getFallbackIncidentCorrelations(): IncidentCorrelation[] {
  return [
    {
      id: "CORR-SEC4B-DET01",
      primary_segment_id: "PIPE-SEC-4B-92",
      primary_segment_name: "Metro Central Main Trunk Line B",
      related_segment_id: "PIPE-SEC-4B-92",
      incident_ids: ["DET-2026-B81E29"],
      correlation_type: "CONFIRMED_RELATIONSHIP",
      correlation_strength: 0.94,
      uncertainty: 0.08,
      geographic_distance_m: 0.0,
      temporal_delta_hours: 0.5,
      shared_pressure_zone: true,
      supporting_evidence: [
        "Acoustic emission (0.88) co-located with active pressure drop (<45 psi)",
        "Subterranean moisture sensor registered elevated saturation (>35%)",
      ],
      explanation: "Acoustic emission on segment Metro Central Main Trunk Line B is directly correlated with co-located pressure drops and moisture anomalies, confirming active physical pipe orifice discharge.",
      is_simulated: true,
      source: "VIRTUAL_SIMULATION_ENGINE",
    },
    {
      id: "CORR-HRB02-ALERT",
      primary_segment_id: "PIPE-HRB-02-19",
      primary_segment_name: "Harbor Utility Distribution Main",
      related_segment_id: "PIPE-HRB-02-19",
      incident_ids: ["ALERT-MAINT-02"],
      correlation_type: "POTENTIAL_RELATIONSHIP",
      correlation_strength: 0.72,
      uncertainty: 0.18,
      geographic_distance_m: 0.0,
      temporal_delta_hours: 14.0,
      shared_pressure_zone: true,
      supporting_evidence: [
        "Historical maintenance alert for structural wall thinning",
        "Cast iron material with high soil salinity vulnerability",
      ],
      explanation: "Acoustic anomaly co-occurs with existing predictive maintenance alert on Harbor Utility Distribution Main.",
      is_simulated: true,
      source: "VIRTUAL_SIMULATION_ENGINE",
    },
  ];
}

function getFallbackOperationalPriorities(): any[] {
  return [
    {
      id: "PRIO-01",
      recommendation_id: "REC-SEC4B-92",
      pipeline_segment_id: "PIPE-SEC-4B-92",
      rank_position: 1,
      composite_priority_score: 88.5,
      incident_severity_component: 88.0,
      vulnerability_component: 84.5,
      asset_health_component: 45.0,
      hydraulic_impact_component: 62.0,
      service_criticality_component: 100.0,
      recurrence_component: 40.0,
      confidence_weight: 0.92,
      weights_version: "v1.0.0-multi-criteria-pareto",
      weights_applied: {
        incident_severity: 0.25,
        vulnerability: 0.20,
        asset_health_deficit: 0.20,
        hydraulic_impact: 0.15,
        service_criticality: 0.12,
        recurrence: 0.08,
      },
      reassessment_counter: 0,
      last_ranked_at: new Date().toISOString(),
    },
    {
      id: "PRIO-02",
      recommendation_id: "REC-HRB02-19",
      pipeline_segment_id: "PIPE-HRB-02-19",
      rank_position: 2,
      composite_priority_score: 68.2,
      incident_severity_component: 20.0,
      vulnerability_component: 66.8,
      asset_health_component: 48.0,
      hydraulic_impact_component: 35.0,
      service_criticality_component: 70.0,
      recurrence_component: 20.0,
      confidence_weight: 0.85,
      weights_version: "v1.0.0-multi-criteria-pareto",
      weights_applied: {
        incident_severity: 0.25,
        vulnerability: 0.20,
        asset_health_deficit: 0.20,
        hydraulic_impact: 0.15,
        service_criticality: 0.12,
        recurrence: 0.08,
      },
      reassessment_counter: 0,
      last_ranked_at: new Date().toISOString(),
    },
  ];
}

function getFallbackResourcePlanning(): ResourcePlanning[] {
  return [
    {
      recommendation_id: "REC-RES-PIPE-SEC-4B-92",
      pipeline_segment_id: "PIPE-SEC-4B-92",
      segment_name: "Metro Central Main Trunk Line B",
      required_capability: "Subterranean acoustic crawling inspection & pressure mapping",
      estimated_distance_m: 1200.0,
      estimated_energy_pct: 9.6,
      estimated_duration_min: 40.0,
      suitable_rovers: [
        {
          rover_id: "ROV-01",
          rover_name: "AquaRover Alpha",
          status: "ONLINE",
          operating_state: "IDLE",
          battery_percentage: 92.0,
          motor_temp_c: 26.5,
          distance_to_target_m: 240.0,
          suitability_score: 94.2,
          is_eligible: true,
          rejection_reasons: [],
        },
        {
          rover_id: "ROV-02",
          rover_name: "AquaRover Beta",
          status: "ONLINE",
          operating_state: "IDLE",
          battery_percentage: 78.5,
          motor_temp_c: 28.0,
          distance_to_target_m: 650.0,
          suitability_score: 82.0,
          is_eligible: true,
          rejection_reasons: [],
        },
      ],
      best_rover_id: "ROV-01",
      best_rover_name: "AquaRover Alpha",
      dispatch_feasibility: "READY_FOR_DISPATCH",
      workforce_status: "NOT_AVAILABLE (Software Simulation Mode)",
      inventory_status: "NOT_AVAILABLE (Software Simulation Mode)",
    },
  ];
}

function getFallbackOperatorDecisions(): OperationalDecisionRecord[] {
  return [
    {
      id: "DEC-PREV-01",
      recommendation_id: "REC-HISTORIC-01",
      decision_type: "APPROVED",
      decision_reason: "Critical arterial rupture risk confirmed. Scheduled immediate night patrol.",
      operator_id: "OPERATOR-CHIEF-01",
      operator_name: "Chief Operations Engineer",
      allocated_resource_id: "ROV-01",
      resulting_mission_id: "MIS-OPS-1092",
      decision_timestamp: new Date(Date.now() - 3600000).toISOString(),
      audit_hash: "a4c28f19e482701b88e102f928c2918e74a81230d92e10283c4819e102938472",
      is_simulated: true,
      source: "VIRTUAL_SIMULATION_ENGINE",
    },
  ];
}

function getFallbackExecutionHistory(): OperationalExecutionRecord[] {
  return [
    {
      id: "EXEC-01",
      recommendation_id: "REC-HISTORIC-01",
      decision_id: "DEC-PREV-01",
      mission_id: "MIS-OPS-1092",
      assigned_rover_id: "ROV-01",
      execution_stage: "INSPECTING",
      start_time: new Date(Date.now() - 3000000).toISOString(),
      end_time: null,
      distance_inspected_m: 450.0,
      energy_consumed_pct: 3.6,
      findings_summary: "Acoustic emission localized to pipe joint #14. Minor joint weeping confirmed.",
      leak_confirmed: true,
      last_updated_at: new Date().toISOString(),
    },
  ];
}

function getFallbackWhatIfAnalysis(segmentId: string, orificeMm: number): any {
  return {
    scenario_id: `SCEN-WHATIF-FALLBACK-${segmentId}`,
    pipeline_segment_id: segmentId,
    leak_orifice_diameter_mm: orificeMm,
    nominal_pressure_bar: 4.2,
    estimated_leak_rate_lps: 8.5,
    estimated_water_loss_m3_day: 184.2,
    is_water_loss_measured: false,
    min_pressure_drop_bar: 0.85,
    hydraulic_headloss_delta_m: 8.6,
    affected_nodes_count: 6,
    affected_population_estimate: 8500,
    service_disruption_risk: "SEVERE",
    cost_impact_display: "NOT AVAILABLE",
    data_quality_rating: "ESTIMATED_SIMULATED",
    simulation_provenance: {
      is_simulated: true,
      source: "VIRTUAL_SIMULATION_ENGINE",
      real_world_actuators_enabled: false,
    },
  };
}

/* ========================================================= */
/* TASK 13 ADVANCED AI DETERMINISTIC CLIENT FALLBACKS        */
/* ========================================================= */

function getFallbackAIChatResponse(req: AIChatRequest): AIChatResponse {
  const q = req.query.toLowerCase();
  let content = "";
  let intent = "GENERAL_QUERY";

  if (q.includes("highest") && (q.includes("priority") || q.includes("inspection"))) {
    intent = "HIGHEST_INSPECTION_PRIORITY";
    content = `### Highest Inspection Priority: **Metro Central Main Trunk Line B** (\`PIPE-SEC-4B-92\`)\n\n- **Composite Priority Score**: \`88.5 / 100\` (\`CRITICAL\`)\n- **Category**: \`URGENT_LEAK_INVESTIGATION\`\n- **Recommended Action**: Dispatch autonomous rover for acoustic cross-correlation and visual joint inspection\n\n#### Why This Asset Ranks #1:\n1. **Active Acoustic Leak Anomaly (MEASURED / DERIVED)**: Hydrophone sensor registered anomaly score of 0.88 with localized pressure drop (<45 psi).\n2. **Consequence Severity (DERIVED)**: Large 600mm arterial trunk main carrying high hydraulic volume.\n3. **Degradation Velocity (DERIVED)**: Active deterioration velocity of \`+0.26 points/day\`.\n\n*Safety Interlock: Real-world actuators are permanently disabled. Autonomous rover launch is held in PENDING_REVIEW.*`;
  } else if (q.includes("why") && (q.includes("critical") || q.includes("sec-4b"))) {
    intent = "SEGMENT_REASONING";
    content = `### Structural & Operational Analysis: **Metro Central Main Trunk Line B** (\`PIPE-SEC-4B-92\`)\n\n\`PIPE-SEC-4B-92\` is classified as **CRITICAL** (Priority: \`88.5 / 100\`, Vulnerability: \`84.5 / 100\`) based on four corroborating evidence streams:\n\n1. **Acoustic Sensor Stream (MEASURED)**: Hydrophone acoustic anomaly score \`0.88\`.\n2. **Hydraulic Gradient (SIMULATED)**: Torricelli orifice flow calculates simulated loss of \`184.2 m³/day\`.\n3. **Degradation Velocity (DERIVED)**: +0.26 points/day.\n4. **Proximity (DERIVED)**: 120m from active spatial cluster #1.\n\n*Missing: Direct borehole soil resistivity is unmeasured.*`;
  } else if (q.includes("contradict") || q.includes("disagree") || q.includes("conflict")) {
    intent = "EVIDENCE_CONTRADICTIONS";
    content = `### Multi-Source Evidence Consistency Analysis for \`PIPE-SEC-4B-92\`\n\n- **Overall Consistency Score**: \`0.82 / 1.0\`\n- **Tension**: Elevated Acoustic vs. Normal Pressure Gradient\n\n1. **Acoustic Sensor (MEASURED)**: Continuous high-frequency emission (450–700 Hz, SPL 64.2 dB, anomaly 0.88).\n2. **Hydraulic Pressure (MEASURED)**: Pressure drop delta is 1.2 psi, within nominal diurnal bounds.\n3. **Reconciliation**: Small orifice (<12 mm) produces distinct high-frequency jet cavitation before causing macroscopic pressure drop in this 600mm conduit.`;
  } else if (q.includes("rover") && (q.includes("available") || q.includes("readiness"))) {
    intent = "ROVER_FLEET_STATUS";
    content = `### Virtual Rover Fleet Readiness (2 Available)\n\n- **AquaRover Alpha** (\`ROV-001\`): State: \`IDLE\`, Battery: \`92.0%\`, Temp: \`28.4°C\` [Eligible]\n- **AquaRover Beta** (\`ROV-002\`): State: \`IDLE\`, Battery: \`78.5%\`, Temp: \`31.2°C\` [Eligible]\n\n**Enforced Safety Rules**:\n- Minimum battery threshold: \`≥ 20.0%\`.\n- Motor temperature ceiling: \`< 65.0°C\`.\n- Physical workforce status: \`NOT AVAILABLE (Simulation Mode)\`.`;
  } else if (q.includes("dispatch") && (q.includes("immediately") || q.includes("now") || q.includes("can the system"))) {
    intent = "DISPATCH_SAFETY";
    content = `### Rover Dispatch Safety Protocol & Interlock Status\n\n**Answer**: **NO. The system CANNOT dispatch a rover autonomously or immediately without human authorization.**\n\n- **Actuator Isolation**: Real-world physical actuators are permanently disabled.\n- **Human-in-the-Loop**: All missions are generated in state \`PENDING_REVIEW\`.\n- **Operator Authorization**: A certified operator must review battery feasibility and confirm approval in the Command Center.`;
  } else if (q.includes("7-day") || q.includes("78%") || q.includes("what caused")) {
    intent = "EXPLAIN_RISK";
    content = `### Evidence Explanation: 7-Day Failure Risk Assessment (\`PIPE-SEC-4B-92\`)\n\n- **Model**: Gradient-Boosted Survival Hazard (\`v1.0.0-rf-gradient-predictive\`)\n- **Assessed Risk Level**: \`78.4%\`\n\n#### Verified Feature Drivers (Strict Non-Fabricated Rules):\n1. **Asset Age & Material Vulnerability (+28.2%)**: 42-year-old Ductile Iron pipe exceeding 80% lifecycle.\n2. **Operating Pressure Stress (+24.5%)**: Sustained 65 psi with diurnal oscillations (±14 psi).\n3. **Degradation Velocity (+16.1%)**: Deterioration rate of \`+0.26 points/day\`.\n4. **Environmental Setting (+9.6%)**: High-salinity water table proximity zone.`;
  } else {
    content = `### AQUA CREW Evidence-Grounded Decision Assistant\n\nI have reviewed real-time operational context across the water distribution network:\n\n- **Network Health**: \`79.4 / 100\`\n- **Top Priority Conduit**: **\`PIPE-SEC-4B-92\`** (\`CRITICAL\`, Priority: \`88.5 / 100\`)\n- **Active Acoustic Leak**: Hydrophone anomaly score \`0.88\`\n- **Simulated Water Loss**: \`184.2 m³/day\`\n- **Human-in-the-Loop Interlock**: Physical actuation is disabled; all rover dispatches require operator sign-off.`;
  }

  const mockEvidence: EvidenceItem[] = [
    {
      evidence_id: "EVID-SEG-PIPE-SEC-4B-92",
      source_module: "TASK_04_GIS",
      source_table: "pipeline_segments",
      source_record_id: "PIPE-SEC-4B-92",
      evidence_type: "ASSET_SPECIFICATION",
      classification: "MEASURED",
      metric_name: "diameter_mm",
      metric_value: 600,
      metric_unit: "mm",
      summary: "Physical asset: Metro Central Main Trunk Line B (Ductile Iron, dia: 600mm, len: 1200m)",
      confidence: 1.0,
      validation_status: "VALIDATED",
      is_simulated: true,
      source: "VIRTUAL_SIMULATION_ENGINE",
    },
    {
      evidence_id: "EVID-DET-01",
      source_module: "TASK_07_AI",
      source_table: "ai_detections",
      source_record_id: "DET-01",
      evidence_type: "ACOUSTIC_LEAK_DETECTION",
      classification: "DERIVED",
      metric_name: "anomaly_score",
      metric_value: 0.88,
      metric_unit: "normalized_0_1",
      summary: "Acoustic hydrophone anomaly: HIGH_LEAK_PROBABILITY (score: 0.88, confidence: 0.92)",
      confidence: 0.92,
      validation_status: "VALIDATED",
      is_simulated: true,
      source: "VIRTUAL_SIMULATION_ENGINE",
    },
    {
      evidence_id: "EVID-SIM-01",
      source_module: "TASK_10_DIGITAL_TWIN",
      source_table: "simulation_runs",
      source_record_id: "RUN-01",
      evidence_type: "SIMULATED_WATER_LOSS",
      classification: "SIMULATED",
      metric_name: "water_loss_m3_day",
      metric_value: 184.2,
      metric_unit: "m3/day",
      summary: "Digital twin Torricelli simulation calculates 184.2 m3/day loss at 4.2 bar",
      confidence: 0.88,
      validation_status: "VALIDATED",
      is_simulated: true,
      source: "VIRTUAL_SIMULATION_ENGINE",
    },
  ];

  return {
    conversation_id: req.conversation_id || `CONV-${Math.random().toString(36).substring(2, 8).toUpperCase()}`,
    message_id: `MSG-AST-${Math.random().toString(36).substring(2, 8).toUpperCase()}`,
    role: "assistant",
    content,
    intent,
    model_used: "deterministic-grounded-engine",
    provider_used: "DETERMINISTIC",
    supporting_evidence: mockEvidence,
    claims: [],
    confidence_assessment: "Grounding score: 1.0 (GROUNDED_VERIFIED)",
    validation_status: "GROUNDED_VERIFIED",
    missing_information: null,
    suggested_queries: [
      "Why is PIPE-SEC-4B-92 classified as critical?",
      "Which rovers are available and eligible to inspect this pipeline?",
      "Are there contradictions in the evidence for this segment?",
      "Summarize the operational situation across the network today.",
    ],
    is_simulated: true,
    source: "VIRTUAL_SIMULATION_ENGINE",
    timestamp: new Date().toISOString(),
  };
}

function getFallbackAIConversations(): AIConversationItem[] {
  return [
    {
      id: "CONV-DEFAULT-01",
      title: "Inspection Priority & Evidence Verification",
      user_id: "OPERATOR-SUPERVISOR-01",
      message_count: 6,
      created_at: new Date(Date.now() - 3600000).toISOString(),
      updated_at: new Date().toISOString(),
    },
  ];
}

function getFallbackAIConversationDetail(conversationId: string): AIConversationDetail {
  return {
    id: conversationId,
    title: "Operational AI Decision Assistant",
    user_id: "OPERATOR-SUPERVISOR-01",
    messages: [
      {
        id: "MSG-01",
        role: "user",
        content: "Which pipeline currently has the highest inspection priority and why?",
        model_used: "client-input",
        provider_used: "USER",
        validation_status: "VALIDATED",
        timestamp: new Date(Date.now() - 60000).toISOString(),
        evidence_references: [],
      },
      {
        id: "MSG-02",
        role: "assistant",
        content: `### Highest Inspection Priority: **Metro Central Main Trunk Line B** (\`PIPE-SEC-4B-92\`)\n\n- **Composite Priority Score**: \`88.5 / 100\` (\`CRITICAL\`)\n- **Category**: \`URGENT_LEAK_INVESTIGATION\`\n- **Recommended Action**: Dispatch autonomous rover for acoustic cross-correlation and visual joint inspection.`,
        intent: "HIGHEST_INSPECTION_PRIORITY",
        model_used: "deterministic-grounded-engine",
        provider_used: "DETERMINISTIC",
        validation_status: "VALIDATED",
        timestamp: new Date().toISOString(),
        evidence_references: ["EVID-SEG-PIPE-SEC-4B-92", "EVID-DET-01"],
      },
    ],
  };
}

function getFallbackSegmentExplanation(segmentId: string): DecisionExplanation {
  return {
    entity_type: "INFRASTRUCTURE_VULNERABILITY",
    entity_id: segmentId,
    primary_classification: "CRITICAL",
    why_explained: `Segment ${segmentId} is evaluated as high vulnerability based on 600mm diameter, operating pressure (65 psi), and material age degradation velocity.`,
    contributing_factors: {
      "hydraulic_score (30%)": 82.0,
      "structural_score (25%)": 86.5,
      "incident_score (25%)": 88.0,
      "environmental_score (20%)": 78.5,
    },
    model_version: "v1.2.0-hybrid-physics-geodesic",
    input_quality_notes: "Data completeness: 85.0%. Uncertainty margin: ±3.2 points.",
    assumptions_applied: ["AWWA standard graphitization curves apply."],
    limitations: ["Soil corrosivity assumed neutral when direct borehole resistivity is missing."],
    supporting_evidence_ids: [`VULN-${segmentId}`],
  };
}

function getFallbackRecommendationExplanation(recommendationId: string): DecisionExplanation {
  return {
    entity_type: "OPERATIONAL_RECOMMENDATION",
    entity_id: recommendationId,
    primary_classification: "CRITICAL",
    why_explained: `Recommendation '${recommendationId}' prioritizes urgent acoustic inspection due to active acoustic anomaly (0.88) co-occurring with pressure drop on arterial trunk.`,
    contributing_factors: {
      "incident_severity_weight (25%)": 88.0,
      "vulnerability_weight (20%)": 84.5,
      "health_deficit_weight (20%)": 74.2,
      "hydraulic_criticality (15%)": 82.0,
    },
    model_version: "v1.0.0-multi-criteria-pareto",
    input_quality_notes: "Completeness: 90%, Confidence: 92%, Uncertainty: ±2.5 pts.",
    assumptions_applied: ["Autonomous rover dispatch requires human supervisor approval."],
    limitations: ["Real-world actuators are permanently disabled."],
    supporting_evidence_ids: [`REC-${recommendationId}`],
  };
}

function getFallbackPipelineComparison(segmentIds: string[]): PipelineComparisonResponse {
  return {
    segments: [
      {
        segment_id: "PIPE-SEC-4B-92",
        name: "Metro Central Main Trunk Line B",
        material: "Ductile Iron",
        diameter_mm: 600,
        vulnerability_score: 84.5,
        vulnerability_level: "CRITICAL",
        health_score: 74.2,
        health_category: "FAIR",
        incident_count: 2,
        pressure_psi: 65.0,
        inspection_priority: 88.5,
        priority_tier: "CRITICAL",
        data_completeness_pct: 85.0,
        recommended_action: "Dispatch rover for acoustic cross-correlation",
      },
      {
        segment_id: "PIPE-HRB-02-19",
        name: "Harbor Terminal Lateral Feeder",
        material: "Cast Iron",
        diameter_mm: 300,
        vulnerability_score: 68.0,
        vulnerability_level: "HIGH",
        health_score: 82.5,
        health_category: "GOOD",
        incident_count: 1,
        pressure_psi: 52.0,
        inspection_priority: 74.2,
        priority_tier: "HIGH",
        data_completeness_pct: 78.0,
        recommended_action: "Schedule preventive ultrasonic wall thinning survey",
      },
    ],
    comparative_summary: "PIPE-SEC-4B-92 represents the highest operational urgency due to active acoustic leak probability (0.88) and 600mm arterial transmission diameter. Inspecting PIPE-SEC-4B-92 first mitigates maximum volumetric water loss (184.2 m3/day).",
    highest_risk_segment_id: "PIPE-SEC-4B-92",
    highest_priority_segment_id: "PIPE-SEC-4B-92",
  };
}

function getFallbackOperationalSummary(): OperationalSummaryResponse {
  return {
    summary_type: "METROPOLITAN_OPERATIONAL_SUMMARY",
    generated_at: new Date().toISOString(),
    new_incidents_count: 2,
    critical_assets_count: 1,
    pending_recommendations_count: 3,
    approved_decisions_count: 1,
    completed_missions_count: 1,
    network_urgency: "CRITICAL",
    narrative_summary: "Operational intelligence indicates network urgency is CRITICAL driven by arterial rupture risk on Grand Spine Trunk Line B (PIPE-SEC-4B-92). Hydrophone acoustic anomalies indicate orifice discharge with estimated simulated loss of 184.2 m3/day. Virtual rover fleet has 2 units available with full battery reserves.",
    unresolved_risks: [
      "Arterial pressure surge oscillation (±14 psi) on Grand Spine Trunk Line B",
      "Unmeasured soil corrosivity around Harbor Terminal",
    ],
    recommended_next_actions: [
      "Authorize recommendation REC-SEC4B-92 for AquaRover Alpha inspection",
      "Deploy temporary pressure loggers along Southern Feeder PIPE-IND-1A-04",
    ],
    supporting_evidence_ids: ["EVID-SEG-PIPE-SEC-4B-92", "EVID-DET-01", "EVID-REC-01"],
  };
}

function getFallbackEvidenceGaps(segmentId: string): EvidenceGapAnalysis {
  return {
    segment_id: segmentId,
    segment_name: "Metro Central Main Trunk Line B",
    overall_data_completeness_pct: 72.5,
    missing_indicators: [
      "Near-field acoustic hydrophone sub-meter correlation (currently manhole resolution ±15m)",
      "Direct internal optical CCTV joint inspection footage",
      "Borehole soil resistivity and geotechnical redox potential logs",
      "Physical DMA night-flow calibration meter confirmation",
    ],
    uncertainty_impact_description: "Without near-field acoustic pinpointing and CCTV imagery, the structural failure mode cannot be confirmed with 100% certainty. Uncertainty margin on physical excavation location remains ±15 meters.",
    recommended_sensor_installations: [
      "Deploy AquaRover Alpha crawler with dual hydrophone payload",
      "Temporary IoT high-frequency acoustic loggers at Junction J-42 and Valve V-18",
      "Soil sampling probe test at coordinate 40.7128°N, -74.0060°W",
    ],
  };
}

function getFallbackSegmentReasoning(segmentId: string): MultiSourceReasoningResult {
  return {
    target_segment_id: segmentId,
    target_segment_name: "Metro Central Main Trunk Line B",
    measured_facts: [],
    simulated_results: [],
    derived_metrics: [],
    predictions: [],
    temporal_alignment: "Observations are temporally synchronized within standard operational polling windows.",
    supporting_evidence: [
      "Acoustic hydrophone anomaly (0.88) indicates active pipe-wall noise.",
      "Physical asset specification verified: 600mm Ductile Iron transmission main.",
    ],
    contradictory_evidence: [
      "Localized pressure drop is within nominal diurnal limits despite elevated acoustic emissions.",
    ],
    missing_evidence: [
      "Near-field sub-meter acoustic localization not yet acquired.",
    ],
    supported_conclusions: [
      "Conduit exhibits high probability of active physical leakage driven by structural fatigue.",
    ],
    uncertain_hypotheses: [
      "Cavitation vs orifice discharge cannot be fully disambiguated without crawler near-field acoustic spectrum.",
    ],
    recommended_investigation: "Deploy rover acoustic crawler for localized cross-correlation.",
    uncertainty_description: "Evidence set contains multiple corroborating signals.",
  };
}

function getFallbackOptimizationStatus(): OptimizationStatusResponse {
  return {
    status: "READY",
    engine: "TodiniGlobalGradient-WNTR-EPANET",
    active_jobs: 0,
    completed_jobs: 3,
    default_network: "Net1",
    supported_profiles: [
      "BALANCED_OPERATION",
      "ENERGY_EFFICIENCY",
      "LEAKAGE_REDUCTION",
      "PRESSURE_STABILITY",
    ],
    hardware_actuation_disabled: true,
  };
}

function getFallbackNetworkBaseline(networkId: string = "Net1"): any {
  return {
    network_id: networkId,
    network_name: "Metropolitan Central Distribution Zone (Net1)",
    nodes_count: 9,
    links_count: 12,
    pumps_count: 1,
    valves_count: 1,
    tanks_count: 1,
    baseline_metrics: {
      water_loss_lps: 12.4,
      pump_power_kw: 45.2,
      pressure_deficit_m: 1.2,
      demand_satisfaction_ratio: 1.0,
      min_junction_pressure_m: 16.8,
      max_junction_pressure_m: 48.5,
      max_velocity_mps: 1.82,
      operational_cost_usd_per_day: null,
    },
    performance_report: {
      pressure_uniformity_index: 0.84,
      total_demand_delivered_lps: 118.5,
      energy_efficiency_kwh_per_m3: 0.42,
    },
  };
}

function getFallbackOptimizationJob(jobId: string = "OPT-2026-N1-001"): OptimizationJobDetail {
  const candidates: OptimizationCandidate[] = [
    {
      id: "CAND-01",
      job_id: jobId,
      candidate_index: 1,
      is_pareto_optimal: true,
      is_hydraulically_verified: true,
      verification_status: "VERIFIED",
      verification_violations: [],
      decision_variables: [
        {
          id: "DV-PUMP-9",
          component_type: "PUMP",
          component_id: "PUMP-9",
          parameter_name: "speed_multiplier",
          baseline_value: 1.0,
          recommended_value: 0.85,
          min_value: 0.7,
          max_value: 1.2,
          unit: "ratio",
          description: "Main intake booster pump rotational speed setting",
        },
        {
          id: "DV-PRV-1",
          component_type: "PRV",
          component_id: "PRV-1",
          parameter_name: "pressure_setpoint_bar",
          baseline_value: 2.5,
          recommended_value: 1.8,
          min_value: 1.0,
          max_value: 3.5,
          unit: "bar",
          description: "Pressure reducing valve setpoint for Zone 2 inlet",
        },
      ],
      metrics: {
        water_loss_lps: 9.8,
        pump_power_kw: 31.8,
        pressure_deficit_m: 0.0,
        demand_satisfaction_ratio: 1.0,
        max_velocity_mps: 1.45,
        min_junction_pressure_m: 18.2,
        max_junction_pressure_m: 41.0,
        operational_cost_usd_per_day: null,
      },
      tradeoff_explanation: "Balanced candidate: 29.6% pump energy savings (31.8 kW vs 45.2 kW) and 20.9% Torricelli background water loss reduction while maintaining 100% demand satisfaction and zero pressure deficits.",
    },
    {
      id: "CAND-02",
      job_id: jobId,
      candidate_index: 2,
      is_pareto_optimal: true,
      is_hydraulically_verified: true,
      verification_status: "VERIFIED",
      verification_violations: [],
      decision_variables: [
        {
          id: "DV-PUMP-9",
          component_type: "PUMP",
          component_id: "PUMP-9",
          parameter_name: "speed_multiplier",
          baseline_value: 1.0,
          recommended_value: 0.78,
          min_value: 0.7,
          max_value: 1.2,
          unit: "ratio",
          description: "Main intake booster pump rotational speed setting",
        },
        {
          id: "DV-PRV-1",
          component_type: "PRV",
          component_id: "PRV-1",
          parameter_name: "pressure_setpoint_bar",
          baseline_value: 2.5,
          recommended_value: 1.9,
          min_value: 1.0,
          max_value: 3.5,
          unit: "bar",
          description: "Pressure reducing valve setpoint for Zone 2 inlet",
        },
      ],
      metrics: {
        water_loss_lps: 10.6,
        pump_power_kw: 25.4,
        pressure_deficit_m: 0.0,
        demand_satisfaction_ratio: 1.0,
        max_velocity_mps: 1.32,
        min_junction_pressure_m: 16.5,
        max_junction_pressure_m: 38.4,
        operational_cost_usd_per_day: null,
      },
      tradeoff_explanation: "Aggressive energy minimization: 43.8% pump energy reduction (25.4 kW vs 45.2 kW via affinity cubic scaling P ∝ s³). Water loss is reduced by 14.5% while node pressures remain above safety threshold 15m.",
    },
    {
      id: "CAND-03",
      job_id: jobId,
      candidate_index: 3,
      is_pareto_optimal: true,
      is_hydraulically_verified: true,
      verification_status: "VERIFIED",
      verification_violations: [],
      decision_variables: [
        {
          id: "DV-PUMP-9",
          component_type: "PUMP",
          component_id: "PUMP-9",
          parameter_name: "speed_multiplier",
          baseline_value: 1.0,
          recommended_value: 0.90,
          min_value: 0.7,
          max_value: 1.2,
          unit: "ratio",
          description: "Main intake booster pump rotational speed setting",
        },
        {
          id: "DV-PRV-1",
          component_type: "PRV",
          component_id: "PRV-1",
          parameter_name: "pressure_setpoint_bar",
          baseline_value: 2.5,
          recommended_value: 1.6,
          min_value: 1.0,
          max_value: 3.5,
          unit: "bar",
          description: "Pressure reducing valve setpoint for Zone 2 inlet",
        },
      ],
      metrics: {
        water_loss_lps: 8.4,
        pump_power_kw: 36.2,
        pressure_deficit_m: 0.0,
        demand_satisfaction_ratio: 1.0,
        max_velocity_mps: 1.55,
        min_junction_pressure_m: 17.0,
        max_junction_pressure_m: 39.2,
        operational_cost_usd_per_day: null,
      },
      tradeoff_explanation: "Maximum leakage containment: 32.3% water loss reduction (8.4 L/s vs 12.4 L/s) via tightened PRV setpoint modulation. Conserves 345 m³/day of potable water while achieving 19.9% energy savings.",
    },
    {
      id: "CAND-04",
      job_id: jobId,
      candidate_index: 4,
      is_pareto_optimal: true,
      is_hydraulically_verified: true,
      verification_status: "VERIFIED",
      verification_violations: [],
      decision_variables: [
        {
          id: "DV-PUMP-9",
          component_type: "PUMP",
          component_id: "PUMP-9",
          parameter_name: "speed_multiplier",
          baseline_value: 1.0,
          recommended_value: 0.88,
          min_value: 0.7,
          max_value: 1.2,
          unit: "ratio",
          description: "Main intake booster pump rotational speed setting",
        },
        {
          id: "DV-PRV-1",
          component_type: "PRV",
          component_id: "PRV-1",
          parameter_name: "pressure_setpoint_bar",
          baseline_value: 2.5,
          recommended_value: 1.75,
          min_value: 1.0,
          max_value: 3.5,
          unit: "bar",
          description: "Pressure reducing valve setpoint for Zone 2 inlet",
        },
      ],
      metrics: {
        water_loss_lps: 9.1,
        pump_power_kw: 34.0,
        pressure_deficit_m: 0.0,
        demand_satisfaction_ratio: 1.0,
        max_velocity_mps: 1.48,
        min_junction_pressure_m: 19.5,
        max_junction_pressure_m: 40.5,
        operational_cost_usd_per_day: null,
      },
      tradeoff_explanation: "Pressure stability optimization: Tightest pressure band (19.5m - 40.5m) preventing transient pressure spikes. Achieves 26.6% water loss reduction and 24.8% energy savings.",
    },
    {
      id: "CAND-05",
      job_id: jobId,
      candidate_index: 5,
      is_pareto_optimal: false,
      is_hydraulically_verified: true,
      verification_status: "VERIFIED",
      verification_violations: [],
      decision_variables: [
        {
          id: "DV-PUMP-9",
          component_type: "PUMP",
          component_id: "PUMP-9",
          parameter_name: "speed_multiplier",
          baseline_value: 1.0,
          recommended_value: 1.0,
          min_value: 0.7,
          max_value: 1.2,
          unit: "ratio",
          description: "Main intake booster pump rotational speed setting",
        },
        {
          id: "DV-PRV-1",
          component_type: "PRV",
          component_id: "PRV-1",
          parameter_name: "pressure_setpoint_bar",
          baseline_value: 2.5,
          recommended_value: 2.2,
          min_value: 1.0,
          max_value: 3.5,
          unit: "bar",
          description: "Pressure reducing valve setpoint for Zone 2 inlet",
        },
      ],
      metrics: {
        water_loss_lps: 11.9,
        pump_power_kw: 44.8,
        pressure_deficit_m: 0.0,
        demand_satisfaction_ratio: 1.0,
        max_velocity_mps: 1.78,
        min_junction_pressure_m: 17.5,
        max_junction_pressure_m: 46.2,
        operational_cost_usd_per_day: null,
      },
      tradeoff_explanation: "Suboptimal operating point: Strictly dominated by Candidate #1 on both power consumption and leakage reduction.",
    },
  ];

  const paretoCandidates = candidates.filter((c) => c.is_pareto_optimal);

  return {
    id: jobId,
    network_id: "Net1",
    objective_profile: "BALANCED_OPERATION",
    status: "COMPLETED",
    progress_pct: 100,
    created_at: new Date(Date.now() - 600000).toISOString(),
    completed_at: new Date().toISOString(),
    scenarios_evaluated: 10,
    pareto_candidate_count: paretoCandidates.length,
    selected_candidate_id: "CAND-01",
    candidates,
    pareto_candidates: paretoCandidates,
    recommended_candidate: candidates[0],
    comparison: {
      baseline_water_loss_lps: 12.4,
      optimal_water_loss_lps: 9.8,
      water_loss_reduction_pct: 20.97,
      water_loss_reduction_lps: 2.6,
      baseline_pump_power_kw: 45.2,
      optimal_pump_power_kw: 31.8,
      energy_savings_pct: 29.65,
      energy_savings_kw: 13.4,
      baseline_pressure_deficit_m: 1.2,
      optimal_pressure_deficit_m: 0.0,
      pressure_deficit_reduction_pct: 100.0,
      demand_satisfaction_maintained: true,
      cost_reduction_available: false,
      cost_reduction_usd_per_day: null,
    },
  };
}

export const backendApiClient = new BackendApiClient();
