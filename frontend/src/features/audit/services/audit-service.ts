import { apiFetch } from "@/lib/http";
import type { AuditEventPage } from "@/types/api";

export interface AuditFilters { workspaceId: string; initiativeId?: string; resource?: string; resourceId?: string; cursor?: string; }
export function listAuditEvents(filters: AuditFilters) {
  const params = new URLSearchParams({ workspace_id: filters.workspaceId, limit: "20" });
  if (filters.initiativeId) params.set("initiative_id", filters.initiativeId);
  if (filters.resource) params.set("resource", filters.resource);
  if (filters.resourceId) params.set("resource_id", filters.resourceId);
  if (filters.cursor) params.set("cursor", filters.cursor);
  return apiFetch<AuditEventPage>(`/audit-events?${params.toString()}`);
}
