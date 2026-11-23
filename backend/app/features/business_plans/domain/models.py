from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class InitiativeReference:
    id: str
    workspace_id: str