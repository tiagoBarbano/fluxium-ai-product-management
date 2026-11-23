import { apiFetch } from "@/lib/http";
export interface Product { id: string; workspace_id: string; name: string; description: string | null; vision: string | null; status: string; created_by: string; created_at: string; updated_at: string; version: number; }
export function listProducts(workspaceId: string) { return apiFetch<{ items: Product[] }>(`/products?workspace_id=${encodeURIComponent(workspaceId)}`); }
export function createProduct(payload: { workspace_id: string; name: string; description?: string; vision?: string; created_by: string }) { return apiFetch<Product>("/products", { method: "POST", body: JSON.stringify(payload) }); }
