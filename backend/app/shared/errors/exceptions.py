from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ApplicationError(Exception):
    status_code: int
    title: str
    detail: str
    error_type: str = "about:blank"
