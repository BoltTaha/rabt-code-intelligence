# Semantic Graph Memory — Architecture

This document describes the software design so the MVP stays maintainable and ready for the research paper.

## Layers (single responsibility)

| Layer      | Responsibility                    | Depends on        |
|-----------|------------------------------------|-------------------|
| **parser** | AST → nodes + static edges         | core.types only   |
| **graph**  | Build, persist, query DiGraph      | parser output, core, runtime events |
| **runtime**| Call/mutation tracing → runtime events; read `.runtime_events.jsonl` | core.types |
| **agent**  | Query → intent → traversal → subgraph → text (with impact weights) | graph, core |
| **llm**    | Subgraph + query → answer + confidence (Gemini when key set) | config, subgraph |
| **run_pipeline** | Orchestrate only; load default config; no business logic | all layers   |

Data flows one way: **Parser + Runtime logs → Graph (merged) → Agent → LLM**.

Intent routing: the agent can use deterministic regex or an optional LLM router (JSON intent) with regex fallback, configured in `config/default.yaml` under `intent`.

## Contracts (core/types.py)

- **Node** — id, kind (function/class/variable/module), name, module, line, metadata
- **Edge** — source_id, target_id, edge_type (CALLS, IMPORTS, INHERITS, REFERENCES, RuntimeCall, MODIFIED_BY), weight
- **ParserOutput** — nodes, edges (parser output)
- **RuntimeEvent** — event_type, source_id, target_id, variable_id, count (runtime layer output)

All layers use these types; no layer-specific structs in the pipeline.

## Project layout

```
├── core/           # Shared types (contracts)
├── config/         # Default YAML config
├── parser/         # Static analysis (AST → ParserOutput)
├── graph/          # Build, storage, queries
├── runtime/        # Tracer (track_runtime, track_mutation), collect_runtime_events
├── agent/          # Intent, traversal, subgraph → text (incl. "executed N times")
├── llm/            # Prompt + Gemini API (real answers when GEMINI_API_KEY set)
├── evaluation/     # (Future) Baselines, metrics for paper
├── examples/       # sample_repo (3–5 files)
├── tests/          # Unit + integration
├── run_pipeline.py # Single entry point
└── requirements.txt
```

## Running

```bash
# Create venv (recommended)
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt

# Optional: generate runtime events (call + mutation) then run pipeline
.venv/bin/python examples/sample_repo/main.py   # append to .runtime_events.jsonl
.venv/bin/python run_pipeline.py --repo examples/sample_repo -q "Who calls save_user?"

# Pipeline loads config/default.yaml by default (runtime.main_module, llm, etc.)
```

## Testing

```bash
.venv/bin/python -m pytest tests/ -v
```

## Config

`config/default.yaml` — traversal limits, persist path, optional LLM and runtime settings. Override with `--config path/to/config.yaml`.

## Week 9 tools (visualization, change detection, baseline)

- **Visualization:** After running the pipeline, generate a graph image (red = hot path, blue = cold):
  ```bash
  .venv/bin/pip install matplotlib   # if not already installed
  .venv/bin/python visualize_graph.py --graph .graph.json --out graph.png
  ```
- **Change detection:** Rebuild the graph only if the repo has changed (e.g. after editing code or in a git hook):
  ```bash
  .venv/bin/python update_graph_if_changed.py --repo examples/sample_repo
  ```
  Use `--force` to rebuild even when git reports no changes.
- **Baseline comparison:** Compare full-repo context vs Rabt subgraph (tokens and answers):
  ```bash
  .venv/bin/python -m evaluation.baseline_comparison --repo examples/sample_repo --query "Where is userData modified?"
  ```
