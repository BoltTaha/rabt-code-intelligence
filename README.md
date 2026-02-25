# Rabt (رَبط)

**Rabt** (project and research paper name): *Rabt: Computing Minimal Dependency Context for LLM-Based Code Intelligence.*  
A Graph-RAG system for code that **computes the right context** using a dependency graph and minimal subgraph (instead of probabilistic retrieval like Cursor/Copilot). Rabt = connection/link — the graph encodes the codebase’s structural links; the minimal subgraph is the precise connection needed to answer a query.

## Quick start

**First time:** create the venv and install deps. **Every time you open a new terminal**, activate the venv before running any Python commands:

```bash
# First time only
python3 -m venv .venv
source .venv/bin/activate   # Linux/macOS. On Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Every time (from project root)
source .venv/bin/activate
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

## Intent routing (regex + optional LLM)

By default, Rabt uses **deterministic regex** to map queries to intents (e.g., "Who calls save_user?" → `who_calls` intent). You can enable an **LLM-based intent router** that accepts natural variations:

- "Who calls save_user?" ✅
- "Which functions are calling save_user?" ✅
- "hey I need to figure out what is calling the request function" ✅

The LLM router outputs strict JSON (`{"intent": "who_calls", "target": "save_user"}`) and falls back to regex if unavailable or if the LLM fails.

**Config** (`config/default.yaml`):
```yaml
intent:
  router: "auto"   # regex | llm | auto
  model: ""        # optional override (defaults to llm.model)
```

**Behavior**:
- `regex`: deterministic only (no LLM call)
- `llm`: use LLM, then fallback to regex
- `auto`: LLM if `GEMINI_API_KEY` is set, else regex (default)

See [docs/README.md](docs/README.md) for more details.

Run all commands from the **project root** (this directory).
