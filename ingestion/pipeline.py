import argparse
import logging
import sys
import uuid
from pathlib import Path
from typing import Dict, Any, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

# Add project root to sys.path
root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))
backend_dir = root_dir / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.db.session import SessionLocal
from app.models.document import DocumentModel
from app.models.chunk import DocumentChunkModel
from ingestion.config import IngestionConfig, get_ingestion_config
from ingestion.loaders import load_directory, load_file
from ingestion.chunker import DocumentChunker
from ingestion.embedder import get_embedder, BaseEmbedder

logger = logging.getLogger("ingestion.pipeline")


import subprocess
import time

def clone_or_update_repo(repo_url: str, target_dir: Path) -> bool:
    """Clone or pull the required transcript repository idempotently."""
    target_dir.parent.mkdir(parents=True, exist_ok=True)
    if (target_dir / ".git").exists():
        logger.info(f"Repository already exists at {target_dir}. Running git pull...")
        try:
            res = subprocess.run(
                ["git", "-C", str(target_dir), "pull"],
                capture_output=True,
                text=True,
                timeout=30,
            )
            logger.info(f"git pull completed: {res.stdout.strip() or 'up to date'}")
            return True
        except Exception as e:
            logger.warning(f"git pull failed (offline or network issue, using existing files): {e}")
            return True
    else:
        logger.info(f"Cloning transcript corpus from {repo_url} into {target_dir}...")
        try:
            res = subprocess.run(
                ["git", "clone", "--depth", "1", repo_url, str(target_dir)],
                capture_output=True,
                text=True,
                timeout=120,
            )
            if res.returncode != 0:
                logger.error(f"git clone failed: {res.stderr}")
                return False
            logger.info(f"Successfully cloned {repo_url} into {target_dir}")
            return True
        except Exception as e:
            logger.error(f"git clone failed: {e}")
            return False


class IngestionPipeline:
    """End-to-end ingestion pipeline for transcripts and newsletters."""

    def __init__(
        self,
        config: Optional[IngestionConfig] = None,
        embedder: Optional[BaseEmbedder] = None,
    ):
        self.config = config or get_ingestion_config()
        self.chunker = DocumentChunker(
            chunk_size=self.config.chunk_size,
            chunk_overlap=self.config.chunk_overlap,
        )
        self.embedder = embedder or get_embedder(self.config.embedding_provider)

    def clean_synthetic_demo_docs(self, db: Session) -> int:
        """Remove previously seeded synthetic demo documents without affecting user sessions or messages."""
        stmt = select(DocumentModel).where(
            (DocumentModel.external_id.like("%demo%"))
            | (DocumentModel.title.like("Demo %"))
        )
        demo_docs = db.scalars(stmt).all()
        count = len(demo_docs)
        for d in demo_docs:
            db.delete(d)
        if count > 0:
            db.commit()
            logger.info(f"Cleaned {count} synthetic demo documents from database.")
        return count

    def prune_stale_documents(self, db: Session, active_hashes: set) -> int:
        """Remove documents that are no longer present in the source files, preserving all sessions and messages."""
        stmt = select(DocumentModel)
        all_docs = db.scalars(stmt).all()
        stale = [
            d for d in all_docs
            if d.content_hash not in active_hashes and d.external_id not in active_hashes
        ]
        count = len(stale)
        for d in stale:
            db.delete(d)
        if count > 0:
            db.commit()
            logger.info(f"Pruned {count} stale documents from database.")
        return count

    def run(
        self,
        db: Session,
        force_reingest: bool = False,
        clean_demo: bool = True,
        prune_stale: bool = False,
        limit: Optional[int] = None,
    ) -> Dict[str, Any]:
        start_time = time.time()
        data_path = Path(self.config.data_dir)
        if not data_path.is_absolute():
            data_path = root_dir / data_path

        # Step 1: Clean synthetic demo docs if requested
        cleaned_demo_count = 0
        if clean_demo:
            cleaned_demo_count = self.clean_synthetic_demo_docs(db)

        logger.info(f"Starting ingestion from: {data_path}")
        discovered_docs = load_directory(data_path)
        if limit and limit > 0:
            discovered_docs = discovered_docs[:limit]

        metrics = {
            "discovered": len(discovered_docs),
            "inserted": 0,
            "skipped": 0,
            "failed": 0,
            "chunks_created": 0,
            "cleaned_demo": cleaned_demo_count,
            "pruned_stale": 0,
            "elapsed_seconds": 0.0,
            "errors": [],
        }

        active_hashes = set()

        for idx, doc in enumerate(discovered_docs, 1):
            active_hashes.add(doc.content_hash)
            if doc.external_id:
                active_hashes.add(doc.external_id)

            try:
                # Check for existing document by content_hash or external_id
                existing = db.scalars(
                    select(DocumentModel).where(
                        (DocumentModel.content_hash == doc.content_hash)
                        | (DocumentModel.external_id == doc.external_id)
                    )
                ).first()

                if existing and not force_reingest:
                    metrics["skipped"] += 1
                    continue

                if existing and force_reingest:
                    db.delete(existing)
                    db.flush()

                # Create document model
                doc_record = DocumentModel(
                    id=uuid.uuid4(),
                    source_type=doc.source_type,
                    title=doc.title,
                    source_url=doc.source_url,
                    published_at=doc.published_at,
                    external_id=doc.external_id,
                    content_hash=doc.content_hash,
                    doc_metadata=doc.metadata,
                )
                db.add(doc_record)
                db.flush()

                # Chunk document
                chunks = self.chunker.chunk_document(doc)
                if not chunks:
                    logger.warning(f"No chunks produced for: {doc.title}")
                    continue

                # Generate embeddings
                contents = [c.content for c in chunks]
                try:
                    embeddings = self.embedder.embed_batch(contents)
                except Exception as e:
                    logger.warning(f"Embedder failed: {e}. Falling back to deterministic local embedder.")
                    from ingestion.embedder import DeterministicLocalEmbedder
                    fallback = DeterministicLocalEmbedder(dim=self.embedder.dimension)
                    embeddings = fallback.embed_batch(contents)

                # Store chunks in batch
                chunk_records = [
                    DocumentChunkModel(
                        id=uuid.uuid4(),
                        document_id=doc_record.id,
                        chunk_index=chunk.chunk_index,
                        content=chunk.content,
                        token_count=chunk.token_count,
                        embedding=emb,
                        chunk_metadata=chunk.metadata,
                    )
                    for chunk, emb in zip(chunks, embeddings)
                ]
                db.add_all(chunk_records)
                db.commit()

                metrics["inserted"] += 1
                metrics["chunks_created"] += len(chunks)

                if idx % 25 == 0 or idx == len(discovered_docs):
                    logger.info(
                        f"[{idx}/{len(discovered_docs)}] Ingested '{doc.title[:40]}' ({len(chunks)} chunks). Total chunks: {metrics['chunks_created']}"
                    )

            except Exception as e:
                db.rollback()
                logger.error(f"Failed to ingest '{doc.title}': {str(e)}")
                metrics["failed"] += 1
                metrics["errors"].append({"document": doc.title, "error": str(e)})

        # Step 2: Prune stale documents if requested
        if prune_stale and active_hashes:
            metrics["pruned_stale"] = self.prune_stale_documents(db, active_hashes)

        metrics["elapsed_seconds"] = round(time.time() - start_time, 2)
        logger.info(f"Ingestion complete in {metrics['elapsed_seconds']}s: {metrics}")
        return metrics


def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    parser = argparse.ArgumentParser(description="Ingest Lenny Podcast transcripts from ChatPRD into pgvector")
    parser.add_argument("--data-dir", type=str, default=None, help="Directory containing transcripts")
    parser.add_argument("--provider", type=str, default=None, help="Embedding provider (ollama, openai, local)")
    parser.add_argument("--force", action="store_true", help="Force re-ingest existing documents")
    parser.add_argument("--clone", action="store_true", help="Clone or pull required transcript repository first")
    parser.add_argument("--repo-url", type=str, default="https://github.com/ChatPRD/lennys-podcast-transcripts", help="Git repo URL to clone")
    parser.add_argument("--clean-demo", action="store_true", default=True, help="Clean synthetic demo documents from database")
    parser.add_argument("--prune-stale", action="store_true", help="Prune documents no longer in corpus")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of documents to ingest")
    args = parser.parse_args()

    cfg = get_ingestion_config()
    if args.data_dir:
        cfg.data_dir = Path(args.data_dir)
    if args.provider:
        cfg.embedding_provider = args.provider
    if args.repo_url:
        cfg.corpus_repo_url = args.repo_url

    # Run git clone/pull if requested
    if args.clone:
        target_dir = cfg.data_dir if cfg.data_dir.is_absolute() else (root_dir / cfg.data_dir)
        clone_or_update_repo(cfg.corpus_repo_url, target_dir)

    pipeline = IngestionPipeline(config=cfg)
    with SessionLocal() as db:
        result = pipeline.run(
            db=db,
            force_reingest=args.force,
            clean_demo=args.clean_demo,
            prune_stale=args.prune_stale,
            limit=args.limit,
        )
        print("\n==========================================")
        print("     CHATPRD TRANSCRIPT INGESTION REPORT   ")
        print("==========================================")
        print(f"Repository:       {cfg.corpus_repo_url}")
        print(f"Directory:        {cfg.data_dir}")
        print(f"Discovered:       {result['discovered']}")
        print(f"Inserted:         {result['inserted']}")
        print(f"Skipped:          {result['skipped']}")
        print(f"Failed:           {result['failed']}")
        print(f"Chunks Created:   {result['chunks_created']}")
        print(f"Demo Docs Cleaned:{result['cleaned_demo']}")
        print(f"Stale Docs Pruned:{result['pruned_stale']}")
        print(f"Elapsed Time:     {result['elapsed_seconds']}s")
        if result["errors"]:
            print(f"Errors ({len(result['errors'])}):")
            for err in result["errors"][:5]:
                print(f"  - {err['document']}: {err['error']}")
        print("==========================================\n")


if __name__ == "__main__":
    main()
