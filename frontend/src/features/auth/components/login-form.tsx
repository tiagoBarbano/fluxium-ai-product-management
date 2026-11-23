"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import { login } from "../services/auth-service";
import { useI18n } from "@/components/i18n-provider";

export function LoginForm() {
  const router = useRouter(); const { t } = useI18n(); const [username, setUsername] = useState(""); const [password, setPassword] = useState(""); const [tenantId, setTenantId] = useState(""); const [error, setError] = useState<string | null>(null); const [loading, setLoading] = useState(false);
  async function submit(event: FormEvent<HTMLFormElement>) { event.preventDefault(); setError(null); setLoading(true); try { await login({ username, password, tenantId }); router.push("/"); router.refresh(); } catch (requestError) { setError(requestError instanceof Error ? requestError.message : t("login.error")); } finally { setLoading(false); } }
  return <form className="login-form" onSubmit={submit}><span className="eyebrow">{t("login.access")}</span><h1>{t("login.title")}</h1><p>{t("login.description")}</p><label htmlFor="tenant">{t("login.tenant")}</label><input id="tenant" value={tenantId} onChange={(event) => setTenantId(event.target.value)} required placeholder="tenant-1" /><label htmlFor="username">{t("login.username")}</label><input id="username" value={username} onChange={(event) => setUsername(event.target.value)} required autoComplete="username" /><label htmlFor="password">{t("login.password")}</label><input id="password" type="password" value={password} onChange={(event) => setPassword(event.target.value)} required autoComplete="current-password" />{error && <div className="error-box" role="alert">{error}</div>}<button className="primary-button" type="submit" disabled={loading}>{loading ? t("login.submitting") : t("login.submit")}<span aria-hidden="true">↗</span></button></form>;
}
