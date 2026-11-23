from enum import StrEnum


class OpportunityStatus(StrEnum):
    NEW = "NEW"
    DISCOVERY = "DISCOVERY"
    QUALIFIED = "QUALIFIED"
    REJECTED = "REJECTED"
    CONVERTED = "CONVERTED"