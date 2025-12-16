from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Final, Mapping


DEFAULT_SEED: Final[int] = 42

OPENAI_NON_REASONING_PARAMS: Final[dict[str, Any]] = {
    "temperature": 0.0,
    "top_p": 1.0,
    "n": 1,
    "seed": DEFAULT_SEED,
    "presence_penalty": 0.0,
    "frequency_penalty": 0.0,
}

OPENAI_REASONING_PARAMS: Final[dict[str, Any]] = {
    "seed": DEFAULT_SEED,
    "reasoning_effort": "high",
}

ANTHROPIC_PARAMS: Final[dict[str, Any]] = {
    "temperature": 0.0,
}

GEMINI_PARAMS: Final[dict[str, Any]] = {
    "temperature": 0.0,
    "top_k": 1,
    "n": 1,
}


@dataclass(frozen=True, slots=True)
class LLMConfig:
    client_kwargs: Mapping[str, Any] = field(default_factory=dict)

    def as_kwargs(self) -> dict[str, Any]:
        return dict(self.client_kwargs)


def openai_conf(
    *,
    reasoning: bool,
    **overrides: Any,
) -> LLMConfig:
    base = OPENAI_REASONING_PARAMS if reasoning else OPENAI_NON_REASONING_PARAMS
    return LLMConfig({**base, **overrides})


def anthropic_conf(**overrides: Any) -> LLMConfig:
    return LLMConfig({**ANTHROPIC_PARAMS, **overrides})


def gemini_conf(**overrides: Any) -> LLMConfig:
    return LLMConfig({**GEMINI_PARAMS, **overrides})


MODEL_CONFIGS: Final[dict[str, dict[str, LLMConfig]]] = {
    "openai": {
        "gpt-5.2": openai_conf(reasoning=True),
        "gpt-5.2-2025-12-11": openai_conf(reasoning=True),
        "gpt-5.1": openai_conf(reasoning=True),
        "gpt-5.1-2025-11-13": openai_conf(reasoning=True),
        "gpt-5": openai_conf(reasoning=True),
        "gpt-5-2025-08-07": openai_conf(reasoning=True),
        "gpt-5-mini": openai_conf(reasoning=True),
        "gpt-5-mini-2025-08-07": openai_conf(reasoning=True),
        "gpt-5-nano": openai_conf(reasoning=True),
        "gpt-5-nano-2025-08-07": openai_conf(reasoning=True),
        "gpt-4.1": openai_conf(reasoning=False),
        "gpt-4.1-2025-04-14": openai_conf(reasoning=False),
        "gpt-4.1-nano": openai_conf(reasoning=False),
        "gpt-4.1-nano-2025-04-14": openai_conf(reasoning=False),
        "gpt-4.1-mini": openai_conf(reasoning=False),
        "gpt-4.1-mini-2025-04-14": openai_conf(reasoning=False),
    },
    "anthropic": {
        "claude-sonnet-4-5": anthropic_conf(),
        "claude-sonnet-4-5-20250929": anthropic_conf(),
        "claude-haiku-4-5": anthropic_conf(),
        "claude-haiku-4-5-20251001": anthropic_conf(),
        "claude-opus-4-1": anthropic_conf(),
        "claude-opus-4-1-20250805": anthropic_conf(),
        "claude-opus-4-5": anthropic_conf(),
        "claude-3-5-sonnet": anthropic_conf(),
        "claude-3-5-sonnet-20240620": anthropic_conf(),
        "claude-3-5-haiku": anthropic_conf(),
        "claude-3-5-haiku-20241022": anthropic_conf(),
    },
    "gemini": {
        "gemini-3-pro-preview": gemini_conf(),
        "gemini-2.5-pro": gemini_conf(),
        "gemini-2.5-flash": gemini_conf(),
        "gemini-2.5-flash-lite": gemini_conf(),
        "gemini-2.0-flash": gemini_conf(),
    },
}

MODEL_ALIASES: Final[dict[str, dict[str, str]]] = {
    "openai": {
        "gpt-5.1-latest": "gpt-5.1",
    },
    "anthropic": {},
    "gemini": {
        "gemini-flash-latest": "gemini-2.5-flash",
        "gemini-pro-latest": "gemini-2.5-pro",
    },
}


__all__ = ["LLMConfig", "MODEL_CONFIGS", "MODEL_ALIASES"]
