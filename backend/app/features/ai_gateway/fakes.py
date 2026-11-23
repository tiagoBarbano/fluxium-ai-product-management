from .domain.entities import AIGenerationCommand, ProviderGeneration


class FakeAIProvider:
    name = "fake"

    def __init__(self, generation: ProviderGeneration | None = None, error: Exception | None = None) -> None:
        self.generation = generation or ProviderGeneration({"ok": True}, self.name, "fake-model")
        self.error = error
        self.commands: list[AIGenerationCommand] = []

    async def generate(self, command: AIGenerationCommand) -> ProviderGeneration:
        self.commands.append(command)
        if self.error is not None:
            raise self.error
        return self.generation