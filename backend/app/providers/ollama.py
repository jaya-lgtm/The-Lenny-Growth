import logging
from typing import Optional
import httpx
from app.providers.base import (
    BaseLLMProvider,
    LLMResponse,
    ProviderStatus,
    ProviderUnavailableException,
)

logger = logging.getLogger("backend.providers.ollama")


class OllamaProvider(BaseLLMProvider):
    """Local Ollama inference provider."""

    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        model: str = "llama3.1:8b",
        timeout: float = 30.0,
    ):
        self._base_url = base_url.rstrip("/")
        self._model = model
        self._timeout = timeout

    @property
    def provider_name(self) -> str:
        return "ollama"

    @property
    def model_name(self) -> str:
        return self._model

    def health_check(self) -> ProviderStatus:
        try:
            with httpx.Client(timeout=3.0) as client:
                res = client.get(f"{self._base_url}/api/tags")
                if res.status_code == 200:
                    models = [m.get("name", "") for m in res.json().get("models", [])]
                    has_model = any(self._model in m for m in models)
                    msg = "Online" if has_model else f"Ollama running, but model '{self._model}' not found. Run: `ollama pull {self._model}`"
                    return ProviderStatus(
                        provider=self.provider_name,
                        model=self.model_name,
                        is_available=has_model,
                        status_message=msg,
                    )
        except Exception as e:
            return ProviderStatus(
                provider=self.provider_name,
                model=self.model_name,
                is_available=False,
                status_message=f"Cannot connect to Ollama at {self._base_url}: {str(e)}",
            )
        return ProviderStatus(
            provider=self.provider_name,
            model=self.model_name,
            is_available=False,
            status_message=f"Ollama returned unexpected status",
        )

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 600,
        temperature: float = 0.2,
        **kwargs,
    ) -> LLMResponse:
        url = f"{self._base_url}/api/chat"
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self._model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
                "num_thread": 6,
            },
        }

        try:
            with httpx.Client(timeout=self._timeout) as client:
                res = client.post(url, json=payload)
                if res.status_code == 404:
                    raise ProviderUnavailableException(
                        self.provider_name,
                        f"Model '{self._model}' was not found in Ollama. Run: `ollama pull {self._model}`.",
                        details={"base_url": self._base_url, "model": self._model},
                    )
                if res.status_code != 200:
                    raise ProviderUnavailableException(
                        self.provider_name,
                        f"Ollama API error HTTP {res.status_code}: {res.text[:200]}",
                        details={"status_code": res.status_code},
                    )

                data = res.json()
                content = data.get("message", {}).get("content", "")
                eval_count = data.get("eval_count", 0)
                prompt_eval_count = data.get("prompt_eval_count", 0)

                return LLMResponse(
                    content=content,
                    provider=self.provider_name,
                    model=self.model_name,
                    token_usage={
                        "prompt_tokens": prompt_eval_count,
                        "completion_tokens": eval_count,
                        "total_tokens": prompt_eval_count + eval_count,
                    },
                    raw_metadata={"total_duration": data.get("total_duration")},
                )
        except (httpx.ConnectError, httpx.ConnectTimeout) as e:
            logger.warning(f"Ollama connection error at {self._base_url}: {e}")
            raise ProviderUnavailableException(
                self.provider_name,
                f"Could not connect to Ollama daemon at {self._base_url}. Please ensure Ollama is installed and running (`ollama serve`).",
                details={"base_url": self._base_url},
            )
        except httpx.TimeoutException:
            logger.warning(f"Ollama timed out after {self._timeout}s")
            raise ProviderUnavailableException(
                self.provider_name,
                f"Request to Ollama timed out after {self._timeout} seconds.",
                details={"timeout": self._timeout},
            )
