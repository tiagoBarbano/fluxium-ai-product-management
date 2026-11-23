import { apiFetch } from "@/lib/http";

export type Workspace = { id: string; tenant_id: string; name: string; description: string | null; status: string; created_by: string; created_at: string };

export async function createWorkspace(input: { name: string; description?: string }): Promise<Workspace> {
  return apiFetch<Workspace>("/workspaces", { method: "POST", body: JSON.stringify(input) });
}