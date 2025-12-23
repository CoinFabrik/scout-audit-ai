# Scout AI Proof-of-Concept Overview

## 28-Nov-25

# Purpose of this document

High level description about a Proof-of-concept which implements a selected approach to add AI for vulnerability detection in the context of Scout security bug detection tool.

# Proof-Of-Concept Purpose

* Help Rust smart-contract reviewers quickly assemble a structured audit prompt for an LLM.  
* Keep runs as reproducible as practical: deterministic-leaning model presets, explicit catalogs, and visible inputs (noting that LLM backends may still vary slightly run-to-run).  
* Stay lightweight so teams can inspect or extend prompts without deep framework knowledge or prior experience.

# High-Level Architecture

* CLI wrapper: `scout-ai-poc` shell script forwards into the Python entrypoint (`scout_ai_poc/main.py`) and its CLI parser.  
* Config intake: reads a `scout.json` JSON file under the target directory (or via `--config`), plus optional `--model` override and `--extra-prompt` snippet.  
* Prompt assembly: merges the base template, catalog entries for the declared `contract_type`, optional extra prompt text/JSON, and the contents of the listed files. File content is inlined so the LLM has full context.  
* Optional dependency expansion: when `--include-deps` is set, a Rust-aware dependency walker pulls local modules into the file list up to the requested depth.  
* Provider dispatch: the declared model maps to a provider preset; if an `API_KEY` is present and not in `--dry-run`, the LangChain pipeline calls the chosen backend, otherwise it prints the composed prompt for inspection.

# How to Run

* Install once from source: `python3.12 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt`  
* Invoke anywhere: `./scout-ai-poc examples --dry-run` prints the composed prompt without calling an LLM.  
* Bring your own extras: `./scout-ai-poc examples --dry-run --extra-prompt ./prompts/input_validation.json` to stitch in custom checks.  
* Add context automatically for multi-module Rust projects: `./scout-ai-poc examples/complex --dry-run --include-deps --dependency-depth 2`  
* Define `API_KEY=...` for live calls; drop `--dry-run` when ready. Model names in `scout.json` (or `--model`) pick the provider; unsupported names are rejected with clear guidance.

# Strengths

* Deterministic model presets minimize surprise behavior across providers.  
* Dry-run mode and explicit prompt rendering make it easy to review what will be sent before spending tokens.  
* Catalog-driven context keeps findings aligned to contract type while staying editable.  
* Optional dependency scanning reduces "missing module" blind spots on Rust projects.  
* Simple, file-based inputs (JSON/text) lower the barrier to contribute new checks or prompts.  
* Minimal operator burden: once installed, reviewers can run the CLI without Python expertise.

# Current Limitations

* LLM outputs remain probabilistic even with zeroed temperatures and seeded configs; expect minor variation across runs.  
* Predefined vulnerability catalogs may not align with every project's threat model; custom prompts might be needed.  
* Dependency discovery is Rust-focused and local-file-only; generated code or external crates are out of scope.  
* A single environment-wide `API_KEY` is assumed per run; per-provider or per-project credentials are not yet modeled.

# Initial Set of Test Contracts

* We used Blend Protocol to do an initial test for the POC. Blend is a universal liquidity protocol primitive that enables the permissionless creation of lending pools.
* Repo is located here: https://github.com/code-423n4/2025-02-blend
* The full list of smart contract analyzed has 27099 LOCs.
