export type JobState = "PENDING" | "RUNNING" | "SUCCEEDED" | "FAILED";

export interface ReadinessAssessmentJob {
  job_id: string;
  state: JobState;
  idempotency_key: string;
  correlation_id: string;
  retry_count: number;
  error: string | null;
  assessment_id: string | null;
}

export interface ReadinessDimension { name: string; score: number; justification: string; }
export interface ReadinessAssessment {
  id: string; initiative_id: string; workspace_id: string; score: number;
  dimensions: ReadinessDimension[]; missing_information: string[]; open_questions: string[];
  confidence: number; context_version: string; provider: string; model: string;
  prompt_version: string; created_at: string; created_by: string; source_context: Record<string, unknown>;
}
export type ProposalStatus = "PENDING" | "APPROVED" | "REJECTED";
export interface ProposalBusinessDocument { title: string; questions: Array<{ key: string; question: string; answer: string }>; manual_content: string; }
export interface Proposal {
  id: string; initiative_id: string; assessment_id: string; changes: Record<string, unknown>;
  status: ProposalStatus; created_by: string; decided_by: string | null;
  decision_reason: string | null; created_at: string; decided_at: string | null;
  expected_initiative_version: number;
  business_document: ProposalBusinessDocument;
}
export interface AuditEvent {
  event_id: string; tenant_id: string; workspace_id: string; actor: string; action: string;
  resource: string; resource_id: string; before_version: number | null; after_version: number | null;
  assessment: string | null; provider: string | null; model: string | null; prompt: string | null;
  correlation_id: string | null; trace_id: string | null; metadata: Record<string, unknown>; created_at: string;
}
export interface AuditEventPage { items: AuditEvent[]; next_cursor: string | null; }
