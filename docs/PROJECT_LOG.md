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
4. (Planned) Sending that minimal subgraph to an LLM to produce a short, precise answer.

**Why minimal context?** While LLMs have large context windows, feeding them unrelated code reduces reasoning performance (the "Lost in the Middle" phenomenon). This tool is not mainly about *fitting* code into the window; it is about **focus**. By giving the LLM only the precise logical slice required to answer the query, we reduce noise and increase **answer accuracy**, not just token savings.

So: **the system computes the right context using structural graphs instead of probabilistic retrieval.** That is what we built and demonstrate in this MVP.

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
   - Subgraph (text): **main CALLS save_user**.
   - Answer: (Today this is a placeholder; later an LLM would turn that subgraph into a sentence like “The function `main` in main.py calls `save_user`.”)
   - Confidence: MEDIUM (see confidence logic below).

So **what it solves** in this example: given a natural-language question about the codebase, it **finds the exact callers** of `save_user` and returns only the minimal dependency slice (main → save_user) instead of the entire repo or a random set of files.

**Confidence logic (explicit):**

| Level   | Meaning |
|--------|---------|
| **HIGH**   | Found a direct static link (e.g. explicit import, clear CALLS edge). |
| **MEDIUM** | Found a name match but path is ambiguous, or based on static analysis only (no runtime data). |
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
  - Building the **static** dependency graph from Python (modules, functions, classes, variables; CALLS, IMPORTS, INHERITS, REFERENCES).
  - **Cross-file** resolution (e.g. main in one file calling save_user in another).
  - Asking **natural-language questions** such as “Who calls save_user?”, “What does X import?”, “Where is Y modified?” (the last uses the graph structure; runtime tracking is not yet implemented).
  - Getting back a **minimal subgraph** and its text form (e.g. “main CALLS save_user”).
  - Saving and loading the graph to/from a file.
- **Planned but not yet implemented (so out of current “running” scope):**
  - **Runtime instrumentation** — Observing which functions actually run and how often; adding “runtime call” and “modified by” edges so that “where is userData modified?” can use execution data. *Limitation:* Executing arbitrary user code is hard (infinite loops, side effects, environment dependencies). A more realistic first step may be **trace-based analysis** (e.g. analyzing existing logs) rather than live execution; we do not claim to safely run any random repo.
  - **Impact scoring** — Weights on edges (e.g. by call frequency or importance) to rank which parts of the code matter most.
  - **Real LLM integration** — Replacing the placeholder answer with a model that turns the minimal subgraph + question into a short natural-language answer.
  - **Change detection** — Updating the graph when the code changes (e.g. after a git commit).
  - **Visualization** — Drawing the graph or subgraph.
  - **Evaluation** — Comparing “full repo vs minimal subgraph” for metrics (correctness, token use, etc.) for a paper or report.

**Limitations and risks (acknowledged):**

- **Static analysis in Python.** Python is a dynamic language. Our parser catches **explicit** structure: direct imports, direct function calls, class definitions. It does **not** catch dynamic patterns such as `getattr(module, "save_" + "user")()` or calls built at runtime. So some real dependencies may be missing from the graph. This is why "Planned: Runtime" (or trace-based analysis) is important—it is the way to capture behavior that static analysis cannot see. We do not claim static analysis catches everything in Python.
- **Confidence** reflects this: answers based only on static links are MEDIUM; with runtime or direct evidence they could be HIGH.

So **current scope** = static graph + natural-language query → minimal subgraph + text summary + placeholder answer. Everything else is planned and described in the project plan (e.g. PLAN.md), but not part of “what the system does today” in this report.

---

## 5. Summary in One Paragraph

We built an MVP that **parses a small Python codebase** (our example: four files with main, user_service, data_handler, utils), **builds a dependency graph** (who calls whom, who imports what), and **answers questions like “Who calls save_user?”** by returning only the **minimal relevant slice** (e.g. “main CALLS save_user”) instead of the whole repo. It is a **Graph-RAG system for code**: existing tools use probabilistic retrieval (embeddings); this one uses **deterministic retrieval** (structural graphs). The goal is **focus**, not just token savings—feeding the LLM only the precise slice improves answer accuracy (e.g. "Lost in the Middle" reduction). Right now it uses **static analysis only**; we acknowledge that Python's dynamism means some dependencies are missed; runtime or trace-based analysis is planned. This report is written so that someone who only reads the document (and does not run the code) can understand what the project is, what example we use, what problem it solves, how it works, and what is in scope today.

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
| **Parser** | Done | AST → nodes + edges (CALLS, IMPORTS, INHERITS, REFERENCES). Cross-file resolution, package re-exports, scope-respecting (e.g. file_b.main → file_b.process_data). |
| **Graph** | Done | Build from parser output, persist/load (e.g. JSON), queries (who_calls, nodes_by_name, etc.). |
| **Query agent** | Done | Intent from natural language ("Who calls X?", "What does Y depend on?"), bounded traversal, minimal subgraph, subgraph → text. |
| **Pipeline** | Done | Single entry: `run_pipeline.py --repo <path> -q "<query>"`. Config (default.yaml), no business logic in entry point. |
| **Evaluation** | Done | Main protocol (structural, functional, context reduction, robustness) + five brutal tests (dog food, scope, syntax torture, cycles, context bloat). All passing. |
| **Runtime** | Stub | `runtime/` returns empty events; no instrumentation yet. |
| **LLM** | Stub | `llm/` returns a placeholder answer and MEDIUM confidence; no API call. |
| **Impact scoring** | Not started | No weights from call frequency or downstream dependents. |
| **Change detection** | Not started | No git-diff or incremental graph update. |
| **Visualization** | Not started | No graph/subgraph rendering. |

So today: **static graph + natural-language query → minimal subgraph + text** is fully working and tested. Runtime, LLM, impact, change detection, and visualization are the next steps.

**Where to go further (in order)**

1. **Real LLM integration** — Replace the stub in `llm/` with a real API (e.g. OpenAI). Prompt = subgraph text + user query → short answer + confidence. Proves "minimal context reduces hallucination."
2. **Runtime instrumentation** — Implement `runtime/`: decorators or wrappers to log calls and (optionally) variable mutations. Merge RuntimeCall (and MODIFIED_BY) edges into the graph. Proves "runtime info improves correctness."
3. **Impact scoring** — Weights on edges from call frequency and/or downstream dependents. Enables "top N critical nodes" and better ranking.
4. **Change detection** — Git diff → re-parse changed files → update graph (and optionally impact). Keeps the graph fresh.
5. **Visualization** — Render graph or subgraph (e.g. Matplotlib/Plotly) for demos and debugging.
6. **Baseline comparison** — Same queries with (a) full repo, (b) file-level context, (c) your minimal subgraph. Compare correctness, token use, hallucination. Strong evidence for a paper or report.

For a **report or demo today**, you already have enough: working pipeline, evaluation protocol, brutal tests, and docs. For a **full research prototype**, the next concrete step is **LLM integration** (biggest visible win) or **runtime** (biggest novelty).
