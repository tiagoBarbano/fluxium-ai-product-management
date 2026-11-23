import json
from typing import Any

import httpx

from ....config.settings import Settings, get_settings
from ..domain.entities import AIGenerationCommand, ProviderGeneration
from ..errors import AIProviderError, AIProviderTimeoutError


class OllamaProvider:
    name = "ollama"

    def __init__(
        self,
        settings: Settings | None = None,
        client: httpx.AsyncClient | None = None,
        timeout: float = 120.0,
    ) -> None:
        self._settings = settings or get_settings()
        self._client = client
        self._timeout = timeout

    async def generate(self, command: AIGenerationCommand) -> ProviderGeneration:
        payload = {
            "model": self._settings.ollama_model,
            "prompt": self._build_prompt(command),
            "stream": False,
        }
        client = self._client or httpx.AsyncClient(
            base_url=self._settings.ollama_base_url.rstrip("/"),
            timeout=self._timeout,
        )
        try:
            response = await client.post("/api/generate", json=payload)
            response.raise_for_status()
        except httpx.TimeoutException as exc:
            raise AIProviderTimeoutError(
                self.name,
                "Ollama request timed out",
                manual_content=command.manual_content,
            ) from exc
        except httpx.HTTPError as exc:
            raise AIProviderError(
                self.name,
                "Ollama request failed",
                manual_content=command.manual_content,
            ) from exc
        finally:
            if self._client is None:
                await client.aclose()

        data = response.json()
        return ProviderGeneration(
            result=self._decode_result(data.get("response", "")),
            provider=self.name,
            model=data.get("model") or self._settings.ollama_model,
        )

    @staticmethod
    def _build_prompt(command: AIGenerationCommand) -> str:
        language_name = {"pt-BR": "Brazilian Portuguese", "en-US": "English"}.get(command.language, command.language)
        return json.dumps(
            {
                "instruction": f"Respond exclusively in {language_name}. Keep every textual field in this language.",
                "task": command.task,
                "context": command.context,
                "output_schema": command.output_schema,
                "prompt_version": command.prompt_version,
                "context_version": command.context_version,
                "language": command.language,
                "manual_content": command.manual_content,
            },
            ensure_ascii=True,
        )

    @staticmethod
    def _decode_result(value: Any) -> Any:
        if not isinstance(value, str):
            return value
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return value