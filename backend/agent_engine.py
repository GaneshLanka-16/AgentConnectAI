
import os
import logging
from functools import lru_cache

from dotenv import load_dotenv
from google import genai

load_dotenv()

logger = logging.getLogger(__name__)

MODEL_NAME = os.getenv(
    "GEMINI_MODEL",
    "gemini-3.5-flash-lite"
)


@lru_cache(maxsize=1)
def get_gemini_client():
    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise ValueError("GEMINI_API_KEY is missing from backend .env")

    return genai.Client(api_key=api_key)


def generate_comment(
    agent_name: str,
    post_content: str,
    agent_company: str = "",
    agent_interests: str = ""
) -> str:

    prompt = f"""
You are {agent_name}, an AI agent representing {agent_company or "a company"}.

Your interests are: {agent_interests or "business collaboration"}.

Another company published this post:

{post_content}

Write a natural, professional and meaningful social-network comment
as this AI agent.

Rules:
- Write only 2 to 3 sentences.
- Be relevant to the original post.
- Mention a realistic collaboration opportunity when appropriate.
- Do not invent facts, offers, or commitments.
- Do not repeat the original post.
- Return only the comment text.
"""

    try:
        client = get_gemini_client()

        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt
        )

        comment = (response.text or "").strip()

        if not comment:
            raise ValueError("Gemini returned an empty response")

        logger.info("Gemini generated a comment for %s", agent_name)

        return comment

    except Exception:
        logger.exception("Gemini comment generation failed")

        return (
            f"{agent_name} has reviewed this update. "
            "This appears relevant to our interests. "
            "We would be interested in exploring possible collaboration."
        )
