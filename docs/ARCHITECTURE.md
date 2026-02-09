# Semantic Graph Memory — Architecture

This document describes the software design so the MVP stays maintainable and ready for the research paper.

## Layers (single responsibility)

| Layer      | Responsibility                    | Depends on        |
|-----------|------------------------------------|-------------------|
| **parser** | AST → nodes + static edges         | core.types only   |
| **graph**  | Build, persist, query DiGraph      | parser output, core |
| **runtime**| Instrumentation → runtime events   | core.types (stub in MVP) |
| **agent**  | Query → intent → traversal → subgraph | graph, core     |
| **llm**    | Subgraph + query → answer + confidence | (stub in MVP)  |
| **run_pipeline** | Orchestrate only; no business logic | all layers   |

Data flows one way: **Parser → Graph → Agent → LLM**.

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
├── runtime/        # Instrumentation (stub until Phase 2)
├── agent/          # Intent, traversal, subgraph text
├── llm/            # Prompt + API (stub until Phase 5)
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
.venv/bin/python run_pipeline.py --repo examples/sample_repo --query "Who calls save_user?"

# Or with system packages if available
python3 run_pipeline.py --repo examples/sample_repo -q "Who calls save_user?"
```

## Testing

```bash
.venv/bin/python -m pytest tests/ -v
```

## Config

`config/default.yaml` — traversal limits, persist path, optional LLM and runtime settings. Override with `--config path/to/config.yaml`.
