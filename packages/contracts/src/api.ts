/**
 * Standard API Response Envelope
 */
export interface ApiResponse<T> {
  success: boolean;
  data: T;
  message?: string;
  timestamp: string;
}

/**
 * Standard API Error Response
 */
export interface ApiErrorResponse {
  success: false;
  error: {
    code: string;
    message: string;
    details?: Array<{ field?: string; issue: string }>;
  };
  timestamp: string;
}

/**
 * Health Check Response Model
 */
export interface HealthStatusResponse {
  status: 'healthy' | 'degraded' | 'unhealthy';
  version: string;
  environment: string;
  timestamp: string;
  services: {
    database: string;
    simulation_engine: string;
    hardware_gateway: string;
  };
}

