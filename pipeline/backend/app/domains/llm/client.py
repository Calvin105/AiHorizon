"""Thin Groq client. Groq's chat-completions endpoint is OpenAI-compatible,
so a plain httpx POST is enough — no SDK dependency for one call shape.

Every call site is expected to check `is_configured()` first and to have
its own per-case "already used" flag (see cases/model.py's llm_*_used
columns) — this module does not enforce the budget itself, it just makes
one call when asked.

It does protect the screen from the network. A failed call used to be
retried on the next re-rank and the next report view, each waiting out a
20-second timeout, so a dead venue Wi-Fi froze every click. Now one failure
opens a short circuit: for COOLDOWN_SECONDS every caller is told the LLM is
unavailable at once, and the code-written path runs instead.
"""

import time

import httpx

from app.core.config import get_settings

GROQ_CHAT_URL = "https://api.groq.com/openai/v1/chat/completions"

#: Fail fast on a dead link, but let a slow completion finish.
TIMEOUT = httpx.Timeout(12.0, connect=4.0)
COOLDOWN_SECONDS = 120.0

_unavailable_until = 0.0


def reset_circuit() -> None:
    global _unavailable_until
    _unavailable_until = 0.0


def is_configured() -> bool:
    """Whether a call is worth attempting right now: a key is set, the
    LLM_ENABLED switch is on, and the last call hasn't just failed."""
    settings = get_settings()
    return bool(settings.groq_api_key) and settings.llm_enabled and time.monotonic() >= _unavailable_until


def chat(
    messages: list[dict[str, str]], *, temperature: float = 0.2, max_tokens: int = 600
) -> str | None:
    """One chat-completion call. Returns None (never raises) on any
    failure — missing key, switched off, network error, bad response — so a
    caller can always fall back to the deterministic, code-written path
    DESIGN.md requires when the LLM step is unavailable.

    openai/gpt-oss-20b is a reasoning model: it spends completion tokens on
    a hidden `reasoning` field before `content`, so a small max_tokens can
    exhaust the budget before any content is written. reasoning_effort
    "low" keeps that overhead small for the short, structured tasks this
    pipeline actually asks of it (map one value, rank 7 causes, write a
    few sentences) — none of them need deep chain-of-thought.
    """
    global _unavailable_until
    if not is_configured():
        return None

    settings = get_settings()
    try:
        response = httpx.post(
            GROQ_CHAT_URL,
            headers={"Authorization": f"Bearer {settings.groq_api_key}"},
            json={
                "model": settings.groq_model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "reasoning_effort": "low",
            },
            timeout=TIMEOUT,
        )
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]
        return content or None
    except (httpx.HTTPError, KeyError, IndexError, ValueError):
        _unavailable_until = time.monotonic() + COOLDOWN_SECONDS
        return None
