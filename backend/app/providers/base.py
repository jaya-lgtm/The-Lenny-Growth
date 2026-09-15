import abc
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from app.api.errors import AppException


class ProviderUnavailableException(AppException):
    def __init__(self, provider: str, message: str, details: Any = None):
        super().__init__(
            code="PROVIDER_UNAVAILABLE",
            message=f"LLM Provider '{provider}' is unavailable: {message}",
            status_code=503,
            details=details,
        )


class ProviderConfigurationException(AppException):
    def __init__(self, provider: str, message: str, details: Any = None):
        super().__init__(
            code="PROVIDER_CONFIG_ERROR",
            message=f"LLM Provider '{provider}' configuration error: {message}",
            status_code=400,
            details=details,
        )


class LLMResponse(BaseModel):
    content: str
    provider: str
    model: str
    token_usage: Dict[str, int] = Field(default_factory=dict)
    raw_metadata: Dict[str, Any] = Field(default_factory=dict)


class ProviderStatus(BaseModel):
    provider: str
    model: str
    is_available: bool
    status_message: str


class BaseLLMProvider(abc.ABC):
    """Abstract interface for all LLM inference providers."""

    @property
    @abc.abstractmethod
    def provider_name(self) -> str:
        pass

    @property
    @abc.abstractmethod
    def model_name(self) -> str:
        pass

    @abc.abstractmethod
    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 1500,
        temperature: float = 0.2,
        **kwargs,
    ) -> LLMResponse:
        pass

    @abc.abstractmethod
    def health_check(self) -> ProviderStatus:
        pass
