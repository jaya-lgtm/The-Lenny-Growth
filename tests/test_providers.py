import pytest
from app.providers.factory import get_llm_provider
from app.providers.ollama import OllamaProvider
from app.providers.cloud import OpenAIProvider, AnthropicProvider, MockLLMProvider
from app.providers.base import ProviderUnavailableException, ProviderConfigurationException


def test_provider_factory_resolution():
    """Provider factory instantiates correct classes based on requested name."""
    ollama = get_llm_provider("ollama")
    assert isinstance(ollama, OllamaProvider)
    assert ollama.provider_name == "ollama"

    mock = get_llm_provider("mock")
    assert isinstance(mock, MockLLMProvider)
    assert mock.provider_name == "mock"

    openai = get_llm_provider("openai")
    assert isinstance(openai, OpenAIProvider)
    assert openai.provider_name == "openai"

    anthropic = get_llm_provider("anthropic")
    assert isinstance(anthropic, AnthropicProvider)
    assert anthropic.provider_name == "anthropic"


def test_invalid_provider_name_raises():
    """Requesting an unknown provider raises ProviderConfigurationException."""
    with pytest.raises(ProviderConfigurationException) as exc:
        get_llm_provider("non_existent_provider")
    assert "Unsupported LLM provider" in str(exc.value.message)


def test_ollama_unavailable_handling():
    """When Ollama cannot connect, it raises ProviderUnavailableException."""
    # Point to a dead port
    provider = OllamaProvider(base_url="http://127.0.0.1:59999", timeout=1.0)
    with pytest.raises(ProviderUnavailableException) as exc:
        provider.generate("test prompt")
    assert "Could not connect to Ollama" in str(exc.value.message)
    assert exc.value.status_code == 503


def test_missing_openai_api_key_raises():
    """OpenAIProvider raises ProviderConfigurationException when API key is empty."""
    provider = OpenAIProvider(api_key="")
    with pytest.raises(ProviderConfigurationException) as exc:
        provider.generate("test prompt")
    assert "OPENAI_API_KEY environment variable is required" in str(exc.value.message)
    assert exc.value.status_code == 400


def test_missing_anthropic_api_key_raises():
    """AnthropicProvider raises ProviderConfigurationException when API key is empty."""
    provider = AnthropicProvider(api_key="")
    with pytest.raises(ProviderConfigurationException) as exc:
        provider.generate("test prompt")
    assert "ANTHROPIC_API_KEY environment variable is required" in str(exc.value.message)
    assert exc.value.status_code == 400


def test_mock_provider_generation():
    """MockProvider returns grounded answers containing evidence context."""
    provider = MockLLMProvider()
    res = provider.generate("How do I improve user activation?")
    assert "activation" in res.content.lower()
    assert res.provider == "mock"
    assert "Aha! Moment" in res.content
