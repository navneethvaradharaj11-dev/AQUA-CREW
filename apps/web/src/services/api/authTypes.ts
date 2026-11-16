/**
 * AQUA CREW — Authentication, RBAC and Security Types (Task 13.6)
 */

export type UserRole = "VIEWER" | "OPERATOR" | "ENGINEER" | "ADMINISTRATOR";

export interface UserProfile {
  id: string;
  username: string;
  email: string;
  full_name: string;
  role: UserRole;
  is_active: boolean;
  created_at: string;
}

export interface LoginRequest {
  username_or_email: string;
  password: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in_seconds: number;
  user: UserProfile;
}

export interface RefreshTokenRequest {
  refresh_token: string;
}

export interface UserCreateRequest {
  username: string;
  email: string;
  password: string;
  full_name?: string;
  role?: UserRole;
}

export interface UserUpdateRequest {
  email?: string;
  full_name?: string;
  role?: UserRole;
  is_active?: boolean;
}

export interface SecurityAuditEvent {
  id: string;
  timestamp: string;
  event_type: string;
  user_id?: string;
  username?: string;
  ip_address?: string;
  user_agent?: string;
  resource_id?: string;
  status: string;
  details?: Record<string, any>;
}

