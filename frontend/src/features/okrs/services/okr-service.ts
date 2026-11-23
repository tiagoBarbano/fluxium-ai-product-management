import { apiFetch } from "@/lib/http";

export type KeyResult = {
  id: string;
  metric: string;
  target: number;
  due_date: string;
  current_value: number | null;
  unit: string | null;
  created_at: string | null;
  updated_at: string | null;
};

export type Objective = {
  id: string;
  workspace_id: string | null;
  title: string;
  description: string;
  key_results: KeyResult[];
  product_id: string | null;
  created_at: string | null;
  updated_at: string | null;
};

type KeyResultInput = {
  metric: string;
  target: string;
  due_date: string;
  current_value?: string;
  unit?: string;
};

type ObjectiveInput = {
  title: string;
  description: string;
  key_results: KeyResultInput[];
  product_id: string;
};

export function listObjectives(workspaceId: string) {
  return apiFetch<Objective[]>(
    `/objectives?workspace_id=${encodeURIComponent(workspaceId)}`,
  );
}

export function createObjective(workspaceId: string, input: ObjectiveInput) {
  return apiFetch<Objective>(
    `/objectives?workspace_id=${encodeURIComponent(workspaceId)}`,
    {
      method: "POST",
      body: JSON.stringify(input),
    },
  );
}

export function updateObjective(
  objectiveId: string,
  input: {
    title?: string;
    description?: string;
    key_results?: Array<KeyResultInput & { id?: string }>;
  },
) {
  return apiFetch<Objective>(`/objectives/${objectiveId}`, {
    method: "PATCH",
    body: JSON.stringify(input),
  });
}
