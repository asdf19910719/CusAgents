import json
from decimal import Decimal
from typing import Type

import httpx
from pydantic import BaseModel

from app.providers.llm.base import BaseLlmProvider, StructuredGenerationResult, TextGenerationResult


class OpenAICompatibleProvider(BaseLlmProvider):
    def __init__(self, base_url, api_key, default_model, http_client=None, timeout_seconds=90.0, retry_attempts=1):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.default_model = default_model
        self.timeout_seconds = timeout_seconds
        self.retry_attempts = max(0, int(retry_attempts))
        self.http_client = http_client or httpx.Client(
            base_url=self.base_url,
            timeout=self.timeout_seconds,
            trust_env=False,
        )

    def _request(self, prompt, model=None):
        last_error = None
        for attempt in range(self.retry_attempts + 1):
            try:
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
            except httpx.ReadTimeout as exc:
                last_error = exc
                if attempt >= self.retry_attempts:
                    raise
        raise last_error

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
        parsed = self._parse_structured_content(text_result.content, schema=schema)
        if parsed is None:
            repaired_result = self.generate_text(
                self._build_repair_prompt(text_result.content, schema),
                model=model,
            )
            parsed = self._parse_structured_content(repaired_result.content, schema=schema)
            if parsed is None:
                raise ValueError("model did not return valid structured JSON")
            total_input_tokens = text_result.input_tokens + repaired_result.input_tokens
            total_output_tokens = text_result.output_tokens + repaired_result.output_tokens
            total_tokens = text_result.total_tokens + repaired_result.total_tokens
            cost = text_result.cost + repaired_result.cost
            content = repaired_result.content
            raw_response = {
                "initial": text_result.raw_response,
                "repair": repaired_result.raw_response,
            }
        else:
            total_input_tokens = text_result.input_tokens
            total_output_tokens = text_result.output_tokens
            total_tokens = text_result.total_tokens
            cost = text_result.cost
            content = text_result.content
            raw_response = text_result.raw_response
        return StructuredGenerationResult(
            parsed=parsed,
            content=content,
            input_tokens=total_input_tokens,
            output_tokens=total_output_tokens,
            total_tokens=total_tokens,
            cost=cost,
            raw_response=raw_response,
        )

    def estimate_cost(self, input_tokens, output_tokens):
        return Decimal("0.0000")

    def _parse_structured_content(self, content, schema: Type[BaseModel]):
        content = (content or "").strip()
        if not content:
            return None
        candidates = [content]
        fenced = self._extract_markdown_json(content)
        if fenced and fenced not in candidates:
            candidates.append(fenced)
        snippet = self._extract_json_snippet(content)
        if snippet and snippet not in candidates:
            candidates.append(snippet)
        for candidate in candidates:
            try:
                parsed_json = json.loads(candidate)
                return schema.model_validate(parsed_json)
            except Exception:
                continue
        return None

    def _extract_markdown_json(self, content):
        marker = "```"
        if marker not in content:
            return ""
        blocks = content.split(marker)
        for block in blocks:
            normalized = block.strip()
            if not normalized:
                continue
            if normalized.lower().startswith("json"):
                normalized = normalized[4:].strip()
            if normalized.startswith("{") or normalized.startswith("["):
                return normalized
        return ""

    def _extract_json_snippet(self, content):
        openings = [("{", "}"), ("[", "]")]
        for start_char, end_char in openings:
            start = content.find(start_char)
            end = content.rfind(end_char)
            if start != -1 and end != -1 and end > start:
                return content[start : end + 1]
        return ""

    def _build_repair_prompt(self, content, schema: Type[BaseModel]):
        return (
            "Convert the following content into strict JSON only.\n"
            "Do not add markdown, explanations, or code fences.\n"
            "The JSON must satisfy this schema:\n"
            "{0}\n\n"
            "Content to convert:\n"
            "{1}"
        ).format(json.dumps(schema.model_json_schema(), ensure_ascii=False), content)
