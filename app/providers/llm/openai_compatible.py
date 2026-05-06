import json
from decimal import Decimal
from typing import Type

import httpx
from pydantic import BaseModel

from app.providers.llm.base import BaseLlmProvider, StructuredGenerationResult, TextGenerationResult


class OpenAICompatibleProvider(BaseLlmProvider):
    def __init__(self, base_url, api_key, default_model, http_client=None):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.default_model = default_model
        self.http_client = http_client or httpx.Client(base_url=self.base_url, timeout=30.0, trust_env=False)

    def _request(self, prompt, model=None):
        response = self.http_client.post(
            "/chat/completions",
            headers={"Authorization": "Bearer " + self.api_key},
            json={
                "model": model or self.default_model,
                "messages": [{"role": "user", "content": prompt}],
            },
        )
        response.raise_for_status()
        return response.json()

    def _extract_usage(self, payload):
        usage = payload.get("usage", {})
        input_tokens = int(usage.get("prompt_tokens", 0))
        output_tokens = int(usage.get("completion_tokens", 0))
        total_tokens = int(usage.get("total_tokens", input_tokens + output_tokens))
        return input_tokens, output_tokens, total_tokens

    def _extract_content(self, payload):
        choices = payload.get("choices", [])
        if not choices:
            return ""
        return choices[0].get("message", {}).get("content", "")

    def generate_text(self, prompt, model=None):
        payload = self._request(prompt, model=model)
        content = self._extract_content(payload)
        input_tokens, output_tokens, total_tokens = self._extract_usage(payload)
        return TextGenerationResult(
            content=content,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=total_tokens,
            cost=self.estimate_cost(input_tokens, output_tokens),
            raw_response=payload,
        )

    def generate_structured(self, prompt, schema: Type[BaseModel], model=None):
        text_result = self.generate_text(prompt, model=model)
        parsed = schema.model_validate(json.loads(text_result.content))
        return StructuredGenerationResult(
            parsed=parsed,
            content=text_result.content,
            input_tokens=text_result.input_tokens,
            output_tokens=text_result.output_tokens,
            total_tokens=text_result.total_tokens,
            cost=text_result.cost,
            raw_response=text_result.raw_response,
        )

    def estimate_cost(self, input_tokens, output_tokens):
        return Decimal("0.0000")
