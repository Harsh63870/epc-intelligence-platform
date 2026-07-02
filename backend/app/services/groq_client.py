"""Groq LLM client (OpenAI-compatible API)."""
from __future__ import annotations

import json
import re

import httpx

from app.config import settings

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
DEFAULT_MODEL = "llama-3.3-70b-versatile"


class GroqError(Exception):
    pass


def chat_completion(
    *,
    system: str,
    user: str,
    model: str = DEFAULT_MODEL,
    temperature: float = 0.1,
    json_mode: bool = False,
) -> str:
    if not settings.groq_api_key or settings.groq_api_key.startswith("your_"):
        raise GroqError("GROQ_API_KEY is not configured in backend/.env")

    payload: dict = {
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "temperature": temperature,
    }
    if json_mode:
        payload["response_format"] = {"type": "json_object"}

    with httpx.Client(timeout=60.0) as client:
        response = client.post(
            GROQ_API_URL,
            headers={
                "Authorization": f"Bearer {settings.groq_api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
        )
        if response.status_code != 200:
            raise GroqError(f"Groq API error {response.status_code}: {response.text}")
        data = response.json()

    return data["choices"][0]["message"]["content"]


def parse_json_response(text: str) -> dict:
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            return json.loads(match.group())
        raise GroqError("Failed to parse JSON from Groq response") from None
