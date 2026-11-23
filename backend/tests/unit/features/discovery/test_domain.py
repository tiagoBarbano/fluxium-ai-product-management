import pytest

from app.features.discovery.domain.entities import DiscoveryContext, DiscoverySession
from app.features.discovery.domain.enums import DiscoverySessionStatus


def test_session_allows_manual_lifecycle_transitions() -> None:
    session = DiscoverySession(opportunity_id="opp-1", workspace_id="ws-1", created_by="user-1")

    session.transition_to(DiscoverySessionStatus.PAUSED)
    session.transition_to(DiscoverySessionStatus.ACTIVE)
    session.transition_to(DiscoverySessionStatus.COMPLETED)

    assert session.status is DiscoverySessionStatus.COMPLETED


def test_completed_session_rejects_context_changes() -> None:
    session = DiscoverySession(opportunity_id="opp-1", workspace_id="ws-1", created_by="user-1")
    session.transition_to(DiscoverySessionStatus.COMPLETED)

    with pytest.raises(ValueError, match="Completed"):
        session.update_context(DiscoveryContext(observed_problem="A problem"), expected_version=1)


def test_context_update_requires_current_version() -> None:
    session = DiscoverySession(opportunity_id="opp-1", workspace_id="ws-1", created_by="user-1")

    session.update_context(DiscoveryContext(observed_problem="A problem"), expected_version=1)

    with pytest.raises(ValueError, match="modified"):
        session.update_context(DiscoveryContext(observed_problem="Another problem"), expected_version=1)