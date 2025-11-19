# Repository Guidelines

## Project Structure & Module Organization

The CLI logic lives inside `scout_ai_poc/`: `cli.py` handles argument parsing,
`data_loader.py` ingests `.scout` configs plus prompt files, `runner.py`
stitches vulnerability catalogs into the final payload, and `main.py` wires
everything together. `prompts/` stores reusable template fragments (edit
`base_prompt.txt` to shift tone, and drop JSON snippets that can be referenced
with `--extraPrompt`). Use `examples/` for contract fixtures such as
`contracts/swap.rs`; the canonical config there is `examples/.scout`. The
root-level `scout-ai-poc` Bash shim simply forwards to
`python3 -m scout_ai_poc.main`, allowing you to invoke the tool without touching
PYTHONPATH.

## Build, Test, and Development Commands

- `python3 -m venv .venv && source .venv/bin/activate` — create an isolated
  environment.
- `pip install -r requirements.txt` — sync LangChain + OpenAI/Anthropic
  dependencies.
- `./scout-ai-poc examples --dry-run` — autodetects `examples/.scout` and
  renders the composed prompt without calling an LLM; ideal for debugging
  configs.
- `OPENAI_API_KEY=... ./scout-ai-poc <target> --extraPrompt prompts/input_validation.json`
  — run end-to-end against OpenAI (default provider).
- `ANTHROPIC_API_KEY=... ./scout-ai-poc <target> --provider anthropic --model claude-sonnet-4-5-20250929`
  — run end-to-end against Anthropic. Override provider with `SCOUT_AI_PROVIDER`
  and model with `SCOUT_AI_MODEL` as needed. Pass `--config <path>` only when
  the `.scout` file lives outside `<target>`.

## Coding Style & Naming Conventions

Stick to idiomatic Python 3.11: 4-space indentation, type hints, and
single-responsibility functions that mirror the current modules. Use snake_case
for files, functions, and CLI arguments (`--extraPrompt` stays camelCase because
it reflects the legacy contract). Keep prompts as plain text or pretty-printed
JSON; name new templates descriptively (for example,
`prompts/reentrancy_checklist.json`). Run `python -m compileall scout_ai_poc` or
a formatter such as `ruff format` before committing if you introduce new
modules.

## Testing Guidelines

There is no automated suite yet, so prefer adding targeted `pytest` cases under
a new `tests/` directory, mirroring module names (e.g.,
`tests/test_data_loader.py`). Name tests after the behavior under scrutiny
(`test_merges_extra_prompt_when_json`). For manual validation, rely on
`--dry-run` plus small `.scout` fixtures inside `examples/`. Treat regression
scenarios by diffing the rendered prompt output; aim for high coverage on
catalog expansion and file path resolution logic since those affect every run.

## Commit & Pull Request Guidelines

Follow a concise, present-tense style such as `feat: add wasm target catalog` or
`fix: guard missing prompt`. Each PR should describe the motivation, list the
CLI commands you used for verification, and reference related `.scout` samples
or issues. Include screenshots of prompt diffs only when they clarify behavior
changes. Keep changes scoped (CLI parsing, runner behavior, or catalog data) so
reviewers can quickly reason about risk.

## Security & Configuration Tips

Never commit real `OPENAI_API_KEY` values or production `.scout` files—treat
them as secrets and load through environment variables. Validate `.scout` inputs
before running remote analyses, especially if contract sources come from
untrusted repositories. When sharing prompt snippets, scrub customer-identifying
details and keep the minimal set of files required to reproduce the
vulnerability context.
