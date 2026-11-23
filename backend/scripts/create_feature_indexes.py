import asyncio

from app.database.mongo import get_database
from app.features.business_problems.repository import MongoBusinessProblemRepository
from app.features.discovery.repository import MongoDiscoveryRepository
from app.features.evidence.repository import MongoEvidenceRepository
from app.features.hypotheses.repository import MongoHypothesisRepository
from app.features.initiatives.repository import MongoInitiativeRepository
from app.features.business_plans.repository import MongoBusinessPlanRepository
from app.features.readiness.repository import MongoReadinessAssessmentRepository
from app.features.proposals.repository import MongoProposalRepository
from app.shared.audit.repository import MongoAuditRepository
from app.features.okrs.repository import MongoObjectiveRepository
from app.features.opportunities.repository import MongoOpportunityRepository
from app.features.products.repository import MongoProductRepository


async def main() -> None:
    database = get_database()
    repositories = (
        MongoProductRepository(database["products"]),
        MongoOpportunityRepository(database["opportunities"]),
        MongoObjectiveRepository(database["objectives"]),
        MongoBusinessProblemRepository(database["business_problems"]),
        MongoHypothesisRepository(database["hypotheses"]),
        MongoInitiativeRepository(database["initiatives"]),
        MongoBusinessPlanRepository(database["business_plans"], database["initiatives"]),
        MongoReadinessAssessmentRepository(database["assessments"], database["initiatives"]),
        MongoProposalRepository(database["proposals"]),
        MongoAuditRepository(database["audit_events"]),
        MongoEvidenceRepository(database["evidence"]),
        MongoDiscoveryRepository(database["discovery_sessions"], database["discovery_messages"]),
    )
    for repository in repositories:
        await repository.ensure_indexes()
    await database.client.close()


if __name__ == "__main__":
    asyncio.run(main())