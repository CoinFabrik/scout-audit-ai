"""High-level orchestration for scout-ai-poc."""

from __future__ import annotations

import logging
import os
import sys
from pathlib import Path
from typing import Dict, Iterable

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import (
    ChatPromptTemplate,
    HumanMessagePromptTemplate,
    SystemMessagePromptTemplate,
)
from langchain_core.runnables import RunnableSequence

from .data_loader import (
    build_files_context,
    load_config,
    load_extra_inputs,
    read_prompt_file,
)
from .paths import DEFAULT_PROMPT_PATH
from .vulnerability_catalog import get_vulnerabilities

CONFIG_FILENAME = ".scout"
logger = logging.getLogger(__name__)

PROVIDER_TO_ENV = {
    "openai": "OPENAI_API_KEY",
    "anthropic": "ANTHROPIC_API_KEY",
    "gemini": "GOOGLE_API_KEY",
}


def should_execute_llm(explicit_dry_run: bool, provider: str) -> bool:
    if explicit_dry_run:
        logger.info("Dry-run flag active; LLM execution disabled.")
        return False
    api_key_env = PROVIDER_TO_ENV[provider]
    has_key = bool(os.getenv(api_key_env))
    if not has_key:
        logger.warning(f"{api_key_env} not set; defaulting to dry-run output.")
    return has_key


def build_prompt(prompt_text: str) -> ChatPromptTemplate:
    """Return a chat prompt that keeps system rules separate from file context."""
    return ChatPromptTemplate.from_messages(
        [
            SystemMessagePromptTemplate.from_template(prompt_text),
            HumanMessagePromptTemplate.from_template(
                """Analyze the following files and report exploitable vulnerabilities only:\n{files_context}"""
            ),
        ]
    )


def create_chain(
    prompt: ChatPromptTemplate, model_name: str, provider: str
) -> RunnableSequence:
    logger.info(
        "Creating LangChain pipeline with provider '%s' and model '%s'.",
        provider,
        model_name,
    )
    match provider:
        case "openai":
            try:
                from langchain_openai import ChatOpenAI
            except ImportError:
                raise ImportError(
                    "langchain_openai is not installed. Install it with: pip install langchain-openai"
                )
            llm = ChatOpenAI(
                model=model_name,
                temperature=1,
                model_kwargs={"reasoning_effort": "high"},
            )
        case "anthropic":
            try:
                from langchain_anthropic import ChatAnthropic
            except ImportError:
                raise ImportError(
                    "langchain_anthropic is not installed. Install it with: pip install langchain-anthropic"
                )
            llm = ChatAnthropic(model=model_name, temperature=1)
        case "gemini":
            try:
                from langchain_google_genai import ChatGoogleGenerativeAI
            except ImportError:
                raise ImportError(
                    "langchain_google_genai is not installed. Install it with: pip install langchain-google-genai"
                )
            llm = ChatGoogleGenerativeAI(model=model_name, temperature=1)
        case _:
            raise ValueError(f"Unsupported provider: {provider}")
    return prompt | llm | StrOutputParser()


def format_known_vulnerabilities(vulnerabilities: Iterable[str]) -> str:
    """Present catalog entries as a numbered list with a graceful empty fallback."""
    entries = [entry.strip() for entry in vulnerabilities if entry and entry.strip()]
    if not entries:
        return "\n- None documented."
    return "\n" + "\n".join(
        f"    {idx}. {entry}" for idx, entry in enumerate(entries, 1)
    )


def assemble_chain_inputs(
    contract_type: str,
    file_paths: Iterable[str],
    target_root: Path,
    extra_prompt_path: Path | None,
) -> Dict[str, str]:
    file_list = list(file_paths)
    files_context = build_files_context(file_list, target_root)
    vulnerabilities = get_vulnerabilities(contract_type)
    extra_inputs = load_extra_inputs(extra_prompt_path)
    logger.info(
        "Prepared chain inputs for contract_type='%s' (%d files, extra prompt: %s).",
        contract_type,
        len(file_list),
        "yes" if extra_prompt_path else "no",
    )

    return {
        "contract_type": contract_type,
        "known_vulnerabilities": format_known_vulnerabilities(vulnerabilities),
        "files_context": files_context,
        "extra_inputs": extra_inputs,
    }


def resolve_config_path(target_root: Path, config_override: str | None) -> Path:
    """Locate the canonical .scout file."""
    search_root = Path(config_override).expanduser() if config_override else target_root
    search_root = search_root.resolve()
    logger.debug(
        "Resolving config path. target_root=%s override=%s",
        target_root,
        config_override,
    )

    if search_root.is_file() and search_root.name != CONFIG_FILENAME:
        raise ValueError(
            f"Config file must be named '{CONFIG_FILENAME}', got {search_root.name!r}"
        )

    candidate = (
        search_root
        if search_root.name == CONFIG_FILENAME
        else search_root / CONFIG_FILENAME
    )

    if candidate.name != CONFIG_FILENAME:
        raise ValueError(
            f"Config path must resolve to '{CONFIG_FILENAME}', got {candidate.name!r}"
        )

    if not candidate.exists():
        raise FileNotFoundError(
            f"No '{CONFIG_FILENAME}' file found under {search_root}."
        )

    logger.info("Using config file at %s", candidate)
    return candidate


def run_analysis(args) -> int:
    target_root = Path(args.target).resolve()
    logger.info(
        "Starting analysis run. target=%s dry_run=%s", target_root, args.dry_run
    )

    # Set default model based on provider if not specified
    if not os.getenv("SCOUT_AI_MODEL"):
        if args.provider == "anthropic":
            args.model = "claude-sonnet-4-5-20250929"
        # openai already defaults to gpt-5

    config_path = resolve_config_path(target_root, args.config)
    config = load_config(config_path)
    prompt_text = read_prompt_file(DEFAULT_PROMPT_PATH)

    extra_prompt_path = Path(args.extra_prompt) if args.extra_prompt else None
    chain_inputs = assemble_chain_inputs(
        config["contract_type"],
        config["files"],
        target_root,
        extra_prompt_path,
    )
    prompt = build_prompt(prompt_text)

    if not should_execute_llm(args.dry_run, args.provider):
        logger.info("Rendering composed prompt without executing the LLM.")
        api_key_name = (
            "OPENAI_API_KEY" if args.provider == "openai" else "ANTHROPIC_API_KEY"
        )
        print(
            f"[DRY-RUN] Displaying composed prompt. Provide {api_key_name} to execute.\n"
        )
        messages = prompt.format_messages(**chain_inputs)
        for message in messages:
            role = message.type.upper()
            print(f"[{role}]\n{message.content}\n")
        return 0

    try:
        chain = create_chain(prompt, args.model, args.provider)
        result = chain.invoke(chain_inputs)
    except Exception as exc:
        logger.exception("Failed to execute LangChain pipeline.")
        print(f"Failed to execute LangChain pipeline: {exc}", file=sys.stderr)
        return 1

    output_text = result.get("text") if isinstance(result, dict) else result
    logger.info("LLM execution completed successfully.")
    print(output_text)
    return 0


__all__ = ["run_analysis"]
