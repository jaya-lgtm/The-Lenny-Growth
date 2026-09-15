from pathlib import Path
import sys
from typing import List, Optional

root_dir = Path(__file__).resolve().parent.parent.parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from app.config import get_settings
from ingestion.embedder import get_embedder, BaseEmbedder

_cached_embedder: Optional[BaseEmbedder] = None


def get_query_embedder() -> BaseEmbedder:
    global _cached_embedder
    if _cached_embedder is None:
        settings = get_settings()
        _cached_embedder = get_embedder(settings.embedding_provider)
    return _cached_embedder


def embed_query_text(text: str) -> List[float]:
    """Generate vector embedding for a user query."""
    embedder = get_query_embedder()
    return embedder.embed_text(text)
