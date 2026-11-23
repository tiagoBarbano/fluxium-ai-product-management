from enum import StrEnum


class BusinessProblemStatus(StrEnum):
    OPEN = "OPEN"
    VALIDATED = "VALIDATED"
    RESOLVED = "RESOLVED"
    REJECTED = "REJECTED"