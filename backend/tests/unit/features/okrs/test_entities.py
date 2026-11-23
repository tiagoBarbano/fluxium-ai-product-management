from datetime import date
from decimal import Decimal

import pytest

from app.features.okrs.domain.entities import KeyResult, Objective


def build_key_result(metric: str = "Ativacao") -> KeyResult:
    return KeyResult(
        metric=metric,
        target=Decimal("0.75"),
        due_date=date(2026, 12, 31),
    )


def test_objective_accepts_multiple_key_results() -> None:
    objective = Objective(
        title="Aumentar a ativacao",
        description="Criar uma experiencia inicial mais clara para novos usuarios.",
        key_results=[build_key_result("Ativacao"), build_key_result("Retencao")],
    )

    assert len(objective.key_results) == 2
    assert objective.key_results[0].metric == "Ativacao"


def test_objective_rejects_empty_key_results() -> None:
    with pytest.raises(ValueError, match="at least one key result"):
        Objective(
            title="Aumentar a ativacao",
            description="Criar uma experiencia inicial mais clara.",
            key_results=[],
        )


def test_objective_can_add_key_result_without_replacing_existing_ones() -> None:
    objective = Objective(
        title="Aumentar a ativacao",
        description="Criar uma experiencia inicial mais clara.",
        key_results=[build_key_result()],
    )

    objective.add_key_result(build_key_result("Retencao"))

    assert [result.metric for result in objective.key_results] == [
        "Ativacao",
        "Retencao",
    ]


@pytest.mark.parametrize(
    ("metric", "target", "due_date", "message"),
    [
        ("", Decimal("1"), date(2026, 12, 31), "metric"),
        ("Ativacao", None, date(2026, 12, 31), "target"),
        ("Ativacao", Decimal("1"), None, "due date"),
    ],
)
def test_key_result_rejects_missing_quantitative_fields(
    metric: str,
    target: Decimal | None,
    due_date: date | None,
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        KeyResult(metric=metric, target=target, due_date=due_date)