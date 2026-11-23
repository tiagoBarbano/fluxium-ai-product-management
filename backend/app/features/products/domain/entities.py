from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import uuid4

from .enums import ProductStatus
from .value_objects import ProductName


class ProductVersionConflict(ValueError):
    """Raised when a write is based on a stale Product version."""


def _required_identifier(value: str, field_name: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field_name} must not be blank")
    return normalized


def _utc_now() -> datetime:
    return datetime.now(UTC)


@dataclass(slots=True)
class Product:
    id: str
    workspace_id: str
    name: ProductName
    description: str | None
    vision: str | None
    status: ProductStatus
    created_by: str
    created_at: datetime
    updated_at: datetime
    version: int = 1

    @classmethod
    def create(
        cls,
        *,
        workspace_id: str,
        name: str,
        created_by: str,
        description: str | None = None,
        vision: str | None = None,
        product_id: str | None = None,
        now: datetime | None = None,
    ) -> "Product":
        timestamp = now or _utc_now()
        if timestamp.tzinfo is None:
            raise ValueError("Product timestamps must be timezone-aware")
        return cls(
            id=_required_identifier(product_id or str(uuid4()), "id"),
            workspace_id=_required_identifier(workspace_id, "workspace_id"),
            name=ProductName(name),
            description=_optional_text(description, "description", 2_000),
            vision=_optional_text(vision, "vision", 2_000),
            status=ProductStatus.ACTIVE,
            created_by=_required_identifier(created_by, "created_by"),
            created_at=timestamp,
            updated_at=timestamp,
        )

    def update(
        self,
        *,
        expected_version: int,
        name: str | None = None,
        description: str | None = None,
        vision: str | None = None,
        now: datetime | None = None,
    ) -> None:
        self._check_version(expected_version)
        if self.status is ProductStatus.ARCHIVED:
            raise ValueError("Archived Products cannot be updated")
        if name is not None:
            self.name = ProductName(name)
        if description is not None:
            self.description = _optional_text(description, "description", 2_000)
        if vision is not None:
            self.vision = _optional_text(vision, "vision", 2_000)
        self._touch(now)

    def archive(self, *, expected_version: int, now: datetime | None = None) -> None:
        self._check_version(expected_version)
        if self.status is ProductStatus.ARCHIVED:
            raise ValueError("Product is already archived")
        self.status = ProductStatus.ARCHIVED
        self._touch(now)

    def activate(self, *, expected_version: int, now: datetime | None = None) -> None:
        self._check_version(expected_version)
        if self.status is ProductStatus.ACTIVE:
            raise ValueError("Product is already active")
        self.status = ProductStatus.ACTIVE
        self._touch(now)

    def _check_version(self, expected_version: int) -> None:
        if expected_version != self.version:
            raise ProductVersionConflict(
                f"Expected Product version {expected_version}, current version is {self.version}"
            )

    def _touch(self, now: datetime | None) -> None:
        timestamp = now or _utc_now()
        if timestamp.tzinfo is None:
            raise ValueError("Product timestamps must be timezone-aware")
        self.version += 1
        self.updated_at = timestamp


def _optional_text(value: str | None, field_name: str, max_length: int) -> str | None:
    if value is None:
        return None
    normalized = value.strip()
    if len(normalized) > max_length:
        raise ValueError(f"{field_name} must contain at most {max_length} characters")
    return normalized or None