import { SimulatedMission } from "./types";
import { backendApiClient } from "../api/backendApiClient";

export type { SimulatedMission };

/**
 * Returns all simulated inspection missions.
 * Prioritizes FastAPI backend REST response and falls back to local engine if disconnected.
 */
export async function fetchMissions(): Promise<SimulatedMission[]> {
  return backendApiClient.getMissions();
}
