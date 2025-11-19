# scout-ai-poc

Proof-of-concept CLI that wires a LangChain prompt around Rust smart contract files. The tool reads a `.scout` configuration, enriches it with a per-contract vulnerability catalog, merges any extra prompt snippets, and prepares a final request for an LLM.

## Quickstart

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Environment Setup

For LLM API access, set up your environment variables:

```bash
# Load environment variables from .env file
source .envrc

# Or manually set:
export OPENAI_API_KEY="your-api-key-here"
export ANTHROPIC_API_KEY="your-anthropic-key-here"  # for Anthropic Claude
export SCOUT_AI_PROVIDER="openai"  # or "anthropic", defaults to openai
export SCOUT_AI_MODEL="gpt-5"  # optional, defaults to gpt-5 for openai, claude-sonnet-4-5-20250929 for anthropic
```

The `.envrc` script automatically loads variables from a `.env` file (which is gitignored for security).

Usage mirrors the requested interface:

```bash
./scout-ai-poc examples \
  --extraPrompt ./prompts/input_validation.json \
  --dry-run
```

The CLI automatically looks for a file named `.scout` inside the target directory. Pass `--config <path>` only when you need to point discovery at a different directory (or at an explicit `.scout` file).

Remove `--dry-run` and set the appropriate API key once you are ready to hit your provider. Use `--provider anthropic` to switch to Anthropic Claude models. Define `SCOUT_AI_MODEL` to override the default model name (defaults to `gpt-5` for OpenAI, `claude-sonnet-4-5-20250929` for Anthropic).

## Project layout

- `scout_ai_poc/main.py` – tiny entry point delegating to the CLI + runner.
- `scout_ai_poc/cli.py` – argument parsing and default selection.
- `scout_ai_poc/data_loader.py` – config parsing plus file/prompt ingestion helpers.
- `scout_ai_poc/runner.py` – orchestrates vulnerability catalog lookups and LangChain execution.
- `scout_ai_poc/vulnerability_catalog.py` – curated vulnerabilities per contract type.
- `prompts/base_prompt.txt` – primary template; edit this file to adjust model instructions.
- `prompts/input_validation.json` – example extra prompt payload wired via `--extraPrompt`.
- `examples/.scout` – demo configuration pointing at `contracts/swap.rs`.
- `scout-ai-poc` – thin wrapper so you can run `scout-ai-poc …` locally.

## .scout file format

Each project keeps a single file literally named `.scout`, located at the directory passed as `target` (or the directory supplied via `--config`). The file is a plain JSON document with the following minimal schema:

```json
{
  "contract_type": "dex",
  "files": [
    "relative/or/absolute/path/to/file.rs"
  ]
}
```

`contract_type` is used to select known vulnerabilities. `files` entries are resolved relative to the CLI's `target` argument and inlined into the prompt in the order provided.

## Extra prompt inputs

`--extraPrompt` accepts any text file. If the file extension is `.json`, the CLI pretty-prints its contents before stitching it into the template, which makes it easy to keep structured checklists such as `prompts/input_validation.json`.

## Running against real models

1. Export `OPENAI_API_KEY` for OpenAI models or `ANTHROPIC_API_KEY` for Anthropic Claude models.
2. Optionally set `SCOUT_AI_PROVIDER` to "anthropic" to use Anthropic (defaults to "openai").
3. Drop the `--dry-run` flag.
4. Execute the CLI as shown above; LangChain's runnable pipeline (`prompt | llm | parser`) will render the template and send it to the model.

The CLI prints the composed prompt when credentials are absent, so you can verify everything before burning tokens.
