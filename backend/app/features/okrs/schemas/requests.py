from datetime import date
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class CreateKeyResultRequest(BaseModel):
    metric: str = Field(min_length=1, max_length=200)
    target: Decimal
    due_date: date
    current_value: Decimal | None = None
    unit: str | None = Field(default=None, min_length=1, max_length=50)

    model_config = ConfigDict(str_strip_whitespace=True)

    @field_validator("target", "current_value")
    @classmethod
    def validate_finite_value(cls, value: Decimal | None) -> Decimal | None:
        if value is not None and not value.is_finite():
            raise ValueError("value must be finite")
        return value


class UpdateKeyResultRequest(BaseModel):
    id: str | None = Field(default=None, min_length=1, max_length=100)
    metric: str | None = Field(default=None, min_length=1, max_length=200)
    target: Decimal | None = None
    due_date: date | None = None
    current_value: Decimal | None = None
    unit: str | None = Field(default=None, min_length=1, max_length=50)

    model_config = ConfigDict(str_strip_whitespace=True)

    @field_validator("target", "current_value")
    @classmethod
    def validate_finite_value(cls, value: Decimal | None) -> Decimal | None:
        if value is not None and not value.is_finite():
            raise ValueError("value must be finite")
        return value


class CreateObjectiveRequest(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str = Field(min_length=1, max_length=2000)
    key_results: list[CreateKeyResultRequest] = Field(min_length=1, max_length=50)
    product_id: str = Field(min_length=1)

    model_config = ConfigDict(str_strip_whitespace=True)



class UpdateObjectiveRequest(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, min_length=1, max_length=2000)
    key_results: list[UpdateKeyResultRequest] | None = Field(default=None, min_length=1, max_length=50)

    model_config = ConfigDict(str_strip_whitespace=True)