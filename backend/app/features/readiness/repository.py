from typing import Any, Protocol

from pymongo import ASCENDING, DESCENDING
from pymongo.asynchronous.collection import AsyncCollection

from .domain.entities import ReadinessAssessment, ReadinessDimensionScore
from .domain.models import InitiativeContext, InitiativeReference


class ReadinessAssessmentRepository(Protocol):
    async def ensure_indexes(self) -> None: ...
    async def find_initiative(self, tenant_id: str, initiative_id: str) -> InitiativeReference | None: ...
    async def find_initiative_context(self, tenant_id: str, initiative_id: str) -> InitiativeContext | None: ...
    async def insert(self, tenant_id: str, assessment: ReadinessAssessment, job_id: str | None = None) -> None: ...
    async def find_by_id(self, tenant_id: str, workspace_ids: set[str], assessment_id: str) -> ReadinessAssessment | None: ...
    async def list_by_initiative(self, tenant_id: str, workspace_ids: set[str], initiative_id: str) -> list[ReadinessAssessment]: ...
    async def find_id_by_job(self, tenant_id: str, workspace_ids: set[str], job_id: str) -> str | None: ...


class MongoReadinessAssessmentRepository:
    def __init__(self, assessments: AsyncCollection, initiatives: AsyncCollection) -> None:
        self._assessments = assessments
        self._initiatives = initiatives

    async def ensure_indexes(self) -> None:
        await self._assessments.create_index(
            [("tenant_id", ASCENDING), ("workspace_id", ASCENDING), ("initiative_id", ASCENDING), ("created_at", DESCENDING)],
            name="ix_readiness_assessments_tenant_workspace_initiative_created",
        )
        await self._assessments.create_index(
            [("tenant_id", ASCENDING), ("workspace_id", ASCENDING), ("id", ASCENDING)],
            name="ix_readiness_assessments_tenant_workspace_id",
            unique=True,
        )
        await self._assessments.create_index(
            [("tenant_id", ASCENDING), ("workspace_id", ASCENDING), ("job_id", ASCENDING)],
            name="ix_readiness_assessments_tenant_workspace_job",
            unique=True,
            sparse=True,
        )

    async def find_initiative(self, tenant_id: str, initiative_id: str) -> InitiativeReference | None:
        document = await self._initiatives.find_one({"tenant_id": tenant_id, "id": initiative_id})
        return InitiativeReference(id=document["id"], workspace_id=document["workspace_id"]) if document else None

    async def find_initiative_context(self, tenant_id: str, initiative_id: str) -> InitiativeContext | None:
        document = await self._initiatives.find_one({"tenant_id": tenant_id, "id": initiative_id})
        if document is None:
            return None
        return InitiativeContext(
            id=document["id"], workspace_id=document["workspace_id"], product_id=document["product_id"],
            opportunity_id=document["opportunity_id"], problem_id=document.get("problem_id"),
            title=document["title"], objective=document["objective"],
            hypothesis_ids=document.get("hypothesis_ids", []), objective_ids=document.get("objective_ids", []),
            evidence_ids=document.get("evidence_ids", []), scope=document["scope"],
            out_of_scope=document.get("out_of_scope"), status=document["status"], version=document["version"],
        )

    async def insert(self, tenant_id: str, assessment: ReadinessAssessment, job_id: str | None = None) -> None:
        await self._assessments.insert_one(self._to_document(tenant_id, assessment, job_id))

    async def find_by_id(self, tenant_id: str, workspace_ids: set[str], assessment_id: str) -> ReadinessAssessment | None:
        document = await self._assessments.find_one(
            {"tenant_id": tenant_id, "workspace_id": {"$in": list(workspace_ids)}, "id": assessment_id}
        )
        return self._from_document(document) if document else None

    async def list_by_initiative(self, tenant_id: str, workspace_ids: set[str], initiative_id: str) -> list[ReadinessAssessment]:
        cursor = self._assessments.find(
            {"tenant_id": tenant_id, "workspace_id": {"$in": list(workspace_ids)}, "initiative_id": initiative_id},
            sort=[("created_at", DESCENDING), ("id", ASCENDING)],
        )
        return [self._from_document(document) async for document in cursor]

    async def find_id_by_job(self, tenant_id: str, workspace_ids: set[str], job_id: str) -> str | None:
        document = await self._assessments.find_one(
            {"tenant_id": tenant_id, "workspace_id": {"$in": list(workspace_ids)}, "job_id": job_id},
            projection={"_id": 0, "id": 1},
        )
        return document["id"] if document else None

    @staticmethod
    def _to_document(tenant_id: str, assessment: ReadinessAssessment, job_id: str | None = None) -> dict[str, Any]:
        document = {
            "id": assessment.id,
            "tenant_id": tenant_id,
            "initiative_id": assessment.initiative_id,
            "workspace_id": assessment.workspace_id,
            "score": assessment.score,
            "dimensions": [
                {"name": dimension.name, "score": dimension.score, "justification": dimension.justification}
                for dimension in assessment.dimensions
            ],
            "missing_information": list(assessment.missing_information),
            "open_questions": list(assessment.open_questions),
            "confidence": assessment.confidence,
            "context_version": assessment.context_version,
            "provider": assessment.provider,
            "model": assessment.model,
            "prompt_version": assessment.prompt_version,
            "created_at": assessment.created_at,
            "created_by": assessment.created_by,
            "source_context": assessment.source_context,
        }
        if job_id is not None:
            document["job_id"] = job_id
        return document

    @staticmethod
    def _from_document(document: dict[str, Any]) -> ReadinessAssessment:
        return ReadinessAssessment(
            id=document["id"],
            initiative_id=document["initiative_id"],
            workspace_id=document["workspace_id"],
            score=document["score"],
            dimensions=tuple(ReadinessDimensionScore(**dimension) for dimension in document["dimensions"]),
            missing_information=tuple(document.get("missing_information", ())),
            open_questions=tuple(document.get("open_questions", ())),
            confidence=document["confidence"],
            context_version=document["context_version"],
            provider=document["provider"],
            model=document["model"],
            prompt_version=document["prompt_version"],
            created_at=document["created_at"],
            created_by=document["created_by"],
            source_context=document.get("source_context", {}),
        )