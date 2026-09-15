import abc
import hashlib
import logging
import math
import re
import sys
from pathlib import Path
from typing import List, Optional
import httpx

backend_dir = Path(__file__).resolve().parent.parent / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.api.errors import AppException

logger = logging.getLogger("ingestion.embedder")


class EmbeddingException(AppException):
    def __init__(self, code: str, message: str, status_code: int = 503, details: any = None):
        super().__init__(code=code, message=message, status_code=status_code, details=details)


class BaseEmbedder(abc.ABC):
    @property
    @abc.abstractmethod
    def dimension(self) -> int:
        pass

    @abc.abstractmethod
    def embed_text(self, text: str) -> List[float]:
        pass

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        return [self.embed_text(t) for t in texts]


class DeterministicLocalEmbedder(BaseEmbedder):
    """
    Deterministic 768-dimensional local embedder for offline evaluation,
    testing, and fallback when local Ollama is not installed or running.
    Uses token hashing and n-gram term frequencies to produce normalized unit vectors.
    """

    def __init__(self, dim: int = 768):
        self._dim = dim

    @property
    def dimension(self) -> int:
        return self._dim

    def embed_text(self, text: str) -> List[float]:
        if not text or not text.strip():
            return [0.0] * self._dim

        vec = [0.0] * self._dim
        tokens = re.findall(r"\w+", text.lower())

        for token in tokens:
            # Deterministic bucket
            h = int(hashlib.md5(token.encode("utf-8")).hexdigest(), 16)
            idx = h % self._dim
            sign = 1.0 if (h >> 8) & 1 else -1.0
            vec[idx] += sign

        # Add bigram hashes for context
        for i in range(len(tokens) - 1):
            bigram = f"{tokens[i]}_{tokens[i+1]}"
            h = int(hashlib.md5(bigram.encode("utf-8")).hexdigest(), 16)
            idx = h % self._dim
            sign = 1.0 if (h >> 8) & 1 else -1.0
            vec[idx] += 0.5 * sign

        # L2 Normalize
        norm = math.sqrt(sum(v * v for v in vec))
        if norm > 0:
            vec = [round(v / norm, 6) for v in vec]
        else:
            vec[0] = 1.0
        return vec


class OllamaEmbedder(BaseEmbedder):
    """Ollama embedding client calling /api/embeddings (e.g. nomic-embed-text)."""

    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        model: str = "nomic-embed-text",
        dim: int = 768,
        timeout: float = 15.0,
    ):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self._dim = dim
        self.timeout = timeout

    @property
    def dimension(self) -> int:
        return self._dim

    def embed_text(self, text: str) -> List[float]:
        if not text or not text.strip():
            return [0.0] * self._dim

        url = f"{self.base_url}/api/embeddings"
        payload = {"model": self.model, "prompt": text}

        try:
            with httpx.Client(timeout=self.timeout) as client:
                res = client.post(url, json=payload)

                if res.status_code == 404:
                    raise EmbeddingException(
                        code="OLLAMA_MODEL_NOT_FOUND",
                        message=f"Embedding model '{self.model}' was not found in Ollama. Run: `ollama pull {self.model}`.",
                        status_code=503,
                    )
                if res.status_code != 200:
                    raise EmbeddingException(
                        code="OLLAMA_ERROR",
                        message=f"Ollama returned HTTP {res.status_code}: {res.text[:200]}",
                        status_code=503,
                    )

                data = res.json()
                embedding = data.get("embedding")
                if not embedding or not isinstance(embedding, list):
                    raise EmbeddingException(
                        code="OLLAMA_INVALID_RESPONSE",
                        message="Ollama returned an empty or invalid embedding payload.",
                        status_code=503,
                    )
                return embedding

        except (httpx.ConnectError, httpx.ConnectTimeout) as e:
            logger.warning(f"Ollama embedding unavailable at {self.base_url}: {e}")
            raise EmbeddingException(
                code="OLLAMA_UNAVAILABLE",
                message=f"Cannot connect to Ollama at {self.base_url}. Ensure Ollama is running (`ollama serve`).",
                status_code=503,
            )
        except httpx.TimeoutException:
            logger.warning(f"Ollama embedding timed out after {self.timeout}s")
            raise EmbeddingException(
                code="OLLAMA_TIMEOUT",
                message=f"Embedding generation timed out after {self.timeout}s.",
                status_code=504,
            )


class OpenAIEmbedder(BaseEmbedder):
    """OpenAI embedding client calling /v1/embeddings."""

    def __init__(
        self,
        api_key: str,
        model: str = "text-embedding-3-small",
        dim: int = 768,
        timeout: float = 15.0,
    ):
        self.api_key = api_key
        self.model = model
        self._dim = dim
        self.timeout = timeout

    @property
    def dimension(self) -> int:
        return self._dim

    def embed_text(self, text: str) -> List[float]:
        if not self.api_key:
            raise EmbeddingException(
                code="OPENAI_API_KEY_MISSING",
                message="OpenAI API key is missing. Set OPENAI_API_KEY in environment or .env.",
                status_code=400,
            )
        url = "https://api.openai.com/v1/embeddings"
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        payload = {"model": self.model, "input": text, "dimensions": self._dim}

        try:
            with httpx.Client(timeout=self.timeout) as client:
                res = client.post(url, headers=headers, json=payload)
                if res.status_code != 200:
                    raise EmbeddingException(
                        code="OPENAI_EMBEDDING_ERROR",
                        message=f"OpenAI returned HTTP {res.status_code}: {res.text[:200]}",
                        status_code=503,
                    )
                data = res.json()
                return data["data"][0]["embedding"]
        except Exception as e:
            raise EmbeddingException(
                code="OPENAI_EMBEDDING_FAILED",
                message=f"OpenAI embedding request failed: {str(e)}",
                status_code=503,
            )


def get_embedder(provider_name: Optional[str] = None) -> BaseEmbedder:
    from app.config import get_settings
    settings = get_settings()
    name = (provider_name or settings.embedding_provider or "ollama").lower()

    if name == "ollama":
        return OllamaEmbedder(
            base_url=settings.ollama_base_url,
            model=settings.ollama_embedding_model,
            dim=settings.embedding_dim,
        )
    elif name in ("openai", "cloud"):
        return OpenAIEmbedder(
            api_key=settings.openai_api_key,
            model="text-embedding-3-small",
            dim=settings.embedding_dim,
        )
    elif name in ("local", "mock", "deterministic"):
        return DeterministicLocalEmbedder(dim=settings.embedding_dim)
    else:
        # Default to local deterministic if unknown
        return DeterministicLocalEmbedder(dim=settings.embedding_dim)
