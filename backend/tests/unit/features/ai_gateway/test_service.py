import pytest

from app.features.ai_gateway.domain.entities import ProviderGeneration
from app.features.ai_gateway.errors import AIProviderError, AIProviderTimeoutError
from app.features.ai_gateway.fakes import FakeAIProvider
from app.features.ai_gateway.schemas.requests import AIGenerationRequest
from app.features.ai_gateway.service import AIGatewayService


@pytest.mark.asyncio
async def test_generate_returns_minimal_auditable_payload() -> None:
    provider = FakeAIProvider(
        ProviderGeneration(
            {"summary": "clear", "confidence": 0.65, "missing_information": ["KPI"]},
            "fake",
            "test-model",
        )
    )
    request = AIGenerationRequest(
        task="assess discovery",
        context={"problem": "onboarding"},
        output_schema={"type": "object"},
        prompt_version="prompt-1",
        context_version="context-3",
    )

    response = await AIGatewayService(provider).generate(request)

    assert response.model_dump() == {
        "result": {"summary": "clear", "confidence": 0.65, "missing_information": ["KPI"]},
        "confidence": 0.65,
        "missing_information": ["KPI"],
        "open_questions": [],
        "evidence_refs": [],
        "provider": "fake",
        "model": "test-model",
        "prompt_version": "prompt-1",
        "context_version": "context-3",
    }
    assert provider.commands[0].context == {"problem": "onboarding"}


@pytest.mark.asyncio
async def test_generate_does_not_invent_confidence_when_provider_omits_it() -> None:
    provider = FakeAIProvider(ProviderGeneration({"summary": "clear"}, "fake", "test-model"))
    request = AIGenerationRequest(
        task="review",
        context_version="context-1",
        prompt_version="prompt-1",
    )

    response = await AIGatewayService(provider).generate(request)

    assert response.confidence == 0.0


@pytest.mark.asyncio
async def test_generate_normalizes_percentage_confidence_from_provider() -> None:
    provider = FakeAIProvider(ProviderGeneration({"confidence": 30}, "fake", "test-model"))
    request = AIGenerationRequest(task="review", prompt_version="prompt-1", context_version="context-1")

    response = await AIGatewayService(provider).generate(request)

    assert response.confidence == 0.3


@pytest.mark.asyncio
async def test_provider_timeout_is_typed_and_manual_content_is_preserved() -> None:
    manual_content = {"title": "Keep this"}
    provider = FakeAIProvider(error=AIProviderTimeoutError("ollama", "timed out", manual_content))
    request = AIGenerationRequest(
        task="review",
        prompt_version="prompt-1",
        context_version="context-1",
        manual_content=manual_content,
    )

    with pytest.raises(AIProviderTimeoutError) as error:
        await AIGatewayService(provider).generate(request)

    assert error.value.provider == "ollama"
    assert error.value.manual_content == manual_content
    assert request.manual_content == manual_content


@pytest.mark.asyncio
async def test_untyped_provider_failure_is_wrapped_without_mutating_manual_content() -> None:
    manual_content = "draft"
    provider = FakeAIProvider(error=ConnectionError("offline"))
    request = AIGenerationRequest(
        task="extract",
        prompt_version="prompt-1",
        context_version="context-1",
        manual_content=manual_content,
    )

    with pytest.raises(AIProviderError) as error:
        await AIGatewayService(provider).generate(request)

    assert error.value.provider == "fake"
    assert error.value.manual_content == manual_content
    assert request.manual_content == manual_content