from abc import ABC, abstractmethod
from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Type

from pydantic import BaseModel


@dataclass
class TextGenerationResult:
    content: str
    input_tokens: int
    output_tokens: int
    total_tokens: int
    cost: Decimal
    raw_response: dict[str, Any]


@dataclass
class StructuredGenerationResult:
    parsed: BaseModel
    content: str
    input_tokens: int
    output_tokens: int
    total_tokens: int
    cost: Decimal
    raw_response: dict[str, Any]


class BaseLlmProvider(ABC):
    @abstractmethod
    def generate_text(self, prompt: str, model: str | None = None) -> TextGenerationResult:
        raise NotImplementedError

    @abstractmethod
    def generate_structured(
        self,
        prompt: str,
        schema: Type[BaseModel],
        model: str | None = None,
    ) -> StructuredGenerationResult:
        raise NotImplementedError

    @abstractmethod
    def estimate_cost(self, input_tokens: int, output_tokens: int) -> Decimal:
        raise NotImplementedError
