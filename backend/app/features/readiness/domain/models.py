from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class InitiativeReference:
    id: str
    workspace_id: str


@dataclass(frozen=True, slots=True)
class InitiativeContext:
    id: str
    workspace_id: str
    product_id: str
    opportunity_id: str
    problem_id: str | None
    title: str
    objective: str
    hypothesis_ids: list[str]
    objective_ids: list[str]
    evidence_ids: list[str]
    scope: str
    out_of_scope: str | None
    status: str
    version: int