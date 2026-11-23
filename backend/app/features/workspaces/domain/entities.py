from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import uuid4


@dataclass(frozen=True)
class Workspace:
    id: str
    tenant_id: str
    name: str
    description: str | None
    created_by: str
    created_at: datetime
    status: str = "ACTIVE"

    @classmethod
    def create(cls, tenant_id: str, name: str, description: str | None, created_by: str) -> "Workspace":
        return cls(
            id=str(uuid4()),
            tenant_id=tenant_id,
            name=name,
            description=description,
            created_by=created_by,
            created_at=datetime.now(UTC),
        )