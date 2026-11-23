from datetime import date
from decimal import Decimal

from bson import BSON

from app.features.okrs.domain.entities import KeyResult, Objective
from app.features.okrs.repository import MongoObjectiveRepository


def test_objective_document_serializes_and_restores_due_date() -> None:
    objective = Objective(
        title="Aumentar a ativacao",
        description="Criar uma experiencia inicial mais clara.",
        product_id="product-1",
        workspace_id="workspace-1",
        key_results=[
            KeyResult(
                metric="Ativacao",
                target=Decimal("0.75"),
                due_date=date(2026, 12, 31),
            )
        ],
    )

    document = MongoObjectiveRepository._to_document("tenant-1", objective)
    encoded_document = BSON.encode(document)
    restored = MongoObjectiveRepository._from_document(BSON(encoded_document).decode())

    assert restored.key_results[0].due_date == date(2026, 12, 31)
