"""
Brutal Tests Protocol — "Eat your own dog food" and stress tests.
Run with: python -m evaluation.brutal_protocol
"""

from pathlib import Path
import sys
import signal

# Project root
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from parser import parse_path
from graph import build_graph
from agent import parse_intent, extract_subgraph, subgraph_to_text
from graph.queries import nodes_by_name, who_calls


# Timeout for traversal (Test 4: cycle of death)
TIMEOUT_SEC = 5


def _timeout_handler(signum, frame):
    raise TimeoutError("Traversal timed out (possible infinite loop)")


def _run_with_timeout(func, *args, timeout=TIMEOUT_SEC, **kwargs):
    """Run func; raise TimeoutError if it runs longer than timeout seconds."""
    if hasattr(signal, "SIGALRM"):
        signal.signal(signal.SIGALRM, _timeout_handler)
        signal.alarm(timeout)
    try:
        result = func(*args, **kwargs)
        return result
    finally:
        if hasattr(signal, "SIGALRM"):
            signal.alarm(0)


# ---------- Test 1: Eat Your Own Dog Food ----------

def run_test_1_dog_food():
    """Run the tool on its own source. No crash; run_pipeline uses parser (parse_path)."""
    result = {"passed": False, "crashed": False, "notes": ""}
    try:
        # Parse entire project (all .py under root: core, parser, graph, agent, run_pipeline, tests, examples, evaluation)
        out = parse_path(str(_ROOT))
        G = build_graph(out, None)
    except Exception as e:
        result["crashed"] = True
        result["notes"] = f"Parse/build crashed: {e!r}"
        return result

    result["node_count"] = G.number_of_nodes()
    result["edge_count"] = G.number_of_edges()

    # Pass: (1) no crash, (2) run_pipeline.run eventually depends on parser (parse_path).
    # Query "What does run depend on?" and check subgraph contains parser/parse_path (entry calls parser).
    intent = parse_intent("What does run depend on?")
    if not intent:
        result["notes"] = "Intent 'What does run depend on?' not parsed."
        return result

    run_ids = nodes_by_name(G, "run")
    if not run_ids:
        result["notes"] = "No node named 'run' in graph."
        return result

    try:
        # Use first 'run' that is in run_pipeline (in case multiple modules have 'run')
        run_id = next((r for r in run_ids if "run_pipeline" in G.nodes[r].get("module", "")), run_ids[0])
        intent.target_name = "run"
        subgraph = extract_subgraph(G, intent, max_depth=5, max_nodes=200)
    except Exception as e:
        result["crashed"] = True
        result["notes"] = f"Traversal crashed: {e!r}"
        return result

    # Subgraph should contain something from parser (parse_path or parser.ast_parser module)
    subgraph_names = {G.nodes[n].get("name", "") for n in subgraph.nodes()}
    subgraph_modules = {G.nodes[n].get("module", "") for n in subgraph.nodes()}
    has_parse_path = "parse_path" in subgraph_names or any("parser" in m for m in subgraph_modules)
    result["run_depends_on_parser"] = has_parse_path
    result["passed"] = not result["crashed"] and has_parse_path
    result["notes"] = f"Graph: {result['node_count']} nodes, {result['edge_count']} edges. run depends on parser/parse_path: {has_parse_path}. Modules in subgraph: {subgraph_modules}"
    return result


# ---------- Test 2: Hidden Disconnect (scope) ----------

def run_test_2_hidden_disconnect():
    """main in file_b must link to file_b.process_data, NOT file_a.process_data."""
    repo = _ROOT / "examples" / "brutal_tests" / "test2_hidden_disconnect"
    if not repo.exists():
        return {"passed": False, "notes": "Fixture test2_hidden_disconnect not found."}

    try:
        out = parse_path(str(repo))
        G = build_graph(out, None)
    except Exception as e:
        return {"passed": False, "crashed": True, "notes": f"Crash: {e!r}"}

    intent = parse_intent("What does main depend on?")
    if not intent:
        return {"passed": False, "notes": "Intent not parsed."}

    subgraph = extract_subgraph(G, intent, max_depth=3, max_nodes=50)
    # main should call process_data. The process_data node in subgraph must be from file_b (same module as main)
    main_ids = nodes_by_name(G, "main")
    process_data_ids = nodes_by_name(G, "process_data")
    if not main_ids or not process_data_ids:
        return {"passed": False, "notes": "main or process_data node missing."}

    # Find which process_data is called by main (successors of main with CALLS)
    main_id = main_ids[0]
    main_module = G.nodes[main_id].get("module", "")
    # main should be in file_b
    if "file_b" not in main_module:
        return {"passed": False, "notes": f"main is in {main_module}, expected file_b."}

    # Successors of main via CALLS
    callees = []
    for succ in G.successors(main_id):
        if G.has_edge(main_id, succ) and G.edges[main_id, succ].get("edge_type") == "CALLS":
            callees.append(succ)

    if not callees:
        return {"passed": False, "notes": "main has no CALLS successors."}

    # The callee must be process_data from file_b (module contains file_b)
    for c in callees:
        mod = G.nodes[c].get("module", "")
        name = G.nodes[c].get("name", "")
        if name == "process_data" and "file_b" in mod:
            return {"passed": True, "notes": "main correctly links to file_b.process_data, not file_a."}
        if name == "process_data" and "file_a" in mod:
            return {"passed": False, "notes": "WRONG: main links to file_a.process_data (should be file_b)."}

    return {"passed": False, "notes": f"main's callees: {callees}; none is file_b.process_data."}


# ---------- Test 3: Syntax Torture ----------

def run_test_3_syntax_torture():
    """Parse torture.py (lambdas, nested classes, decorators). No crash. Query 'Who calls method?'."""
    repo = _ROOT / "examples" / "brutal_tests" / "test3_syntax_torture"
    if not repo.exists():
        return {"passed": False, "notes": "Fixture test3_syntax_torture not found."}

    try:
        out = parse_path(str(repo))
        G = build_graph(out, None)
    except Exception as e:
        return {"passed": False, "crashed": True, "notes": f"Parser crashed on torture.py: {e!r}"}

    intent = parse_intent("Who calls method?")
    if not intent:
        return {"passed": False, "notes": "Intent not parsed."}

    try:
        subgraph = extract_subgraph(G, intent, max_depth=5, max_nodes=50)
        text = subgraph_to_text(subgraph)
    except Exception as e:
        return {"passed": False, "crashed": True, "notes": f"Traversal/subgraph crashed: {e!r}"}

    # In torture.py nobody calls method() — so empty result is correct. Pass = no crash.
    result = {"passed": True, "notes": "Parsed and queried without crash. (No callers of method is correct.)"}
    result["subgraph_lines"] = len(text.splitlines())
    return result


# ---------- Test 4: Cycle of Death ----------

def run_test_4_cycle():
    """ping <-> pong. Query 'Who calls ping?' must not hang or RecursionError."""
    repo = _ROOT / "examples" / "brutal_tests" / "test4_cycle"
    if not repo.exists():
        return {"passed": False, "notes": "Fixture test4_cycle not found."}

    try:
        out = parse_path(str(repo))
        G = build_graph(out, None)
    except Exception as e:
        return {"passed": False, "crashed": True, "notes": f"Parse/build crashed: {e!r}"}

    intent = parse_intent("Who calls ping?")
    if not intent:
        return {"passed": False, "notes": "Intent not parsed."}

    try:
        if hasattr(signal, "SIGALRM"):
            signal.signal(signal.SIGALRM, _timeout_handler)
            signal.alarm(TIMEOUT_SEC)
        subgraph = extract_subgraph(G, intent, max_depth=5, max_nodes=50)
        if hasattr(signal, "SIGALRM"):
            signal.alarm(0)
    except TimeoutError:
        if hasattr(signal, "SIGALRM"):
            signal.alarm(0)
        return {"passed": False, "crashed": True, "notes": "Traversal timed out (infinite loop?)."}
    except RecursionError as e:
        return {"passed": False, "crashed": True, "notes": f"RecursionError: {e!r}"}
    except Exception as e:
        return {"passed": False, "crashed": True, "notes": f"Crash: {e!r}"}

    return {"passed": True, "notes": "Traversal terminated (max_depth/max_nodes); no hang or RecursionError."}


# ---------- Test 5: Context Bloat ----------

def run_test_5_context_bloat():
    """Query about a small function in a large codebase; subgraph must be small, not whole file."""
    # Use own codebase; pick a small helper. E.g. "Who calls _node_id?" in parser (small helper).
    try:
        out = parse_path(str(_ROOT))
        G = build_graph(out, None)
    except Exception as e:
        return {"passed": False, "crashed": True, "notes": f"Parse crashed: {e!r}"}

    # Find largest file (by line count) that has a small function we can query
    # We'll query "Who calls _node_id?" - _node_id is in parser/ast_parser.py (small helper)
    intent = parse_intent("Who calls _node_id?")
    if not intent:
        return {"passed": False, "notes": "Intent 'Who calls _node_id?' not parsed."}

    subgraph = extract_subgraph(G, intent, max_depth=5, max_nodes=100)
    text = subgraph_to_text(subgraph)
    subgraph_lines = len(text.splitlines())
    subgraph_nodes = subgraph.number_of_nodes()

    # parser/ast_parser.py is ~217 lines. If we returned "whole file" we'd have huge subgraph.
    # Good: subgraph is minimal (only callers of _node_id). _node_id is called from _parse_module and _resolve_call_target.
    # So we expect a handful of nodes, not hundreds.
    full_nodes = G.number_of_nodes()
    reduction = (1.0 - subgraph_nodes / full_nodes) * 100 if full_nodes else 0

    # Pass: subgraph is much smaller than full graph (e.g. >50% reduction)
    passed = reduction > 50 and subgraph_nodes < full_nodes
    result = {
        "passed": passed,
        "full_graph_nodes": full_nodes,
        "subgraph_nodes": subgraph_nodes,
        "subgraph_lines": subgraph_lines,
        "reduction_pct": round(reduction, 1),
        "notes": f"Subgraph has {subgraph_nodes} nodes ({reduction:.1f}% reduction). Bloat would be returning whole graph.",
    }
    return result


# ---------- Run all and report ----------

def run_all():
    return {
        "test_1_dog_food": run_test_1_dog_food(),
        "test_2_hidden_disconnect": run_test_2_hidden_disconnect(),
        "test_3_syntax_torture": run_test_3_syntax_torture(),
        "test_4_cycle": run_test_4_cycle(),
        "test_5_context_bloat": run_test_5_context_bloat(),
    }


def main():
    print("Brutal Tests Protocol\n" + "=" * 60)
    results = run_all()

    for name, r in results.items():
        status = "PASS" if r.get("passed") else "FAIL"
        print(f"\n{name}: {status}")
        print(f"  {r.get('notes', '')}")

    print("\n" + "=" * 60)
    print("Summary table (for report)")
    print("| Test | Description                    | Status |")
    print("|------|--------------------------------|--------|")
    print(f"| 1    | Dog food (run on self)        | {'PASS' if results['test_1_dog_food'].get('passed') else 'FAIL'} |")
    print(f"| 2    | Hidden disconnect (scope)     | {'PASS' if results['test_2_hidden_disconnect'].get('passed') else 'FAIL'} |")
    print(f"| 3    | Syntax torture                | {'PASS' if results['test_3_syntax_torture'].get('passed') else 'FAIL'} |")
    print(f"| 4    | Cycle of death (no infinite loop) | {'PASS' if results['test_4_cycle'].get('passed') else 'FAIL'} |")
    print(f"| 5    | Context bloat (minimal subgraph) | {'PASS' if results['test_5_context_bloat'].get('passed') else 'FAIL'} |")

    return 0 if all(r.get("passed") for r in results.values()) else 1


if __name__ == "__main__":
    sys.exit(main())
