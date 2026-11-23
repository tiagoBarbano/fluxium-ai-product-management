"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useI18n } from "@/components/i18n-provider";
import { getSession } from "@/features/auth/services/auth-service";
import { getInitiative, type Initiative } from "@/features/initiatives/services/initiative-service";
import { listInitiativeProposals } from "@/features/readiness/services/readiness-service";
import type { Proposal, ProposalStatus } from "@/types/api";

const statusClass: Record<ProposalStatus, string> = {
  PENDING: "pending",
  APPROVED: "approved",
  REJECTED: "rejected",
};

export function InitiativeProposalHistory({ initiativeId }: { initiativeId: string }) {
  const { t, locale } = useI18n();
  const hasSession = Boolean(getSession());
  const [initiative, setInitiative] = useState<Initiative | null>(null);
  const [proposals, setProposals] = useState<Proposal[]>([]);
  const [error, setError] = useState<string | null>(hasSession ? null : t("proposals.signIn"));
  const [loading, setLoading] = useState(hasSession);

  useEffect(() => {
    if (!hasSession) return;
    Promise.all([getInitiative(initiativeId), listInitiativeProposals(initiativeId)])
      .then(([nextInitiative, nextProposals]) => {
        setInitiative(nextInitiative);
        setProposals(nextProposals);
      })
      .catch((requestError) => setError(requestError instanceof Error ? requestError.message : t("error.request")))
      .finally(() => setLoading(false));
  }, [hasSession, initiativeId, t]);

  return (
    <div className="stack-lg">
      <section className="hero-panel">
        <div>
          <span className="eyebrow">{t("proposalHistory.eyebrow")}</span>
          <h1>{initiative?.title ?? initiativeId}</h1>
          <p>{t("proposalHistory.description")}</p>
          <small className="muted entity-id">{initiativeId}</small>
        </div>
        <div className="hero-mark" aria-hidden="true">P<span>↺</span></div>
      </section>
      <div className="proposal-history-actions">
        <Link className="secondary-button compact" href={`/readiness/${initiativeId}`}>{t("proposalHistory.openReadiness")}<span aria-hidden="true">↗</span></Link>
        <Link className="secondary-button compact" href="/proposals">{t("proposalHistory.openPending")}<span aria-hidden="true">↗</span></Link>
      </div>
      {loading && <div className="panel muted">{t("proposalHistory.loading")}</div>}
      {error && <div className="error-box" role="alert">{error} <Link className="text-link" href="/login">{t("shell.signIn")} →</Link></div>}
      {!loading && !error && !proposals.length && <div className="panel empty-state"><p>{t("proposalHistory.empty")}</p></div>}
      {!loading && !error && proposals.length > 0 && (
        <div className="proposal-list">
          {proposals.map((proposal) => (
            <article className={`proposal-row history-row ${statusClass[proposal.status]}`} key={proposal.id}>
              <header>
                <div>
                  <span className="eyebrow">{t("proposalHistory.proposal")}</span>
                  <h2>{Object.keys(proposal.changes).join(", ")}</h2>
                  <small className="muted">{proposal.id}</small>
                </div>
                <span className={`pill ${statusClass[proposal.status]}`}>{t(`proposalHistory.status.${proposal.status}`)}</span>
              </header>
              <dl>
                <div><dt>{t("proposalHistory.created")}</dt><dd>{new Date(proposal.created_at).toLocaleString(locale)}</dd></div>
                <div><dt>{t("proposalHistory.createdBy")}</dt><dd>{proposal.created_by}</dd></div>
                {proposal.decided_at && <div><dt>{t("proposalHistory.decided")}</dt><dd>{new Date(proposal.decided_at).toLocaleString(locale)}</dd></div>}
                {proposal.decided_by && <div><dt>{t("proposalHistory.decidedBy")}</dt><dd>{proposal.decided_by}</dd></div>}
              </dl>
              <ul>{Object.entries(proposal.changes).map(([key, value]) => <li key={key}>{formatChange(key, value, t)}</li>)}</ul>
              {proposal.decision_reason && <p className="proposal-decision-reason"><strong>{t("proposalHistory.reason")}:</strong> {proposal.decision_reason}</p>}
            </article>
          ))}
        </div>
      )}
    </div>
  );
}

function formatChange(key: string, value: unknown, translate: (key: string) => string) {
  if (key === "readiness_score" && typeof value === "number") return `${translate("proposals.score")}: ${Math.round(value * 100)}/100`;
  if (key === "readiness_confidence" && typeof value === "number") return `${translate("proposals.confidence")}: ${Math.round(value * 100)}%`;
  return `${key}: ${String(value)}`;
}
