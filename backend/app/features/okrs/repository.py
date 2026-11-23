from datetime import date, datetime, time, timezone
from decimal import Decimal
from typing import Any, Protocol

from bson.decimal128 import Decimal128
from pymongo import ASCENDING
from pymongo.asynchronous.collection import AsyncCollection

from .domain.entities import KeyResult, Objective


class ObjectiveRepository(Protocol):
    async def insert(self, tenant_id: str, objective: Objective) -> None:
        ...

    async def find_by_id(self, tenant_id: str, objective_id: str) -> Objective | None:
        ...

    async def list_by_workspace(self, tenant_id: str, workspace_id: str) -> list[Objective]:
        ...

    async def replace(self, tenant_id: str, objective: Objective) -> None:
        ...


class MongoObjectiveRepository:
    def __init__(self, collection: AsyncCollection) -> None:
        self._collection = collection

    async def ensure_indexes(self) -> None:
        await self._collection.create_index(
            [("tenant_id", ASCENDING), ("workspace_id", ASCENDING), ("id", ASCENDING)],
            name="ix_objectives_tenant_workspace_id",
        )

    async def insert(self, tenant_id: str, objective: Objective) -> None:
        await self._collection.insert_one(self._to_document(tenant_id, objective))

    async def find_by_id(self, tenant_id: str, objective_id: str) -> Objective | None:
        document = await self._collection.find_one({"tenant_id": tenant_id, "id": objective_id})
        return self._from_document(document) if document else None

    async def list_by_workspace(self, tenant_id: str, workspace_id: str) -> list[Objective]:
        cursor = self._collection.find(
            {"tenant_id": tenant_id, "workspace_id": workspace_id},
            sort=[("created_at", ASCENDING), ("id", ASCENDING)],
        )
        return [self._from_document(document) async for document in cursor]

    async def replace(self, tenant_id: str, objective: Objective) -> None:
        await self._collection.replace_one(
            {"tenant_id": tenant_id, "id": objective.id},
            self._to_document(tenant_id, objective),
        )

    @staticmethod
    def _to_document(tenant_id: str, objective: Objective) -> dict[str, Any]:
        return {
            "id": objective.id,
            "tenant_id": tenant_id,
            "workspace_id": objective.workspace_id,
            "title": objective.title,
            "description": objective.description,
            "product_id": objective.product_id,
            "key_results": [
                {
                    "id": result.id,
                    "metric": result.metric,
                    "target": Decimal128(result.target),
                    "due_date": datetime.combine(result.due_date, time.min, tzinfo=timezone.utc),
                    "current_value": Decimal128(result.current_value)
                    if result.current_value is not None
                    else None,
                    "unit": result.unit,
                    "created_at": result.created_at,
                    "updated_at": result.updated_at,
                }
                for result in objective.key_results
            ],
            "created_at": objective.created_at,
            "updated_at": objective.updated_at,
        }

    @staticmethod
    def _from_document(document: dict[str, Any]) -> Objective:
        def decimal_value(value: Decimal128 | Decimal | int | float | str) -> Decimal:
            return value.to_decimal() if isinstance(value, Decimal128) else Decimal(str(value))

        key_results = [
            KeyResult(
                id=result["id"],
                metric=result["metric"],
                target=decimal_value(result["target"]),
                due_date=(
                    result["due_date"].date()
                    if isinstance(result["due_date"], datetime)
                    else result["due_date"]
                ),
                current_value=decimal_value(result["current_value"])
                if result.get("current_value") is not None
                else None,
                unit=result.get("unit"),
                created_at=result.get("created_at", datetime.now().astimezone()),
                updated_at=result.get("updated_at", datetime.now().astimezone()),
            )
            for result in document["key_results"]
        ]
        return Objective(
            id=document["id"],
            title=document["title"],
            description=document["description"],
            key_results=key_results,
            product_id=document.get("product_id"),
            workspace_id=document.get("workspace_id"),
            created_at=document.get("created_at", datetime.now().astimezone()),
            updated_at=document.get("updated_at", datetime.now().astimezone()),
        )