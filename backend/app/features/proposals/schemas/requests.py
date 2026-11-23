from pydantic import BaseModel, ConfigDict, Field, model_validator


class DecideProposalRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    decision_reason: str | None = Field(default=None, min_length=1, max_length=2_000)


class CreateProposalRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    initiative_id: str = Field(min_length=1, max_length=100)
    assessment_id: str = Field(min_length=1, max_length=100)
    changes: dict[str, object] = Field(min_length=1)
    expected_initiative_version: int = Field(gt=0)

    @model_validator(mode="after")
    def validate_change_fields(self) -> "CreateProposalRequest":
        from ..domain.entities import Proposal

        unsupported = set(self.changes) - Proposal.MUTABLE_INITIATIVE_FIELDS
        if unsupported:
            raise ValueError(f"Unsupported Initiative changes: {sorted(unsupported)}")
        return self