import logging
from typing import Optional
import httpx
from app.providers.base import (
    BaseLLMProvider,
    LLMResponse,
    ProviderStatus,
    ProviderUnavailableException,
    ProviderConfigurationException,
)

logger = logging.getLogger("backend.providers.cloud")


class OpenAIProvider(BaseLLMProvider):
    """OpenAI Cloud inference provider via REST API."""

    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4o-mini",
        timeout: float = 30.0,
    ):
        self._api_key = api_key
        self._model = model
        self._timeout = timeout

    @property
    def provider_name(self) -> str:
        return "openai"

    @property
    def model_name(self) -> str:
        return self._model

    def health_check(self) -> ProviderStatus:
        if not self._api_key:
            return ProviderStatus(
                provider=self.provider_name,
                model=self.model_name,
                is_available=False,
                status_message="OPENAI_API_KEY is not configured.",
            )
        return ProviderStatus(
            provider=self.provider_name,
            model=self.model_name,
            is_available=True,
            status_message="API key configured.",
        )

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 1500,
        temperature: float = 0.2,
        **kwargs,
    ) -> LLMResponse:
        if not self._api_key:
            raise ProviderConfigurationException(
                self.provider_name,
                "OPENAI_API_KEY environment variable is required to use OpenAI provider.",
            )

        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self._model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }

        try:
            with httpx.Client(timeout=self._timeout) as client:
                res = client.post(url, headers=headers, json=payload)
                if res.status_code == 401:
                    raise ProviderConfigurationException(
                        self.provider_name,
                        "Invalid OpenAI API key. Check OPENAI_API_KEY.",
                    )
                if res.status_code != 200:
                    raise ProviderUnavailableException(
                        self.provider_name,
                        f"OpenAI API error HTTP {res.status_code}: {res.text[:200]}",
                    )
                data = res.json()
                content = data["choices"][0]["message"]["content"]
                usage = data.get("usage", {})

                return LLMResponse(
                    content=content,
                    provider=self.provider_name,
                    model=self.model_name,
                    token_usage={
                        "prompt_tokens": usage.get("prompt_tokens", 0),
                        "completion_tokens": usage.get("completion_tokens", 0),
                        "total_tokens": usage.get("total_tokens", 0),
                    },
                )
        except (httpx.ConnectError, httpx.TimeoutException) as e:
            raise ProviderUnavailableException(
                self.provider_name,
                f"OpenAI connection error: {str(e)}",
            )


class AnthropicProvider(BaseLLMProvider):
    """Anthropic Cloud inference provider via REST API."""

    def __init__(
        self,
        api_key: str,
        model: str = "claude-3-5-sonnet-20241022",
        timeout: float = 30.0,
    ):
        self._api_key = api_key
        self._model = model
        self._timeout = timeout

    @property
    def provider_name(self) -> str:
        return "anthropic"

    @property
    def model_name(self) -> str:
        return self._model

    def health_check(self) -> ProviderStatus:
        if not self._api_key:
            return ProviderStatus(
                provider=self.provider_name,
                model=self.model_name,
                is_available=False,
                status_message="ANTHROPIC_API_KEY is not configured.",
            )
        return ProviderStatus(
            provider=self.provider_name,
            model=self.model_name,
            is_available=True,
            status_message="API key configured.",
        )

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 1500,
        temperature: float = 0.2,
        **kwargs,
    ) -> LLMResponse:
        if not self._api_key:
            raise ProviderConfigurationException(
                self.provider_name,
                "ANTHROPIC_API_KEY environment variable is required to use Anthropic provider.",
            )

        url = "https://api.anthropic.com/v1/messages"
        headers = {
            "x-api-key": self._api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self._model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        if system_prompt:
            payload["system"] = system_prompt

        try:
            with httpx.Client(timeout=self._timeout) as client:
                res = client.post(url, headers=headers, json=payload)
                if res.status_code == 401:
                    raise ProviderConfigurationException(
                        self.provider_name,
                        "Invalid Anthropic API key. Check ANTHROPIC_API_KEY.",
                    )
                if res.status_code != 200:
                    raise ProviderUnavailableException(
                        self.provider_name,
                        f"Anthropic API error HTTP {res.status_code}: {res.text[:200]}",
                    )
                data = res.json()
                content = data["content"][0]["text"]
                usage = data.get("usage", {})

                return LLMResponse(
                    content=content,
                    provider=self.provider_name,
                    model=self.model_name,
                    token_usage={
                        "prompt_tokens": usage.get("input_tokens", 0),
                        "completion_tokens": usage.get("output_tokens", 0),
                        "total_tokens": usage.get("input_tokens", 0) + usage.get("output_tokens", 0),
                    },
                )
        except (httpx.ConnectError, httpx.TimeoutException) as e:
            raise ProviderUnavailableException(
                self.provider_name,
                f"Anthropic connection error: {str(e)}",
            )


class MockLLMProvider(BaseLLMProvider):
    """Deterministic mock provider for automated tests and offline verification."""

    def __init__(self, model: str = "mock-growth-v1"):
        self._model = model

    @property
    def provider_name(self) -> str:
        return "mock"

    @property
    def model_name(self) -> str:
        return self._model

    def health_check(self) -> ProviderStatus:
        return ProviderStatus(
            provider=self.provider_name,
            model=self.model_name,
            is_available=True,
            status_message="Mock provider ready",
        )

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 1500,
        temperature: float = 0.2,
        **kwargs,
    ) -> LLMResponse:
        import re
        if "determine if the user's message requires retrieving" in prompt.lower():
            u_match = re.search(r'User message:\s*"([^"]+)"', prompt)
            u_text = u_match.group(1).lower().strip() if u_match else prompt.lower()
            if any(w in u_text for w in ["hi", "hello", "hey", "how are you", "who are you", "what can you do", "thanks", "thank you", "help"]):
                return LLMResponse(content="CONVERSATION", provider=self.provider_name, model=self.model_name)
        # Dynamic source extraction from prompt
        sources_found = re.findall(r'\[\d+\]\s*Source:\s*"([^"]+)"(?:\s*with\s*([^\n(]+))?', prompt)
        formatted_citations = []
        for title, guest in sources_found:
            g_str = f" with {guest.strip()}" if guest and guest.strip() else ""
            formatted_citations.append(f"\"{title.strip()}\"{g_str}")

        primary_citation = formatted_citations[0] if formatted_citations else "the available transcripts"
        all_citations_str = ", ".join(formatted_citations) if formatted_citations else primary_citation

        # Extract user question from prompt
        q_match = re.search(r"User Question:\s*(.+)", prompt, re.DOTALL)
        question_text = q_match.group(1).lower().strip() if q_match else prompt.lower().strip()

        is_greeting = any(
            re.search(rf"\b{word}\b", question_text)
            for word in ["hello", "hi", "hey", "greetings", "good morning", "good afternoon", "good evening", "who are you", "what can you do"]
        ) or question_text in ["hello", "hi", "hey", "help"]

        is_how_are_you = any(
            w in question_text for w in ["how are you", "how's it going", "how are you doing", "what's up"]
        )

        is_thanks = any(
            w in question_text for w in ["thank you", "thanks", "thx", "appreciate it"]
        )

        if is_how_are_you:
            content = (
                "I'm doing great, thanks for asking! 😊 Ready to explore product strategy, user activation, retention curves, or experimentation frameworks from Lenny's Podcast whenever you are. What are you working on today?"
            )
        elif is_thanks:
            content = (
                "You're very welcome! Let me know if you'd like to dig deeper into any specific episode insights or generate a prioritized plan."
            )
        elif is_greeting:
            content = (
                "Hey there! 👋 I'm **The Lenny Growth Assistant**.\n\n"
                "I'm here to help you solve product and growth challenges, grounded in real wisdom from over 270 Lenny's Podcast episodes.\n\n"
                "You can ask me questions like:\n"
                "- *What are the most important lessons from Lenny's Podcast about improving user activation?*\n"
                "- *How do I know if I have product-market fit?*\n"
                "- *Create a prioritized experiment plan to improve onboarding.*\n\n"
                "What product or growth challenge are you tackling today?"
            )
        # Transparent limitation check for substantive queries with no evidence
        elif (not sources_found and "no transcripts retrieved" in prompt.lower()) or "quantum physics" in question_text or "unsupported" in question_text:
            return LLMResponse(
                content=(
                    "I searched the transcript repository, but could not find sufficient evidence or discussion on this topic in the available transcripts. "
                    "My knowledge base is focused on Lenny's Podcast and Newsletter insights covering product strategy, user activation, "
                    "retention curves, growth loops, and experimentation. "
                    "Could you reframe your question around one of these product areas, or ask about a specific growth challenge you are facing?"
                ),
                provider=self.provider_name,
                model=self.model_name,
            )
        elif "experiment plan" in question_text or ("prioritize" in question_text and "experiment" in question_text):
            evidence_section = (
                f"### Relevant Evidence from Sources\n"
                f"Direct transcript evidence from {all_citations_str} highlights:\n"
                "- Optimizing onboarding to eliminate early cognitive friction is the highest-leverage growth lever for sustainable cohort retention.\n"
                "- Reducing the time to first meaningful value prevents new signups from falling into early drop-off dropouts."
                if sources_found else
                "### Relevant Evidence from Sources\n"
                "The available transcript corpus does not contain sufficient direct evidence for this activation question. "
                "The following experiments are general product-growth hypotheses, not direct podcast recommendations."
            )
            content = (
                "### Activation Definition and Assumptions\n"
                "Assumption: activation means a new user completes one meaningful workflow and receives a useful outcome.\n\n"
                "We define the activation journey across three critical milestones:\n"
                "1. **Setup Moment**: Baseline configuration completed without unnecessary friction.\n"
                "2. **Aha! Moment**: The first emotional realization of the core value proposition.\n"
                "3. **Habit Moment**: Recurring usage within the natural product cadence establishing long-term retention.\n\n"
                f"{evidence_section}\n\n"
                "### Prioritized Experiment Backlog\n\n"
                "| Priority | Experiment | Hypothesis | Impact | Confidence | Ease | Primary Metric |\n"
                "| :--- | :--- | :--- | :---: | :---: | :---: | :--- |\n"
                "| **P0** | Reduce Time to First Value | Bypassing non-essential onboarding screens will increase initial workflow completion | 5 | 5 | 4 | Time to First Value (minutes) |\n"
                "| **P0** | Remove Unnecessary Onboarding Friction | Eliminating optional profile questions reduces early session drop-off | 5 | 4 | 5 | Onboarding Completion Rate |\n"
                "| **P0** | Streamline First Meaningful Workflow | Pre-populating workspaces with starter templates guides users to their eureka moment | 4 | 4 | 4 | Aha! Moment Rate |\n"
                "| **P1** | Intent-Based Onboarding Personalization | Routing users by primary job-to-be-done delivers tailored first-run actions | 4 | 3 | 3 | Day-7 Retention |\n"
                "| **P1** | First-Workflow Abandonment Recovery | Sending contextual in-app nudges to users who stalled mid-flow recovers intent | 3 | 4 | 4 | Workflow Recovery Rate |\n"
                "| **P2** | Motivation-Driven Activation Prompts | Testing milestone progress indicators encourages habit formation once friction is low | 3 | 3 | 3 | Habit Moment Rate |\n\n"
                "### Experiment Details\n\n"
                "#### Experiment 1: Reduce Time to First Value (P0)\n"
                "- **Target users**: All new self-serve signups in their first session.\n"
                "- **Problem addressed**: Users abandon signup flow before experiencing the primary value proposition.\n"
                "- **Proposed change**: Defer team invitation and secondary settings until after the first core workflow is completed.\n"
                "- **Control and variant**: Control requires 5 setup steps; Variant presents a 2-step setup directing straight into the core action.\n"
                "- **Primary activation metric**: Percentage of new users completing their first core workflow within 15 minutes of signup.\n"
                "- **Secondary metrics**: Day-1 and Day-7 active user retention.\n"
                "- **Guardrail metrics**: Account security verification rate and support ticket volume.\n"
                "- **Success criteria**: Statistically significant lift of >= 15% in first-day activation (p < 0.05).\n"
                "- **Implementation effort**: Low (2 engineering sprints).\n\n"
                "#### Experiment 2: Remove Unnecessary Onboarding Friction (P0)\n"
                "- **Target users**: New accounts created via organic and paid search.\n"
                "- **Problem addressed**: High drop-off at initial information gathering modal.\n"
                "- **Proposed change**: Remove optional company demographic questions from initial modal.\n"
                "- **Control and variant**: Control has 6 input fields; Variant has only 2 required fields.\n"
                "- **Primary activation metric**: Setup completion rate (step 1 to step 2 conversion).\n"
                "- **Secondary metrics**: Time spent on registration screen.\n"
                "- **Guardrail metrics**: Data completeness for enterprise sales leads.\n"
                "- **Success criteria**: Relative lift of >= 10% in registration throughput.\n"
                "- **Implementation effort**: Very Low (1 engineering sprint).\n\n"
                "### Recommended Execution Order\n"
                "1. **Phase 1 (Immediate - P0)**: Run Experiment 2 and Experiment 1 concurrently to eliminate friction and minimize time-to-first-value. Removing artificial barriers creates a clean baseline.\n"
                "2. **Phase 2 (Fast Follow - P1)**: Deploy intent-based personalization and abandonment recovery once the friction-free path is established.\n"
                "3. **Phase 3 (Optimization - P2)**: Test motivational prompts only if subsequent analytics indicate cognitive motivation is the remaining bottleneck."
            )
        elif "lesson" in question_text or "activation" in question_text or "onboarding" in question_text:
            content = (
                "### Most Important Lessons\n\n"
                f"- **Lesson 1: Treat Onboarding as the Bedrock of Long-Term Retention**\n"
                f"  - *Explanation*: In {primary_citation}, the evidence highlights that onboarding drop-off is fatal to product growth. If users fail to see value in the first session, no downstream marketing or email campaigns can recover them.\n"
                "  - *Why it matters*: Retention curves flatten or plunge based almost entirely on early user trajectory.\n"
                "  - *Practical implication*: Focus initial growth engineering sprints on eliminating early cognitive barriers rather than building top-of-funnel acquisition loops.\n"
                f"  - *Citation*: Source: {primary_citation}\n\n"
                f"- **Lesson 2: Clearly Differentiate Harmful Friction from Intentional Friction**\n"
                f"  - *Explanation*: Transcripts from {all_citations_str} emphasize that not all friction is bad. Intentional friction (e.g. asking for user goals, team size, or use cases) allows the product to route users to personalized aha moments.\n"
                "  - *Why it matters*: Prematurely dropping users into an empty, generic canvas leads to paralysis.\n"
                "  - *Practical implication*: Strip away mechanical password and verification friction, but preserve questions that personalize the workspace.\n"
                f"  - *Citation*: Source: {all_citations_str}\n\n"
                "- **Lesson 3: Establish a Clear Milestone Progression (Setup -> Aha! Moment -> Habit Moment)**\n"
                f"  - *Explanation*: Grounded evidence demonstrates that activation is not a single binary event, but a graduated sequence from baseline setup configuration to the emotional eureka Aha! Moment, followed by recurring habit loops.\n"
                "  - *Why it matters*: Measuring only account creation masks severe activation drop-offs.\n"
                "  - *Practical implication*: Instrument separate telemetry events for Setup, Aha, and Habit moments and track cohort velocity between each step.\n"
                f"  - *Citation*: Source: {primary_citation}\n\n"
                "### Evidence Limitations\n"
                "The available transcripts provide detailed strategic frameworks on onboarding friction and milestone definitions; however, specific platform technical constraints (e.g. third-party OAuth provider timeouts) are not discussed in the corpus and represent general implementation recommendations."
            )
        elif "pmf" in question_text or "product-market fit" in question_text:
            content = (
                "### Most Important Lessons\n\n"
                f"- **Lesson 1: True PMF Shows in Flattening Cohort Retention Curves**\n"
                f"  - *Explanation*: According to {primary_citation}, the single most definitive objective indicator of product-market fit is a cohort retention curve that flattens asymptotically parallel to the x-axis over 3 to 6 months.\n"
                "  - *Why it matters*: If retention asymptotically degrades to zero, growth spend merely burns capital into a leaky bucket.\n"
                "  - *Practical implication*: Hold off on scaling paid acquisition or hiring large sales teams until cohort curves demonstrably flatten.\n"
                f"  - *Citation*: Source: {primary_citation}\n\n"
                f"- **Lesson 2: Measure Must-Have User Sentiment (The 40% Benchmark)**\n"
                f"  - *Explanation*: As highlighted in {all_citations_str}, surveying active users with the question 'How would you feel if you could no longer use this product?' provides an early signal; achieving >= 40% responding 'Very Disappointed' strongly correlates with viable PMF.\n"
                "  - *Why it matters*: High customer satisfaction does not equal indispensability; only genuine distress upon loss signals true fit.\n"
                "  - *Practical implication*: Regularly poll your core user cohort and double down on the specific segment answering 'Very Disappointed'.\n"
                f"  - *Citation*: Source: {all_citations_str}\n\n"
                "### Evidence Limitations\n"
                "The podcast corpus strongly validates retention curves and customer pull; specific financial burn ratios and investor term negotiations are outside the core transcript evidence."
            )
        else:
            content = (
                "### Most Important Lessons\n\n"
                f"- **Core Insight**: Based on transcript evidence from {primary_citation}, sustainable growth originates from disciplined prioritization and validated user feedback loops.\n"
                "  - *Why it matters*: Unfocused execution disperses engineering capacity across low-leverage initiatives.\n"
                "  - *Practical implication*: Maintain a tight experiment backlog and focus on measurable cohort improvements.\n"
                f"  - *Citation*: Source: {primary_citation}\n\n"
                "### Evidence Limitations\n"
                "Additional tactical nuances beyond the direct transcript evidence represent generalized product methodologies."
            )

        return LLMResponse(
            content=content,
            provider=self.provider_name,
            model=self.model_name,
            token_usage={"prompt_tokens": 120, "completion_tokens": 180, "total_tokens": 300},
        )
