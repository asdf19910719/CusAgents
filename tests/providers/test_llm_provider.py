from decimal import Decimal

import httpx
from pydantic import BaseModel

from app.providers.llm.openai_compatible import OpenAICompatibleProvider


class DemoStructuredResponse(BaseModel):
    summary: str
    shots: int


def build_transport(payload):
    def handler(request):
        assert request.method == "POST"
        return httpx.Response(200, json=payload)

    return httpx.MockTransport(handler)


def test_generate_text_parses_content_and_usage():
    payload = {
        "choices": [
            {
                "message": {
                    "content": "A revenge story unfolds in a rainy city."
                }
            }
        ],
        "usage": {
            "prompt_tokens": 120,
            "completion_tokens": 80,
            "total_tokens": 200,
        },
    }
    client = httpx.Client(transport=build_transport(payload), base_url="https://example.com")
    provider = OpenAICompatibleProvider(
        base_url="https://example.com",
        api_key="test-key",
        default_model="demo-model",
        http_client=client,
    )

    result = provider.generate_text("Write a short story outline.")

    assert result.content == "A revenge story unfolds in a rainy city."
    assert result.input_tokens == 120
    assert result.output_tokens == 80
    assert result.total_tokens == 200
    assert result.cost == Decimal("0.0000")


def test_generate_structured_parses_json_into_schema():
    payload = {
        "choices": [
            {
                "message": {
                    "content": "{\"summary\": \"A duel at dawn\", \"shots\": 6}"
                }
            }
        ],
        "usage": {
            "prompt_tokens": 90,
            "completion_tokens": 50,
            "total_tokens": 140,
        },
    }
    client = httpx.Client(transport=build_transport(payload), base_url="https://example.com")
    provider = OpenAICompatibleProvider(
        base_url="https://example.com",
        api_key="test-key",
        default_model="demo-model",
        http_client=client,
    )

    result = provider.generate_structured("Return JSON only.", DemoStructuredResponse)

    assert result.parsed.summary == "A duel at dawn"
    assert result.parsed.shots == 6
    assert result.input_tokens == 90
    assert result.output_tokens == 50


def test_estimate_cost_returns_decimal_value():
    provider = OpenAICompatibleProvider(
        base_url="https://example.com",
        api_key="test-key",
        default_model="demo-model",
    )

    cost = provider.estimate_cost(1000, 500)

    assert isinstance(cost, Decimal)
    assert cost >= Decimal("0.0000")
