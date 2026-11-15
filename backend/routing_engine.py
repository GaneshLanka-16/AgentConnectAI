
from functools import lru_cache

import numpy as np
from sentence_transformers import SentenceTransformer, util


MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

# Load the model once and reuse it for future routing requests.
@lru_cache(maxsize=1)
def get_model():
    return SentenceTransformer(MODEL_NAME)


def calculate_relevance(post_content: str, agent_interests: str) -> float:
    if not post_content.strip() or not agent_interests.strip():
        return 0.0

    model = get_model()

    embeddings = model.encode(
        [post_content, agent_interests],
        convert_to_tensor=True,
        normalize_embeddings=True
    )

    similarity = util.cos_sim(
        embeddings[0],
        embeddings[1]
    ).item()

    return round(max(0.0, min(1.0, similarity)), 3)


def find_relevant_agents(
    post_content,
    agents,
    author_id=None,
    threshold=0.35
):
    relevant_agents = []

    for agent in agents:
        if agent.id == author_id:
            continue

        score = calculate_relevance(
            post_content,
            agent.interests
        )

        if score >= threshold:
            relevant_agents.append({
                "agent": agent,
                "score": score
            })

    return relevant_agents
