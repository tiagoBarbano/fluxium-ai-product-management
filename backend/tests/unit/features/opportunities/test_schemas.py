import pytest
from pydantic import ValidationError

from app.features.opportunities.domain.entities import Opportunity
from app.features.opportunities.domain.enums import OpportunityStatus
from app.features.opportunities.schemas.requests import (
    CreateOpportunityRequest,
    UpdateOpportunityRequest,
)
from app.features.opportunities.schemas.responses import OpportunityResponse


def test_create_request_normalizes_and_validates_required_fields() -> None:
    request = CreateOpportunityRequest(
        product_id=" product-1 ",
        title=" Improve onboarding ",
        description=" Reduce friction. ",
    )

    assert request.product_id == "product-1"
    assert request.title == "Improve onboarding"
    assert request.description == "Reduce friction."


def test_create_request_accepts_multiple_objectives() -> None:
    request = CreateOpportunityRequest(
        product_id="product-1",
        title="Improve onboarding",
        description="Reduce friction.",
        objective_ids=["objective-1", "objective-2"],
    )

    assert request.objective_ids == ["objective-1", "objective-2"]


@pytest.mark.parametrize("field_name", ["product_id", "title", "description"])
def test_create_request_rejects_blank_fields(field_name: str) -> None:
    values = {
        "product_id": "product-1",
        "title": "A title",
        "description": "A description",
    }
    values[field_name] = "   "

    with pytest.raises(ValidationError):
        CreateOpportunityRequest(**values)


def test_update_request_allows_partial_updates() -> None:
    request = UpdateOpportunityRequest(title="New title")

    assert request.title == "New title"
    assert request.product_id is None
    assert request.description is None


def test_response_serializes_domain_entity() -> None:
    opportunity = Opportunity(
        id="opportunity-1",
        product_id="product-1",
        title="Improve onboarding",
        description="Reduce friction.",
        status=OpportunityStatus.DISCOVERY,
    )

    response = OpportunityResponse.model_validate(opportunity)

    assert response.model_dump() == {
        "id": "opportunity-1",
        "product_id": "product-1",
        "title": "Improve onboarding",
        "description": "Reduce friction.",
        "objective_ids": [],
        "status": OpportunityStatus.DISCOVERY,
        "workspace_id": None,
        "created_by": None,
        "created_at": opportunity.created_at,
        "updated_at": opportunity.updated_at,
        "version": 1,
    }