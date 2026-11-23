from pydantic import BaseModel, ConfigDict, Field, model_validator


class CreateProductRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    workspace_id: str = Field(min_length=1, max_length=100)
    name: str = Field(min_length=1, max_length=120)
    description: str | None = Field(default=None, max_length=2_000)
    vision: str | None = Field(default=None, max_length=2_000)
    created_by: str = Field(min_length=1, max_length=100)


class UpdateProductRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    expected_version: int = Field(gt=0)
    name: str | None = Field(default=None, min_length=1, max_length=120)
    description: str | None = Field(default=None, max_length=2_000)
    vision: str | None = Field(default=None, max_length=2_000)

    @model_validator(mode="after")
    def require_mutable_field(self) -> "UpdateProductRequest":
        if self.name is None and self.description is None and self.vision is None:
            raise ValueError("At least one Product field must be provided")
        return self