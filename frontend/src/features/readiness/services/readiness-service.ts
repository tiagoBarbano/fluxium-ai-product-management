import { apiFetch } from "@/lib/http";
import type { Proposal, ReadinessAssessment, ReadinessAssessmentJob } from "@/types/api";
import type { ReadinessJobRequest } from "../types";

export function createReadinessJob(initiativeId: string, payload: ReadinessJobRequest) {
  return apiFetch<ReadinessAssessmentJob>(`/initiatives/${initiativeId}/readiness-assessment-jobs`, {
    method: "POST", headers: { "X-Idempotency-Key": crypto.randomUUID() }, body: JSON.stringify(payload),
  });
}
export function getReadinessJob(jobId: string) { return apiFetch<ReadinessAssessmentJob>(`/readiness-assessment-jobs/${jobId}`); }
export function retryReadinessJob(jobId: string) { return apiFetch<ReadinessAssessmentJob>(`/readiness-assessment-jobs/${jobId}/retry`, { method: "POST" }); }
export function getReadinessAssessment(assessmentId: string) { return apiFetch<ReadinessAssessment>(`/readiness-assessments/${assessmentId}`); }
export function listProposals(initiativeId: string, assessmentId: string) { return apiFetch<Proposal[]>(`/initiatives/${initiativeId}/readiness-assessments/${assessmentId}/proposals`); }
export function listInitiativeProposals(initiativeId: string, status?: Proposal["status"]) { const query = status ? `?status=${status}` : ""; return apiFetch<Proposal[]>(`/initiatives/${initiativeId}/proposals${query}`); }
export function listFilteredProposals(filters: { status?: Proposal["status"]; productId?: string; opportunityId?: string; initiativeId?: string; limit?: number } = {}) {
  const params = new URLSearchParams({ limit: String(filters.limit ?? 100) });
  if (filters.status) params.set("status", filters.status);
  if (filters.productId) params.set("product_id", filters.productId);
  if (filters.opportunityId) params.set("opportunity_id", filters.opportunityId);
  if (filters.initiativeId) params.set("initiative_id", filters.initiativeId);
  return apiFetch<Proposal[]>(`/proposals?${params.toString()}`);
}
export function listPendingProposals(limit = 50) { return listFilteredProposals({ status: "PENDING", limit }); }
export function listApprovedProposals(limit = 50) { return apiFetch<Proposal[]>(`/proposals?status=APPROVED&limit=${limit}`); }
export function createProposal(payload: { initiative_id: string; assessment_id: string; changes: Record<string, unknown>; expected_initiative_version: number }) { return apiFetch<Proposal>("/proposals", { method: "POST", body: JSON.stringify(payload) }); }
export function approveProposal(proposalId: string, decisionReason?: string) { return apiFetch<Proposal>(`/proposals/${proposalId}/approve`, { method: "POST", body: JSON.stringify(decisionReason ? { decision_reason: decisionReason } : {}) }); }
export function rejectProposal(proposalId: string, decisionReason: string) { return apiFetch<Proposal>(`/proposals/${proposalId}/reject`, { method: "POST", body: JSON.stringify({ decision_reason: decisionReason }) }); }
