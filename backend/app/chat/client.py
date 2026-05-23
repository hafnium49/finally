"""LiteLLM client wrapper for the FinAlly chat subsystem.

Live mode follows the **cerebras-inference** project skill:
    - Library: LiteLLM (`litellm.completion`)
    - Model:   ``openrouter/openai/gpt-oss-120b``
    - Provider routing: ``extra_body={"provider": {"order": ["cerebras"]}}``
    - Auth:    ``OPENROUTER_API_KEY`` from environment

Mock mode (``LLM_MOCK=true``) dispatches to :mod:`app.chat.mock` instead and
returns deterministic responses without touching the network.
"""

from __future__ import annotations

import os
from typing import Optional

from .mock import respond as mock_respond
from .schemas import LLMResponse


# Cerebras-inference skill constants ---------------------------------------

MODEL = "openrouter/openai/gpt-oss-120b"
EXTRA_BODY = {"provider": {"order": ["cerebras"]}}
DEFAULT_TEMPERATURE = 0.2
DEFAULT_MAX_TOKENS = 1024


class LLMResponseError(RuntimeError):
    """Raised when the live LLM returns malformed structured output."""


class LLMConfigError(RuntimeError):
    """Raised at startup when live mode is requested but env is incomplete."""


def _is_mock_mode() -> bool:
    return os.environ.get("LLM_MOCK", "").strip().lower() == "true"


def validate_config() -> None:
    """Raise :class:`LLMConfigError` if the configuration is missing.

    Called from the FastAPI lifespan startup hook so the server fails fast
    rather than 500-ing on the first ``/api/chat`` request. In mock mode
    no key check is performed.
    """
    if _is_mock_mode():
        return
    key = os.environ.get("OPENROUTER_API_KEY", "").strip()
    if not key:
        raise LLMConfigError(
            "OPENROUTER_API_KEY is not set and LLM_MOCK != 'true'. "
            "Either set the OpenRouter API key or run the backend with LLM_MOCK=true."
        )


def assert_ready() -> None:
    """Alias retained for symmetry with the contract's earlier wording."""
    validate_config()


def complete(
    system_prompt: str,
    user_text: str,
    *,
    temperature: float = DEFAULT_TEMPERATURE,
    max_tokens: int = DEFAULT_MAX_TOKENS,
    reasoning_effort: Optional[str] = "low",
) -> LLMResponse:
    """Run one LLM turn and return the parsed :class:`LLMResponse`.

    In mock mode the live call is skipped and :func:`app.chat.mock.respond`
    is invoked with ``user_text`` instead.

    Raises :class:`LLMResponseError` if the live provider returns content
    that cannot be parsed into :class:`LLMResponse`.
    """
    if _is_mock_mode():
        return mock_respond(user_text)

    # Imported lazily so tests that only exercise mock mode do not pay the
    # litellm import cost (and don't fail in environments where the package
    # isn't installed but mock mode is intended).
    from litellm import completion  # type: ignore[import-not-found]

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_text},
    ]

    kwargs: dict = {
        "model": MODEL,
        "messages": messages,
        "response_format": LLMResponse,
        "extra_body": EXTRA_BODY,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    if reasoning_effort is not None:
        kwargs["reasoning_effort"] = reasoning_effort

    response = completion(**kwargs)

    try:
        content = response.choices[0].message.content
    except (AttributeError, IndexError) as exc:  # pragma: no cover - defensive
        raise LLMResponseError(f"LLM returned an unexpected envelope: {exc}") from exc

    if not content:
        raise LLMResponseError("LLM returned empty content.")

    try:
        return LLMResponse.model_validate_json(content)
    except Exception as exc:
        raise LLMResponseError(
            f"LLM returned content that failed schema validation: {exc}"
        ) from exc
