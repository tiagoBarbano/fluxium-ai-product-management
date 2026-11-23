export interface ReadinessJobRequest {
  context: Record<string, unknown>;
  context_version: string;
  prompt_version: string;
  language: "pt-BR" | "en-US";
  manual_content?: unknown;
}
