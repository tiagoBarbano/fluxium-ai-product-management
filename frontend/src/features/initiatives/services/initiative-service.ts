import { apiFetch } from "@/lib/http";
export interface Initiative {
  id: string;
  workspace_id: string;
  product_id: string;
  opportunity_id: string;
  problem_id: string | null;
  title: string;
  objective: string;
  scope: string;
  objective_ids: string[];
  status: string;
  readiness_score: number | null;
  readiness_confidence: number | null;
  created_at: string;
  updated_at: string;
  version: number;
}
export function listInitiatives(productId: string) {
  return apiFetch<Initiative[]>(`/products/${productId}/initiatives`);
}
export function getInitiative(initiativeId: string) {
  return apiFetch<Initiative>(`/initiatives/${initiativeId}`);
}
export function createInitiative(
  opportunityId: string,
  payload: {
    title: string;
    objective: string;
    scope: string;
    product_id: string;
    objective_ids?: string[];
    out_of_scope?: string;
  },
) {
  return apiFetch<Initiative>(`/opportunities/${opportunityId}/initiatives`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}
