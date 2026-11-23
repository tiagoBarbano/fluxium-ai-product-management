"use client";

import { useSyncExternalStore } from "react";
import { AuditTable } from "@/features/audit/components/audit-table";
import { getSession } from "@/features/auth/services/auth-service";
import { useI18n } from "@/components/i18n-provider";

export default function AuditPage() {
  const { t } = useI18n();
  const workspaceId = useSyncExternalStore(() => () => undefined, () => getSession()?.workspaceIds[0] ?? "", () => null);
  return <div className="stack-lg"><section className="page-intro"><div><span className="eyebrow">{t("audit.eyebrow")}</span><h1>{t("audit.title")}</h1><p>{t("audit.description")}</p></div></section>{workspaceId === null ? <p className="muted">{t("audit.loading")}</p> : workspaceId ? <AuditTable workspaceId={workspaceId} /> : <div className="error-box" role="alert">{t("overview.signInData")}</div>}</div>;
}
