# Testing & Evaluation Report

This document summarizes the **Testing Protocol** results for the Semantic Graph Memory MVP. You can paste the summary table and metrics into the **Experiments** section of your research paper.

---

## How the protocol was run

- **Codebase:** The 4-file sample repo (`examples/sample_repo/`: main.py, user_service.py, data_handler.py, utils.py).
- **Pipeline:** Parse → build graph → run queries (who calls X, what does X depend on) → extract minimal subgraph → measure context size.
- **Run the protocol:** From project root, `python -m evaluation.protocol` (or `pytest evaluation/protocol.py -v` for pytest).

---

## Summary table (for your report)

*This is the structure of the table the protocol prints. Do **not** treat the numbers here as fixed; always use the output of your latest run (`python -m evaluation.protocol`).*

| Test Category   | Test Case                    | Status (example)   | Notes (example) |
|-----------------|------------------------------|--------------------|-----------------|
| Structural      | Node Discovery               | ✅ Pass            | All expected function nodes detected; missing: none. |
| Structural      | Cross-File Linking           | ✅ Pass            | `main` has a CALLS edge to `user_service.save_user`. |
| Functional      | "Who calls X?"               | ✅ Pass            | Returns the direct caller only (not indirect callers). |
| Functional      | "What does main depend on?"  | ✅ Pass            | Subgraph contains only the functions that `main` actually calls. |
| Performance     | Context Reduction            | ✅ Pass            | High context reduction (exact % from your run output). |
| Robustness      | Aliased Imports              | ⚠️ Todo            | `import X as Y; Y.func()` requires a future parser update. |
| Robustness      | Circular Dependencies        | ✅ Pass            | Traversal terminates; no infinite loop on A→B→A. |

### How to fill this table for your report

- Run: `python -m evaluation.protocol`.
- Copy the **status** and **notes** columns directly from the console output into your paper.
- If you re-run the protocol later, **use the new output**; you do not need to edit this file.

---

## Context reduction (value metric)

- **Full repo:** Total lines of code in the 4 Python files (e.g. ~65 lines).
- **Minimal subgraph:** For a query like "Who calls save_user?", the system returns only the relevant slice (e.g. one line: "main CALLS save_user").
- **Reduction:** `(full_lines - subgraph_lines) / full_lines` as a percentage.

In a typical run you should see a **very high reduction** (for example, around 98%), but the **exact number must always come from your latest protocol output**. In your report, you can write something like:

> \"The tool reduces context noise by ~98% for this query, so the LLM sees only the relevant dependency instead of the full repo.\"

Re-run `python -m evaluation.protocol` to refresh numbers if the sample repo changes.

---

## Phase-by-phase description (for Methods / Experiments)

**Phase 1 — Structural integrity**  
We verified that the graph matches the code: every function in the 4 files has a corresponding node, and that calls across files (e.g. main → save_user in user_service) are represented as edges to the correct defining node, not a generic name.

**Phase 2 — Functional queries**  
We tested that "Who calls update_user?" returns only the direct caller (save_user) and that "What does main depend on?" returns the correct set of dependencies (save_user, get_user, validate_input) and excludes functions main does not call (e.g. delete_user).

**Phase 3 — Value test**  
We measured context reduction: lines (or tokens) in the full repo vs lines in the minimal subgraph for a representative query. The result is the percentage reported above.

**Phase 4 — Edge cases**  
We documented that aliased imports (`import X as Y`) are not yet supported (Todo) and that circular call chains (A→B→A) are handled safely by bounded traversal (max_depth/max_nodes).

---

## Checklist for the paper

When writing the "Testing & Evaluation" section, you can use:

- The **summary table** above (optionally with your latest run’s numbers).
- The **context reduction** percentage from your run (e.g. "~98% reduction").
- Short descriptions of **Phase 1–4** as in the section above.
- A note that **aliased imports** are left as future work.

Re-run `python -m evaluation.protocol` and `python -m evaluation.brutal_protocol` before submitting to refresh the numbers and notes.

---

## Brutal Tests ("Eat your own dog food" and stress tests)

A separate protocol runs five **brutal tests** to stress the tool on itself and on edge cases. Run from project root: `python -m evaluation.brutal_protocol`.

The script prints a table like this (structure only — the actual Status column should come from your latest run):

| Test | Description                    | Status (example) |
|------|--------------------------------|------------------|
| 1    | Dog food (run on self)        | PASS / FAIL      |
| 2    | Hidden disconnect (scope)     | PASS / FAIL      |
| 3    | Syntax torture                | PASS / FAIL      |
| 4    | Cycle of death (no infinite loop) | PASS / FAIL  |
| 5    | Context bloat (minimal subgraph) | PASS / FAIL  |

### How to use these results in your report

- Run: `python -m evaluation.brutal_protocol`.
- Copy the summary table and per-test notes from the console into your report as evidence that the tool handles self-graphing, scope, weird syntax, cycles, and context bloat.
- Do **not** rely on any numbers in this file; always use the live output from the script.

### What each test checks

| Test | Description | Pass condition (conceptual) |
|------|-------------|----------------------------|
| 1. Dog food | Run the tool on its own source (project root, excluding `.venv`/`__pycache__`) | No crash; \"What does run depend on?\" shows that `run_pipeline.run` depends on the parser (e.g. `parse_path`). |
| 2. Hidden disconnect | Two files: `file_a.process_data` and `file_b.process_data`; `file_b.main()` calls its local `process_data()` | Graph links `main` to **file_b.process_data** only, not file_a (scope-respecting). |
| 3. Syntax torture | Parse `torture.py` (lambda in args, list comp, nested class, decorator) | No crash; \"Who calls method?\" runs (empty result is correct if there are no callers). |
| 4. Cycle of death | Mutual recursion: `ping` → `pong` → `ping` | No hang, no RecursionError; traversal bounded by `max_depth`/`max_nodes`. |
| 5. Context bloat | Query a small utility in a large codebase (\"Who calls _node_id?\") | Subgraph is minimal (strong context reduction), not the whole graph. |

**Fixtures:** Under `examples/brutal_tests/`: `test2_hidden_disconnect/`, `test3_syntax_torture/`, `test4_cycle/`. Tests 1 and 5 use the project’s own source.
