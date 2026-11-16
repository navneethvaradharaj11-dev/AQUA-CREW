"""
AI Provider Factory (Task 13 / 13.5)
Instantiates the configured LLM inference provider or defaults to the deterministic fallback engine.
Enforces automatic fallback to DeterministicProvider if external API keys or networks fail.
Reports genuine live-verification status without false claims of connectivity.
"""
import logging
from typing import Dict, Any, Optional

from app.config import settings
from app.services.advanced_ai.providers.base_provider import BaseLLMProvider
from app.services.advanced_ai.providers.deterministic_provider import DeterministicProvider
from app.services.advanced_ai.providers.openai_nim_provider import OpenAINimProvider

logger = logging.getLogger("aqua_crew.advanced_ai.factory")


class AIProviderFactory:
    _instance: Optional[BaseLLMProvider] = None
    _is_live_verified: bool = False

    @classmethod
    def set_live_verified(cls, verified: bool = True):
        cls._is_live_verified = verified

    @classmethod
    def get_provider(cls, force_reload: bool = False) -> BaseLLMProvider:
        """
        Retrieves or initializes the active AI provider.
        Defaults reliably to DeterministicProvider if no API key is configured.
        """
        if cls._instance is not None and not force_reload:
            return cls._instance

        provider_choice = (settings.AI_PROVIDER or "DETERMINISTIC").upper().strip()

        if provider_choice in ["NVIDIA_NIM", "OPENAI"]:
            if settings.AI_API_KEY and settings.AI_API_KEY.strip():
                logger.info(f"Initializing {provider_choice} provider with model: {settings.AI_MODEL}")
                nim_provider = OpenAINimProvider(
                    api_key=settings.AI_API_KEY,
                    base_url=settings.AI_BASE_URL,
                    model_name=settings.AI_MODEL,
                    timeout_seconds=settings.AI_TIMEOUT,
                )
                if nim_provider.is_available():
                    cls._instance = nim_provider
                    return cls._instance
                else:
                    logger.warning("Configured provider reported unavailable. Falling back to DeterministicProvider.")
            else:
                logger.info(f"AI_PROVIDER={provider_choice} configured but no AQUA_AI_API_KEY found. Using DeterministicProvider.")

        # Default to DeterministicProvider
        logger.info("Active AI provider: DETERMINISTIC (rule-based evidence reasoning engine)")
        cls._instance = DeterministicProvider()
        return cls._instance

    @classmethod
    def get_provider_status(cls) -> Dict[str, Any]:
        """
        Returns structured metadata regarding the current AI provider configuration.
        Masks all credentials and reports honest live-verification status.
        """
        configured_provider = (settings.AI_PROVIDER or "DETERMINISTIC").upper()
        active_provider = cls.get_provider()
        is_fallback = isinstance(active_provider, DeterministicProvider) and configured_provider != "DETERMINISTIC"

        has_api_key = bool(settings.AI_API_KEY and len(settings.AI_API_KEY.strip()) > 0)
        masked_key = (
            f"{settings.AI_API_KEY[:4]}...{settings.AI_API_KEY[-4:]}"
            if has_api_key and len(settings.AI_API_KEY) > 8
            else ("configured" if has_api_key else "none")
        )

        live_status = (
            "LIVE-VERIFIED"
            if cls._is_live_verified
            else "NOT LIVE-VERIFIED (No active external credentials configured; running in deterministic fallback mode)"
        )

        return {
            "configured_provider": configured_provider,
            "active_provider": "DETERMINISTIC" if isinstance(active_provider, DeterministicProvider) else configured_provider,
            "active_model": settings.AI_MODEL if not isinstance(active_provider, DeterministicProvider) else "deterministic-grounded-engine",
            "is_available": active_provider.is_available(),
            "is_fallback": is_fallback,
            "is_live_verified": cls._is_live_verified,
            "live_verification_status": live_status,
            "base_url": settings.AI_BASE_URL or ("https://integrate.api.nvidia.com/v1" if configured_provider == "NVIDIA_NIM" else None),
            "api_key_configured": has_api_key,
            "api_key_status": masked_key,
            "timeout_seconds": settings.AI_TIMEOUT,
            "max_tokens": settings.AI_MAX_TOKENS,
            "temperature": settings.AI_TEMPERATURE,
            "supported_models": [
                "meta/llama-3.1-70b-instruct",
                "meta/llama-3.1-8b-instruct",
                "mistralai/mixtral-8x22b-instruct-v0.1",
                "gpt-4o",
                "gpt-4o-mini",
                "deterministic-grounded-engine"
            ]
        }
