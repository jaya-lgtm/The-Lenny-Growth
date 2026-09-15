import hashlib
import re
from typing import List, Dict, Any
from pydantic import BaseModel, Field
from ingestion.loaders import LoadedDocument


class Chunk(BaseModel):
    chunk_index: int
    content: str
    token_count: int
    chunk_hash: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class DocumentChunker:
    """Paragraph and sentence aware text chunker with configurable overlap."""

    def __init__(self, chunk_size: int = 800, chunk_overlap: int = 150):
        if chunk_overlap >= chunk_size:
            raise ValueError("chunk_overlap must be strictly less than chunk_size")
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def chunk_text(self, text: str, doc_metadata: Dict[str, Any] = None) -> List[Chunk]:
        if not text or not text.strip():
            return []

        doc_metadata = doc_metadata or {}
        # Break text by paragraphs first
        paragraphs = text.split("\n\n")
        chunks: List[Chunk] = []

        current_text = ""
        chunk_idx = 0

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue

            # If adding this paragraph exceeds chunk_size and we already have content
            if len(current_text) + len(para) + 2 > self.chunk_size and current_text:
                # Save current chunk
                chunk_str = current_text.strip()
                chunks.append(self._create_chunk(chunk_str, chunk_idx, doc_metadata))
                chunk_idx += 1

                # Calculate overlap: take the tail of current_text
                overlap_text = current_text[-self.chunk_overlap:] if len(current_text) > self.chunk_overlap else current_text
                # Find space in overlap to avoid slicing mid-word
                space_idx = overlap_text.find(" ")
                if space_idx != -1 and space_idx < len(overlap_text) - 10:
                    overlap_text = overlap_text[space_idx + 1:]

                current_text = overlap_text + "\n\n" + para
            else:
                if current_text:
                    current_text += "\n\n" + para
                else:
                    current_text = para

        # Remaining text
        if current_text.strip():
            chunks.append(self._create_chunk(current_text.strip(), chunk_idx, doc_metadata))

        return chunks

    def chunk_document(self, doc: LoadedDocument) -> List[Chunk]:
        base_meta = {
            "title": doc.title,
            "source_type": doc.source_type,
            "source_url": doc.source_url,
            "external_id": doc.external_id,
            "content_hash": doc.content_hash,
            **doc.metadata,
        }
        return self.chunk_text(doc.content, base_meta)

    def _create_chunk(self, text: str, chunk_index: int, doc_metadata: Dict[str, Any]) -> Chunk:
        token_count = len(text.split())
        chunk_hash = hashlib.sha256(f"{doc_metadata.get('content_hash', '')}_{chunk_index}_{text}".encode("utf-8")).hexdigest()
        meta = {
            **doc_metadata,
            "chunk_index": chunk_index,
            "char_count": len(text),
        }
        return Chunk(
            chunk_index=chunk_index,
            content=text,
            token_count=token_count,
            chunk_hash=chunk_hash,
            metadata=meta,
        )
