from typing import Any, Protocol

from pymongo import ASCENDING
from pymongo.asynchronous.collection import AsyncCollection

from .domain.entities import BusinessPlan
from .domain.models import InitiativeReference


class BusinessPlanRepository(Protocol):
    async def ensure_indexes(self) -> None: ...
    async def find_initiative(self, tenant_id: str, initiative_id: str) -> InitiativeReference | None: ...
    async def find_by_initiative(self, tenant_id: str, workspace_ids: set[str], initiative_id: str) -> BusinessPlan | None: ...
    async def insert(self, tenant_id: str, plan: BusinessPlan) -> None: ...
    async def replace(self, tenant_id: str, plan: BusinessPlan, expected_version: int) -> bool: ...


class MongoBusinessPlanRepository:
    def __init__(self, plans: AsyncCollection, initiatives: AsyncCollection) -> None:
        self._plans = plans
        self._initiatives = initiatives

    async def ensure_indexes(self) -> None:
        await self._plans.create_index(
            [("tenant_id", ASCENDING), ("workspace_id", ASCENDING), ("initiative_id", ASCENDING)],
            name="ix_business_plans_tenant_workspace_initiative",
            unique=True,
        )

    async def find_initiative(self, tenant_id: str, initiative_id: str) -> InitiativeReference | None:
        document = await self._initiatives.find_one({"tenant_id": tenant_id, "id": initiative_id})
        return (
            InitiativeReference(id=document["id"], workspace_id=document["workspace_id"])
            if document
            else None
        )

    async def find_by_initiative(
        self, tenant_id: str, workspace_ids: set[str], initiative_id: str
    ) -> BusinessPlan | None:
        document = await self._plans.find_one(
            {"tenant_id": tenant_id, "workspace_id": {"$in": list(workspace_ids)}, "initiative_id": initiative_id}
        )
        return self._from_document(document) if document else None

    async def insert(self, tenant_id: str, plan: BusinessPlan) -> None:
        await self._plans.insert_one(self._to_document(tenant_id, plan))

    async def replace(self, tenant_id: str, plan: BusinessPlan, expected_version: int) -> bool:
        result = await self._plans.replace_one(
            {"tenant_id": tenant_id, "workspace_id": plan.workspace_id, "initiative_id": plan.initiative_id, "version": expected_version},
            self._to_document(tenant_id, plan),
        )
        return result.modified_count == 1

    @staticmethod
    def _to_document(tenant_id: str, plan: BusinessPlan) -> dict[str, Any]:
        return {
            "id": plan.id,
            "tenant_id": tenant_id,
            "initiative_id": plan.initiative_id,
            "workspace_id": plan.workspace_id,
            "rationale": plan.rationale,
            "what": plan.what,
            "why": plan.why,
            "where": plan.where,
            "when": plan.when,
            "who": plan.who,
            "how": plan.how,
            "how_much": plan.how_much,
            "metrics": list(plan.metrics),
            "risks": list(plan.risks),
            "created_at": plan.created_at,
            "updated_at": plan.updated_at,
            "version": plan.version,
        }

    @staticmethod
    def _from_document(document: dict[str, Any]) -> BusinessPlan:
        return BusinessPlan(
            id=document["id"], initiative_id=document["initiative_id"], workspace_id=document["workspace_id"],
            rationale=document["rationale"], what=document.get("what"), why=document.get("why"),
            where=document.get("where"), when=document.get("when"), who=document.get("who"),
            how=document.get("how"), how_much=document.get("how_much"),
            metrics=tuple(document.get("metrics", ())), risks=tuple(document.get("risks", ())),
            created_at=document["created_at"], updated_at=document["updated_at"], version=document["version"],
        )