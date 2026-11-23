from collections.abc import Awaitable, Callable
from typing import Any, Protocol

from .domain.entities import AIGenerationCommand, ProviderGeneration


class AIProvider(Protocol):
    name: str

    async def generate(self, command: AIGenerationCommand) -> ProviderGeneration:
        """Generate a provider response for a gateway command."""


class AsyncPostClient(Protocol):
    async def post(self, url: str, *, json: dict[str, Any]) -> Any:
        """Execute an asynchronous JSON POST request."""


ProviderFactory = Callable[[], Awaitable[ProviderGeneration]]