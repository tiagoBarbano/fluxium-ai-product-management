from .domain.entities import AIGenerationCommand
from .errors import AIProviderError
from .protocols import AIProvider
from .schemas.requests import AIGenerationRequest
from .schemas.responses import AIGenerationResponse


def _normalize_confidence(value: object) -> float:
    confidence = float(value)
    if 1.0 < confidence <= 100.0:
        return confidence / 100.0
    return confidence


class AIGatewayService:
    def __init__(self, provider: AIProvider) -> None:
        self._provider = provider

    async def generate(self, request: AIGenerationRequest) -> AIGenerationResponse:
        command = AIGenerationCommand(
            task=request.task,
            context=request.context,
            output_schema=request.output_schema,
            prompt_version=request.prompt_version,
            context_version=request.context_version,
            language=request.language,
            manual_content=request.manual_content,
        )
        try:
            generated = await self._provider.generate(command)
        except AIProviderError:
            raise
        except Exception as exc:
            raise AIProviderError(
                getattr(self._provider, "name", "unknown"),
                "AI provider failed",
                manual_content=request.manual_content,
            ) from exc
        result = generated.result
        result_fields = result if isinstance(result, dict) else {}
        return AIGenerationResponse(
            result=result,
            confidence=_normalize_confidence(result_fields.get("confidence", 0.0)),
            missing_information=result_fields.get("missing_information", []),
            open_questions=result_fields.get("open_questions", []),
            provider=generated.provider,
            model=generated.model,
            prompt_version=request.prompt_version,
            context_version=request.context_version,
        )