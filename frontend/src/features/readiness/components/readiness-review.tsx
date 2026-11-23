"use client";

import { useEffect, useState } from "react";
import type { Initiative } from "@/features/initiatives/services/initiative-service";
import type {
  Proposal,
  ReadinessAssessment,
  ReadinessAssessmentJob,
} from "@/types/api";
import { ApiError } from "@/lib/http";
import { getInitiative } from "@/features/initiatives/services/initiative-service";
import {
  approveProposal,
  createProposal,
  createReadinessJob,
  getReadinessAssessment,
  getReadinessJob,
  listProposals,
  rejectProposal,
  retryReadinessJob,
} from "../services/readiness-service";
import { useI18n } from "@/components/i18n-provider";

const dimensions = [
  [
    "problem",
    "Clareza do problema",
    "Qual problema concreto precisa ser resolvido e para quem?",
  ],
  [
    "audience",
    "Público",
    "Quem é afetado, em qual situação e com que frequência?",
  ],
  ["value", "Proposta de valor", "Que mudança de valor esperamos entregar?"],
  [
    "evidence",
    "Evidências",
    "Que fatos, dados, relatos ou observações sustentam o problema?",
  ],
  [
    "solution",
    "Direção da solução",
    "Que abordagem está sendo considerada e por quê?",
  ],
  [
    "feasibility",
    "Viabilidade",
    "Quais restrições técnicas, operacionais ou legais existem?",
  ],
  [
    "alignment",
    "Alinhamento estratégico",
    "Qual objetivo estratégico ou resultado esta iniciativa apoia?",
  ],
  ["measurement", "Medição", "Como saberemos que a iniciativa funcionou?"],
] as const;
const labels: Record<string, string> = Object.fromEntries(
  dimensions.map(([key, label]) => [key, label]),
);
const initialDimensionContext = Object.fromEntries(
  dimensions.map(([key]) => [key, ""]),
);
type ReadinessTab = "context" | "review" | "result";

export function ReadinessReview({ initiativeId }: { initiativeId: string }) {
  const { t, locale } = useI18n();
  const [job, setJob] = useState<ReadinessAssessmentJob | null>(null);
  const [assessment, setAssessment] = useState<ReadinessAssessment | null>(
    null,
  );
  const [manualContent, setManualContent] = useState("");
  const [dimensionContext, setDimensionContext] = useState<Record<string, string>>(
    initialDimensionContext,
  );
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [proposals, setProposals] = useState<Proposal[]>([]);
  const [proposalBusy, setProposalBusy] = useState(false);
  const [initiative, setInitiative] = useState<Initiative | null>(null);
  const [activeTab, setActiveTab] = useState<ReadinessTab>("review");

  useEffect(() => {
    let active = true;
    getInitiative(initiativeId)
      .then((loadedInitiative) => {
        if (active) setInitiative(loadedInitiative);
      })
      .catch(() => undefined);
    return () => {
      active = false;
    };
  }, [initiativeId]);

  useEffect(() => {
    if (!job || job.state === "SUCCEEDED" || job.state === "FAILED") return;
    const timer = window.setInterval(async () => {
      try {
        const next = await getReadinessJob(job.job_id);
        setJob(next);
        if (next.assessment_id) {
          setAssessment(await getReadinessAssessment(next.assessment_id));
          setActiveTab("result");
        }
      } catch (requestError) {
        setError(errorMessage(requestError));
      }
    }, 2000);
    return () => window.clearInterval(timer);
  }, [job]);

  useEffect(() => {
    if (!assessment) return;
    let active = true;
    listProposals(assessment.initiative_id, assessment.id)
      .then((items) => {
        if (active) setProposals(items);
      })
      .catch((requestError) => {
        if (active) setError(errorMessage(requestError));
      });
    return () => {
      active = false;
    };
  }, [assessment]);

  async function submit() {
    setError(null);
    setAssessment(null);
    setProposals([]);
    setActiveTab("review");
    setSubmitting(true);
    try {
      const created = await createReadinessJob(initiativeId, {
        context: {
          initiative_id: initiativeId,
          readiness_dimensions: dimensionContext,
        },
        context_version: "mvp-v2",
        prompt_version: "readiness-v2",
        language: locale,
        manual_content: manualContent || undefined,
      });
      setJob(created);
      if (created.assessment_id) {
        setAssessment(await getReadinessAssessment(created.assessment_id));
        setActiveTab("result");
      }
    } catch (requestError) {
      setError(errorMessage(requestError));
    } finally {
      setSubmitting(false);
    }
  }
  async function retry() {
    if (!job) return;
    setError(null);
    try {
      setJob(await retryReadinessJob(job.job_id));
    } catch (requestError) {
      setError(errorMessage(requestError, "proposal"));
    }
  }
  async function proposeAssessment() {
    if (!assessment) return;
    setProposalBusy(true);
    setError(null);
    try {
      const initiative = await getInitiative(assessment.initiative_id);
      const proposal = await createProposal({
        initiative_id: assessment.initiative_id,
        assessment_id: assessment.id,
        changes: {
          readiness_score: assessment.score / 100,
          readiness_confidence: assessment.confidence,
        },
        expected_initiative_version: initiative.version,
      });
      setProposals((current) => [...current, proposal]);
    } catch (requestError) {
        setError(errorMessage(requestError, "proposal"));
    } finally {
      setProposalBusy(false);
    }
  }
  async function decideProposal(
    proposalId: string,
    decision: "approve" | "reject",
  ) {
    const reason =
      decision === "reject"
        ? window.prompt(t("readiness.rejectReason"))?.trim()
        : undefined;
    if (decision === "reject" && !reason) return;
    setProposalBusy(true);
    setError(null);
    try {
      const proposal =
        decision === "approve"
          ? await approveProposal(proposalId)
          : await rejectProposal(proposalId, reason as string);
      setProposals((current) =>
        current.map((item) => (item.id === proposal.id ? proposal : item)),
      );
    } catch (requestError) {
        setError(errorMessage(requestError, "proposal"));
    } finally {
      setProposalBusy(false);
    }
  }
  const working = job?.state === "PENDING" || job?.state === "RUNNING";

  function reviewContext() {
    document
      .getElementById("manual-content")
      ?.scrollIntoView({ behavior: "smooth", block: "center" });
    document.getElementById("manual-content")?.focus();
  }

  return (
    <div className="stack-lg">
      <section className="hero-panel">
        <div>
          <span className="eyebrow">
            {t("readiness.support", { id: initiative?.title ?? initiativeId })}
          </span>
          <small className="muted entity-id">{initiativeId}</small>
          <h1>{t("readiness.title")}</h1>
          <p>{t("readiness.description")}</p>
        </div>
        <div className="hero-mark" aria-hidden="true">
          R<span>R</span>
        </div>
      </section>
      <div className="readiness-tabs" role="tablist" aria-label={t("readiness.tabs") }>
        <ReadinessTabButton active={activeTab === "context"} label={t("readiness.contextTab")} number="01" onClick={() => setActiveTab("context")} />
        <ReadinessTabButton active={activeTab === "review"} label={t("readiness.reviewTab")} number="02" onClick={() => setActiveTab("review")} />
        <ReadinessTabButton active={activeTab === "result"} disabled={!assessment} label={t("readiness.resultTab")} number="03" onClick={() => setActiveTab("result")} />
      </div>
      {activeTab === "context" && <section className="panel readiness-initiative-context">
        <div className="panel-heading">
          <div>
            <span className="eyebrow">{t("readiness.initiativeContext")}</span>
            <h2>{initiative?.title ?? initiativeId}</h2>
          </div>
          {initiative && <span className="context-chip">{initiative.status}</span>}
        </div>
        <dl>
          <div><dt>{t("readiness.objective")}</dt><dd>{initiative?.objective ?? t("readiness.contextLoading")}</dd></div>
          <div><dt>{t("readiness.scope")}</dt><dd>{initiative?.scope ?? t("readiness.contextLoading")}</dd></div>
        </dl>
      </section>}
      {activeTab === "review" && <section className="review-grid">
        <div className="panel request-panel">
          <div className="panel-heading">
            <div>
              <span className="eyebrow">{t("readiness.start")}</span>
              <h2>{t("readiness.question")}</h2>
            </div>
            <span className="status-dot" />
          </div>
          <p className="muted">{t("readiness.dimensionGuide")}</p>
          <div className="dimension-guide">
            {dimensions.map(([key, label, question]) => (
              <label key={key} htmlFor={`dimension-${key}`}>
                <span>{label}</span>
                <small>{question}</small>
                <textarea
                  id={`dimension-${key}`}
                  value={dimensionContext[key] ?? ""}
                  onChange={(event) =>
                    setDimensionContext((current) => ({
                      ...current,
                      [key]: event.target.value,
                    }))
                  }
                  placeholder={t("readiness.dimensionPlaceholder")}
                />
              </label>
            ))}
          </div>
          <label htmlFor="manual-content">
            {t("readiness.context")} <span>{t("readiness.optional")}</span>
          </label>
          <textarea
            id="manual-content"
            value={manualContent}
            onChange={(event) => setManualContent(event.target.value)}
            placeholder={t("readiness.placeholder")}
          />
          <div className="source-note">
            <span className="source-icon">i</span>
            <span>{t("readiness.aiNote")}</span>
          </div>
          <button
            className="primary-button"
            type="button"
            onClick={submit}
            disabled={submitting || working}
          >
            {submitting
              ? t("readiness.submitting")
              : working
                ? t("readiness.working")
                : t("readiness.submit")}
            <span aria-hidden="true">↗</span>
          </button>
          {error && (
            <div className="error-box" role="alert">
              {error}
              <button
                type="button"
                onClick={() => setError(null)}
                aria-label={t("readiness.dismiss")}
              >
                ×
              </button>
            </div>
          )}
        </div>
        <div className="panel progress-panel">
          <div className="panel-heading">
            <div>
              <span className="eyebrow">{t("readiness.status")}</span>
              <h2>{job ? statusLabel(job.state) : t("readiness.ready")}</h2>
            </div>
            {job && (
              <span className={`pill ${job.state.toLowerCase()}`}>
                {job.state}
              </span>
            )}
          </div>
          {!job ? (
            <div className="empty-state">
              <div className="empty-number">01</div>
              <p>{t("readiness.empty")}</p>
            </div>
          ) : (
            <>
              <div className="progress-track">
                <span className={`progress-fill ${job.state.toLowerCase()}`} />
              </div>
              <p className="muted">
                {job.state === "FAILED"
                  ? (job.error ?? t("readiness.failed"))
                  : job.state === "SUCCEEDED"
                    ? t("readiness.succeeded")
                    : t("readiness.processing")}
              </p>
              <dl className="job-meta">
                <div>
                  <dt>{t("readiness.job")}</dt>
                  <dd>{job.job_id.slice(0, 8)}...</dd>
                </div>
                <div>
                  <dt>{t("readiness.retry")}</dt>
                  <dd>{job.retry_count}</dd>
                </div>
                <div>
                  <dt>{t("readiness.correlation")}</dt>
                  <dd>{job.correlation_id.slice(0, 8)}...</dd>
                </div>
              </dl>
              {job.state === "FAILED" && (
                <button
                  className="secondary-button"
                  type="button"
                  onClick={retry}
                >
                  {t("readiness.retryReview")}
                </button>
              )}
            </>
          )}
        </div>
      </section>}
      {activeTab === "result" && assessment && (
        <AssessmentResult
          assessment={assessment}
          proposals={proposals}
          proposalBusy={proposalBusy}
          error={error}
          onReviewContext={reviewContext}
          onRunAgain={submit}
          onPropose={proposeAssessment}
          onDecide={decideProposal}
        />
      )}
      {activeTab === "result" && !assessment && <section className="panel empty-state readiness-result-empty"><p>{t("readiness.resultEmpty")}</p><button className="secondary-button" type="button" onClick={() => setActiveTab("review")}>{t("readiness.reviewTab")}</button></section>}
    </div>
  );
}

function ReadinessTabButton({ active, disabled, label, number, onClick }: { active: boolean; disabled?: boolean; label: string; number: string; onClick: () => void }) {
  return <button className={`readiness-tab${active ? " is-active" : ""}`} role="tab" aria-selected={active} disabled={disabled} type="button" onClick={onClick}><span>{number}</span>{label}{active && <i aria-hidden="true" />}</button>;
}

function AssessmentResult({
  assessment,
  proposals,
  proposalBusy,
  error,
  onReviewContext,
  onRunAgain,
  onPropose,
  onDecide,
}: {
  assessment: ReadinessAssessment;
  proposals: Proposal[];
  proposalBusy: boolean;
  error: string | null;
  onReviewContext: () => void;
  onRunAgain: () => void;
  onPropose: () => void;
  onDecide: (proposalId: string, decision: "approve" | "reject") => void;
}) {
  const { t, locale } = useI18n();
  const pendingProposal = proposals.find(
    (proposal) => proposal.status === "PENDING",
  );
  return (
    <section className="stack-lg" aria-live="polite">
      <div className="result-header">
        <div>
          <span className="eyebrow">
            Avaliação /{" "}
            {new Date(assessment.created_at).toLocaleDateString(locale)}
          </span>
          <h2>{t("readiness.signal")}</h2>
        </div>
        <div className="score-lockup">
          <strong>{Math.round(assessment.score)}</strong>
          <span>{t("readiness.readinessScore")}</span>
        </div>
      </div>
      <div className="assessment-grid">
        <div className="panel score-panel">
          <span className="eyebrow">{t("readiness.confidence")}</span>
          <div className="confidence-value">
            {Math.round(assessment.confidence * 100)}
            <small>%</small>
          </div>
          <p>{t("readiness.confidenceDescription")}</p>
          <span className="model-tag">
            {assessment.provider} / {assessment.model}
          </span>
        </div>
        <div className="panel dimensions-panel">
          <div className="panel-heading">
            <div>
              <span className="eyebrow">{t("readiness.dimensions")}</span>
              <h2>{t("readiness.signalSource")}</h2>
            </div>
          </div>
          <div className="dimension-list">
            {assessment.dimensions.map((dimension) => (
              <div className="dimension-row" key={dimension.name}>
                <div className="dimension-name">
                  <span>{labels[dimension.name] ?? dimension.name}</span>
                  <strong>{Math.round(dimension.score)}</strong>
                </div>
                <div className="dimension-track">
                  <span style={{ width: `${dimension.score}%` }} />
                </div>
                <p>{dimension.justification}</p>
              </div>
            ))}
          </div>
        </div>
      </div>
      <div className="insight-grid">
        <InsightList
          title={t("readiness.missing")}
          items={assessment.missing_information}
          tone="amber"
        />
        <InsightList
          title={t("readiness.questions")}
          items={assessment.open_questions}
          tone="coral"
        />
      </div>
      <div className="panel">
        <div className="panel-heading">
          <div>
            <span className="eyebrow">{t("readiness.proposal")}</span>
            <h2>
              {pendingProposal
                ? t("readiness.proposalPending")
                : t("readiness.proposalQuestion")}
            </h2>
          </div>
          {pendingProposal && <span className="pill pending">PENDING</span>}
        </div>
        {pendingProposal ? (
          <div className="stack-lg">
            <p className="muted">{t("readiness.proposalChanges")}</p>
            {error && <div className="error-box" role="alert">{error}</div>}
            <button
              className="primary-button"
              type="button"
              disabled={proposalBusy}
              onClick={() => onDecide(pendingProposal.id, "approve")}
            >
              {t("readiness.approveProposal")}
            </button>
            <button
              className="secondary-button"
              type="button"
              disabled={proposalBusy}
              onClick={() => onDecide(pendingProposal.id, "reject")}
            >
              {t("readiness.rejectProposal")}
            </button>
          </div>
        ) : proposals.length ? (
          <p className="muted">{t("readiness.proposalDecided")}</p>
        ) : (
          <button
            className="primary-button"
            type="button"
            disabled={proposalBusy}
            onClick={onPropose}
          >
            {t("readiness.proposeUpdate")}
            <span aria-hidden="true">↗</span>
          </button>
        )}
      </div>
      <div className="stack-lg">
        <button
          className="secondary-button"
          type="button"
          onClick={onReviewContext}
        >
          {t("readiness.reviewContext")}
        </button>
        <button className="primary-button" type="button" onClick={onRunAgain}>
          {t("readiness.runAgain")}
          <span aria-hidden="true">↗</span>
        </button>
      </div>
    </section>
  );
}
function InsightList({
  title,
  items,
  tone,
}: {
  title: string;
  items: string[];
  tone: string;
}) {
  const { t } = useI18n();
  return (
    <div className={`panel insight-panel ${tone}`}>
      <span className="eyebrow">{t("readiness.attention")}</span>
      <h2>{title}</h2>
      {items.length ? (
        <ul>
          {items.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      ) : (
        <p className="muted">{t("readiness.nothing")}</p>
      )}
    </div>
  );
}
function statusLabel(state: string) {
  return state === "PENDING"
    ? "Na fila para revisão"
    : state === "RUNNING"
      ? "Lendo seu contexto"
      : state === "SUCCEEDED"
        ? "Avaliação concluída"
        : "A revisão requer atenção";
}
function errorMessage(error: unknown, area: "review" | "proposal" = "review") {
  if (error instanceof ApiError && error.status === 401)
    return "É necessário entrar para executar uma revisão.";
  if (error instanceof ApiError && error.status === 403)
    return area === "proposal"
      ? "A aprovação exige o papel ADMIN ou PRODUCT_MANAGER."
      : "Você não tem permissão para revisar esta iniciativa.";
  return error instanceof Error
    ? error.message
    : "Não foi possível concluir a solicitação.";
}
