"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { useI18n } from "@/components/i18n-provider";
import { getSession } from "@/features/auth/services/auth-service";
import { getReadinessAssessment, listApprovedProposals, listPendingProposals } from "@/features/readiness/services/readiness-service";
import { AssessmentDetails } from "@/features/readiness/components/assessment-details";
import { listInitiatives, type Initiative } from "@/features/initiatives/services/initiative-service";
import { listObjectives, type Objective } from "@/features/okrs/services/okr-service";
import { listOpportunities, type Opportunity } from "@/features/opportunities/services/opportunity-service";
import { listProducts, type Product } from "@/features/products/services/product-service";
import type { Proposal, ReadinessAssessment } from "@/types/api";

export function OverviewDashboard() {
  const { t } = useI18n();
  const [products, setProducts] = useState<Product[]>([]);
  const [objectives, setObjectives] = useState<Objective[]>([]);
  const [opportunities, setOpportunities] = useState<Opportunity[]>([]);
  const [initiatives, setInitiatives] = useState<Initiative[]>([]);
  const [proposals, setProposals] = useState<Proposal[]>([]);
  const [approvedProposals, setApprovedProposals] = useState<Proposal[]>([]);
  const [selectedProductId, setSelectedProductId] = useState("all");
  const [message, setMessage] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [assessment, setAssessment] = useState<ReadinessAssessment | null>(null);
  const [assessmentLoading, setAssessmentLoading] = useState(false);
  const [assessmentError, setAssessmentError] = useState<string | null>(null);
  const [selectedProposal, setSelectedProposal] = useState<Proposal | null>(null);

  useEffect(() => {
    Promise.resolve().then(async () => {
      const session = getSession();
      const workspaceId = session?.workspaceIds[0];
      if (!workspaceId) {
        setMessage(t("overview.signInData"));
        setLoading(false);
        return;
      }
      try {
        const [productResult, objectiveResult, opportunityResult] = await Promise.all([
          listProducts(workspaceId),
          listObjectives(workspaceId),
          listOpportunities(workspaceId),
        ]);
        const productInitiatives = await Promise.all(productResult.items.map((product) => listInitiatives(product.id)));
        const [pendingProposals, approvedItems] = await Promise.all([listPendingProposals(), listApprovedProposals()]);
        setProducts(productResult.items);
        setObjectives(objectiveResult);
        setOpportunities(opportunityResult);
        setInitiatives(productInitiatives.flat());
        setProposals(pendingProposals);
        setApprovedProposals(approvedItems);
      } catch (error) {
        setMessage(error instanceof Error ? error.message : t("overview.connectDescription"));
      } finally {
        setLoading(false);
      }
    });
  }, [t]);

  const visibleInitiatives = useMemo(
    () => selectedProductId === "all" ? initiatives : initiatives.filter((initiative) => initiative.product_id === selectedProductId),
    [initiatives, selectedProductId],
  );
  const visibleObjectives = useMemo(
    () => selectedProductId === "all" ? objectives : objectives.filter((objective) => objective.product_id === selectedProductId),
    [objectives, selectedProductId],
  );
  const visibleOpportunities = useMemo(
    () => selectedProductId === "all" ? opportunities : opportunities.filter((opportunity) => opportunity.product_id === selectedProductId),
    [opportunities, selectedProductId],
  );
  const visibleProposals = useMemo(
    () => proposals.filter((proposal) => visibleInitiatives.some((initiative) => initiative.id === proposal.initiative_id)),
    [proposals, visibleInitiatives],
  );
  const visibleApprovedProposals = useMemo(
    () => approvedProposals.filter((proposal) => visibleInitiatives.some((initiative) => initiative.id === proposal.initiative_id)),
    [approvedProposals, visibleInitiatives],
  );
  const visibleAllProposals = useMemo(
    () => [...visibleProposals, ...visibleApprovedProposals],
    [visibleApprovedProposals, visibleProposals],
  );

  async function showAssessment(proposal: Proposal) {
    setAssessment(null);
    setAssessmentError(null);
    setAssessmentLoading(true);
    try {
      setAssessment(await getReadinessAssessment(proposal.assessment_id));
    } catch (error) {
      setAssessmentError(error instanceof Error ? error.message : t("error.request"));
    } finally {
      setAssessmentLoading(false);
    }
  }
  return (
    <div className="stack-lg">
      <section className="dashboard-intro">
        <div>
          <span className="eyebrow">{t("overview.eyebrow")}</span>
          <h1>{t("overview.title")}</h1>
          <p>{t("overview.description")}</p>
        </div>
        <Link className="primary-button compact" href="/workspace">
          {t("overview.openContext")}<span aria-hidden="true">↗</span>
        </Link>
      </section>
      {message && <div className="notice-box">{message} {!getSession() && <Link href="/login" className="text-link">{t("overview.signIn")}</Link>}</div>}
      {loading ? <div className="panel muted">{t("overview.loading")}</div> : <>
        <section className="signal-grid">
          <Signal label={t("overview.products")} value={products.length} detail={t("overview.productsSummary")} />
          <Signal label={t("overview.objectives")} value={visibleObjectives.length} detail={t("overview.objectivesSummary")} />
          <Signal label={t("overview.initiatives")} value={visibleInitiatives.length} detail={t("overview.initiativesSummary")} />
          <Signal label={t("overview.pendingProposals")} value={visibleProposals.length} detail={t("overview.pendingSummary")} />
        </section>
        <section className="overview-toolbar">
          <div><span className="eyebrow">{t("overview.productFilter")}</span><h2>{t("overview.navigationTitle")}</h2></div>
          <select aria-label={t("overview.productFilter")} value={selectedProductId} onChange={(event) => setSelectedProductId(event.target.value)}>
            <option value="all">{t("overview.allProducts")}</option>
            {products.map((product) => <option key={product.id} value={product.id}>{product.name}</option>)}
          </select>
        </section>
        <RelationshipMap products={products} objectives={visibleObjectives} opportunities={visibleOpportunities} initiatives={visibleInitiatives} proposals={visibleAllProposals} translate={t} onViewAssessment={showAssessment} onViewBusinessPoints={setSelectedProposal} />
        <section className="panel overview-readiness"><div className="section-heading"><div><span className="eyebrow">{t("overview.readinessEyebrow")}</span><h2>{selectedProductId === "all" ? t("overview.allProducts") : products.find((product) => product.id === selectedProductId)?.name}</h2></div><span className="context-chip">{visibleInitiatives.length}</span></div><div className="initiative-list">{visibleInitiatives.length ? visibleInitiatives.map((initiative) => <div className="initiative-row" key={initiative.id}><div><strong>{initiative.title}</strong><span>{initiative.objective}</span></div><Link className="text-link" href={`/readiness/${initiative.id}`}>{t("overview.openReadiness")} ↗</Link></div>) : <p className="empty-state compact-empty">{t("overview.noReadinessInitiatives")}</p>}</div></section>
      </>}
      {(assessmentLoading || assessmentError || assessment) && <div className="modal-backdrop" role="presentation" onClick={() => setAssessment(null)}><section className="assessment-modal" role="dialog" aria-modal="true" aria-labelledby="overview-assessment-title" onClick={(event) => event.stopPropagation()}><header className="modal-header"><div><span className="eyebrow">{t("proposals.assessment")}</span><h2 id="overview-assessment-title">{assessment ? visibleInitiatives.find((initiative) => initiative.id === assessment.initiative_id)?.title ?? assessment.initiative_id : t("proposals.assessmentLoading")}</h2></div><button className="modal-close" type="button" aria-label={t("proposals.closeAssessment")} onClick={() => setAssessment(null)}>×</button></header>{assessmentLoading && <p className="muted">{t("proposals.assessmentLoading")}</p>}{assessmentError && <div className="error-box" role="alert">{assessmentError}</div>}{assessment && <AssessmentDetails assessment={assessment} translate={t} />}</section></div>}
      {selectedProposal && <div className="modal-backdrop" role="presentation" onClick={() => setSelectedProposal(null)}><section className="assessment-modal proposal-business-modal" role="dialog" aria-modal="true" aria-labelledby="overview-business-points-title" onClick={(event) => event.stopPropagation()}><header className="modal-header"><div><span className="eyebrow">{t("overview.businessPointsEyebrow")}</span><h2 id="overview-business-points-title">{t("overview.businessPointsTitle")}</h2></div><button className="modal-close" type="button" aria-label={t("overview.closeBusinessPoints")} onClick={() => setSelectedProposal(null)}>×</button></header><div className="assessment-modal-content"><h3>{selectedProposal.business_document.title}</h3>{selectedProposal.business_document.questions.length > 0 ? <dl className="business-points-list">{selectedProposal.business_document.questions.map((point) => <div key={point.key}><dt>{point.question}</dt><dd>{point.answer || t("overview.noBusinessAnswer")}</dd></div>)}</dl> : <p className="muted">{t("overview.noBusinessPoints")}</p>}{selectedProposal.business_document.manual_content && <div className="assessment-source-block"><strong>{t("overview.manualBusinessContent")}</strong><p>{selectedProposal.business_document.manual_content}</p></div>}</div></section></div>}
    </div>
  );
}

function RelationshipMap({
  products,
  objectives,
    opportunities,
  initiatives,
  proposals,
  translate,
  onViewAssessment,
  onViewBusinessPoints,
}: {
  products: Product[];
  objectives: Objective[];
  opportunities: Opportunity[];
  initiatives: Initiative[];
  proposals: Proposal[];
  translate: (key: string) => string;
  onViewAssessment: (proposal: Proposal) => void;
  onViewBusinessPoints: (proposal: Proposal) => void;
}) {
  const visibleProducts = products.filter((product) => initiatives.some((initiative) => initiative.product_id === product.id) || objectives.some((objective) => objective.product_id === product.id) || opportunities.some((opportunity) => opportunity.product_id === product.id));
  return (
    <section className="relationship-map" aria-label={translate("overview.relationshipMap")}>
      <div className="section-heading"><div><span className="eyebrow">{translate("overview.relationshipEyebrow")}</span><h2>{translate("overview.relationshipTitle")}</h2></div><span className="muted relationship-legend">{translate("overview.relationshipLegend")}</span></div>
      {!visibleProducts.length ? <p className="muted">{translate("overview.noRelationships")}</p> : <div className="relationship-tree">
        {visibleProducts.map((product) => {
          const productInitiatives = initiatives.filter((initiative) => initiative.product_id === product.id);
          return <div className="relationship-branch" key={product.id}>
            <Link className="relationship-node product-node" href="/workspace"><span className="node-kind">{translate("overview.productNode")}</span><strong>{product.name}</strong><small>{product.status}</small></Link>
            <div className="relationship-children">
              {objectives.filter((objective) => objective.product_id === product.id).map((objective) => {
                const objectiveInitiatives = productInitiatives.filter((initiative) => initiative.objective_ids.includes(objective.id));
                const objectiveOpportunities = opportunities.filter((opportunity) => (opportunity.objective_ids ?? []).includes(objective.id));
                return <div className="relationship-leaf" key={objective.id}>
                  <Link className="relationship-node objective-node" href="/workspace/okrs"><span className="node-kind">{translate("overview.objectiveNode")}</span><strong>{objective.title}</strong><small>{objective.key_results.length} {translate("overview.keyResultsLabel")}</small></Link>
                  <div className="relationship-proposals relationship-objective-children">
                    {objectiveOpportunities.map((opportunity) => <Link className="relationship-node opportunity-node" href="/workspace/opportunities" key={opportunity.id}><span className="node-kind">{translate("overview.opportunityNode")}</span><strong>{opportunity.title}</strong><small>{opportunity.status}</small></Link>)}
                    {objectiveInitiatives.map((initiative) => <InitiativeRelationship initiative={initiative} proposals={proposals} translate={translate} onViewAssessment={onViewAssessment} onViewBusinessPoints={onViewBusinessPoints} key={initiative.id} />)}
                  </div>
                </div>;
              })}
              {opportunities.filter((opportunity) => (opportunity.objective_ids ?? []).length === 0).map((opportunity) => <Link className="relationship-node opportunity-node" href="/workspace/opportunities" key={opportunity.id}><span className="node-kind">{translate("overview.opportunityNode")}</span><strong>{opportunity.title}</strong><small>{opportunity.status}</small></Link>)}
              {productInitiatives.filter((initiative) => initiative.objective_ids.length === 0).map((initiative) => <InitiativeRelationship initiative={initiative} proposals={proposals} translate={translate} onViewAssessment={onViewAssessment} onViewBusinessPoints={onViewBusinessPoints} key={initiative.id} />)}
            </div>
          </div>;
        })}
      </div>}
    </section>
  );
}

function InitiativeRelationship({
  initiative,
  proposals,
  translate,
  onViewAssessment,
  onViewBusinessPoints,
}: {
  initiative: Initiative;
  proposals: Proposal[];
  translate: (key: string) => string;
  onViewAssessment: (proposal: Proposal) => void;
  onViewBusinessPoints: (proposal: Proposal) => void;
}) {
  const initiativeProposals = proposals.filter((proposal) => proposal.initiative_id === initiative.id);
  return <div className="relationship-leaf">
    <Link className="relationship-node initiative-node" href={`/initiatives/${initiative.id}/proposals`}><span className="node-kind">{translate("overview.initiativeNode")}</span><strong>{initiative.title}</strong><small>{initiative.status}</small></Link>
    {initiativeProposals.length > 0 && <div className="relationship-proposals">{initiativeProposals.map((proposal) => <div className="relationship-node proposal-node" key={proposal.id}><button className="proposal-business-trigger" type="button" onClick={() => onViewBusinessPoints(proposal)} aria-label={translate("overview.viewBusinessPoints")}><span className="node-kind">{translate("overview.proposalNode")}</span><small>{proposal.status === "APPROVED" ? translate("overview.approvedLabel") : translate("overview.pendingLabel")}</small><span className="proposal-action-label">{translate("overview.viewBusinessPoints")}</span></button><button className="text-link" type="button" onClick={() => onViewAssessment(proposal)}>{translate("overview.viewAssessment")}</button></div>)}</div>}
  </div>;
}

function Signal({ label, value, detail }: { label: string; value: number; detail: string }) {
  return <div className="signal-card"><span>{label}</span><strong>{value}</strong><small>{detail}</small></div>;
}

