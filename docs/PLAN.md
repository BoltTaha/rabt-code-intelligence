# Rabt (رَبط) — Implementation Plan

**Project Goal:** Build an AI-assisted coding tool that understands real code dependencies (static + dynamic), helps answer questions about code, track variable changes, and prevent errors caused by "context rot."

**Approach:** Start small (3–5 files) → validate each phase → scale.

**Data Flow:** AST → Runtime Graph → Weighted Graph → Query Agent → Minimal Subgraph → LLM → Answer

**One-sentence summary:**  
You're building a system that creates a *living* dependency graph of code (static + runtime), then feeds only the relevant slice of that graph to an LLM so it answers accurately without losing context.

**Cursor vs this project:** Cursor guesses context. You compute context.  
- Cursor = smart autocomplete  
- This = code intelligence engine

**Verdict:** This plan is ready to implement. No major components need to be added before starting. Follow the week-by-week checklist. Not over-engineered — 3–5 files, NetworkX, simple decorators = research-grade MVP.

---

## Plan Strengths (What's Already Solid)

| Strength | Why it helps |
|----------|--------------|
| **Step-by-step MVP** | Start small (3–5 files) → static graph → runtime edges → query → LLM → auto-update → visualization. Perfect for research + implementation. |
| **Clear novelty** | Runtime edges, impact scoring, minimal subgraph, auto-update, visualization — all new vs Cursor / existing tools. |
| **Validation metrics** | Query correctness, subgraph minimality, hallucination reduction, graph freshness — what reviewers/supervisors ask for. |
| **Week-by-week checklist** | Actionable; follow it and you get a working prototype in ~10 weeks. |
| **Optional enhancements** | Multi-repo, dashboard, CI/CD deferred — MVP stays focused. |

---

## Cursor vs This Project (What's NOT Solved)

Cursor solves ~60% of this. You're targeting the remaining ~40%.

| Your feature | Cursor |
|--------------|--------|
| Runtime-aware edges (what actually ran) | ❌ |
| Variable mutation tracking over time | ❌ |
| Impact scoring based on execution frequency | ❌ |
| Minimal dependency subgraph (not just files) | ❌ |
| Change → graph update with downstream impact | ❌ |
| Explicit graph you can query / test / visualize | ❌ |

**Different game, different users.**

| | Cursor | This project |
|---|--------|--------------|
| **Optimizes** | Speed, UX, autocomplete happiness | Correctness, reasoning, deep understanding, safety in large codebases |
| **Target users** | General developers | Infra teams, backend-heavy systems, fintech / health / enterprise, research & audits |

---

## Lock In Early (3 Recommendations)

Add these early — they massively improve trust, debuggability, and proof.

### 1️⃣ Failure mode handling (confidence score)

**Problem:** Plan assumes things work. What if runtime logs are missing? Variable modified via `setattr` or dict keys? Graph incomplete?

**Fix:** Attach a confidence score per answer:

| Score | Meaning |
|-------|---------|
| **HIGH** | Static + runtime agree |
| **MEDIUM** | Static only (no runtime data) |
| **LOW** | Inferred / best guess |

**Intentional failure example (builds credibility):** Include 1 known failure case in docs or tests:  
"This query returns MEDIUM confidence because runtime data is missing."  
This actually increases credibility, not weakness — shows you know the limits.

### 2️⃣ Query → intent mapping (explicit)

Map natural-language queries to traversal strategy — makes testing and benchmarking clean.

| Query pattern | Intent | Edge type / traversal |
|---------------|--------|------------------------|
| "Where is X modified?" | Modification tracking | MODIFIED_BY |
| "What breaks if I change Y?" | Forward impact | CALLS (downstream) |
| "Why is this function slow?" | Runtime hot path | High-frequency RuntimeCall |

### 3️⃣ Baseline comparison (for proof)

Run the same queries with three contexts. Gold for blog, paper, investors.

| Baseline | What it is |
|----------|------------|
| **LLM + full repo** | All files as context |
| **LLM + Cursor-style** | File-level / semantic search context |
| **LLM + your minimal subgraph** | Your approach |

Compare: correctness, tokens used, hallucination rate.

---

## The Real Risks (Execution Is Where People Fail)

| Risk | Why it hurts | How you handle it |
|------|--------------|-------------------|
| **1. Runtime tracking complexity** | Python runtime tracking sounds easy until: dynamic attributes, dict mutations, lambdas, async. | Limit scope, track selected variables, use confidence scores. Risk is **managed**, not eliminated. That's acceptable. |
| **2. Query understanding drift** | Natural-language queries can explode in complexity. | Query → intent mapping is correct. Keep supported queries **limited early**. Don't chase "understand anything" too soon. |
| **3. Over-building before proof** | Plan is detailed (good), but don't implement blindly. | **Rule:** Each phase must answer a question. If the answer is "meh", pause and adjust. |

### Phase Questions (Answer Before Moving On)

| Phase | Question to answer |
|-------|--------------------|
| Phase 2 (Runtime) | Does runtime info actually improve correctness? |
| Phase 4 (Query Agent) | Is minimal subgraph really smaller? |
| Phase 5 (LLM) | Does minimal context reduce hallucination vs full graph? |

---

## What Could Make It Stronger (Optional Improvements)

| Improvement | Why | When |
|-------------|-----|------|
| **Validation automation** | Unit tests for queries → auto-validate correctness + minimality | Week 11+ |
| **Metrics thresholds** | Define targets (e.g. >95% correctness) — see Validation Metrics section | From start |
| **Runtime scope definition** | Config or decorator to mark tracked modules — reproducible | Week 3 |
| **LLM prompt template** | Standard format for subgraph + question → consistent testing | Week 8 |
| **Change detection earlier** | Move to after Week 4 if you want live-update feedback sooner | Optional |
| **Time dimension** | Right now graph = state. Later: edge timestamps, versioned mutations. Enables "When did this behavior change?" / "Which commit caused this?" | Not MVP — future-proof. |
| **Explainability output** | Besides answers, return *why* this node was included, *why* this edge mattered. E.g. "Included because it modifies userData at runtime." Makes debugging 🔥 | Small win — add when LLM works |

---

## What You Need to Implement (Core Components)

Use this as the master checklist of *what* to build. Each maps to the week-by-week tasks below.

| # | Component | What to build | Novel? |
|---|-----------|---------------|--------|
| 1 | **Parser (Static Analysis)** | Tree-sitter → AST → nodes (functions, classes, variables) + edges (CALLS, IMPORTS, INHERITS) | No |
| 2 | **Graph Storage** | NetworkX DiGraph; persist to JSON/pickle | No |
| 3 | **Runtime Instrumentation** | Decorators + wrappers → log calls + mutations → RuntimeCall, MODIFIED_BY edges | ✅ Yes |
| 4 | **Weighted Edges / Impact Scoring** | Weights from call frequency + downstream dependents; critical variables | ✅ Yes |
| 5 | **Query Agent** | Parse query → weighted BFS/DFS → minimal subgraph | ✅ Yes |
| 6 | **Subgraph Extraction** | Limit depth + node budget; format as text for LLM | ✅ Yes |
| 7 | **LLM Integration** | Prompt = subgraph + query → precise answer | Partially |
| 8 | **Change Detection** | Git diff → re-parse changed files → update graph | ✅ Yes |
| 9 | **Visualization** | Matplotlib/Plotly → nodes + edges + weights | ✅ Yes |

---

## Decisions (Lock These In)

| Decision | Choice | Reason |
|----------|--------|--------|
| Language | Python | Simpler for decorators + NetworkX + Tree-sitter |
| Graph storage (MVP) | NetworkX | No DB setup; easy BFS/DFS |
| Runtime scope | User-selected modules only | Reduces complexity; expand later |
| Test repo | 3–5 Python files | Small enough to debug, big enough to validate |

**Runtime scope (how to mark modules):** Use a config file (e.g. `config.yaml`) or decorator marker:

```yaml
# config.yaml
track_modules:
  - main
  - user_service
  - data_handler
track_variables:
  - userData
  - config
```

Or in code: `@track_runtime` on functions you want to instrument. Reproducible and explicit.

---

## Out of Scope (MVP)

**Not supported in MVP.** Protects you from scope creep. Huge for reviewers.

- Async tracing
- Reflection-heavy code (`getattr`, `setattr`, `__import__`, etc.)
- Metaprogramming
- Dynamic code generation (`exec`, `eval` on runtime strings)

---

## Validation Metrics & Thresholds

| Metric | How to measure | Target |
|--------|----------------|--------|
| Query correctness | Ground truth vs graph/LLM answers | **>95%** correct |
| Subgraph minimality | `(full_nodes - subgraph_nodes) / full_nodes` | **>70%** reduction |
| LLM token reduction | Tokens with minimal subgraph vs full graph | **>60%** fewer tokens |
| Hallucination reduction | Compare LLM answers with vs without minimal subgraph | Fewer false positives |
| Graph freshness | Time from code change to graph update | **<30 seconds** |

**Baseline comparison:** Run same queries with (a) full repo, (b) Cursor-style file context, (c) your minimal subgraph. Compare correctness, token count, hallucination. Gold for blog / paper / investors.

**Validation automation (later):** Write unit tests for queries so correctness and minimality can be validated automatically. Example: `test_query_modification()` expects specific nodes in subgraph.

---

## Phase Overview

| Phase | Deliverable | Est. Time | Question to answer |
|-------|-------------|-----------|--------------------|
| 1 | Static graph + basic queries | Weeks 1–2 | — |
| 2 | Runtime edges | Weeks 3–4 | Does runtime info actually improve correctness? |
| 3 | Impact scoring / weighted edges | Week 5 | — |
| 4 | Query agent + minimal subgraph | Weeks 6–7 | Is minimal subgraph really smaller? |
| 5 | LLM integration | Week 8 | Does minimal context reduce hallucination vs full graph? |
| 6 | Change detection + auto-update | Week 9 | — |
| 7 | Basic visualization | Week 10 | — |
| 8 | Polish + metrics | Week 11+ | — |

---

## Week-by-Week Checklist

### Week 1: Foundation + Static Parser

- [ ] Set up project structure (`parser/`, `graph/`, `runtime/`, `agent/`, `llm/`, `tests/`, `examples/`)
- [ ] Create virtual env + `requirements.txt` (tree-sitter, py-tree-sitter, networkx, pytest)
- [ ] Create `examples/sample_repo/` with 3–5 Python files (functions, classes, imports, cross-file calls)
- [ ] Install Tree-sitter + Python grammar
- [ ] Implement parser: walk AST → extract functions, classes, variables, imports, calls
- [ ] Output: list of nodes + static edges (format: `(from, to, edge_type)`)

### Week 2: Graph Storage + Basic Queries

- [ ] Build NetworkX DiGraph from parser output
- [ ] Edge types: `CALLS`, `IMPORTS`, `INHERITS`, `REFERENCES`
- [ ] Persist graph (JSON or pickle)
- [ ] Implement query: "Which functions call X?"
- [ ] Implement query: "What does Y import?"
- [ ] Document ground truth for 5 sample queries (for later validation)
- [ ] Record: node count, edge count for sample repo

### Week 3: Runtime Instrumentation (Part 1)

- [ ] Add decorator to log function calls (caller → callee, count)
- [ ] Run sample repo; log runtime events to file (JSON)
- [ ] Define `RuntimeCall` edge type
- [ ] Merge runtime edges into graph (same NetworkX graph)
- [ ] Validate: runtime edges appear for at least 1 call chain in sample repo

### Week 4: Runtime Instrumentation (Part 2)

- [ ] Add variable mutation tracking (Python wrappers or decorators on selected functions)
- [ ] Define `MODIFIED_BY` edge type
- [ ] Track at least 1 critical variable (e.g. `userData`) in sample repo
- [ ] Merge `MODIFIED_BY` edges into graph
- [ ] Validate: "Where is X modified?" returns correct answer

### Week 5: Impact Scoring

- [ ] Compute call frequency from runtime logs → assign to edges
- [ ] Compute transitive downstream dependents per node
- [ ] Define simple impact score: e.g. `0.5 * frequency_norm + 0.5 * downstream_norm`
- [ ] Attach weights to edges (0–1)
- [ ] Implement: "Top N nodes by impact"
- [ ] Validate: critical path (main → save → update) ranks high

### Week 6: Query Agent (Part 1)

- [ ] Define query → intent mapping (e.g. "Where is X modified?" → MODIFIED_BY; "What breaks if Y?" → forward CALLS)
- [ ] Parse user query → extract target node(s) + relationship type
- [ ] Implement weighted BFS/DFS from seed nodes
- [ ] Depth limit: 3–5 hops; node budget: 50–100
- [ ] Extract minimal subgraph
- [ ] Format subgraph as text, e.g.:
  ```
  function saveUser calls updateUser
  function updateUser MODIFIES userData
  ```
- [ ] Validate: subgraph for "Where is userData modified?" < 20 nodes

### Week 7: Query Agent (Part 2) + Subgraph Metrics

- [ ] Support 3+ query types (modification, calls, impact)
- [ ] Compute subgraph minimality: `(full_graph_nodes - subgraph_nodes) / full_graph_nodes`
- [ ] Target: >70% reduction for typical queries
- [ ] Document baseline: full graph node count vs minimal subgraph

### Week 8: LLM Integration

- [ ] Define prompt template: subgraph (text) + user query
- [ ] Integrate OpenAI API (or other provider)
- [ ] System prompt: "You are a code dependency expert."
- [ ] Add confidence score per answer: HIGH (static+runtime agree), MEDIUM (static only), LOW (inferred)
- [ ] Optional: add explainability — return why each node was included (e.g. "Included because it modifies userData at runtime")
- [ ] Test on 5 ground-truth queries; compare LLM answers to manual answers
- [ ] Record: correctness rate, token usage

**LLM prompt template (standardize for testing):**

```
System: You are a code dependency expert. Answer based only on the subgraph provided.

User:
Subgraph:
function saveUser CALLS updateUser
function updateUser MODIFIES userData
function validateInput CALLS getUser

Question: Where is userData modified?

Answer:
```

### Week 9: Change Detection + Auto-Update

- [ ] Use `git diff` to detect changed files
- [ ] Re-parse only changed files
- [ ] Update graph: add/remove nodes and edges
- [ ] Recompute impact scores for affected subgraph
- [ ] Optional: git hook or CLI command to trigger update
- [ ] Validate: change 1 file → graph updates in < 30 seconds

**Optional ordering:** Change detection can be moved earlier (e.g. after Week 4) if you want to test dynamic updates as soon as you have runtime edges. Current flow works fine too — it depends on whether you want live-update feedback sooner.

### Week 10: Basic Visualization

- [ ] Use Matplotlib or Plotly to render subgraph
- [ ] Color nodes by impact; show edge weights
- [ ] Save as image for debugging
- [ ] Optional: simple interactive viewer (click to expand)

### Week 11+: Polish + Metrics

- [ ] Add **reproducibility script**: one command runs everything.  
  `python run_pipeline.py --repo examples/sample_repo --query "Where is userData modified?"`  
  Makes demos, grading, and reviews smooth.
- [ ] Run baseline comparison: same queries with full repo vs Cursor-style vs minimal subgraph (correctness, tokens, hallucination)
- [ ] Run full evaluation: correctness, minimality, hallucination comparison
- [ ] Write unit tests for queries (e.g. `test_query_modification`, `test_subgraph_minimality`) — enables validation automation
- [ ] Document novelty vs existing tools (runtime edges, impact scoring, minimal subgraph, auto-update)
- [ ] Write README with usage + architecture
- [ ] Optional: blog post or paper outline

---

## Optional Enhancements (After MVP)

- [ ] Cross-repo / monorepo support
- [ ] Advanced impact scoring (test coverage integration)
- [ ] Interactive dashboard (React + D3)
- [ ] Multi-language support (JS, etc.)
- [ ] CI/CD integration (auto-update on merge)
- [ ] **Time dimension** — edge timestamps, versioned mutations. "When did this behavior change?" / "Which commit caused this?" (Not MVP — future-proof.)
- [ ] **Explainability output** — return why each node was included, why each edge mattered. E.g. "Included because it modifies userData at runtime." Makes debugging 🔥

---

## Quick Reference: Novelty vs Existing Tools

| Feature | Status |
|---------|--------|
| Runtime-aware edges | Novel |
| Impact scoring / weighted edges | Novel |
| Minimal subgraph extraction | Novel |
| Change detection + auto-update | Novel |
| Visualization (runtime + weights) | Novel |
| Static AST + basic graph | Already exists |

---

## Edge Types & Query Examples (from idea.txt)

**Edge types:** `CALLS`, `IMPORTS`, `INHERITS`, `REFERENCES` (static) | `RuntimeCall`, `MODIFIED_BY` (dynamic)

**Sample queries to support:** (see Query → intent mapping in "Lock In Early" above)
- "Where is userData modified?" → MODIFIED_BY
- "Which functions call function_A?" → CALLS (reverse)
- "Which functions/classes are impacted by this change?" → forward CALLS
- "What does module_X import?" → IMPORTS

---

## What You Are NOT Missing (Stay Calm)

You don't need any of these. You stayed in the right abstraction layer.

- ❌ OS internals  
- ❌ Compilers  
- ❌ Kernel tracing  
- ❌ LLVM  
- ❌ Distributed systems  
- ❌ Big databases  

---

## Outcome / Deliverables

- Fully working prototype for small repos (3–5 files)
- Query agent + LLM integration → precise code insights
- Runtime-aware edges + impact scoring
- Change detection + auto-update
- Visualization dashboard (basic or interactive)
- Paper or blog documenting novelty & results
- Potential to scale to enterprise monorepos
- **Reproducibility script** — one command: `python run_pipeline.py --repo examples/sample_repo --query "Where is userData modified?"`

---

## Final Truth

This plan:

- is **not** over-engineered  
- is **not** naive  
- is **not** vague  
- is **not** academic-only  

It's **buildable**, **measurable**, and **defensible**.

Most people fail because they don't write a plan like this. You already did the hard thinking.

---

*Use this file as a living checklist. Check off items as you complete them and adjust timelines as needed.*
