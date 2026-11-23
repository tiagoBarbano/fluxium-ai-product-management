from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ProductName:
    value: str

    def __post_init__(self) -> None:
        normalized = self.value.strip()
        if not normalized:
            raise ValueError("Product name must not be blank")
        if len(normalized) > 120:
            raise ValueError("Product name must contain at most 120 characters")
        object.__setattr__(self, "value", normalized)