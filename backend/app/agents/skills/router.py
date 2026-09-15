import re
from typing import Tuple, Optional

SKILL_MODES = {
    "grounded_qa": "Grounded Q&A",
    "growth_action_plan": "Growth Action Plan",
    "ship30_essay": "Ship 30 Essay",
    "framework": "Growth Framework",
    "checklist": "Audit Checklist",
    "experiment_plan": "Experiment Plan",
    "strategy_doc": "Strategy Document",
    "html_css": "HTML/CSS Component",
}


class IntentRouter:
    """
    Classifies user intent and routes to specialized growth skills.
    Supports explicit mode selection or heuristic natural language classification.
    """

    @staticmethod
    def classify(user_message: str, explicit_mode: Optional[str] = "auto") -> Tuple[str, str]:
        """
        Returns (effective_mode, skill_display_name).
        """
        if explicit_mode and explicit_mode.lower() != "auto":
            normalized = explicit_mode.lower().strip()
            if normalized == "html_css_component":
                normalized = "html_css"
            if normalized in SKILL_MODES:
                return normalized, SKILL_MODES[normalized]

        text = user_message.lower()


        # Heuristic intent classification
        if any(w in text for w in ["ship 30", "essay", "write an essay", "longform article", "opinion piece"]):
            return "ship30_essay", SKILL_MODES["ship30_essay"]

        if any(w in text for w in ["action plan", "growth plan", "growth action plan", "30-60-90", "milestone plan"]):
            return "growth_action_plan", SKILL_MODES["growth_action_plan"]

        if any(w in text for w in ["checklist", "audit", "check list", "readiness checklist", "assessment checklist"]):
            return "checklist", SKILL_MODES["checklist"]

        if any(w in text for w in ["experiment", "experiment plan", "ab test", "a/b test", "hypothesis", "ice score", "rice score"]):
            return "experiment_plan", SKILL_MODES["experiment_plan"]

        if any(w in text for w in ["framework", "mental model", "matrix", "decision tree", "ladder", "taxonomy"]):
            return "framework", SKILL_MODES["framework"]

        if any(w in text for w in ["strategy doc", "strategy document", "strategic roadmap", "strategic plan"]):
            return "strategy_doc", SKILL_MODES["strategy_doc"]

        if any(w in text for w in ["html", "interactive widget", "calculator", "visual chart", "css component", "html/css"]):
            return "html_css", SKILL_MODES["html_css"]

        return "grounded_qa", SKILL_MODES["grounded_qa"]

    @staticmethod
    def is_conversational(user_message: str) -> bool:
        """
        Detects if user message is a greeting, pleasantry, or introductory question,
        which should be answered naturally without forcing transcript retrieval or citations.
        """
        cleaned = user_message.strip().lower()
        cleaned = re.sub(r"[!.,?]+$", "", cleaned).strip()

        if cleaned in {
            "hi", "hello", "hey", "heyy", "heyyy", "howdy", "sup", "yo", "hola",
            "good morning", "good afternoon", "good evening",
            "who are you", "what are you", "what can you do", "tell me about yourself",
            "how are you", "how's it going", "how are you doing", "what's up",
            "thanks", "thank you", "thx", "appreciate it", "thank you so much",
            "help", "can you help me",
        }:
            return True

        patterns = [
            r"^(hi|hello|hey|heyy|howdy|sup|yo|greetings|hola)\b",
            r"^good\s+(morning|afternoon|evening|day)\b",
            r"^(who\s+are\s+you|what\s+are\s+you|what\s+can\s+you\s+do|tell\s+me\s+about\s+yourself)\b",
            r"^(how\s+are\s+you|how's\s+it\s+going|how\s+are\s+you\s+doing|what's\s+up)\b",
            r"^(thanks|thank\s+you|thx|appreciate\s+it)\b",
        ]
        return any(re.search(p, cleaned) for p in patterns)

    @staticmethod
    def should_retrieve(provider: any, user_message: str) -> bool:
        """
        Uses an LLM classification prompt to determine whether the user query
        requires retrieving transcript evidence from Lenny's Podcast, or is a
        conversational turn (greeting, pleasantry, chit-chat, meta-question).
        """
        if IntentRouter.is_conversational(user_message):
            return False

        if not provider:
            return True

        try:
            prompt = (
                "You are a routing controller for an AI growth assistant specializing in Lenny's Podcast.\n"
                "Determine if the user's message requires retrieving factual product/growth knowledge from Lenny's Podcast transcripts, "
                "or if it is a conversational turn (greeting, pleasantry, general polite remark, or general small-talk).\n\n"
                f"User message: \"{user_message}\"\n\n"
                "Reply with ONLY one word: 'RETRIEVE' or 'CONVERSATION'."
            )
            response = provider.generate(
                prompt=prompt,
                max_tokens=5,
                temperature=0.0,
            )
            decision = (response.content or "").strip().upper()
            if "CONVERSATION" in decision:
                return False
            return True
        except Exception:
            return True


