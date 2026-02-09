# Rabt (رَبط)

**Rabt** (project and research paper name): *Rabt: Computing Minimal Dependency Context for LLM-Based Code Intelligence.*  
A Graph-RAG system for code that **computes the right context** using a dependency graph and minimal subgraph (instead of probabilistic retrieval like Cursor/Copilot). Rabt = connection/link — the graph encodes the codebase’s structural links; the minimal subgraph is the precise connection needed to answer a query.

## Quick start

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python run_pipeline.py --repo examples/sample_repo -q "Who calls save_user?"
```

## Documentation (all in `docs/`)

| Document | Purpose |
|----------|---------|
| [docs/PROJECT_LOG.md](docs/PROJECT_LOG.md) | **Start here.** What the project is, the example, what it solves, how it works, current scope. Easy to show to a mentor. |
| [docs/TESTING_REPORT.md](docs/TESTING_REPORT.md) | Testing protocol summary and table for the Experiments section of your report/paper. |
| [docs/README.md](docs/README.md) | Full project overview, architecture, feature comparison, validation metrics. |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | Software layers, contracts, project layout, run/test commands. |
| [docs/SETUP.md](docs/SETUP.md) | Venv and system-package setup. |
| [docs/PLAN.md](docs/PLAN.md) | Full implementation plan (week-by-week, phases, checklist). |

Run all commands from the **project root** (this directory).
