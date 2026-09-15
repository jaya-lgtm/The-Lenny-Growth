import re
from typing import List, Set, Optional
from dataclasses import dataclass, field

STOPWORDS: Set[str] = {
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and",
    "any", "are", "aren't", "as", "at", "be", "because", "been", "before", "being",
    "below", "between", "both", "but", "by", "can't", "cannot", "could", "couldn't",
    "did", "didn't", "do", "does", "doesn't", "doing", "don't", "down", "during",
    "each", "few", "for", "from", "further", "had", "hadn't", "has", "hasn't",
    "have", "haven't", "having", "he", "he'd", "he'll", "he's", "her", "here",
    "here's", "hers", "herself", "him", "himself", "his", "how", "how's", "i",
    "i'd", "i'll", "i'm", "i've", "if", "in", "into", "is", "isn't", "it", "it's",
    "its", "itself", "let's", "me", "more", "most", "mustn't", "my", "myself",
    "no", "nor", "not", "of", "off", "on", "once", "only", "or", "other", "ought",
    "our", "ours", "ourselves", "out", "over", "own", "same", "shan't", "she",
    "she'd", "she'll", "she's", "should", "shouldn't", "so", "some", "such",
    "than", "that", "that's", "the", "their", "theirs", "them", "themselves",
    "then", "there", "there's", "these", "they", "they'd", "they'll", "they're",
    "they've", "this", "those", "through", "to", "too", "under", "until", "up",
    "very", "was", "wasn't", "we", "we'd", "we'll", "we're", "we've", "were",
    "weren't", "what", "what's", "when", "when's", "where", "where's", "which",
    "while", "who", "who's", "whom", "why", "why's", "with", "won't", "would",
    "wouldn't", "you", "you'd", "you'll", "you're", "you've", "your", "yours",
    "yourself", "yourselves",
    # Conversational podcast query filler
    "lenny", "lenny's", "podcast", "episode", "episodes", "guest", "guests",
    "tell", "give", "show", "know", "say", "said", "lessons", "lesson",
    "important", "best", "ways", "way", "please", "can", "could", "would",
}


@dataclass
class TopicIntent:
    domain: str
    clean_query: str
    substantive_terms: List[str]
    target_concepts: List[str]
    negative_terms: List[str] = field(default_factory=list)


class QueryTopicClassifier:
    """Classifies user queries into topic domains and extracts topical signals."""

    @staticmethod
    def extract_substantive_terms(query: str) -> List[str]:
        tokens = re.findall(r"[a-zA-Z0-9_\-]+", query.lower())
        meaningful = [t for t in tokens if len(t) > 2 and t not in STOPWORDS]
        return meaningful

    @staticmethod
    def classify(query: str) -> TopicIntent:
        lowered = query.lower()
        substantive = QueryTopicClassifier.extract_substantive_terms(query)
        clean_text = " ".join(substantive) if substantive else query.strip().lower()

        # Domain 1: Activation & Onboarding
        if any(term in lowered for term in [
            "activation", "onboarding", "aha moment", "setup moment", "habit moment",
            "time to value", "time-to-value", "time to first value", "first run", "new user experience", "nux", "first action"
        ]):
            activation_clean = f"user activation onboarding time to first value aha moment {clean_text}".strip()
            return TopicIntent(
                domain="activation_onboarding",
                clean_query=activation_clean,
                substantive_terms=substantive,
                target_concepts=[
                    "activation", "onboarding", "time to first value", "time to value",
                    "aha moment", "first meaningful", "first run", "product adoption",
                    "adoption", "retention", "growth experiments", "activation metrics",
                    "product-led growth", "plg", "setup moment", "habit moment", "friction"
                ],
                negative_terms=[
                    "mentorship", "mentor", "mentors", "career", "career advice", "uplevel", "promotion",
                    "interviewing", "pm career", "jules walter",
                    "world model", "world models", "robotics", "robots", "dr. fei-fei li", "fei-fei", "ai research",
                    "neural network", "godmother of ai", "agi", "large language model research",
                    "good strategy bad strategy", "richard rumelt", "rumelt",
                    "leadership", "executive coaching", "management", "1-on-1", "1:1",
                    "performance review", "recruiting", "hiring", "headcount", "compensation",
                    "board meeting", "managing people", "team structure", "org design",
                    "sales quota", "sales commission", "cold calling"
                ],
            )

        # Domain 2: Product-Market Fit (PMF)
        if any(term in lowered for term in [
            "product market fit", "product-market fit", "pmf", "find pmf", "reach pmf",
            "must-have", "retention curve", "flattening curve", "sean ellis"
        ]):
            return TopicIntent(
                domain="product_market_fit",
                clean_query=clean_text,
                substantive_terms=substantive,
                target_concepts=[
                    "product-market fit", "pmf", "retention curve", "must-have",
                    "flattening", "sean ellis", "organic pull", "demand", "validation", "hair on fire"
                ],
                negative_terms=[
                    "code editor", "dev tools", "ide", "sales commission", "recruiter",
                    "executive coaching", "1-on-1s", "leadership styles"
                ],
            )

        # Domain 3: Experimentation & Prioritization
        if any(term in lowered for term in [
            "experiment", "experimentation", "prioritize", "prioritization", "ice score",
            "rice score", "a/b test", "hypothesis", "experiment backlog"
        ]):
            return TopicIntent(
                domain="growth_experiments",
                clean_query=clean_text,
                substantive_terms=substantive,
                target_concepts=[
                    "experiment", "prioritization", "hypothesis", "ice score", "rice",
                    "a/b testing", "guardrails", "primary metric", "variant", "backlog"
                ],
                negative_terms=[
                    "fundraising", "pitch deck", "term sheet", "valuation", "angel investing"
                ],
            )

        # Domain 4: Retention & Churn
        if any(term in lowered for term in [
            "retention", "churn", "cohort", "resurrection", "engagement loop", "stickiness"
        ]):
            return TopicIntent(
                domain="retention_churn",
                clean_query=clean_text,
                substantive_terms=substantive,
                target_concepts=[
                    "retention", "churn", "cohort", "stickiness", "resurrection",
                    "frequency", "habits", "engagement loop", "power users"
                ],
                negative_terms=[
                    "pr agency", "media launch", "press release", "recruiter search"
                ],
            )

        # General domain fallback
        return TopicIntent(
            domain="general_growth",
            clean_query=clean_text,
            substantive_terms=substantive,
            target_concepts=substantive,
            negative_terms=[],
        )
