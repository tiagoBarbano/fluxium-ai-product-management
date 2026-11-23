from types import SimpleNamespace

import httpx
import pytest

from app.features.ai_gateway.domain.entities import AIGenerationCommand
from app.features.ai_gateway.errors import AIProviderError, AIProviderTimeoutError
from app.features.ai_gateway.providers.ollama import OllamaProvider


class FakeAsyncClient:
    def __init__(self, response: httpx.Response | None = None, error: Exception | None = None) -> None:
        self.response = response
        self.error = error
        self.payload = None

    async def post(self, url: str, *, json: dict) -> httpx.Response:
        self.payload = (url, json)
        if self.error is not None:
            raise self.error
        return self.response


def command() -> AIGenerationCommand:
    return AIGenerationCommand("assess", {"problem": "slow onboarding"}, {"type": "object"}, "p1", "c2")


@pytest.mark.asyncio
async def test_ollama_posts_expected_payload_and_decodes_json_response() -> None:
    client = FakeAsyncClient(
        httpx.Response(
            200,
            json={"model": "llama3", "response": '{"confidence": 0.7}'},
            request=httpx.Request("POST", "http://ollama/api/generate"),
        )
    )
    provider = OllamaProvider(SimpleNamespace(ollama_base_url="http://ollama", ollama_model="llama3"), client=client)

    result = await provider.generate(command())

    assert client.payload == (
        "/api/generate",
        {
            "model": "llama3",
            "prompt": '{"instruction": "Respond exclusively in Brazilian Portuguese. Keep every textual field in this language.", "task": "assess", "context": {"problem": "slow onboarding"}, "output_schema": {"type": "object"}, "prompt_version": "p1", "context_version": "c2", "language": "pt-BR", "manual_content": null}',
            "stream": False,
        },
    )
    assert result.result == {"confidence": 0.7}
    assert result.provider == "ollama"


@pytest.mark.asyncio
async def test_ollama_timeout_is_typed() -> None:
    client = FakeAsyncClient(error=httpx.ReadTimeout("timeout"))
    provider = OllamaProvider(SimpleNamespace(ollama_base_url="http://ollama", ollama_model="llama3"), client=client)
    generation_command = AIGenerationCommand(
        "assess", {"problem": "slow onboarding"}, {"type": "object"}, "p1", "c2", manual_content="draft"
    )

    with pytest.raises(AIProviderTimeoutError) as error:
        await provider.generate(generation_command)

    assert error.value.manual_content == "draft"


@pytest.mark.asyncio
async def test_ollama_http_failure_is_typed() -> None:
    response = httpx.Response(503, request=httpx.Request("POST", "http://ollama/api/generate"))
    client = FakeAsyncClient(response=response)
    provider = OllamaProvider(SimpleNamespace(ollama_base_url="http://ollama", ollama_model="llama3"), client=client)
    generation_command = AIGenerationCommand(
        "assess", {"problem": "slow onboarding"}, {"type": "object"}, "p1", "c2", manual_content="draft"
    )

    with pytest.raises(AIProviderError) as error:
        await provider.generate(generation_command)

    assert error.value.manual_content == "draft"