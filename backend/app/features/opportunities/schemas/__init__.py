"""Opportunity API schemas."""

from .requests import CreateOpportunityRequest, UpdateOpportunityRequest
from .responses import OpportunityResponse

__all__ = [
    "CreateOpportunityRequest",
    "OpportunityResponse",
    "UpdateOpportunityRequest",
]