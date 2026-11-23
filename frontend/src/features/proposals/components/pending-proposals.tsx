"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useI18n } from "@/components/i18n-provider";
import type { Proposal, ReadinessAssessment } from "@/types/api";
import { approveProposal, getReadinessAssessment, listFilteredProposals, rejectProposal } from "@/features/readiness/services/readiness-service";
import { getInitiative, listInitiatives, type Initiative } from "@/features/initiatives/services/initiative-service";
import { listOpportunities, type Opportunity } from "@/features/opportunities/services/opportunity-service";
import { listProducts, type Product } from "@/features/products/services/product-service";
import { getSession } from "@/features/auth/services/auth-service";
import { AssessmentDetails } from "@/features/readiness/components/assessment-details";
import { readinessPointLabels } from "@/features/readiness/components/assessment-details";

export function PendingProposals() {
  const { t, locale } = useI18n();
  const session = getSession();
  const hasSession = Boolean(session);
  const [proposals, setProposals] = useState<Proposal[]>([]);
  const [error, setError] = useState<string | null>(hasSession ? null : t("proposals.signIn"));
  const [loading, setLoading] = useState(hasSession);
  const [actionError, setActionError] = useState<string | null>(null);
  const [busyProposalId, setBusyProposalId] = useState<string | null>(null);
  const [assessment, setAssessment] = useState<ReadinessAssessment | null>(null);
  const [assessmentLoading, setAssessmentLoading] = useState(false);
  const [assessmentError, setAssessmentError] = useState<string | null>(null);
  const [initiativeNames, setInitiativeNames] = useState<Record<string, string>>({});
  const [proposalAssessments, setProposalAssessments] = useState<Record<string, ReadinessAssessment>>({});
  const [rejectionProposalId, setRejectionProposalId] = useState<string | null>(null);
  const [rejectionReason, setRejectionReason] = useState("");
  const [products, setProducts] = useState<Product[]>([]);
  const [opportunities, setOpportunities] = useState<Opportunity[]>([]);
  const [initiatives, setInitiatives] = useState<Initiative[]>([]);
  const [statusFilter, setStatusFilter] = useState<Proposal["status"] | "">("");
  const [productFilter, setProductFilter] = useState("");
  const [opportunityFilter, setOpportunityFilter] = useState("");
  const [initiativeFilter, setInitiativeFilter] = useState("");

  useEffect(() => {
    const workspaceId = session?.workspaceIds[0];
    if (!workspaceId) return;
    Promise.all([listProducts(workspaceId), listOpportunities(workspaceId)])
      .then(async ([productResponse, opportunityItems]) => {
        const productItems = productResponse.items;
        const initiativeGroups = await Promise.all(productItems.map((product) => listInitiatives(product.id)));
        setProducts(productItems);
        setOpportunities(opportunityItems);
        setInitiatives(initiativeGroups.flat());
      })
      .catch((requestError) => setError(requestError instanceof Error ? requestError.message : t("error.request")));
  }, [session?.workspaceIds, t]);

  useEffect(() => {
    if (!hasSession) return;
    listFilteredProposals({
      status: statusFilter || undefined,
      productId: productFilter || undefined,
      opportunityId: opportunityFilter || undefined,
      initiativeId: initiativeFilter || undefined,
    })
      .then(async (items) => {
        setProposals(items);
        const proposalDetails = await Promise.all(items.map(async (proposal) => {
          try {
            const [initiative, proposalAssessment] = await Promise.all([
              getInitiative(proposal.initiative_id),
              getReadinessAssessment(proposal.assessment_id),
            ]);
            return { proposal, initiative, proposalAssessment };
          } catch {
            return null;
          }
        }));
        setInitiativeNames(Object.fromEntries(proposalDetails.filter((item): item is NonNullable<typeof item> => item !== null).map(({ proposal, initiative }) => [proposal.initiative_id, initiative.title])));
        setProposalAssessments(Object.fromEntries(proposalDetails.filter((item): item is NonNullable<typeof item> => item !== null).map(({ proposal, proposalAssessment }) => [proposal.id, proposalAssessment])));
      })
      .catch((requestError) => setError(requestError instanceof Error ? requestError.message : t("error.request")))
      .finally(() => setLoading(false));
  }, [hasSession, statusFilter, productFilter, opportunityFilter, initiativeFilter, t]);

  const visibleOpportunities = productFilter
    ? opportunities.filter((item) => item.product_id === productFilter)
    : opportunities;
  const visibleInitiatives = initiatives.filter((item) =>
    (!productFilter || item.product_id === productFilter) &&
    (!opportunityFilter || item.opportunity_id === opportunityFilter)
  );

  async function handleApprove(proposalId: string) {
    setActionError(null);
    setBusyProposalId(proposalId);
    try {
      await approveProposal(proposalId);
      setProposals((current) => current.filter((proposal) => proposal.id !== proposalId));
    } catch (requestError) {
      setActionError(requestError instanceof Error ? requestError.message : t("error.request"));
    } finally {
      setBusyProposalId(null);
    }
  }

  async function handleShowAssessment(assessmentId: string) {
    setAssessment(null);
    setAssessmentError(null);
    setAssessmentLoading(true);
    try {
      setAssessment(await getReadinessAssessment(assessmentId));
    } catch (requestError) {
      setAssessmentError(requestError instanceof Error ? requestError.message : t("error.request"));
    } finally {
      setAssessmentLoading(false);
    }
  }

  async function handleReject(proposalId: string) {
    const reason = rejectionReason.trim();
    if (!reason) return;
    setActionError(null);
    setBusyProposalId(proposalId);
    try {
      await rejectProposal(proposalId, reason);
      setProposals((current) => current.filter((proposal) => proposal.id !== proposalId));
      setRejectionProposalId(null);
      setRejectionReason("");
    } catch (requestError) {
      setActionError(requestError instanceof Error ? requestError.message : t("error.request"));
    } finally {
      setBusyProposalId(null);
    }
  }

  return (
    <div className="stack-lg workspace-page">
      <section className="dashboard-intro">
        <div>
          <span className="eyebrow">{t("proposals.eyebrow")}</span>
          <h1>{t("proposals.title")}</h1>
          <p>{t("proposals.description")}</p>
        </div>
      </section>
      {loading && <div className="panel muted">{t("proposals.loading")}</div>}
      {error && <div className="error-box" role="alert">{error} <Link className="text-link" href="/login">{t("shell.signIn")} →</Link></div>}
      {actionError && <div className="error-box" role="alert">{actionError}</div>}
      <section className="panel proposal-filters" aria-label={t("proposals.filters")}>
        <div className="panel-heading"><div><span className="eyebrow">{t("proposals.filterEyebrow")}</span><h2>{t("proposals.filterTitle")}</h2></div></div>
        <div className="proposal-filter-grid">
          <label>{t("proposals.statusFilter")}<select value={statusFilter} onChange={(event) => setStatusFilter(event.target.value as Proposal["status"] | "")}><option value="">{t("proposals.allStatuses")}</option><option value="PENDING">{t("proposalHistory.status.PENDING")}</option><option value="APPROVED">{t("proposalHistory.status.APPROVED")}</option><option value="REJECTED">{t("proposalHistory.status.REJECTED")}</option></select></label>
          <label>{t("workspace.productTitle")}<select value={productFilter} onChange={(event) => { setProductFilter(event.target.value); setOpportunityFilter(""); setInitiativeFilter(""); }}><option value="">{t("overview.allProducts")}</option>{products.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}</select></label>
          <label>{t("workspace.opportunityTitle")}<select value={opportunityFilter} onChange={(event) => { setOpportunityFilter(event.target.value); setInitiativeFilter(""); }}><option value="">{t("proposals.allOpportunities")}</option>{visibleOpportunities.map((item) => <option key={item.id} value={item.id}>{item.title}</option>)}</select></label>
          <label>{t("workspace.initiativeTitle")}<select value={initiativeFilter} onChange={(event) => setInitiativeFilter(event.target.value)}><option value="">{t("proposals.allInitiatives")}</option>{visibleInitiatives.map((item) => <option key={item.id} value={item.id}>{item.title}</option>)}</select></label>
        </div>
      </section>
      {!loading && !error && !proposals.length && <div className="panel empty-state"><p>{t("proposals.empty")}</p></div>}
      <div className="proposal-list">
        {proposals.map((proposal) => (
          <article className="proposal-row" key={proposal.id}>
            <header>
              <div>
                <span className="eyebrow">{t("proposals.initiative")}</span>
                <h2>{initiativeNames[proposal.initiative_id] ?? proposal.initiative_id}</h2>
                <small className="muted">{proposal.initiative_id}</small>
              </div>
              <span className={`pill ${proposal.status.toLowerCase()}`}>{t(`proposalHistory.status.${proposal.status}`)}</span>
            </header>
            <dl>
              <div>
                <dt>{t("proposals.created")}</dt>
                <dd>{new Date(proposal.created_at).toLocaleString(locale)}</dd>
              </div>
              <div>
                <dt>{t("proposals.changes")}</dt>
                <dd>{Object.keys(proposal.changes).join(", ")}</dd>
              </div>
            </dl>
            <ul>
              {Object.entries(proposal.changes).map(([key, value]) => (
                <li key={key}>{formatChange(key, value, t)}</li>
              ))}
            </ul>
            <ProposalContextSummary proposal={proposal} assessment={proposalAssessments[proposal.id]} translate={t} />
            <footer>
              <small className="muted">{proposal.id}</small>
              <div className="proposal-actions">
                {proposal.status === "PENDING" && <button
                  className="primary-button compact"
                  type="button"
                  disabled={busyProposalId !== null}
                  onClick={() => handleApprove(proposal.id)}
                >
                  {busyProposalId === proposal.id ? t("proposals.approving") : t("proposals.approve")}
                </button>}
                {proposal.status === "PENDING" && <button
                  className="secondary-button compact"
                  type="button"
                  disabled={busyProposalId !== null}
                  onClick={() => { setRejectionProposalId(proposal.id); setRejectionReason(""); }}
                >
                  {t("proposals.reject")}
                </button>}
                <button
                  className="secondary-button compact"
                  type="button"
                  disabled={assessmentLoading}
                  onClick={() => handleShowAssessment(proposal.assessment_id)}
                >
                  {t("proposals.showContextAndAssessment")}
                </button>
                <Link className="secondary-button compact" href={`/readiness/${proposal.initiative_id}`}>
                  {t("proposals.open")}<span aria-hidden="true">↗</span>
                </Link>
              </div>
            </footer>
            {rejectionProposalId === proposal.id && <div className="proposal-rejection">
              <label htmlFor={`rejection-${proposal.id}`}>{t("proposals.rejectReason")}</label>
              <textarea
                id={`rejection-${proposal.id}`}
                rows={3}
                value={rejectionReason}
                onChange={(event) => setRejectionReason(event.target.value)}
                placeholder={t("proposals.rejectReasonPlaceholder")}
              />
              <div className="proposal-actions">
                <button className="primary-button compact" type="button" disabled={!rejectionReason.trim() || busyProposalId !== null} onClick={() => handleReject(proposal.id)}>
                  {busyProposalId === proposal.id ? t("proposals.rejecting") : t("proposals.confirmReject")}
                </button>
                <button className="secondary-button compact" type="button" disabled={busyProposalId !== null} onClick={() => { setRejectionProposalId(null); setRejectionReason(""); }}>
                  {t("proposals.cancelReject")}
                </button>
              </div>
            </div>}
          </article>
        ))}
      </div>
      {(assessmentLoading || assessmentError || assessment) && (
        <div className="modal-backdrop" role="presentation" onClick={() => setAssessment(null)}>
          <section
            className="assessment-modal"
            role="dialog"
            aria-modal="true"
            aria-labelledby="assessment-modal-title"
            onClick={(event) => event.stopPropagation()}
          >
            <header className="modal-header">
              <div>
                <span className="eyebrow">{t("proposals.assessment")}</span>
                <h2 id="assessment-modal-title">{assessment ? initiativeNames[assessment.initiative_id] ?? assessment.initiative_id : t("proposals.assessmentLoading")}</h2>
                {assessment && <small className="muted">{assessment.initiative_id}</small>}
              </div>
              <button className="modal-close" type="button" aria-label={t("proposals.closeAssessment")} onClick={() => setAssessment(null)}>×</button>
            </header>
            {assessmentLoading && <p className="muted">{t("proposals.assessmentLoading")}</p>}
            {assessmentError && <div className="error-box" role="alert">{assessmentError}</div>}
            {assessment && <AssessmentDetails assessment={assessment} translate={t} />}
          </section>
        </div>
      )}
    </div>
  );
}

function ProposalContextSummary({ proposal, assessment, translate }: { proposal: Proposal; assessment?: ReadinessAssessment; translate: (key: string) => string }) {
  const proposalQuestions = proposal.business_document?.questions ?? [];
  if (proposalQuestions.length > 0) {
    return <div className="proposal-context-summary"><span className="eyebrow">{translate("proposals.businessDocument")}</span><dl>{proposalQuestions.map(({ key, question, answer }) => <div key={key}><dt>{question}</dt><dd>{answer || translate("proposals.noAnswer")}</dd></div>)}</dl></div>;
  }
  if (!assessment) return null;
  const submittedContext = assessment.source_context.submitted_context && typeof assessment.source_context.submitted_context === "object"
    ? assessment.source_context.submitted_context as Record<string, unknown>
    : {};
  const readinessDimensions = assessment.source_context.readiness_dimensions ?? submittedContext.readiness_dimensions;
  if (!readinessDimensions || typeof readinessDimensions !== "object") return null;
  const points = Object.entries(readinessDimensions as Record<string, unknown>).filter(([, value]) => typeof value === "string" && value.trim());
  if (!points.length) return null;
  return <div className="proposal-context-summary"><span className="eyebrow">{translate("proposals.userReviewPoints")}</span><dl>{points.map(([name, value]) => <div key={name}><dt>{readinessPointLabels[name] ?? name}</dt><dd>{String(value)}</dd></div>)}</dl></div>;
}


function formatChange(key: string, value: unknown, translate: (key: string) => string) {
  if (key === "readiness_score" && typeof value === "number") return `${translate("proposals.score")}: ${Math.round(value * 100)}/100`;
  if (key === "readiness_confidence" && typeof value === "number") return `${translate("proposals.confidence")}: ${Math.round(value * 100)}%`;
  return `${key}: ${String(value)}`;
}
