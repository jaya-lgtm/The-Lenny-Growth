import re
from typing import Optional


def generate_session_title(text: Optional[str]) -> str:
    """
    Generates a concise, high-quality conversation title (max ~45 chars)
    from the user's initial prompt, similar to ChatGPT/Claude.
    """
    if not text or not text.strip():
        return "New Conversation"

    clean = text.strip()
    # Strip leading markdown headers, blockquotes, bullets, backticks
    clean = re.sub(r"^[#>\s*`-]+", "", clean).strip()

    lower = clean.lower()

    # Specialized Growth / Lenny frameworks when specifically requested
    if re.search(r"\b(create|generate|write|make|draft)\b.*?\bgrowth action plan\b", lower):
        topic = re.sub(
            r".*?\bgrowth action plan\s*(for|on|about)?\s*",
            "",
            clean,
            flags=re.IGNORECASE,
        ).strip(" :?-")
        if topic:
            return f"Action Plan: {topic[:32].title()}"
        return "Growth Action Plan"

    if re.search(r"\bship\s*30\b", lower):
        topic = re.sub(
            r".*?\bship\s*30\s*(essay|atomic essay)?\s*(for|on|about)?\s*",
            "",
            clean,
            flags=re.IGNORECASE,
        ).strip(" :?-")
        if topic:
            return f"Ship 30: {topic[:35].title()}"
        return "Ship 30 Essay"

    if re.search(r"\b(create|generate|audit|write|make)\b.*?\bchecklist\b", lower):
        topic = re.sub(
            r".*?\bchecklist\s*(for|on|about)?\s*",
            "",
            clean,
            flags=re.IGNORECASE,
        ).strip(" :?-")
        if topic:
            return f"Checklist: {topic[:35].title()}"
        return "Audit Checklist"

    if re.search(r"\b(create|generate|write|draft)\b.*?\bexperiment plan\b", lower):
        topic = re.sub(
            r".*?\bexperiment plan\s*(for|on|about)?\s*",
            "",
            clean,
            flags=re.IGNORECASE,
        ).strip(" :?-")
        if topic:
            return f"Experiment Plan: {topic[:32].title()}"
        return "Experiment Plan"

    # Handle "What did X say about Y" -> "X on Y"
    say_match = re.match(r"^what did\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s+say\s+(?:about|on|regarding)\s+(.*)", clean, flags=re.IGNORECASE)
    if say_match:
        person = say_match.group(1).title()
        subject = say_match.group(2).strip(' .?!,;:"\'')
        candidate = f"{person} on {subject}"
        if len(candidate) > 45:
            truncated = candidate[:45]
            last_space = truncated.rfind(" ")
            return (truncated[:last_space] if last_space > 20 else truncated) + "..."
        return candidate

    # Conversational opening prefixes to strip
    prefixes = [
        r"^can you please\s+",
        r"^can you\s+",
        r"^could you please\s+",
        r"^could you\s+",
        r"^please\s+",
        r"^i want you to\s+",
        r"^i want to\s+",
        r"^i'd like to\s+",
        r"^tell me about\s+",
        r"^give me an? (overview|summary|breakdown) of\s+",
        r"^what did\s+",
        r"^what are (the |some )?",
        r"^what is (the |an? )?",
        r"^how (do|can|should|would) (i|we|you)\s+",
        r"^how to\s+",
        r"^explain\s+(to me\s+)?",
    ]

    candidate = clean
    for prefix in prefixes:
        match = re.match(prefix, candidate, flags=re.IGNORECASE)
        if match:
            candidate = candidate[match.end():].strip()
            break

    candidate = candidate.strip(' .?!,;:"\'')
    if not candidate:
        candidate = clean.strip(' .?!,;:"\'')

    # Capitalize first letter
    if candidate:
        candidate = candidate[0].upper() + candidate[1:]

    # Truncate cleanly at word boundary (max 45 chars)
    if len(candidate) > 45:
        truncated = candidate[:45]
        last_space = truncated.rfind(" ")
        if last_space > 20:
            candidate = truncated[:last_space].rstrip(",;:- ") + "..."
        else:
            candidate = truncated.rstrip(",;:- ") + "..."

    return candidate or "New Conversation"
