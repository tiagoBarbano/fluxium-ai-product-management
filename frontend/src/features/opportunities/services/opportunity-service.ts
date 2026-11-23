import { apiFetch } from "@/lib/http";

export interface Opportunity {
  id: string;
  product_id: string;
  title: string;
  description: string;
  objective_ids: string[];
  status: string;
  workspace_id: string | null;
  created_at: string;
  updated_at: string;
  version: number;
}

export function listOpportunities(workspaceId: string) {
  return apiFetch<Opportunity[]>(`/opportunities?workspace_id=${encodeURIComponent(workspaceId)}`);
}

export function createOpportunity(payload: { product_id: string; title: string; description: string; objective_ids?: string[] }) {
  return apiFetch<Opportunity>("/opportunities", { method: "POST", body: JSON.stringify(payload) });
}

export function updateOpportunity(
  opportunityId: string,
  payload: { title?: string; description?: string; objective_ids?: string[]; expected_version: number },
) {
  return apiFetch<Opportunity>(`/opportunities/${encodeURIComponent(opportunityId)}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}