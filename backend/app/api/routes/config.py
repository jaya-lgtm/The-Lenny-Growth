from typing import List, Dict, Any
from fastapi import APIRouter, status
from pydantic import BaseModel

from app.config import get_settings
from app.providers.factory import get_llm_provider
from app.providers.base import ProviderStatus

router = APIRouter(tags=["Configuration"])


class ConfigResponse(BaseModel):
    app_name: str
    environment: str
    active_llm_provider: str
    active_llm_model: str
    active_embedding_provider: str
    active_embedding_model: str
    retrieval_top_k: int
    available_providers: List[ProviderStatus]


@router.get(
    "/config",
    response_model=ConfigResponse,
    status_code=status.HTTP_200_OK,
    summary="Get non-secret runtime configuration and provider statuses",
)
def get_config() -> ConfigResponse:
    settings = get_settings()
    statuses: List[ProviderStatus] = []

    for name in ["ollama", "openai", "anthropic", "mock"]:
        try:
            prov = get_llm_provider(name)
            statuses.append(prov.health_check())
        except Exception as e:
            statuses.append(
                ProviderStatus(
                    provider=name,
                    model="unknown",
                    is_available=False,
                    status_message=str(e),
                )
            )

    return ConfigResponse(
        app_name=settings.app_name,
        environment=settings.environment,
        active_llm_provider=settings.llm_provider,
        active_llm_model=settings.ollama_model if settings.llm_provider == "ollama" else (
            settings.openai_model if settings.llm_provider == "openai" else (
                settings.anthropic_model if settings.llm_provider == "anthropic" else "mock-growth-v1"
            )
        ),
        active_embedding_provider=settings.embedding_provider,
        active_embedding_model=settings.ollama_embedding_model,
        retrieval_top_k=settings.retrieval_top_k,
        available_providers=statuses,
    )
