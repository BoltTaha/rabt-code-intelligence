# Week 9 Features — Simple Concepts & What You Can Change

This doc explains the three "polish" features in plain language and **where to change** them in the code.

---

## 1. Visualization (the graph picture)

**What it is:**  
A script that reads your saved graph (`.graph.json`) and draws it as an image. Nodes that have **lots of traffic** (high execution count on their edges) are **red** (hot). Nodes with little traffic are **blue** (cold). So you can see at a glance which parts of the code are "hot" vs "cold."

**How to run:**
```bash
.venv/bin/pip install matplotlib
.venv/bin/python visualize_graph.py --graph .graph.json --out graph.png
```

**What you can change:**

| What | File | Where |
|------|------|--------|
| **Input graph path** | Command line | `--graph mygraph.json` |
| **Output image path** | Command line | `--out mypicture.png` |
| **Layout** (how nodes are arranged) | Command line | `--layout spring` or `shell` or `kamada` |
| **Hot = red, cold = blue** | `visualize_graph.py` | Around line 60: `node_colors` — change the formula that turns `heat` into (r, g, b). Right now: red when hot, blue when cold. |
| **Node size** | `visualize_graph.py` | Search for `node_size=800` and change the number. |
| **Label size** | `visualize_graph.py` | Search for `font_size=7` and change. |

**Concept in one line:**  
The graph is already built by the pipeline; this script only **draws** it and colors nodes by how much they are used (weight on edges).

---

## 2. Change detection (keep the graph fresh)

**What it is:**  
Your graph is built from the code. When you **edit the code** (e.g. add a function), the graph should be rebuilt. This script uses **git** to see if any `.py` file changed. If yes, it re-runs the parser and saves a new graph. If nothing changed, it does nothing (so you don’t rebuild every time).

**How to run:**
```bash
.venv/bin/python update_graph_if_changed.py --repo examples/sample_repo
# Force rebuild even when git says "no changes":
.venv/bin/python update_graph_if_changed.py --repo examples/sample_repo --force
```

**What you can change:**

| What | File | Where |
|------|------|--------|
| **Which repo to watch** | Command line | `--repo path/to/your/repo` |
| **"Changed since when?"** | `graph/change_detection.py` | In `get_changed_python_files(..., ref="HEAD")` — `ref` can be `HEAD`, `HEAD~1`, or a commit hash. |
| **What counts as "changed"** | `graph/change_detection.py` | `get_changed_python_files` uses `git diff --name-only`. You could add more logic (e.g. only certain folders). |
| **Where the graph is saved** | `config/default.yaml` | Under `graph.persist_path` (e.g. `.graph.json`). |

**Concept in one line:**  
Git tells us "did any Python file change?" → if yes, we re-parse the repo and save a new graph so the picture and the pipeline stay in sync with the code.

---

## 3. Baseline comparison (proof Rabt uses less context)

**What it is:**  
Same question is asked **twice**:  
1. **Full repo:** Send the **entire codebase** (all files) to the LLM and ask the question.  
2. **Rabt:** Run the normal pipeline (minimal subgraph only) and ask the question.  

Then we compare: how many **tokens** (or characters) each used, and what **answer** each gave. So you can say: "Rabt answered with 98% less context and still got it right."

**How to run:**
```bash
.venv/bin/python -m evaluation.baseline_comparison --repo examples/sample_repo --query "Where is userData modified?"
```

**What you can change:**

| What | File | Where |
|------|------|--------|
| **Repo and question** | Command line | `--repo ...` and `--query "Your question?"` |
| **Max context size for full repo** | `evaluation/baseline_comparison.py` | Search for `context[:120000]` — that’s the cap so we don’t send too much to the API. Change the number if needed. |
| **Prompt text for "full repo"** | `evaluation/baseline_comparison.py` | In `_call_gemini_full_context`, the `prompt = f"""..."""` block. You can change the instructions. |
| **Which model** | `config/default.yaml` | Under `llm.model` (e.g. `gemini-2.5-flash-lite`). |

**Concept in one line:**  
We ask the same question with "whole codebase" vs "only Rabt’s slice" and compare token use and answers to show Rabt is cheaper and still accurate.

---

## Quick reference

| Feature | Main script / module | One-line idea |
|---------|----------------------|----------------|
| **Visualization** | `visualize_graph.py` | Draw `.graph.json`; color nodes by weight (red = hot, blue = cold). |
| **Change detection** | `update_graph_if_changed.py` + `graph/change_detection.py` | If git says "files changed", re-parse and save graph. |
| **Baseline** | `evaluation/baseline_comparison.py` | Same question → full context vs Rabt → compare size and answer. |

If you want to change **how** something works (e.g. different colors, or what "changed" means), edit the file and the place in the table above. If you only want to change **inputs** (which repo, which query, which graph file), use the **command-line flags** shown in "How to run."
