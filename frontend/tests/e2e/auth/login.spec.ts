import { test, expect } from "@playwright/test";

test("user can sign in and reach the workspace", async ({ page }) => {
  await page.route("**/api/v1/identity/users/token", async (route) => route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify({ access_token: "eyJhbGciOiJub25lIn0.eyJzdWIiOiJhbGljZSIsInRlbmFudF9pZCI6InRlbmFudC0xIiwid29ya3NwYWNlX2lkcyI6WyJ3cy0xIl19.x", token_type: "bearer", expires_in_seconds: 3600, refresh_token: "refresh-token-value-12345678901234567890", refresh_expires_in_seconds: 7200 }) }));
  await page.goto("/login");
  await page.getByLabel("ID do tenant").fill("tenant-1"); await page.getByLabel("Usuário").fill("alice"); await page.getByLabel("Senha").fill("a-strong-password"); await page.getByRole("button", { name: "Entrar" }).click();
  await expect(page).toHaveURL("/"); await expect(page.getByText("ws-1")).toBeVisible();
});
