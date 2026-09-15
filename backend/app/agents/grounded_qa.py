import logging
from typing import List, Optional
from app.agents.schemas import AgentContext, AgentOutput, SourceCitation
from app.agents.prompts import (
    GROUNDED_QA_SYSTEM_PROMPT,
    GROUNDED_QA_CONTEXT_TEMPLATE,
    UNSUPPORTED_QUESTION_RESPONSE,
)
from app.providers.base import BaseLLMProvider
from app.retrieval.schemas import RetrievalResult
from app.agents.pi_agent_runner import PiGroundedAgent

logger = logging.getLogger("backend.agents.grounded_qa")


class GroundedQAAgent:
    """
    Grounded Q&A Agent built on the assignment-required Pi Coding Agent framework.
    Delegates reasoning, sandbox execution, and tool-assisted grounding to PiGroundedAgent.
    """

    def __init__(self, provider: BaseLLMProvider):
        self.provider = provider
        self.pi_agent = PiGroundedAgent(provider=provider)

    def run(self, context: AgentContext, retrieval_results: List[RetrievalResult]) -> AgentOutput:
        from app.agents.skills.router import IntentRouter

        # If user query is a conversational greeting/pleasantry, run naturally through Pi Agent without forcing citations
        if IntentRouter.is_conversational(context.user_question):
            return self.pi_agent.run(context=context, retrieval_results=[])

        # For substantive questions: if retrieval returned zero evidence, honestly acknowledge limitation
        if not retrieval_results:
            return AgentOutput(
                content=UNSUPPORTED_QUESTION_RESPONSE,
                provider=self.provider.provider_name,
                model=self.provider.model_name,
                retrieval_count=0,
                sources=[],
                raw_metadata={"framework": "pi-coding-agent", "unsupported": True},
            )

        # Delegate execution to Pi Coding Agent framework
        return self.pi_agent.run(context=context, retrieval_results=retrieval_results)

