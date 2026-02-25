# Rabt (رَبط) — Official Demo Script

**Goal:** Prove that the tool doesn’t just *read* code; it *watches* it run and learns from it.

This script shows the **Before vs After** effect: static analysis alone → then with runtime feedback. Use it for your presentation or report.

---

## Setup (Reset the State)

Before you start, reset the environment so the demo is clean and reproducible.

```bash
# 1. Activate the environment
source .venv/bin/activate

# 2. Clear old runtime logs (start fresh)
rm -f .runtime_events.jsonl

# 3. Clear the graph cache (force a re-parse)
rm -f .graph.json
```

---

## Act 1: The "Static" Baseline (The "Before")

**Narrator:** *"First, let's see what a standard static analysis tool sees. It knows main calls save_user, but it doesn't know if that code is actually used."*

### 1. Run the pipeline (no runtime data yet)

```bash
python run_pipeline.py --repo examples/sample_repo -q "Who calls save_user?"
```

### 2. Show the result

- **Look for:** `main CALLS save_user`
- **Point out:** There is no execution count. It’s just a structural fact.
- **The answer:** *"The main function calls save_user."* — a standard, static-only answer.

---

## Act 2: The "Runtime" Injection (The Execution)

**Narrator:** *"Now, let's actually run the application. Imagine this is a production environment or a test suite running."*

### 1. Run the sample code 5 times

(This simulates a "hot path" in the code.)

```bash
for i in {1..5}; do python examples/sample_repo/main.py; done
```

### 2. Verify the log exists (optional "trust me" step)

```bash
cat .runtime_events.jsonl
```

You will see: `"event_type": "call"`, `"event_type": "mutation"`, etc.

---

## Act 3: The "Impact" Reveal (The "After")

**Narrator:** *"Now that we have runtime data, let's ask the exact same question again. Watch how the answer changes."*

### 1. Run the pipeline again

```bash
python run_pipeline.py --repo examples/sample_repo -q "Who calls save_user?"
```

### 2. The "mic drop" moment

- **Look for:**  
  **Subgraph (text):** `main CALLS save_user (executed 6 times)`  
  (1 from static + 5 from runtime = 6)

- **The answer:** The LLM may now say something like: *"The function main calls save_user, and this path was executed 6 times."*

### 3. The "Mutation" query (the bonus)

**Narrator:** *"Finally, let's ask a question that static analysis can't usually answer: Who is modifying the data?"*

```bash
python run_pipeline.py --repo examples/sample_repo -q "Where is userData modified?"
```

- **Result:** `update_user MODIFIED_BY userData`
- **Why it's cool:** You are tracking **state changes**, not just function calls.

---

## Why This Demo Wins

| Aspect | What you show |
|--------|----------------|
| **Visual** | Seeing `(executed 6 times)` appear is clear, concrete proof of runtime feedback. |
| **Logical** | You show the progression: **Static → Execution → Hybrid**. |
| **Dead-code** | If a function has 0 executions, a developer knows they might remove it. If it has 1,000, they know to be careful. |
| **Novel** | You close the loop between *what the code says* (static) and *what the code does* (runtime). |

---

## One-Line Summary for the Report

> **Rabt combines static analysis (code structure) with dynamic analysis (runtime behavior) so the graph and the LLM see not only who calls whom, but how often—and who modifies what.**

---

*You have a working, novel, research-grade prototype. Go write that report.*
