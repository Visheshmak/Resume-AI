import json
from abc import ABC, abstractmethod
from typing import Any

import httpx

from app.ai.context import AIContext
from app.ai.errors import AIServiceError
from app.core.config import settings

SYSTEM_INSTRUCTION = "You must only make factual claims supported by the supplied resume evidence. Never invent skills, metrics, employers, dates, or achievements. Return only valid JSON matching the requested schema."


class LLMProvider(ABC):
    name = "abstract"

    @abstractmethod
    async def generate(self, task: str, context: AIContext, output_schema: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError


class AnalysisProvider(LLMProvider):
    """Backward-compatible provider name for structured AI analysis."""


class MockProvider(LLMProvider):
    name = "mock"

    def __init__(self, responses: dict[str, Any] | None = None, error: Exception | None = None):
        self.responses = responses or {}
        self.error = error
        self.calls: list[str] = []

    async def generate(self, task: str, context: AIContext, output_schema: dict[str, Any]) -> dict[str, Any]:
        self.calls.append(task)
        if self.error:
            raise self.error
        response = self.responses.get(task, {})
        if isinstance(response, Exception):
            raise response
        if callable(response):
            response = response(context)
        return response


class OpenAIProvider(LLMProvider):
    name = "openai"

    async def generate(self, task: str, context: AIContext, output_schema: dict[str, Any]) -> dict[str, Any]:
        if not settings.llm_api_key:
            raise AIServiceError("AI provider is not configured", code="provider_not_configured")
        payload = {"model": settings.llm_model, "temperature": 0, "messages": [{"role": "system", "content": SYSTEM_INSTRUCTION}, {"role": "user", "content": json.dumps({"task": task, "context": context.as_payload()})}], "response_format": {"type": "json_schema", "json_schema": {"name": task.replace("-", "_"), "strict": True, "schema": output_schema}}}
        try:
            async with httpx.AsyncClient(timeout=settings.llm_timeout_seconds) as client:
                response = await client.post(settings.openai_base_url.rstrip("/") + "/chat/completions", headers={"Authorization": f"Bearer {settings.llm_api_key}"}, json=payload)
                response.raise_for_status()
                return json.loads(response.json()["choices"][0]["message"]["content"])
        except (TimeoutError, httpx.TimeoutException) as exc:
            raise AIServiceError("AI provider timed out", code="provider_timeout") from exc
        except (httpx.HTTPError, KeyError, IndexError, TypeError, json.JSONDecodeError) as exc:
            raise AIServiceError("AI provider returned an unusable response", code="provider_response_error") from exc


class GeminiProvider(LLMProvider):
    name = "gemini"

    async def generate(self, task: str, context: AIContext, output_schema: dict[str, Any]) -> dict[str, Any]:
        if not settings.llm_api_key:
            raise AIServiceError("AI provider is not configured", code="provider_not_configured")
        endpoint = f"{settings.gemini_base_url.rstrip('/')}/models/{settings.llm_model}:generateContent"
        payload = {"contents": [{"parts": [{"text": SYSTEM_INSTRUCTION + "\n" + json.dumps({"task": task, "context": context.as_payload()})}]}], "generationConfig": {"temperature": 0, "responseMimeType": "application/json", "responseSchema": output_schema}}
        try:
            async with httpx.AsyncClient(timeout=settings.llm_timeout_seconds) as client:
                response = await client.post(endpoint, params={"key": settings.llm_api_key}, json=payload)
                response.raise_for_status()
                return json.loads(response.json()["candidates"][0]["content"]["parts"][0]["text"])
        except (TimeoutError, httpx.TimeoutException) as exc:
            raise AIServiceError("AI provider timed out", code="provider_timeout") from exc
        except (httpx.HTTPError, KeyError, IndexError, TypeError, json.JSONDecodeError) as exc:
            raise AIServiceError("AI provider returned an unusable response", code="provider_response_error") from exc


class UnconfiguredAnalysisProvider(LLMProvider):
    name = "stub"

    async def generate(self, task: str, context: AIContext, output_schema: dict[str, Any]) -> dict[str, Any]:
        raise AIServiceError("AI provider is not configured", code="provider_not_configured")


def build_provider() -> LLMProvider:
    providers = {"mock": MockProvider, "openai": OpenAIProvider, "gemini": GeminiProvider, "stub": UnconfiguredAnalysisProvider}
    provider = providers.get(settings.llm_provider.lower())
    if provider is None:
        raise AIServiceError("Configured AI provider is not supported", code="unsupported_provider")
    return provider()
