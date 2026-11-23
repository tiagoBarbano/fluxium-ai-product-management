from typing import Any


class AIProviderError(RuntimeError):
    def __init__(self, provider: str, message: str, manual_content: Any = None) -> None:
        super().__init__(message)
        self.provider = provider
        self.manual_content = manual_content


class AIProviderTimeoutError(AIProviderError):
    """Raised when a provider does not answer within its configured timeout."""