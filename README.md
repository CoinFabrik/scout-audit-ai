# scout-ai-poc

Proof-of-concept CLI that wires a LangChain prompt around Rust smart contract files. The tool reads a `.scout` configuration, enriches it with a per-contract vulnerability catalog, merges any extra prompt snippets, and prepares a final request for an LLM.

## Quickstart

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Environment Setup

For LLM API access, expose a single `API_KEY` (either by `source .envrc` or by exporting it yourself):

```bash
source .envrc  # loads values from .env automatically

# Or manually:
export API_KEY="your-model-key"
export SCOUT_LOG_LEVEL="INFO"  # optional; controls logging verbosity
```

The CLI reads `.env` automatically through `python-dotenv`, so defining `API_KEY=...` in that file is usually the easiest approach.

Usage mirrors the requested interface:

```bash
./scout-ai-poc examples \
  --extraPrompt ./prompts/input_validation.json \
  --dry-run
```

The CLI automatically looks for a file named `.scout` inside the target directory. Pass `--config <path>` only when you need to point discovery at a different directory (or at an explicit `.scout` file).

Pass `--include-deps` to inspect each listed Rust file for local `mod foo;` declarations and any `use` paths (e.g., `use crate::foo::bar`) so that referenced modules are automatically added to the prompt. Control recursion with `--dependency-depth` (default `1`), which is ignored unless dependencies are enabled. Installing `tree_sitter` and `tree_sitter_rust` is required for this flag.
Remove `--dry-run` and set `API_KEY` once you are ready to hit your provider. The CLI automatically infers which backend to call based on the model string defined in `.scout` (override it per-run via `--model`). Supported models are enumerated inside `scout_ai_poc/llm_config.py`—if you pass an unknown model, the CLI will tell you which options are available per provider.

For a richer dependency graph demo, run the complex example:

```bash
./scout-ai-poc examples/complex \
  --dry-run \
  --include-deps \
  --dependency-depth 2
```

## Project layout

- `scout_ai_poc/main.py` – tiny entry point delegating to the CLI + runner.
- `scout_ai_poc/cli.py` – argument parsing and default selection.
- `scout_ai_poc/data_loader.py` – config parsing plus file/prompt ingestion helpers.
- `scout_ai_poc/runner.py` – orchestrates vulnerability catalog lookups and LangChain execution.
- `scout_ai_poc/vulnerability_catalog.py` – curated vulnerabilities per contract type.
- `prompts/base_prompt.txt` – primary template; edit this file to adjust model instructions.
- `prompts/input_validation.json` – example extra prompt payload wired via `--extraPrompt`.
- `examples/.scout` – demo configuration pointing at `contracts/swap.rs`.
- `examples/complex/.scout` – dependency-heavy sample centered on `contracts/gateway.rs`.
- `scout-ai-poc` – thin wrapper so you can run `scout-ai-poc …` locally.

## .scout file format

Each project keeps a single file literally named `.scout`, located at the directory passed as `target` (or the directory supplied via `--config`). The file is a plain JSON document with the following minimal schema:

```json
{
  "contract_type": "dex",
  "model": "gpt-5.1-mini",
  "files": ["relative/or/absolute/path/to/file.rs"]
}
```

`contract_type` selects the vulnerability catalog. `model` controls which LLM to use (and implicitly which provider is invoked). `files` entries are resolved relative to `target` and inlined into the prompt in the order provided.

### Deterministic LLM configuration

Each supported model has an explicit deterministic preset in `scout_ai_poc/llm_config.py`. We start from a shared base (temperature `0.0`, fixed `seed`, zero penalties) and then specialize by provider/model—for example, Gemini forces `top_p=0`/`top_k=1`, while `gpt-5.1` drops `temperature` entirely because that endpoint rejects it and instead receives only the `reasoning_effort` hint. The adapter only forwards knobs the backend accepts so errors from unsupported parameters are avoided.

## Extra prompt inputs

`--extraPrompt` accepts any text file. If the file extension is `.json`, the CLI pretty-prints its contents before stitching it into the template, which makes it easy to keep structured checklists such as `prompts/input_validation.json`.

## Running against real models

1. Define `API_KEY` (via `.env` or `export API_KEY=...`).
2. Drop the `--dry-run` flag.
3. Ensure your `.scout` file specifies the desired `model` (or pass `--model` to override it).
4. Execute the CLI; LangChain's runnable pipeline (`prompt | llm | parser`) will render the template and send it to the inferred provider.

When `API_KEY` is missing, the CLI prints the composed prompt so you can verify everything before burning tokens.
