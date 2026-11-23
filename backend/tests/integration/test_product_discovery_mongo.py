import asyncio
import copy
import os
from uuid import uuid4

import pytest
from pymongo import AsyncMongoClient

from app.features.business_problems.domain.entities import BusinessProblem
from app.features.business_problems.repository import MongoBusinessProblemRepository
from app.features.discovery.domain.entities import DiscoverySession
from app.features.discovery.domain.enums import DiscoverySessionStatus
from app.features.discovery.repository import MongoDiscoveryRepository
from app.features.discovery.schemas.requests import CreateDiscoveryMessageRequest
from app.features.discovery.service import DiscoveryConflictError, DiscoveryService
from app.features.evidence.domain.entities import Evidence
from app.features.evidence.domain.enums import EvidenceOrigin, EvidenceType
from app.features.evidence.repository import (
    MongoEvidenceRepository,
    MongoHypothesisReferenceRepository,
    MongoProblemReferenceRepository,
)
from app.features.evidence.schemas.requests import CreateEvidenceRequest
from app.features.evidence.service import EvidenceReferenceError, EvidenceService
from app.features.hypotheses.domain.entities import Hypothesis
from app.features.hypotheses.repository import MongoHypothesisRepository
from app.features.opportunities.domain.entities import Opportunity
from app.features.opportunities.domain.enums import OpportunityStatus
from app.features.opportunities.repository import MongoOpportunityRepository


pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(
        os.getenv("FLUXIUM_RUN_MONGO_INTEGRATION") != "1",
        reason="Set FLUXIUM_RUN_MONGO_INTEGRATION=1 to run MongoDB integration tests",
    ),
]


@pytest.fixture
async def mongo_database():
    database_name = f"fluxium_product_test_{uuid4().hex}"
    client = AsyncMongoClient(
        os.getenv("FLUXIUM_MONGO_URI", "mongodb://localhost:27017/?replicaSet=rs0"),
        tz_aware=True,
    )
    database = client[database_name]
    try:
        yield database
    finally:
        await client.drop_database(database_name)
        await client.close()


def make_opportunity(
    opportunity_id: str,
    *,
    tenant_id: str = "tenant-a",
    workspace_id: str = "workspace-a",
) -> Opportunity:
    del tenant_id
    return Opportunity(
        id=opportunity_id,
        product_id="product-1",
        title="Reduce onboarding friction",
        description="New users struggle to complete onboarding.",
        workspace_id=workspace_id,
        created_by="user-1",
    )


async def build_repositories(database):
    opportunities = MongoOpportunityRepository(database["opportunities"])
    problems = MongoBusinessProblemRepository(database["business_problems"])
    discovery = MongoDiscoveryRepository(
        database["discovery_sessions"], database["discovery_messages"]
    )
    evidence = MongoEvidenceRepository(database["evidence"])
    hypotheses = MongoHypothesisRepository(database["hypotheses"])
    await asyncio.gather(
        opportunities.ensure_indexes(),
        problems.ensure_indexes(),
        discovery.ensure_indexes(),
        evidence.ensure_indexes(),
        hypotheses.ensure_indexes(),
    )
    return opportunities, problems, discovery, evidence, hypotheses


async def index_names(collection) -> set[str]:
    cursor = await collection.list_indexes()
    return {index["name"] async for index in cursor}


@pytest.mark.asyncio
async def test_mongodb_indexes_cover_tenant_workspace_access_patterns(mongo_database) -> None:
    await build_repositories(mongo_database)

    assert "ix_opportunities_tenant_workspace_id" in await index_names(mongo_database["opportunities"])
    assert "ix_business_problems_tenant_workspace_id" in await index_names(mongo_database["business_problems"])
    assert "ix_business_problems_tenant_workspace_opportunity" in await index_names(mongo_database["business_problems"])
    assert "ix_discovery_sessions_scope" in await index_names(mongo_database["discovery_sessions"])
    assert "ux_discovery_sessions_active_opportunity" in await index_names(mongo_database["discovery_sessions"])
    assert "ux_discovery_messages_sequence" in await index_names(mongo_database["discovery_messages"])
    assert "ix_evidence_tenant_workspace_opportunity_created" in await index_names(mongo_database["evidence"])
    assert "ix_evidence_tenant_workspace_problem" in await index_names(mongo_database["evidence"])
    assert "ix_hypotheses_tenant_workspace_opportunity_created" in await index_names(mongo_database["hypotheses"])


@pytest.mark.asyncio
async def test_mongodb_filters_isolate_tenant_and_workspace(mongo_database) -> None:
    opportunities, problems, discovery, evidence, hypotheses = await build_repositories(mongo_database)
    opportunity = make_opportunity("opportunity-1")
    await opportunities.insert("tenant-a", opportunity)

    problem = BusinessProblem.create(
        workspace_id="workspace-a",
        product_id=opportunity.product_id,
        opportunity_id=opportunity.id,
        description="Users abandon onboarding.",
        audience="New users",
        reported_impact="Lost activation",
        created_by="user-1",
        problem_id="problem-1",
    )
    await problems.insert("tenant-a", problem)

    session = DiscoverySession(
        opportunity_id=opportunity.id,
        workspace_id="workspace-a",
        created_by="user-1",
        id="session-1",
    )
    await discovery.insert_session("tenant-a", session)

    hypothesis = Hypothesis.create(
        workspace_id="workspace-a",
        opportunity_id=opportunity.id,
        statement="Guided onboarding improves activation.",
        expected_behavior="Users complete the setup flow.",
        expected_outcome="Activation increases.",
        evidence_ids=[],
        confidence=0.5,
        created_by="user-1",
        hypothesis_id="hypothesis-1",
    )
    await hypotheses.insert("tenant-a", hypothesis)

    evidence_item = Evidence.create(
        workspace_id="workspace-a",
        opportunity_id=opportunity.id,
        problem_id=problem.id,
        hypothesis_id=hypothesis.id,
        evidence_type=EvidenceType.INTERVIEW,
        origin=EvidenceOrigin.MANUAL,
        description="Three users reported the same onboarding issue.",
        created_by="user-1",
        evidence_id="evidence-1",
    )
    await evidence.insert("tenant-a", evidence_item)

    assert await opportunities.find_by_id("tenant-b", opportunity.id) is None
    assert await opportunities.list_by_workspace("tenant-a", "workspace-b") == []
    assert await problems.find_by_id("tenant-a", {"workspace-b"}, problem.id) is None
    assert await discovery.find_session("tenant-b", session.id) is None
    assert await evidence.list_by_problem("tenant-a", "workspace-b", problem.id) == []
    assert await hypotheses.list_by_opportunity("tenant-a", "workspace-b", opportunity.id) == []


@pytest.mark.asyncio
async def test_opportunity_transition_is_optimistic_and_atomic(mongo_database) -> None:
    opportunities, *_ = await build_repositories(mongo_database)
    opportunity = make_opportunity("opportunity-transition")
    await opportunities.insert("tenant-a", opportunity)

    results = await asyncio.gather(
        opportunities.transition_new_to_discovery("tenant-a", opportunity.id, 1),
        opportunities.transition_new_to_discovery("tenant-a", opportunity.id, 1),
    )

    assert sum(result is not None for result in results) == 1
    stored = await opportunities.find_by_id("tenant-a", opportunity.id)
    assert stored is not None
    assert stored.status is OpportunityStatus.DISCOVERY
    assert stored.version == 2


@pytest.mark.asyncio
async def test_business_problem_and_hypothesis_replacements_reject_stale_versions(mongo_database) -> None:
    opportunities, problems, _, evidence, hypotheses = await build_repositories(mongo_database)
    opportunity = make_opportunity("opportunity-concurrency")
    await opportunities.insert("tenant-a", opportunity)

    problem = BusinessProblem.create(
        workspace_id="workspace-a",
        product_id=opportunity.product_id,
        opportunity_id=opportunity.id,
        description="Users abandon onboarding.",
        audience="New users",
        reported_impact="Lost activation",
        created_by="user-1",
        problem_id="problem-concurrency",
    )
    await problems.insert("tenant-a", problem)
    problem_update_a = copy.deepcopy(problem)
    problem_update_b = copy.deepcopy(problem)
    problem_update_a.update(expected_version=1, description="Users abandon setup.")
    problem_update_b.update(expected_version=1, description="Users cannot find setup.")
    problem_results = await asyncio.gather(
        problems.replace("tenant-a", problem_update_a, 1),
        problems.replace("tenant-a", problem_update_b, 1),
    )

    assert sorted(problem_results) == [False, True]
    stored_problem = await problems.find_by_id("tenant-a", {"workspace-a"}, problem.id)
    assert stored_problem is not None
    assert stored_problem.version == 2

    hypothesis = Hypothesis.create(
        workspace_id="workspace-a",
        opportunity_id=opportunity.id,
        statement="Guided onboarding improves activation.",
        expected_behavior="Users complete setup.",
        expected_outcome="Activation increases.",
        evidence_ids=[],
        confidence=0.5,
        created_by="user-1",
        hypothesis_id="hypothesis-concurrency",
    )
    await hypotheses.insert("tenant-a", hypothesis)
    hypothesis_update_a = copy.deepcopy(hypothesis)
    hypothesis_update_b = copy.deepcopy(hypothesis)
    hypothesis_update_a.update(expected_version=1, confidence=0.7)
    hypothesis_update_b.update(expected_version=1, confidence=0.9)
    hypothesis_results = await asyncio.gather(
        hypotheses.replace("tenant-a", hypothesis_update_a, 1),
        hypotheses.replace("tenant-a", hypothesis_update_b, 1),
    )

    assert sorted(hypothesis_results) == [False, True]
    stored_hypothesis = await hypotheses.find_by_id("tenant-a", hypothesis.id)
    assert stored_hypothesis is not None
    assert stored_hypothesis.version == 2
    assert await evidence.find_by_id("tenant-a", "missing-evidence") is None


@pytest.mark.asyncio
async def test_discovery_service_transitions_opportunity_and_persists_messages(mongo_database) -> None:
    opportunities, _, discovery, _, _ = await build_repositories(mongo_database)
    opportunity = make_opportunity("opportunity-discovery")
    await opportunities.insert("tenant-a", opportunity)
    service = DiscoveryService(discovery, opportunities)

    session = await service.start(
        opportunity.id,
        "tenant-a",
        "user-1",
        {"workspace-a"},
    )
    message = await service.add_message(
        session.id,
        CreateDiscoveryMessageRequest(content="Who is affected?"),
        "tenant-a",
        "user-1",
        {"workspace-a"},
    )
    stored_opportunity = await opportunities.find_by_id("tenant-a", opportunity.id)
    stored_session, messages = await service.get(session.id, "tenant-a", {"workspace-a"})

    assert stored_opportunity is not None
    assert stored_opportunity.status is OpportunityStatus.DISCOVERY
    assert stored_session.status is DiscoverySessionStatus.ACTIVE
    assert [(item.sequence, item.content) for item in messages] == [(1, message.content)]
    with pytest.raises(DiscoveryConflictError):
        await service.start(opportunity.id, "tenant-a", "user-1", {"workspace-a"})


@pytest.mark.asyncio
async def test_evidence_links_problem_and_opportunity_and_rejects_cross_scope_reference(mongo_database) -> None:
    opportunities, problems, _, evidence, hypotheses = await build_repositories(mongo_database)
    opportunity = make_opportunity("opportunity-evidence")
    await opportunities.insert("tenant-a", opportunity)
    problem = BusinessProblem.create(
        workspace_id="workspace-a",
        product_id=opportunity.product_id,
        opportunity_id=opportunity.id,
        description="Users abandon onboarding.",
        audience="New users",
        reported_impact="Lost activation",
        created_by="user-1",
        problem_id="problem-evidence",
    )
    await problems.insert("tenant-a", problem)
    hypothesis = Hypothesis.create(
        workspace_id="workspace-a",
        opportunity_id=opportunity.id,
        statement="Guidance improves activation.",
        expected_behavior="Users finish setup.",
        expected_outcome="Activation increases.",
        evidence_ids=[],
        confidence=0.6,
        created_by="user-1",
        hypothesis_id="hypothesis-evidence",
    )
    await hypotheses.insert("tenant-a", hypothesis)
    service = EvidenceService(
        evidence,
        opportunities,
        MongoProblemReferenceRepository(mongo_database["business_problems"]),
        MongoHypothesisReferenceRepository(mongo_database["hypotheses"]),
    )

    created = await service.create(
        opportunity.id,
        CreateEvidenceRequest(
            type=EvidenceType.INTERVIEW,
            origin=EvidenceOrigin.MANUAL,
            description="Interview evidence supports the problem.",
            problem_id=problem.id,
            hypothesis_id=hypothesis.id,
        ),
        "tenant-a",
        {"workspace-a"},
        "user-1",
    )
    linked = await service.list_by_problem(problem.id, "tenant-a", {"workspace-a"})

    assert created.opportunity_id == opportunity.id
    assert created.problem_id == problem.id
    assert created.hypothesis_id == hypothesis.id
    assert [item.id for item in linked] == [created.id]
    with pytest.raises(EvidenceReferenceError):
        await service.create(
            opportunity.id,
            CreateEvidenceRequest(
                type=EvidenceType.DOCUMENT,
                origin=EvidenceOrigin.MANUAL,
                description="This reference belongs elsewhere.",
                problem_id="problem-from-another-workspace",
            ),
            "tenant-a",
            {"workspace-a"},
            "user-1",
        )