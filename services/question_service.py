import json
import os
import random
import requests

QUESTIONS_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "questions.json")

with open(QUESTIONS_PATH, "r") as f:
    QUESTION_BANK = json.load(f)


def get_roles():
    return sorted(set(q["role"] for q in QUESTION_BANK))


def get_questions_for_role(role):
    return [q for q in QUESTION_BANK if q["role"] == role]


def get_random_question(role, exclude_ids=None):
    """Pick a question the user hasn't seen yet in this session."""
    exclude_ids = exclude_ids or []
    pool = [q for q in get_questions_for_role(role) if q["id"] not in exclude_ids]
    if not pool:
        return None
    return random.choice(pool)


def generate_ai_question(role, api_key):
    """
    Optional: generate a fresh question using an LLM if the user has supplied
    an API key. Falls back to None on any failure so the caller can use the
    local bank instead. Uses Anthropic's Claude API since that's what most
    users of this project will have a key for; swap the endpoint/model if
    you're using a different provider.
    """
    if not api_key:
        return None

    try:
        response = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": "claude-sonnet-4-6",
                "max_tokens": 300,
                "messages": [{
                    "role": "user",
                    "content": (
                        f"Generate one realistic {role} interview question, plus 6-10 "
                        "keywords a strong answer would include. Respond ONLY as JSON: "
                        '{"question": "...", "ideal_keywords": ["...", "..."]}'
                    )
                }]
            },
            timeout=15
        )
        response.raise_for_status()
        data = response.json()
        text = data["content"][0]["text"]
        parsed = json.loads(text)
        return {
            "id": f"ai-{random.randint(1000,9999)}",
            "role": role,
            "category": "AI-Generated",
            "question": parsed["question"],
            "ideal_keywords": parsed["ideal_keywords"],
            "difficulty": "Medium"
        }
    except Exception:
        # Any failure (no internet, bad key, bad JSON) -> silently fall back
        return None
