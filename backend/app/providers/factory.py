from typing import Optional
from app.config import get_settings
from app.providers.base import BaseLLMProvider, ProviderConfigurationException
from app.providers.ollama import OllamaProvider
from app.providers.cloud import OpenAIProvider, AnthropicProvider, MockLLMProvider


def get_llm_provider(name: Optional[str] = None) -> BaseLLMProvider:
    """Factory creating configured LLM provider instance."""
    settings = get_settings()
    provider_name = (name or settings.llm_provider or "ollama").strip().lower()

    if provider_name == "ollama":
        return OllamaProvider(
            base_url=settings.ollama_base_url,
            model=settings.ollama_model,
            timeout=settings.llm_timeout_seconds,
        )
    elif provider_name == "openai":
        return OpenAIProvider(
            api_key=settings.openai_api_key,
            model=settings.openai_model,
            timeout=settings.llm_timeout_seconds,
        )
    elif provider_name == "anthropic":
        return AnthropicProvider(
            api_key=settings.anthropic_api_key,
            model=settings.anthropic_model,
            timeout=settings.llm_timeout_seconds,
        )
    elif provider_name in ("mock", "test", "local"):
        return MockLLMProvider()
    else:
        raise ProviderConfigurationException(
            provider=provider_name,
            message=f"Unsupported LLM provider '{provider_name}'. Must be one of: 'ollama', 'openai', 'anthropic', 'mock'.",
        )
