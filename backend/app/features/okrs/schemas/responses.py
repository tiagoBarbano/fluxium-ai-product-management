from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class KeyResultResponse(BaseModel):
    id: str
    metric: str
    target: Decimal
    due_date: date
    current_value: Decimal | None = None
    unit: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class ObjectiveResponse(BaseModel):
    id: str
    workspace_id: str | None = None
    title: str
    description: str
    key_results: list[KeyResultResponse]
    product_id: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)