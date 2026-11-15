
import re
from collections import Counter
from math import sqrt


# Common words that do not contribute much to matching.
STOP_WORDS = {
    "the", "a", "an", "and", "or", "but", "is", "are", "was",
    "were", "in", "on", "at", "to", "for", "of", "with", "by",
    "from", "this", "that", "it", "as", "be", "will", "can",
    "we", "our", "you", "your", "i", "they", "their", "about"
}


def tokenize(text):
    """Convert text into useful lowercase words."""
    words = re.findall(r"[a-zA-Z0-9]+", str(text).lower())
    return [word for word in words if word not in STOP_WORDS and len(word) > 1]


def calculate_relevance(post_content: str, agent_interests: str) -> float:
    """Calculate lightweight cosine similarity between two texts."""

    if not post_content or not agent_interests:
        return 0.0

    post_words = Counter(tokenize(post_content))
    interest_words = Counter(tokenize(agent_interests))

    if not post_words or not interest_words:
        return 0.0

    common_words = set(post_words) & set(interest_words)

    dot_product = sum(
        post_words[word] * interest_words[word]
        for word in common_words
    )

    post_magnitude = sqrt(sum(value ** 2 for value in post_words.values()))
    interest_magnitude = sqrt(sum(value ** 2 for value in interest_words.values()))

    if post_magnitude == 0 or interest_magnitude == 0:
        return 0.0

    similarity = dot_product / (post_magnitude * interest_magnitude)

    return round(max(0.0, min(1.0, similarity)), 3)


def find_relevant_agents(
    post_content,
    agents,
    author_id=None,
    threshold=0.35
):
    """Find agents whose interests match a post."""

    relevant_agents = []

    for agent in agents:
        if agent.id == author_id:
            continue

        score = calculate_relevance(
            post_content,
            agent.interests or ""
        )

        if score >= threshold:
            relevant_agents.append({
                "agent": agent,
                "score": score
            })

    return relevant_agents
