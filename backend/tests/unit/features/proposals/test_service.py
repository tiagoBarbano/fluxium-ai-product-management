from datetime import UTC, datetime

import pytest

from app.features.initiatives.domain.entities import Initiative
from app.features.proposals.domain.entities import Proposal
from app.features.proposals.domain.enums import ProposalStatus
from app.features.proposals.schemas.requests import CreateProposalRequest
from app.features.proposals.service import ProposalConflictError, ProposalService, _business_document_from_assessment


class FakeProposalRepository:
    def __init__(self, proposal: Proposal) -> None:
        self.proposal = proposal
        self.decisions: list[tuple[ProposalStatus, str, str | None]] = []

    async def find_by_id(self, tenant_id: str, proposal_id: str) -> Proposal | None:
        return self.proposal if self.proposal.id == proposal_id else None

    async def list_by_assessment(self, tenant_id: str, initiative_id: str, assessment_id: str) -> list[Proposal]:
        return [self.proposal]

    async def list_by_initiative(self, tenant_id: str, initiative_id: str, status: ProposalStatus | None, limit: int) -> list[Proposal]:
        if status is not None and self.proposal.status is not status:
            return []
        return [self.proposal][:limit]

    async def decide(self, tenant_id: str, proposal: Proposal, status: ProposalStatus, decided_by: str, reason: str | None) -> bool:
        self.decisions.append((status, decided_by, reason))
        return True


class FakeInitiativeRepository:
    def __init__(self, initiative: Initiative, replace_result: bool = True) -> None:
        self.initiative = initiative
        self.replace_result = replace_result
        self.replacements: list[int] = []

    async def find_by_id(self, tenant_id: str, initiative_id: str) -> Initiative | None:
        return self.initiative if self.initiative.id == initiative_id else None

    async def replace(self, tenant_id: str, initiative: Initiative, expected_version: int) -> bool:
        self.replacements.append(expected_version)
        if self.replace_result:
            self.initiative = initiative
        return self.replace_result


class FakeAuditService:
    def __init__(self) -> None:
        self.events = []

    async def record(self, **kwargs):
        self.events.append(kwargs)


def _initiative() -> Initiative:
    return Initiative.create(
        initiative_id="initiative-1",
        workspace_id="workspace-1",
        product_id="product-1",
        opportunity_id="opportunity-1",
        title="Old title",
        objective="Old objective",
        scope="Old scope",
        created_by="creator-1",
        now=datetime.now(UTC),
    )


def _proposal(initiative: Initiative) -> Proposal:
    return Proposal.create(
        proposal_id="proposal-1",
        initiative_id=initiative.id,
        assessment_id="assessment-1",
        changes={"objective": "New objective"},
        created_by="assistant-1",
        expected_initiative_version=initiative.version,
        now=datetime.now(UTC),
    )


@pytest.mark.asyncio
async def test_approval_applies_structured_changes_with_expected_version() -> None:
    initiative = _initiative()
    proposals = FakeProposalRepository(_proposal(initiative))
    initiatives = FakeInitiativeRepository(initiative)
    service = ProposalService(proposals, initiatives)

    result = await service.approve("proposal-1", "tenant-1", {"workspace-1"}, "manager-1")

    assert result.status is ProposalStatus.APPROVED
    assert initiatives.initiative.objective == "New objective"
    assert initiatives.initiative.version == 2
    assert initiatives.replacements == [1]
    assert proposals.decisions == [(ProposalStatus.APPROVED, "manager-1", None)]


@pytest.mark.asyncio
async def test_lists_initiative_proposals_with_optional_status_filter() -> None:
    initiative = _initiative()
    proposal = _proposal(initiative)
    proposal.decide(ProposalStatus.REJECTED, "manager-1", "Not aligned")
    service = ProposalService(FakeProposalRepository(proposal), FakeInitiativeRepository(initiative))

    history = await service.list_for_initiative("initiative-1", "tenant-1", {"workspace-1"}, None, 50)
    pending = await service.list_for_initiative("initiative-1", "tenant-1", {"workspace-1"}, ProposalStatus.PENDING, 50)

    assert history == [proposal]
    assert pending == []


@pytest.mark.asyncio
async def test_approval_normalizes_legacy_readiness_score_percentage() -> None:
    initiative = _initiative()
    proposal = _proposal(initiative)
    proposal.changes = {"readiness_score": 72}
    proposals = FakeProposalRepository(proposal)
    initiatives = FakeInitiativeRepository(initiative)
    service = ProposalService(proposals, initiatives)

    result = await service.approve("proposal-1", "tenant-1", {"workspace-1"}, "manager-1")

    assert result.status is ProposalStatus.APPROVED
    assert initiatives.initiative.readiness_score == 0.72


@pytest.mark.asyncio
async def test_rejection_is_recorded_without_changing_initiative() -> None:
    initiative = _initiative()
    proposal = _proposal(initiative)
    proposals = FakeProposalRepository(proposal)
    initiatives = FakeInitiativeRepository(initiative)
    service = ProposalService(proposals, initiatives)

    result = await service.reject("proposal-1", "tenant-1", {"workspace-1"}, "manager-1", "Not aligned")

    assert result.status is ProposalStatus.REJECTED
    assert result.decision_reason == "Not aligned"
    assert initiative.objective == "Old objective"
    assert initiative.version == 1
    assert initiatives.replacements == []


@pytest.mark.asyncio
async def test_approval_returns_conflict_when_initiative_version_is_obsolete() -> None:
    initiative = _initiative()
    proposal = _proposal(initiative)
    proposal.expected_initiative_version = 0
    proposals = FakeProposalRepository(proposal)
    service = ProposalService(proposals, FakeInitiativeRepository(initiative))

    with pytest.raises(ProposalConflictError):
        await service.approve("proposal-1", "tenant-1", {"workspace-1"}, "manager-1")

    assert proposal.status is ProposalStatus.PENDING


@pytest.mark.asyncio
async def test_approval_does_not_mutate_initiative_when_replace_fails() -> None:
    initiative = _initiative()
    proposal = _proposal(initiative)
    service = ProposalService(
        FakeProposalRepository(proposal),
        FakeInitiativeRepository(initiative, replace_result=False),
    )

    with pytest.raises(ProposalConflictError, match="updated by another request"):
        await service.approve("proposal-1", "tenant-1", {"workspace-1"}, "manager-1")

    assert initiative.objective == "Old objective"
    assert initiative.version == 1
    assert proposal.status is ProposalStatus.PENDING


@pytest.mark.asyncio
async def test_rejection_requires_a_reason() -> None:
    initiative = _initiative()
    service = ProposalService(FakeProposalRepository(_proposal(initiative)), FakeInitiativeRepository(initiative))

    with pytest.raises(ProposalConflictError, match="reason"):
        await service.reject("proposal-1", "tenant-1", {"workspace-1"}, "manager-1", None)


@pytest.mark.asyncio
async def test_decision_records_audit_event() -> None:
    initiative = _initiative()
    audit = FakeAuditService()
    service = ProposalService(
        FakeProposalRepository(_proposal(initiative)),
        FakeInitiativeRepository(initiative),
        audit=audit,
    )

    await service.reject("proposal-1", "tenant-1", {"workspace-1"}, "manager-1", "Not aligned")

    assert audit.events[0]["action"] == "proposal.rejected"
    assert audit.events[0]["resource_id"] == "proposal-1"


def test_create_request_rejects_unstructured_initiative_fields() -> None:
    with pytest.raises(ValueError, match="Unsupported"):
        CreateProposalRequest(
            initiative_id="initiative-1",
            assessment_id="assessment-1",
            changes={"created_by": "attacker"},
            expected_initiative_version=1,
        )


def test_business_document_contains_all_readiness_questions_and_answers() -> None:
    document = _business_document_from_assessment({
        "readiness_dimensions": {"problem": "Users cannot complete checkout"},
        "manual_content": "Business context",
    })

    assert len(document["questions"]) == 8
    assert document["questions"][0] == {
        "key": "problem",
        "question": "Qual problema concreto precisa ser resolvido e para quem?",
        "answer": "Users cannot complete checkout",
    }
    assert document["manual_content"] == "Business context"