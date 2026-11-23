from copy import deepcopy
from collections.abc import Collection

from ..initiatives.domain.entities import Initiative
from ..initiatives.repository import InitiativeRepository
from ..readiness.repository import ReadinessAssessmentRepository
from ...shared.audit.service import AuditService
from ...shared.observability.request_context import get_correlation_id, get_trace_id
from .domain.entities import Proposal
from .domain.enums import ProposalStatus
from .repository import ProposalRepository
from .schemas.requests import CreateProposalRequest


READINESS_QUESTIONS: tuple[tuple[str, str], ...] = (
    ("problem", "Qual problema concreto precisa ser resolvido e para quem?"),
    ("audience", "Quem é afetado, em qual situação e com que frequência?"),
    ("value", "Que mudança de valor esperamos entregar?"),
    ("evidence", "Que fatos, dados, relatos ou observações sustentam o problema?"),
    ("solution", "Que abordagem está sendo considerada e por quê?"),
    ("feasibility", "Quais restrições técnicas, operacionais ou legais existem?"),
    ("alignment", "Qual objetivo estratégico ou resultado esta iniciativa apoia?"),
    ("measurement", "Como saberemos que a iniciativa funcionou?"),
)


class ProposalNotFoundError(LookupError):
    pass


class ProposalAccessError(PermissionError):
    pass


class ProposalConflictError(ValueError):
    pass


class ProposalService:
    def __init__(self, repository: ProposalRepository, initiatives: InitiativeRepository, assessments: ReadinessAssessmentRepository | None = None, audit: AuditService | None = None) -> None:
        self._repository = repository
        self._initiatives = initiatives
        self._assessments = assessments
        self._audit = audit

    async def create(self, request: CreateProposalRequest, tenant_id: str, workspace_ids: Collection[str], created_by: str) -> Proposal:
        initiative = await self._get_initiative(request.initiative_id, tenant_id, workspace_ids)
        if self._assessments is None:
            raise ProposalConflictError("Readiness assessment validation is not configured")
        assessment = await self._assessments.find_by_id(tenant_id, set(workspace_ids), request.assessment_id)
        if assessment is None or assessment.initiative_id != initiative.id:
            raise ProposalNotFoundError("Readiness assessment not found")
        proposal = Proposal.create(
            initiative_id=request.initiative_id,
            assessment_id=request.assessment_id,
            changes=request.changes,
            created_by=created_by,
            expected_initiative_version=request.expected_initiative_version,
            business_document=_business_document_from_assessment(assessment.source_context),
        )
        await self._repository.insert(tenant_id, proposal)
        return proposal

    async def list_for_assessment(
        self,
        initiative_id: str,
        assessment_id: str,
        tenant_id: str,
        workspace_ids: Collection[str],
    ) -> list[Proposal]:
        await self._get_initiative(initiative_id, tenant_id, workspace_ids)
        return await self._repository.list_by_assessment(tenant_id, initiative_id, assessment_id)

    async def list_for_initiative(
        self,
        initiative_id: str,
        tenant_id: str,
        workspace_ids: Collection[str],
        status: ProposalStatus | None,
        limit: int,
    ) -> list[Proposal]:
        await self._get_initiative(initiative_id, tenant_id, workspace_ids)
        return await self._repository.list_by_initiative(tenant_id, initiative_id, status, limit)

    async def list_by_status(
        self,
        status: ProposalStatus,
        tenant_id: str,
        workspace_ids: Collection[str],
        limit: int,
    ) -> list[Proposal]:
        proposals = await self._repository.list_by_status(tenant_id, status, limit)
        visible: list[Proposal] = []
        for proposal in proposals:
            try:
                await self._get_initiative(proposal.initiative_id, tenant_id, workspace_ids)
            except (ProposalNotFoundError, ProposalAccessError):
                continue
            visible.append(proposal)
        return visible

    async def list_filtered(
        self,
        tenant_id: str,
        workspace_ids: Collection[str],
        status: ProposalStatus | None,
        product_id: str | None,
        opportunity_id: str | None,
        initiative_id: str | None,
        limit: int,
    ) -> list[Proposal]:
        if initiative_id:
            initiative = await self._get_initiative(initiative_id, tenant_id, workspace_ids)
            initiatives = [initiative]
        else:
            initiatives = []
            for workspace_id in workspace_ids:
                if product_id:
                    initiatives.extend(await self._initiatives.list_by_product(tenant_id, workspace_id, product_id))
                elif opportunity_id:
                    initiatives.extend(await self._initiatives.list_by_opportunity(tenant_id, workspace_id, opportunity_id))
            if product_id or opportunity_id:
                initiatives = list({initiative.id: initiative for initiative in initiatives}.values())

        if product_id and not initiative_id:
            initiatives = [initiative for initiative in initiatives if initiative.product_id == product_id]
        if opportunity_id and not initiative_id:
            initiatives = [initiative for initiative in initiatives if initiative.opportunity_id == opportunity_id]
        if initiative_id and product_id and initiatives[0].product_id != product_id:
            return []
        if initiative_id and opportunity_id and initiatives[0].opportunity_id != opportunity_id:
            return []
        if not product_id and not opportunity_id and not initiative_id:
            initiatives = [
                initiative
                for workspace_id in workspace_ids
                for initiative in await self._initiatives.list_by_workspace(tenant_id, workspace_id)
            ]
        if not initiatives:
            return []
        return await self._repository.list_by_initiatives(tenant_id, [item.id for item in initiatives], status, limit)

    async def approve(
        self,
        proposal_id: str,
        tenant_id: str,
        workspace_ids: Collection[str],
        decided_by: str,
        decision_reason: str | None = None,
    ) -> Proposal:
        return await self._decide(proposal_id, ProposalStatus.APPROVED, decision_reason, tenant_id, workspace_ids, decided_by)

    async def reject(
        self,
        proposal_id: str,
        tenant_id: str,
        workspace_ids: Collection[str],
        decided_by: str,
        decision_reason: str | None,
    ) -> Proposal:
        if not decision_reason:
            raise ProposalConflictError("A rejection reason is required")
        return await self._decide(proposal_id, ProposalStatus.REJECTED, decision_reason, tenant_id, workspace_ids, decided_by)

    async def _decide(
        self,
        proposal_id: str,
        status: ProposalStatus,
        decision_reason: str | None,
        tenant_id: str,
        workspace_ids: Collection[str],
        decided_by: str,
    ) -> Proposal:
        proposal = await self._repository.find_by_id(tenant_id, proposal_id)
        if proposal is None:
            raise ProposalNotFoundError("Proposal not found")
        if proposal.status is not ProposalStatus.PENDING:
            raise ProposalConflictError("Proposal has already been decided")
        initiative = await self._get_initiative(proposal.initiative_id, tenant_id, workspace_ids)
        if status is ProposalStatus.APPROVED:
            updated_initiative = deepcopy(initiative)
            changes = dict(proposal.changes)
            readiness_score = changes.get("readiness_score")
            if isinstance(readiness_score, (int, float)) and 1 < readiness_score <= 100:
                changes["readiness_score"] = readiness_score / 100
            try:
                updated_initiative.update(expected_version=proposal.expected_initiative_version, **changes)
            except ValueError as exc:
                raise ProposalConflictError(str(exc)) from exc
            if not await self._initiatives.replace(tenant_id, updated_initiative, proposal.expected_initiative_version):
                raise ProposalConflictError("Initiative was updated by another request")
        if not await self._repository.decide(tenant_id, proposal, status, decided_by, decision_reason):
            raise ProposalConflictError("Proposal was updated by another request")
        proposal.decide(status, decided_by, decision_reason)
        if self._audit is not None:
            await self._audit.record(
                tenant_id=tenant_id,
                workspace_id=initiative.workspace_id,
                actor=decided_by,
                action=f"proposal.{status.value.lower()}",
                resource="proposal",
                resource_id=proposal.id,
                before_version=proposal.expected_initiative_version,
                after_version=initiative.version if status is ProposalStatus.APPROVED else initiative.version,
                assessment=proposal.assessment_id,
                correlation_id=get_correlation_id() or None,
                trace_id=get_trace_id() or None,
                metadata={"initiative_id": initiative.id, "decision_reason": decision_reason},
            )
        return proposal

    async def _get_initiative(self, initiative_id: str, tenant_id: str, workspace_ids: Collection[str]) -> Initiative:
        initiative = await self._initiatives.find_by_id(tenant_id, initiative_id)
        if initiative is None:
            raise ProposalNotFoundError("Initiative not found")
        if initiative.workspace_id not in workspace_ids:
            raise ProposalAccessError("Workspace access denied")
        return initiative


def _business_document_from_assessment(source_context: dict[str, object]) -> dict[str, object]:
    submitted_context = source_context.get("submitted_context")
    submitted = submitted_context if isinstance(submitted_context, dict) else {}
    raw_dimensions = source_context.get("readiness_dimensions") or submitted.get("readiness_dimensions")
    dimensions = raw_dimensions if isinstance(raw_dimensions, dict) else {}
    return {
        "title": "Documento de negócio da revisão de prontidão",
        "questions": [
            {"key": key, "question": question, "answer": dimensions.get(key, "")}
            for key, question in READINESS_QUESTIONS
        ],
        "manual_content": source_context.get("manual_content") or submitted.get("manual_content") or "",
    }