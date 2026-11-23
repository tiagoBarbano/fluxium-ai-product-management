export interface AuthSession {
  accessToken: string;
  refreshToken: string | null;
  expiresAt: number;
  subject: string;
  username: string;
  tenantId: string;
  workspaceIds: string[];
}

export interface LoginRequest { username: string; password: string; tenantId: string; }
export interface TokenResponse { access_token: string; token_type: string; expires_in_seconds: number; refresh_token: string | null; refresh_expires_in_seconds: number; }
