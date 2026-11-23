export const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api/v1";

export class ApiError extends Error {
  constructor(public readonly status: number, message: string) { super(message); this.name = "ApiError"; }
}

export async function apiFetch<T>(path: string, init: RequestInit = {}): Promise<T> {
  const session = typeof window !== "undefined" ? readSession() : null;
  const headers = new Headers(init.headers);
  headers.set("Accept", "application/json");
  headers.set("Correlation-Id", crypto.randomUUID());
  if (init.body) headers.set("Content-Type", "application/json");
  if (session?.accessToken) headers.set("Authorization", `Bearer ${session.accessToken}`);
  let response = await fetch(`${API_BASE_URL}${path}`, { ...init, headers });
  if (response.status === 401 && session?.refreshToken && typeof window !== "undefined") {
    const refreshed = await refreshAccessToken(session);
    if (refreshed) {
      headers.set("Authorization", `Bearer ${refreshed.accessToken}`);
      response = await fetch(`${API_BASE_URL}${path}`, { ...init, headers });
    }
  }
  if (!response.ok) {
    let message = `Request failed (${response.status})`;
    try { message = ((await response.json()) as { detail?: string }).detail ?? message; } catch { /* status message */ }
    throw new ApiError(response.status, message);
  }
  return (await response.json()) as T;
}

interface StoredSession { accessToken: string; refreshToken: string | null; tenantId: string; }
function readSession(): StoredSession | null { const value = sessionStorage.getItem("fluxium_session"); return value ? JSON.parse(value) as StoredSession : null; }
async function refreshAccessToken(session: StoredSession): Promise<StoredSession | null> {
  const response = await fetch(`${API_BASE_URL}/identity/users/token/refresh`, { method: "POST", headers: { "Content-Type": "application/json", Accept: "application/json" }, body: JSON.stringify({ refresh_token: session.refreshToken, expires_in_seconds: 3600 }) });
  if (!response.ok) { sessionStorage.removeItem("fluxium_session"); return null; }
  const token = await response.json() as { access_token: string; refresh_token: string | null; expires_in_seconds: number };
  const updated = { ...session, accessToken: token.access_token, refreshToken: token.refresh_token ?? session.refreshToken, expiresAt: Date.now() + token.expires_in_seconds * 1000 };
  sessionStorage.setItem("fluxium_session", JSON.stringify(updated));
  return updated;
}
