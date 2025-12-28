# 2025-Q4 Grant Report

## Scout AI & Vulnerability Detection Research

## Executive Summary

This quarter, the project team executed a dual-track strategy focusing on both
theoretical research and practical engineering to advance the state of smart
contract security on Stellar. The primary objective was to move beyond simple
heuristic detection and explore how Artificial Intelligence can be effectively
applied to the specific constraints of the Soroban ecosystem.

Our research into the "State of the Art" (SOTA) revealed a critical industry
shift. The domain is transitioning from static, rule-based detection to dynamic,
agentic reasoning. However, we identified a significant barrier for non-EVM
ecosystems: the "Data Moat." While Ethereum-based tools utilize massive
historical datasets for model fine-tuning , younger ecosystems like Soroban lack
this data volume, rendering standard fine-tuning strategies unviable.

To address this gap, we developed and released **Scout AI**, a Proof-of-Concept
CLI tool designed to facilitate structured, checklist-driven auditing. Following
the development, we conducted experimental validation using advanced models.
This testing yielded a significant validation: combining the tool we developed
with proper check items, we successfully reproduced a finding from an external
audit report, proving our tool could autonomously detect known complex bugs.
However, we also confirmed a major limitation regarding "context dilution":
while GPT-5.2 managed to identify one issue in a broad scope, other models
failed completely when exposed to the full repository.

## The State of the Art Survey

We conducted a comprehensive technical survey to define the factors determining
high-performance vulnerability detection. The findings provided the strategic
foundation for our engineering work.

### The Limits of Current Tooling and the "Data Moat"

Our research indicates that traditional Static Application Security Testing
(SAST) tools have reached a performance plateau, often failing to detect
approximately 50% of vulnerabilities in modern benchmarks. Conversely, the
direct application of Large Language Models (LLMs) in a "zero-shot" capacity
suffers from low recall, frequently omitting critical flaws. The industry
solution has been the adoption of hybrid architectures. Commercial leaders like
Sherlock AI and Zellic have established dominance by leveraging "Data Moats",
proprietary repositories of contest findings used to fine-tune models.

### The Non-EVM Gap

A crucial finding for the Stellar ecosystem is that this "Data Moat" strategy is
not immediately replicable. The Ethereum ecosystem possesses a dataset of
millions of contracts and documented hacks , whereas younger ecosystems lack the
historical data required to train robust LLMs. Consequently, we concluded that
security tools for Stellar cannot rely on "big data" fine-tuning. Instead, they
must utilize hybrid architectures where the AI's role is guided by rigorous
context and static analysis rather than pre-trained knowledge alone. This
insight directly influenced the design of Scout AI to be a context-heavy,
prompt-structuring tool rather than a fine-tuned model.

## Scout AI Proof-of-Concept

In response to our research findings, we delivered **Scout AI**, a lightweight
CLI wrapper designed to help Soroban smart-contract reviewers assemble
structured audit prompts. The tool operates on the philosophy of minimizing
"surprise behavior" by enforcing reproducible, deterministic-leaning model
presets.

### Checklist-Driven Context Assembly

To compensate for the lack of fine-tuned models in the Rust ecosystem, Scout AI
utilizes a "checklist-driven" approach. The tool's core vulnerability database
is a Python module that programmatically assembles prompts based on the selected
check. This design choice ensures a high degree of control and consistency in
prompt generation.

The tool also supports supplementary prompts provided as plain text files. This
hybrid approach allows developers to maintain the core checks in Python while
enabling security researchers to define additional detection patterns without
requiring to modify tool source code.

### Architecture and Dependency Management

A major challenge in auditing Rust projects is ensuring the LLM has visibility
into imported modules. Scout AI addresses this via a Rust-aware dependency
walker. When the \--include-deps flag is active, the tool scans and inlines
local modules up to a requested depth. This reduces the missing module blind
spots that often degrade the performance of generic LLM interfaces.
Additionally, the tool includes a dry-run mode, allowing auditors to render and
inspect the exact prompt composed by the tool before incurring any API costs.

## Experimental Results

Following the release of the POC, we initiated an experimental phase to test the
efficacy of checklists with items that describe a vulnerability's conceptual
logic rather than its syntax. We developed five prompts covering categories such
as governance timing, sentinel values, and array duplication. These were tested
against GPT-5.2, Claude-Sonnet-4-5, and Gemini-3-pro-preview.

### Prompt Development

We derived every checklist item from confirmed vulnerabilities found in past
audit reports. After reviewing the vulnerable code, we drafted abstract check
items to detect the issue. Finally, we ran the tool against these samples and
refined the items through iteration.

### Prompt Validation

We validated the checklist by running the tool against a vulnerability
identified in an audit report. We hypothesized that one of our abstract prompts
would be capable of detecting this specific issue.\
The external audit found that a function accepted an array parameter without
validating it for duplicate elements, which could lead to logic errors in
processing.\
When provided with the relevant file in isolation, Scout AI with our prompt for
duplicated items in array parameters successfully identified the missing
validation. This proved that our check items can effectively catch complex logic
errors found in professional audits.

### Context Dilution

However, when we expanded the scope to simulate a full repository audit,
performance degraded significantly: GPT-5.2 demonstrated partial resilience,
correctly identifying one of the five issues even within the broader context.
Other models failed completely. The introduction of a larger context caused
"Context Dilution", where the models lost track of the specific variable
constraints amidst the noise of the repository.\
This empirically validates our SOTA survey's conclusion regarding the
limitations of monolithic prompts and the necessity for a more complex
architecture.

## Strategic Implications and Roadmap

The work completed in Q4 has crystallized our path forward. We have successfully
engineered a tool for structured prompting and proven that our abstract prompts
can detect confirmed vulnerabilities. However, the experimental results show
that simply feeding more files into a large context window is insufficient for
consistent detection.

Future development will pivot to a research phase designed to solve context
saturation. We plan to evaluate an advanced architecture leveraging multi-agent
workflows and chained API calls. This architectural evolution is intended to
solve the noise issue by intelligently narrowing the scope of analysis before
the final vulnerability assessment takes place.

