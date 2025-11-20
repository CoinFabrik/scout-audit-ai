"""Provider inference, defaults, and factory helpers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Protocol, Tuple

from .llm_config import LLMConfig, MODEL_CONFIGS


class LLMFactory(Protocol):
    def __call__(self, model_name: str, api_key: str, config: LLMConfig) -> object: ...


@dataclass(frozen=True)
class Provider:
    name: str
    models: Dict[str, LLMConfig]
    builder: LLMFactory


def _build_openai(model_name: str, api_key: str, config: LLMConfig):
    try:
        from langchain_openai import ChatOpenAI
    except ImportError as exc:
        raise ImportError(
            "Missing langchain-openai. Install via 'pip install langchain-openai'."
        ) from exc

    kwargs: Dict[str, object] = config.as_kwargs()
    kwargs.update(
        {
            "model": model_name,
            "api_key": api_key,
        }
    )
    return ChatOpenAI(**kwargs)


def _build_anthropic(model_name: str, api_key: str, config: LLMConfig):
    try:
        from langchain_anthropic import ChatAnthropic
    except ImportError as exc:
        raise ImportError(
            "Missing langchain-anthropic. Install via 'pip install langchain-anthropic'."
        ) from exc

    kwargs: Dict[str, object] = config.as_kwargs()
    kwargs.update(
        {
            "model": model_name,
            "api_key": api_key,
        }
    )
    return ChatAnthropic(**kwargs)


def _build_gemini(model_name: str, api_key: str, config: LLMConfig):
    try:
        from langchain_google_genai import ChatGoogleGenerativeAI
    except ImportError as exc:
        raise ImportError(
            "Missing langchain-google-genai. Install via "
            "'pip install langchain-google-genai'."
        ) from exc

    kwargs: Dict[str, object] = config.as_kwargs()
    kwargs.update(
        {
            "model": model_name,
            "google_api_key": api_key,
        }
    )
    return ChatGoogleGenerativeAI(**kwargs)


PROVIDERS: List[Provider] = [
    Provider(
        name="openai",
        models=MODEL_CONFIGS["openai"],
        builder=_build_openai,
    ),
    Provider(
        name="anthropic",
        models=MODEL_CONFIGS["anthropic"],
        builder=_build_anthropic,
    ),
    Provider(
        name="gemini",
        models=MODEL_CONFIGS["gemini"],
        builder=_build_gemini,
    ),
]


def _normalize(name: str) -> str:
    return name.strip().lower()


def infer_provider(model_name: str) -> Tuple[Provider, LLMConfig]:
    if not model_name:
        raise ValueError("Model name must be non-empty when inferring provider.")
    normalized = _normalize(model_name)
    for provider in PROVIDERS:
        for candidate, config in provider.models.items():
            if _normalize(candidate) == normalized:
                return provider, config
    supported = ", ".join(
        f"{provider.name}: {', '.join(provider.models.keys())}"
        for provider in PROVIDERS
    )
    raise ValueError(
        f"Model '{model_name}' is not supported. Available options -> {supported}"
    )

__all__ = ["Provider", "infer_provider", "PROVIDERS"]
