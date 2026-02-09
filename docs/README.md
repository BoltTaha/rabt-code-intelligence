# Rabt (رَبط)

> **A runtime-aware code intelligence engine that computes *correct context* for LLMs instead of guessing it.**

Other docs in this folder: [PROJECT_LOG.md](PROJECT_LOG.md) (report for mentor), [TESTING_REPORT.md](TESTING_REPORT.md), [ARCHITECTURE.md](ARCHITECTURE.md), [SETUP.md](SETUP.md), [PLAN.md](PLAN.md).

---

## 🚀 What This Project Is

**Rabt** is a research-grade prototype that builds a *dependency graph* of a codebase (today: static analysis; runtime is planned).

Instead of sending entire files (or guessing relevant ones) to an LLM, this system:
1. Computes *actual* dependencies
2. Extracts a **minimal, high-signal subgraph**
3. Feeds only that slice to the LLM

The result: **more accurate answers, fewer hallucinations, and dramatically less context**.

---

## 🧠 Why This Exists (The Problem)

Modern AI coding tools (Cursor, Copilot, etc.) rely on:
- semantic search
- embeddings
- file-level heuristics

These approaches **guess context**.

They break down when:
- runtime behavior differs from static structure
- variables are mutated indirectly
- long call chains exist
- side effects matter

This leads to *context rot*: the LLM sees irrelevant code and misses what actually matters.

---

## ✨ Core Idea (One Sentence)

> Build an explicit dependency graph (static + runtime), then give the LLM only the *minimal subgraph* required to answer a question correctly.

---

## 🆚 How This Differs From Existing Tools

| Feature | Cursor / Copilot | This Project |
|------|------------------|--------------|
| Static AST analysis | ✅ | ✅ |
| Runtime-aware dependencies | ❌ | ✅ |
| Variable mutation tracking | ❌ | ✅ |
| Impact scoring | ❌ | ✅ |
| Minimal dependency subgraph | ❌ | ✅ |
| Confidence-aware answers | ❌ | ✅ |
| Explicit inspectable graph | ❌ | ✅ |

**Cursor guesses context. This computes it.**

---

## 🏗️ Architecture Overview

```
AST (static)
   ↓
Runtime Instrumentation
   ↓
Unified Dependency Graph (NetworkX)
   ↓
Weighted / Impact Scoring
   ↓
Query Agent
   ↓
Minimal Subgraph
   ↓
LLM
   ↓
Answer + Confidence Score
```

---

## 🔗 Dependency Graph

### Node Types
- Functions
- Classes
- Variables
- Modules

### Edge Types
**Static**
- `CALLS`
- `IMPORTS`
- `INHERITS`
- `REFERENCES`

**Dynamic (Runtime)**
- `RuntimeCall`
- `MODIFIED_BY`

---

## 🎯 Supported Queries (MVP Scope)

The system supports **explicit, testable query intents**:

| Query | Intent | Traversal |
|------|-------|----------|
| Where is `X` modified? | Mutation tracking | `MODIFIED_BY` |
| Who calls function `Y`? | Reverse calls | `CALLS` |
| What breaks if I change `Z`? | Forward impact | Downstream `CALLS` |
| What does module `M` import? | Dependency lookup | `IMPORTS` |

---

## ⚖️ Confidence Scoring

Every answer includes a confidence level:

| Level | Meaning |
|-----|--------|
| **HIGH** | Static + runtime data agree |
| **MEDIUM** | Static-only evidence |
| **LOW** | Inferred / partial data |

This makes limitations explicit and increases trust.

---

## 📊 Impact Scoring

Each node/edge is weighted based on:
- runtime call frequency
- number of downstream dependents

Example formula:
```
impact = 0.5 * normalized_call_frequency + 0.5 * normalized_downstream_count
```

This allows ranking:
- critical paths
- high-risk changes
- hot functions

---

## 🧪 Validation Metrics

The system is evaluated using measurable criteria:

| Metric | Target |
|------|-------|
| Query correctness | >95% |
| Subgraph reduction | >70% |
| Token reduction | >60% |
| Hallucination rate | Lower vs baselines |
| Graph update latency | <30s |

Baselines:
1. Full-repo context
2. Cursor-style file context
3. Minimal subgraph (this system)

---

## 📂 Project Structure

```
semantic-graph-memory/
├── parser/        # AST parsing (Tree-sitter)
├── runtime/       # Runtime instrumentation
├── graph/         # Graph construction & storage
├── agent/         # Query agent & traversal logic
├── llm/           # LLM integration
├── visualization/ # Graph rendering
├── tests/         # Query + metric tests
├── examples/      # Sample repos (3–5 files)
└── run_pipeline.py
```

---

## ▶️ Quick Start

```bash
# Create virtual environment (recommended)
python3 -m venv .venv
source .venv/bin/activate   # or .venv\Scripts\activate on Windows
pip install -r requirements.txt

# Run pipeline
python run_pipeline.py --repo examples/sample_repo --query "Who calls save_user?"
```

See **ARCHITECTURE.md** for layer design, contracts, and project layout.

---

## 🧩 Runtime Instrumentation (Explicit Scope)

Runtime tracking is **opt-in** via decorators or config.

Example:
```python
@track_runtime
@track_mutations(['userData'])
def update_user(data):
    ...
```

This keeps runtime analysis controlled and reproducible.

---

## 🚫 Out of Scope (MVP)

- Async tracing
- Reflection-heavy code (`getattr`, `setattr`)
- Metaprogramming
- Dynamic code generation (`exec`, `eval`)
- Multi-language support

---

## 🧠 Why This Matters

This project demonstrates that:
- **Structure beats scale** for code reasoning
- Runtime behavior is essential for correctness
- LLMs perform better with computed context

It is suitable for:
- research & academic evaluation
- enterprise code understanding
- safety-critical systems
- future IDE / AI tool integration

---

## 📌 Status

- MVP focused on Python
- Small repositories (3–5 files)
- Research-grade prototype
- Designed to scale after validation

---

## 📜 License

MIT License (prototype / research use)

---

## 🙌 Final Note

This project does **not** try to replace AI coding tools.

It provides something they currently lack:

> **A trustworthy, runtime-aware notion of code context.**

---

*Built to compute truth — not guess it.*

