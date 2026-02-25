# Rabt (رَبط) — Project Report

**Rabt** is the name of this project and the associated research paper: *Rabt: Computing Minimal Dependency Context for LLM-Based Code Intelligence.*  
It is a Graph-RAG system for code (semantic graph memory + minimal dependency slicing). Rabt = connection/link — the graph encodes structural links in the codebase; the minimal subgraph is the precise connection we feed the LLM.

A short report on what the project is, what example we use, what it solves, how it works, and its current scope. Written so that a reader can understand everything without running the code.

---

## 1. What Is This Project?

**Rabt** is a prototype of a **Graph-RAG (Retrieval Augmented Generation) system for code** that answers questions about a codebase by building a **dependency graph** and returning only the **relevant slice** of that graph (and eventually a natural-language answer).

Existing tools (e.g. Cursor, Copilot) use **probabilistic retrieval**: they rely on vector embeddings and semantic search to find code that *looks* or *sounds* similar. This system uses **deterministic retrieval**: it builds a structural graph and *knows* that function A calls function B. So when you ask "Who calls save_user?", vector search might return a comment that mentions "save" and "user"; graph search returns the actual caller.

The pipeline:

1. Parsing the code and building a graph of “who calls whom,” “who imports what,” and similar relations.
2. Understanding the user’s question (e.g. “Who calls function X?”).
3. Extracting a **minimal subgraph** — only the nodes and edges needed to answer that question.
4. Sending that minimal subgraph to an **LLM** (Gemini when `GEMINI_API_KEY` is set) to produce a short, precise answer and a confidence level.

**Why minimal context?** While LLMs have large context windows, feeding them unrelated code reduces reasoning performance (the "Lost in the Middle" phenomenon). This tool is not mainly about *fitting* code into the window; it is about **focus**. By giving the LLM only the precise logical slice required to answer the query, we reduce noise and increase **answer accuracy**, not just token savings.

**The system type:** This is a **Hybrid Graph-RAG system**. It does not rely solely on static text analysis; it incorporates runtime telemetry (execution counts and state mutations) to ground the AI's answers in reality.

So: **the system computes the right context using structural graphs instead of probabilistic retrieval.** That is what we built and demonstrate in this MVP.

**The “money slide” (for your report).** The crucial step is **minimal subgraph extraction**. Vector RAG (Cursor/Copilot) would retrieve *chunks of text* that contain the words “save_user”. Rabt retrieves the **specific caller** (`main`) because it follows the **CALLS edge** in the graph. So for “Who calls save_user?” you get “main CALLS save_user” (2 nodes), not a pile of files. That deterministic, structure-based slice is the core contribution.

---

## 2. The Example We Use

To demonstrate the system we use a **small sample codebase** of four Python files. The reader can imagine this as a tiny “user management” style app.

### The sample repo (in words)

- **main.py** — Entry point. It imports `get_user` and `save_user` from `user_service`, and `validate_input` from `data_handler`. The `main()` function gets a user (e.g. "alice"), validates the data, then calls `save_user(user_data)`.
- **user_service.py** — Defines `get_user`, `save_user`, and `delete_user`. `save_user` takes user data and calls `update_user` from `data_handler`.
- **data_handler.py** — Defines `validate_input`, `update_user`, and `get_user_data`. It has a global variable `userData` that `update_user` modifies. So “where is userData modified?” would point here.
- **utils.py** — A small helper module (e.g. `normalize_id`) used to show imports and cross-file structure.

So we have: **main** → calls **save_user** (in user_service) → which calls **update_user** (in data_handler). There are imports across files and a variable `userData` that gets modified in one place.

### A concrete question we ask

We ask the system a question in plain language, for example:

**“Who calls save_user?”**

Meaning: which functions in the codebase call the function named `save_user`?

### What the system does (step by step, in text)

1. **Parse** — It reads all four Python files and builds a list of “nodes” (modules, functions, classes, variables) and “edges” (calls, imports, etc.). For instance it records that the function `main` (in main.py) *calls* the function `save_user` (in user_service.py), and that `save_user` *calls* `update_user` in data_handler.

2. **Build graph** — It builds a single dependency graph (in memory, and optionally saved to a file like `.graph.json`). For our sample repo this graph has on the order of a dozen nodes and a similar number of edges.

3. **Understand the question** — It maps “Who calls save_user?” to an intent: “find nodes that have a CALLS edge *into* the node named save_user” (i.e. find callers of save_user).

4. **Extract minimal subgraph** — Instead of returning the whole graph, it only keeps the nodes and edges relevant to that intent. For “Who calls save_user?” the relevant part is just: **main** and **save_user**, and the edge **main CALLS save_user**. So the “answer” in graph form is that small slice.

5. **Present the result** — The system can output something like:
   - Graph: 14 nodes, 17 edges (the full graph).
   - Subgraph: 2 nodes.
   - Subgraph (text): **main CALLS save_user** or **main CALLS save_user (executed N times)** when the path was observed at runtime.
   - Answer: Natural-language answer from the LLM (Gemini when configured).
   - Confidence: HIGH when static and runtime agree; MEDIUM when static only; LOW when inferred (see confidence logic below).

So **what it solves** in this example: given a natural-language question about the codebase, it **finds the exact callers** of `save_user` and returns only the minimal dependency slice (main → save_user) instead of the entire repo or a random set of files.

**Confidence logic (explicit):**

| Level   | Meaning |
|--------|---------|
| **HIGH**   | Direct evidence: static link and/or runtime trace (e.g. call or mutation observed in `.runtime_events.jsonl`). |
| **MEDIUM** | Name match but path ambiguous, or static analysis only (no runtime data). |
| **LOW**    | No direct link found; relying on keyword or heuristic matching. |

---

## 3. How It Works (High Level)

- **Input:** A path to a folder (or a single Python file) and, optionally, a natural-language query (e.g. “Who calls save_user?”, “What does main import?”).
- **Pipeline:**
  - **Parser** — Reads Python files, uses the language’s abstract syntax to extract functions, classes, variables, modules, and relationships (calls, imports, inheritance). It respects imports so that a call like `save_user(...)` in main.py is correctly linked to the `save_user` defined in user_service.py.
  - **Graph** — Builds one directed graph where nodes are those entities and edges are the relationships. The graph can be saved to disk (e.g. JSON) and loaded again.
  - **Query agent** — Takes the user’s question, maps it to an “intent” (e.g. “who calls X”, “what does Y import”), then walks the graph from the right starting points (e.g. the node for `save_user`) and collects only the nodes and edges needed to answer. That is the “minimal subgraph.”
  - **Output** — Returns the full graph size, the minimal subgraph size, the subgraph in text form (e.g. “main CALLS save_user”), and a placeholder for an LLM answer and a confidence level.
- **Output (in words):** The user sees how big the full graph is, how small the relevant slice is, and the actual dependency chain that answers the question (e.g. main calls save_user). So even without running the code, one can understand: “the system found that the only caller of save_user in this repo is main.”

---

## 4. Current Scope

What is **in scope** for this report and the current prototype:

- **Supported:** One language (Python). Small repos (we use 3–5 files; the design can scale to more).

- **Working today:**

  - **Hybrid graph construction:** Combining **static analysis** (AST parsing for structure) with **dynamic analysis** (runtime tracing for behavior).

  - **Static features:** Modules, functions, classes, variables; CALLS, IMPORTS, INHERITS, REFERENCES.

  - **Runtime features:**
    - **Execution tracing:** Decorators (`@track_runtime`) log actual function calls to `.runtime_events.jsonl`.
    - **Mutation tracking:** Tracking when global state (e.g. `userData`) is modified (MODIFIED_BY edges).

  - **Impact scoring:** Edges in the graph are weighted by execution count. The LLM sees "executed 5 times" to prioritize hot paths.

  - **Natural-language queries:** Answering "Who calls save_user?" (structural) and "Where is userData modified?" (behavioral).

  - **Minimal subgraph extraction:** Returning only the relevant slice.

  - **LLM integration:** Connected to Gemini Pro/Flash to generate natural-language answers from the subgraph.

- **Planned (future work):**

  - **Change detection** — Updating the graph when the code changes (e.g. after a git commit).
  - **Visualization** — Rendering the graph visually (e.g. using NetworkX/Matplotlib).
  - **Large-scale runtime safety:** Currently we use a manual decorator approach. A future version would use `sys.settrace` to instrument code without modifying source files.
  - **Evaluation** — Formal benchmarking against standard datasets (e.g. HumanEval).

- **Limitations:**

  - **Static analysis:** Python is dynamic; static analysis misses some calls. We mitigate this with our runtime tracing layer.
  - **Runtime overhead:** Tracing adds a small performance cost, currently suitable for debugging/development environments.


## 5. Summary in One Paragraph

We built an MVP that **parses a small Python codebase** (our example: four files with main, user_service, data_handler, utils), **builds a dependency graph** (who calls whom, who imports what), and **answers questions like “Who calls save_user?”** by returning only the **minimal relevant slice** (e.g. “main CALLS save_user”) instead of the whole repo. It is a **Graph-RAG system for code**: existing tools use probabilistic retrieval (embeddings); this one uses **deterministic retrieval** (structural graphs). The goal is **focus**, not just token savings—feeding the LLM only the precise slice improves answer accuracy (e.g. "Lost in the Middle" reduction). **Hybrid analysis** (static + runtime) is implemented and verified; change detection, visualization, and full evaluation are planned. This report is written so that someone who only reads the document (and does not run the code) can understand what the project is, what example we use, what problem it solves, how it works, and what is in scope today.

---

## 6. Related context: Cursor, Copilot, and probabilistic vs deterministic retrieval

Tools like **Cursor** and **GitHub Copilot** primarily rely on **probabilistic retrieval** (semantic search via Vector RAG) to decide what code to show the AI. Here is how they differ from the Rabt approach.

**Probabilistic retrieval (Cursor / Copilot)**

| Aspect | Description |
|--------|-------------|
| **Mechanism** | Vector embeddings turn code into points in a high-dimensional space. |
| **Selection** | When you ask a question, the tool finds code that is “mathematically similar” to your query—it infers relevance from text patterns and proximity. |
| **Downside** | Can introduce **noise** (irrelevant snippets) because the system does not model the actual logic or dependency chain; it only sees that text looks similar. |

**Deterministic retrieval (Rabt)**

| Aspect | Description |
|--------|-------------|
| **Mechanism** | Rabt builds a **structural graph** of the codebase (e.g. “Function A calls Function B”). |
| **Selection** | It follows **actual code paths**. For “Who calls X?”, it does not search for similar text; it follows the direct link from X back to its callers. |
| **Benefit** | Delivers a **minimal dependency slice**—only the code needed to answer the query—so the LLM is not confused by unrelated files. |

**Rabt does not replace Cursor or Copilot; it complements them.** Cursor/Copilot use vector-based retrieval over code chunks. Rabt uses graph-based retrieval over code entities and relationships. We compute the right structural context before calling an LLM.

**Trend:** Many tools started with pure probabilistic search; the industry is moving toward **hybrid** or **GraphRAG** systems to capture these deeper relationships. Rabt is an implementation of GraphRAG for code.

For more on how Cursor-style “whole codebase” awareness works (indexing, retrieval, context injection), see:  
**[Can Cursor read my entire codebase?](https://milvus.io/ai-quick-reference/can-cursor-read-my-entire-codebase)**

---

## 7. Where We Stand and What's Next

**Where we are right now**

| Area | Status | What exists |
|------|--------|-------------|
| **Parser** | Done | AST → nodes + edges (CALLS, IMPORTS, INHERITS, REFERENCES). Cross-file resolution, package re-exports, scope-respecting. |
| **Graph** | Done | Build from parser + runtime events, persist/load (JSON), queries (who_calls, nodes_by_name, where_modified, etc.). |
| **Runtime** | Done | `runtime/tracer.py`: `@track_runtime`, `track_mutation`; `runtime/__init__.py`: reads `.runtime_events.jsonl`, returns RuntimeEvent list. Sample repo instrumented; RuntimeCall and MODIFIED_BY merged into graph. |
| **Query agent** | Done | Intent from natural language (regex + optional LLM router with fallback), bounded traversal, minimal subgraph, subgraph → text **with impact** ("executed N times" when weight > 1). |
| **Intent routing** | Done | Deterministic regex (default) + optional LLM classifier that accepts fuzzy/conversational queries. Config: `intent.router` (regex/llm/auto). Validated JSON output, regex fallback. |
| **Pipeline** | Done | Single entry: `run_pipeline.py --repo <path> -q "<query>"`. Loads `config/default.yaml` by default (runtime.main_module, llm, intent). |
| **LLM** | Done | `llm/` uses Gemini when `GEMINI_API_KEY` is set (e.g. in `.env`); returns natural-language answer + confidence. |
| **Impact visibility** | Done | Edge weights from runtime count; subgraph text shows "(executed N times)" so LLM and user see hot paths. |
| **Evaluation** | Done | Main protocol + five brutal tests. All passing. |
| **Change detection** | Not started | No git-diff or incremental graph update. |
| **Visualization** | Not started | No graph/subgraph rendering. |

So today: **hybrid (static + runtime) graph + natural-language query → minimal subgraph (with impact) + LLM answer + confidence** is fully working. Change detection and visualization are the next steps.

**Where to go further (in order)**

1. **Change detection** — Git diff → re-parse changed files → update graph. Keeps the graph fresh.
2. **Visualization** — Render graph or subgraph (e.g. Matplotlib/Plotly) for demos and debugging.
3. **Baseline comparison** — Same queries with (a) full repo, (b) file-level context, (c) your minimal subgraph. Compare correctness, token use, hallucination. Strong evidence for a paper or report.

For a **report or demo today**, you have: working **hybrid analysis** (static + call tracing + mutation tracking), **impact** in subgraph text, **LLM integration** (Gemini), evaluation protocol, brutal tests, and docs.
