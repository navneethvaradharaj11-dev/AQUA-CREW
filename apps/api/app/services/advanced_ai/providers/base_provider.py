"""
Base Provider Interface for Advanced AI (Task 13 - Phase 6)
Defines common contract for LLM inference providers and deterministic fallbacks.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional


class BaseLLMProvider(ABC):
    @abstractmethod
    def generate_response(
        self,
        messages: List[Dict[str, str]],
        retrieved_context: Dict[str, Any],
        max_tokens: int = 1024,
        temperature: float = 0.2,
    ) -> Dict[str, Any]:
        """
        Generates an evidence-grounded response.
        Returns dictionary containing:
          - content: str
          - model_used: str
          - provider_used: str
          - token_usage: Optional[Dict[str, int]]
          - is_fallback: bool
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Returns True if the provider is configured and operational."""
        pass

