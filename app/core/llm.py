"""OpenRouter chat completions (OpenAI-compatible API)."""

import httpx

from app.core.config import (
    OPENROUTER_API_KEY,
    OPENROUTER_APP_TITLE,
    OPENROUTER_BASE_URL,
    OPENROUTER_HTTP_REFERER,
    OPENROUTER_MODEL,
)


def chat_completion(prompt: str, timeout: float = 120.0) -> str:
    """Single user-message completion; returns assistant text content."""
    url = f"{OPENROUTER_BASE_URL}/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }
    if OPENROUTER_HTTP_REFERER:
        headers["HTTP-Referer"] = OPENROUTER_HTTP_REFERER
    if OPENROUTER_APP_TITLE:
        headers["X-Title"] = OPENROUTER_APP_TITLE

    payload = {
        "model": OPENROUTER_MODEL,
        "messages": [{"role": "user", "content": prompt}],
    }

    with httpx.Client(timeout=timeout) as http:
        res = http.post(url, headers=headers, json=payload)
        try:
            res.raise_for_status()
        except httpx.HTTPStatusError as e:
            detail = e.response.text
            raise RuntimeError(
                f"OpenRouter error {e.response.status_code}: {detail[:500]}"
            ) from e

        data = res.json()
        choices = data.get("choices") or []
        if not choices:
            raise RuntimeError(f"OpenRouter returned no choices: {data!r}"[:500])

        content = choices[0].get("message", {}).get("content")
        if content is None:
            raise RuntimeError(f"OpenRouter missing message content: {data!r}"[:500])

        return content.strip()

def conversational_completion(messages: list[dict], system_prompt: str, timeout: float = 120.0) -> str:
    """Multi-turn completion with a strong system prompt."""
    url = f"{OPENROUTER_BASE_URL}/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }
    if OPENROUTER_HTTP_REFERER:
        headers["HTTP-Referer"] = OPENROUTER_HTTP_REFERER
    if OPENROUTER_APP_TITLE:
        headers["X-Title"] = OPENROUTER_APP_TITLE

    payload_messages = [{"role": "system", "content": system_prompt}] + messages

    payload = {
        "model": OPENROUTER_MODEL,
        "messages": payload_messages,
    }

    with httpx.Client(timeout=timeout) as http:
        res = http.post(url, headers=headers, json=payload)
        try:
            res.raise_for_status()
        except httpx.HTTPStatusError as e:
            detail = e.response.text
            raise RuntimeError(
                f"OpenRouter error {e.response.status_code}: {detail[:500]}"
            ) from e

        data = res.json()
        choices = data.get("choices") or []
        if not choices:
            raise RuntimeError(f"OpenRouter returned no choices: {data!r}"[:500])

        content = choices[0].get("message", {}).get("content")
        if content is None:
            raise RuntimeError(f"OpenRouter missing message content: {data!r}"[:500])

        return content.strip()
