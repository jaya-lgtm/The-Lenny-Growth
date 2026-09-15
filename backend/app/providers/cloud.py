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
        source_match = re.search(r'Source:\s*"([^"]+)"\s*(?:with\s*([^\n(]+))?', prompt)
        if source_match:
            cited_title = source_match.group(1).strip()
            guest_part = f" with {source_match.group(2).strip()}" if source_match.group(2) else ""
            source_attribution = f"**{cited_title}**{guest_part}"
        else:
            source_attribution = "the ingested podcast transcripts"

        # Extract user question from prompt if formatted with User Question:
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
                "I'm doing great, thanks for asking! 😊 Ready to explore some product strategy, growth tactics, or frameworks from Lenny's Podcast whenever you are. What are you working on today?"
            )
        elif is_thanks:
            content = (
                "You're very welcome! Let me know if you'd like to dig deeper into any specific episode insights or generate an artifact."
            )
        elif is_greeting:
            content = (
                "Hey there! 👋 I'm **The Lenny Growth Assistant**.\n\n"
                "I'm here to help you solve product and growth challenges, grounded in real wisdom from over 270 Lenny's Podcast episodes.\n\n"
                "You can ask me questions like:\n"
                "- *What are the three components of activation?*\n"
                "- *How do I set up sustainable growth loops instead of linear funnels?*\n"
                "- *What are the leading indicators of Product-Market Fit?*\n\n"
                "You can also select a specialized mode pill below to generate **Growth Action Plans**, **Ship 30 Essays**, or **Checklists**.\n\n"
                "What product or growth challenge are you tackling today?"
            )
        elif "growth loop" in question_text or "loops" in question_text:
            content = (
                f"Based on insights from {source_attribution}, growth loops generate compounding acquisition and retention. "
                "Unlike linear funnels that require continuous top-of-funnel spend, loops ensure each cohort creates the fuel "
                "for subsequent cohorts through product usage, viral advocacy, or content generation."
            )
        elif "retention" in question_text or "cohort" in question_text:
            content = (
                f"According to {source_attribution}, retention is the bedrock "
                "of sustainable growth. Rather than relying on linear funnels, successful teams build growth loops where existing cohorts "
                "generate inputs that acquire and activate subsequent cohorts (via viral, content, or reinvestment loops)."
            )
        elif "pmf" in question_text or "product-market fit" in question_text:
            content = (
                f"As discussed in {source_attribution}, key signals of product-market fit include:\n"
                "- The Sean Ellis 40% 'very disappointed' survey threshold.\n"
                "- Flattening cohort retention curves over 3-6 months.\n"
                "- Spontaneous organic word-of-mouth velocity and strong user advocacy."
            )
        elif "activation" in question_text or "onboarding" in question_text:
            content = (
                f"Based on the transcript evidence from {source_attribution}, "
                "activation requires guiding new users to three sequential milestones:\n\n"
                "1. **The Setup Moment**: Required baseline configuration (e.g. inviting teammates, installing integrations).\n"
                "2. **The Aha! Moment**: The first moment they experience value directly.\n"
                "3. **The Habit Moment**: Recurring frequency of usage aligned with natural product cadence.\n\n"
                "The evidence emphasizes eliminating harmful friction while preserving intentional friction that customizes the user journey."
            )
        elif "quantum physics" in question_text or "unsupported" in question_text:
            content = (
                "I searched the transcript repository, but could not find sufficient evidence or discussion on this topic. "
                "My knowledge base is focused on Lenny's Podcast transcripts covering product strategy, activation, "
                "retention, and growth experimentation. Please ask a product or growth question, or narrow your query."
            )
        else:
            content = (
                f"Based on the transcript evidence from {source_attribution}, here is the synthesized growth guidance:\n\n"
                "Focus on concrete metrics, rapid experiment validation, and understanding user feedback loops."
            )

        return LLMResponse(
            content=content,
            provider=self.provider_name,
            model=self.model_name,
            token_usage={"prompt_tokens": 120, "completion_tokens": 85, "total_tokens": 205},
        )
