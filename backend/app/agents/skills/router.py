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
