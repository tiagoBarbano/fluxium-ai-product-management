from enum import StrEnum


class HypothesisStatus(StrEnum):
    DRAFT = "DRAFT"
    TESTING = "TESTING"
    VALIDATED = "VALIDATED"
    INVALIDATED = "INVALIDATED"
    ABANDONED = "ABANDONED"