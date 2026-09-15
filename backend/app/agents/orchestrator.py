from datetime import datetime, timezone
import logging
from typing import Optional, Dict, Any, Tuple
import uuid
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models.message import MessageModel
from app.models.artifact import ArtifactModel
from app.services.session_service import SessionService
from app.services.message_service import MessageService
from app.services.artifact_service import ArtifactService
from app.schemas.artifact import ArtifactCreate
from app.retrieval.retriever import VectorRetriever
from app.providers.factory import get_llm_provider
from app.agents.schemas import AgentContext, SourceCitation
from app.agents.grounded_qa import GroundedQAAgent
from app.agents.skills.router import IntentRouter
from app.agents.skills.generators import generate_mock_artifact
from app.services.title_generator import generate_session_title

logger = logging.getLogger("backend.agents.orchestrator")


class AgentOrchestrator:
    """
    Coordinates chat turn: intent routing, retrieval, context construction,
    agent execution, artifact persistence, and message persistence.
    Powered by the Pi Coding Agent framework.
    """

    def __init__(self, retriever: Optional[VectorRetriever] = None):
        self.retriever = retriever or VectorRetriever()

    def process_chat_turn(
        self,
        db: Session,
        session_id: uuid.UUID,
        user_message: str,
        provider_name: Optional[str] = None,
        mode: Optional[str] = "auto",
        top_k: int = 5,
        similarity_threshold: Optional[float] = None,
    ) -> MessageModel:
        # 1. Verify parent session exists (raises SessionNotFoundException if missing)
        session = SessionService.get_session(db, session_id)

        # Auto-name session from user query if session currently has the default placeholder title
        if not session.title or session.title.strip() == "New Conversation" or session.title.startswith("New Conversation"):
            session.title = generate_session_title(user_message)
            logger.info(f"Auto-named session {session_id} to '{session.title}'")

        # 2. Classify user intent and route to specialized skill
        effective_mode, skill_name = IntentRouter.classify(user_message, explicit_mode=mode)
        logger.info(f"Routed query in session {session_id} to skill: {skill_name} (mode: {effective_mode})")

        # 3. Fetch existing messages for context
        history_models = MessageService.list_messages(db, session_id)
        history = [
            {"role": m.role, "content": m.content}
            for m in history_models
        ]

        # 4. Persist user message
        now_user = datetime.now(timezone.utc)
        user_record = MessageModel(
            id=uuid.uuid4(),
            session_id=session_id,
            role="user",
            content=user_message,
            created_at=now_user,
        )
        db.add(user_record)
        db.flush()

        # 5. Resolve LLM provider
        provider = get_llm_provider(name=provider_name)

        # 6. Retrieve relevant transcript chunks (LLM-evaluated)
        needs_retrieval = True
        if effective_mode == "grounded_qa":
            needs_retrieval = IntentRouter.should_retrieve(provider=provider, user_message=user_message)

        if not needs_retrieval:
            retrieval_results = []
            logger.info(f"LLM routed message in session {session_id} to conversation. Skipping vector retrieval.")
        else:
            settings = get_settings()
            effective_provider = (provider_name or settings.llm_provider).lower()
            if effective_provider in ("mock", "local", "test") or settings.embedding_provider in ("mock", "local", "test"):
                from ingestion.embedder import DeterministicLocalEmbedder
                retriever = VectorRetriever(embedder=DeterministicLocalEmbedder(dim=768))
            else:
                retriever = self.retriever

            retrieval_results = retriever.retrieve(
                db=db,
                query=user_message,
                top_k=top_k,
                similarity_threshold=similarity_threshold,
            )

        # 7. Execute Grounded Q&A Agent / Skill
        agent = GroundedQAAgent(provider=provider)
        context = AgentContext(
            session_id=session_id,
            user_question=user_message,
            conversation_history=history,
            retrieved_chunks=retrieval_results,
            provider_override=provider_name,
        )
        agent_output = agent.run(context=context, retrieval_results=retrieval_results)

        # 8. Persist assistant response
        now_assistant = datetime.now(timezone.utc)
        assistant_id = uuid.uuid4()
        meta_dict = {
            "model": agent_output.model,
            "retrieval_count": agent_output.retrieval_count,
            "sources": [s.model_dump() for s in agent_output.sources],
            "agent_framework": "pi-coding-agent",
            "mode": effective_mode,
            "skill_name": skill_name,
        }

        assistant_record = MessageModel(
            id=assistant_id,
            session_id=session_id,
            role="assistant",
            content=agent_output.content,
            provider=agent_output.provider,
            message_metadata=meta_dict,
            created_at=now_assistant,
        )
        db.add(assistant_record)
        db.flush()

        # 9. If specialized artifact mode requested and retrieval succeeded, generate and persist artifact
        artifact_record = None
        if effective_mode != "grounded_qa" and retrieval_results:
            art_data = generate_mock_artifact(
                mode=effective_mode,
                query=user_message,
                citations=agent_output.sources,
            )
            artifact_in = ArtifactCreate(
                session_id=session_id,
                message_id=assistant_id,
                artifact_type=effective_mode,
                content_format=art_data["content_format"],
                schema_version=art_data.get("schema_version", "v1.0"),
                title=art_data["title"],
                content=art_data["content"],
                artifact_metadata=art_data.get("artifact_metadata", {}),
            )
            artifact_record = ArtifactService.create_artifact(
                db=db,
                session_id=session_id,
                message_id=assistant_id,
                artifact_in=artifact_in,
            )
            meta_dict["artifact_id"] = str(artifact_record.id)
            meta_dict["artifact_type"] = artifact_record.artifact_type
            meta_dict["content_format"] = artifact_record.content_format
            meta_dict["schema_version"] = artifact_record.schema_version

            # Update assistant content with executive intro pointing to artifact
            assistant_record.content = (
                f"I have synthesized the requested **{skill_name}** grounded in insights from "
                f"the transcript corpus.\n\n"
                f"{agent_output.content}\n\n"
                f"👉 **Click the artifact card below to open the complete artifact in the Artifact Viewer.**"
            )
            assistant_record.message_metadata = dict(meta_dict)
            from sqlalchemy.orm.attributes import flag_modified
            flag_modified(assistant_record, "message_metadata")
            db.flush()

        # 10. Bump session updated_at
        session.updated_at = now_assistant

        db.commit()
        db.refresh(assistant_record)
        db.refresh(session)

        if artifact_record:
            assistant_record.artifact = artifact_record

        return assistant_record
