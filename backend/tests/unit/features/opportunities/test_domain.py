import pytest

from app.features.opportunities.domain.entities import Opportunity
from app.features.opportunities.domain.enums import OpportunityStatus


def make_opportunity(
    status: OpportunityStatus = OpportunityStatus.NEW,
) -> Opportunity:
    return Opportunity(
        id="opportunity-1",
        product_id="product-1",
        title="Improve onboarding",
        description="Reduce friction in the onboarding flow.",
        status=status,
    )


@pytest.mark.parametrize(
    ("source_status", "target_status"),
    [
        (OpportunityStatus.NEW, OpportunityStatus.DISCOVERY),
        (OpportunityStatus.DISCOVERY, OpportunityStatus.QUALIFIED),
        (OpportunityStatus.DISCOVERY, OpportunityStatus.REJECTED),
        (OpportunityStatus.QUALIFIED, OpportunityStatus.CONVERTED),
    ],
)
def test_allows_valid_transitions(
    source_status: OpportunityStatus,
    target_status: OpportunityStatus,
) -> None:
    opportunity = make_opportunity(source_status)

    opportunity.transition_to(target_status)

    assert opportunity.status is target_status


@pytest.mark.parametrize(
    ("source_status", "target_status"),
    [
        (OpportunityStatus.NEW, OpportunityStatus.QUALIFIED),
        (OpportunityStatus.NEW, OpportunityStatus.REJECTED),
        (OpportunityStatus.DISCOVERY, OpportunityStatus.CONVERTED),
        (OpportunityStatus.QUALIFIED, OpportunityStatus.DISCOVERY),
        (OpportunityStatus.REJECTED, OpportunityStatus.DISCOVERY),
        (OpportunityStatus.CONVERTED, OpportunityStatus.DISCOVERY),
    ],
)
def test_rejects_invalid_transitions(
    source_status: OpportunityStatus,
    target_status: OpportunityStatus,
) -> None:
    opportunity = make_opportunity(source_status)

    with pytest.raises(ValueError, match="Invalid opportunity transition"):
        opportunity.transition_to(target_status)

    assert opportunity.status is source_status


@pytest.mark.parametrize(
    "field_name",
    ["id", "product_id", "title", "description"],
)
def test_rejects_blank_required_domain_fields(field_name: str) -> None:
    values = {
        "id": "opportunity-1",
        "product_id": "product-1",
        "title": "A title",
        "description": "A description",
    }
    values[field_name] = "   "

    with pytest.raises(ValueError, match=f"{field_name} must not be blank"):
        Opportunity(**values)