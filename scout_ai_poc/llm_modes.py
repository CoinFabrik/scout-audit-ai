from typing import Final

LLM_MODE_DETERMINISTIC: Final[str] = "deterministic"
LLM_MODE_CREATIVE: Final[str] = "creative"
LLM_MODES: Final[tuple[str, ...]] = (LLM_MODE_DETERMINISTIC, LLM_MODE_CREATIVE)
DEFAULT_LLM_MODE: Final[str] = LLM_MODE_DETERMINISTIC


def normalize_llm_mode(mode: str | None) -> str | None:
    if mode is None:
        return None
    normalized = mode.strip().lower()
    if normalized not in LLM_MODES:
        raise ValueError(f"'mode' must be one of {', '.join(LLM_MODES)}; got {mode!r}")
    return normalized
