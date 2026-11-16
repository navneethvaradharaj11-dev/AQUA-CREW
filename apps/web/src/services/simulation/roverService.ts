import { SimulatedRover } from "./types";
import { backendApiClient } from "../api/backendApiClient";

export type { SimulatedRover };

/**
 * Returns all simulated rovers.
 * Prioritizes FastAPI backend REST response and falls back to local engine if disconnected.
 */
export async function fetchRovers(): Promise<SimulatedRover[]> {
  return backendApiClient.getRovers();
}

/**
 * Retrieves a specific rover by ID from backend or local fallback.
 */
export async function fetchRoverById(id: string): Promise<SimulatedRover | null> {
  return backendApiClient.getRoverById(id);
}
