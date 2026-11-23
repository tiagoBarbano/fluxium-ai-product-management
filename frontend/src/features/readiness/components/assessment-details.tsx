import type { ReadinessAssessment } from "@/types/api";

export const readinessPointLabels: Record<string, string> = {
  problem: "Problema",
  audience: "Público",
  value: "Proposta de valor",
  evidence: "Evidências",
  solution: "Direção da solução",
  feasibility: "Viabilidade",
  alignment: "Alinhamento estratégico",
  measurement: "Medição",
};

export function AssessmentDetails({
  assessment,
  translate,
}: {
  assessment: ReadinessAssessment;
  translate: (key: string) => string;
}) {
  const manualContent = typeof assessment.source_context.manual_content === "string"
    ? assessment.source_context.manual_content
    : "";
  const submittedContext = assessment.source_context.submitted_context && typeof assessment.source_context.submitted_context === "object"
    ? assessment.source_context.submitted_context as Record<string, unknown>
    : {};
  const readinessDimensions = assessment.source_context.readiness_dimensions ?? submittedContext.readiness_dimensions;
  const dimensionAnswers = readinessDimensions && typeof readinessDimensions === "object"
    ? Object.entries(readinessDimensions as Record<string, unknown>).filter(([, value]) => typeof value === "string" && value.trim())
    : [];

  return (
    <div className="assessment-modal-content">
      <div className="assessment-summary">
        <div><span className="eyebrow">{translate("proposals.score")}</span><strong>{Math.round(assessment.score)}/100</strong></div>
        <div><span className="eyebrow">{translate("proposals.confidence")}</span><strong>{Math.round(assessment.confidence * 100)}%</strong></div>
      </div>
      <div>
        <span className="eyebrow">{translate("proposals.dimensions")}</span>
        <div className="assessment-dimensions">
          {assessment.dimensions.map((dimension) => (
            <div className="assessment-dimension" key={dimension.name}>
              <div><strong>{dimension.name}</strong><span>{Math.round(dimension.score)}/100</span></div>
              <p>{dimension.justification}</p>
            </div>
          ))}
        </div>
      </div>
      <div>
        <span className="eyebrow">{translate("proposals.submittedContext")}</span>
        {manualContent && <div className="assessment-source-block"><strong>{translate("proposals.manualContent")}</strong><p>{manualContent}</p></div>}
        {dimensionAnswers.length > 0 && <div className="assessment-source-block"><strong>{translate("proposals.dimensionAnswers")}</strong><dl>{dimensionAnswers.map(([name, value]) => <div key={name}><dt>{readinessPointLabels[name] ?? name}</dt><dd>{String(value)}</dd></div>)}</dl></div>}
        {!manualContent && !dimensionAnswers.length && <p className="muted">{translate("proposals.noSubmittedContext")}</p>}
      </div>
      <AssessmentList title={translate("proposals.missing")} items={assessment.missing_information} empty={translate("proposals.none")} />
      <AssessmentList title={translate("proposals.questions")} items={assessment.open_questions} empty={translate("proposals.none")} />
    </div>
  );
}

function AssessmentList({ title, items, empty }: { title: string; items: string[]; empty: string }) {
  return <div><span className="eyebrow">{title}</span>{items.length ? <ul>{items.map((item) => <li key={item}>{item}</li>)}</ul> : <p className="muted">{empty}</p>}</div>;
}