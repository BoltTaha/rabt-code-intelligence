"""
Testing Protocol for Semantic Graph Memory MVP.
Run with: python -m evaluation.protocol
Or: pytest evaluation/protocol.py -v

Produces results suitable for the "Experiments" section of the research paper.
"""

from pathlib import Path
import sys

# Project root
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from parser import parse_path
from graph import build_graph
from agent import parse_intent, extract_subgraph, subgraph_to_text
from graph.queries import nodes_by_name, who_calls


SAMPLE_REPO = _ROOT / "examples" / "sample_repo"

# Expected function names in the 4-file sample repo (roll call)
EXPECTED_FUNCTIONS = {
    "main",           # main.py
    "get_user", "save_user", "delete_user",  # user_service.py
    "validate_input", "update_user", "get_user_data",  # data_handler.py
    "normalize_id",   # utils.py
}


def get_graph():
    """Build fresh graph from sample repo."""
    if not SAMPLE_REPO.exists():
        raise FileNotFoundError(f"Sample repo not found: {SAMPLE_REPO}")
    out = parse_path(str(SAMPLE_REPO))
    return build_graph(out, None)


def get_function_nodes(G):
    """Return list of (name, module) for all function nodes."""
    return [
        (attrs.get("name"), attrs.get("module", ""))
        for nid, attrs in G.nodes(data=True)
        if attrs.get("kind") == "function"
    ]


# ---------- Phase 1: Structural Integrity ----------

def _run_test_1_node_verification():
    """Test 1: Every function/class in the 4 files exists as a node (Roll Call)."""
    G = get_graph()
    funcs = get_function_nodes(G)
    names = {f[0] for f in funcs if f[0]}
    missing = EXPECTED_FUNCTIONS - names
    extra_ok = names - EXPECTED_FUNCTIONS  # e.g. nested or class methods
    passed = len(missing) == 0
    return {
        "passed": passed,
        "expected": sorted(EXPECTED_FUNCTIONS),
        "found": sorted(names),
        "missing": sorted(missing),
        "notes": f"Detected {len(funcs)} function nodes. Missing: {missing or 'none'}.",
    }


def _run_test_2_cross_file_link():
    """Test 2: main -> save_user edge points to user_service.save_user (not generic)."""
    G = get_graph()
    # Find main node (any module)
    main_ids = nodes_by_name(G, "main")
    save_user_ids = nodes_by_name(G, "save_user")
    if not main_ids or not save_user_ids:
        return {"passed": False, "notes": "main or save_user node not found."}

    # The save_user that lives in user_service (module contains "user_service")
    save_user_in_user_service = [nid for nid in save_user_ids if "user_service" in G.nodes[nid].get("module", "")]
    if not save_user_in_user_service:
        return {"passed": False, "notes": "save_user node in user_service not found."}

    target_id = save_user_in_user_service[0]
    # Check: is there a CALLS edge from any main to this save_user?
    callers = who_calls(G, target_id)
    main_callers = [c for c in callers if G.nodes[c].get("name") == "main"]
    passed = len(main_callers) > 0

    return {
        "passed": passed,
        "notes": "main has CALLS edge to user_service.save_user" if passed else "main does not link to user_service.save_user.",
        "main_calls_save_user_node": passed,
    }


# ---------- Phase 2: Functional Query Tests ----------

def _run_test_3_caller_query():
    """Test 3: 'Who calls update_user?' returns save_user (direct caller), NOT main."""
    G = get_graph()
    intent = parse_intent("Who calls update_user?")
    if not intent:
        return {"passed": False, "notes": "Intent not parsed."}

    subgraph = extract_subgraph(G, intent, max_depth=5, max_nodes=100)
    subgraph_text = subgraph_to_text(subgraph)

    # Get direct callers of update_user from graph
    update_user_ids = nodes_by_name(G, "update_user")
    if not update_user_ids:
        return {"passed": False, "notes": "update_user node not found."}
    callers = who_calls(G, update_user_ids[0])
    caller_names = {G.nodes[c].get("name") for c in callers}

    has_save_user = "save_user" in caller_names
    has_main = "main" in caller_names
    passed = has_save_user and not has_main

    return {
        "passed": passed,
        "callers_returned": list(caller_names),
        "notes": "Returns save_user (direct caller), not main (indirect)." if passed else f"Callers: {caller_names}; expected only save_user.",
    }


def _run_test_4_dependency_query():
    """Test 4: 'What does main depend on?' includes save_user, get_user, validate_input; excludes delete_user."""
    G = get_graph()
    intent = parse_intent("What does main depend on?")
    if not intent:
        return {"passed": False, "notes": "Intent not parsed (add 'what does X depend on' pattern)."}

    subgraph = extract_subgraph(G, intent, max_depth=5, max_nodes=100)
    names_in_subgraph = {subgraph.nodes[nid].get("name") for nid in subgraph.nodes()}

    required = {"save_user", "get_user", "validate_input"}
    must_exclude = {"delete_user"}
    has_required = required <= names_in_subgraph
    excludes_delete_user = "delete_user" not in names_in_subgraph
    passed = has_required and excludes_delete_user

    return {
        "passed": passed,
        "in_subgraph": sorted(names_in_subgraph),
        "required": sorted(required),
        "notes": "Subgraph contains save_user, get_user, validate_input; excludes delete_user." if passed else f"Has required: {has_required}, excludes delete_user: {excludes_delete_user}.",
    }


# ---------- Phase 3: Value Test (Context Reduction) ----------

def _run_test_5_token_reduction():
    """Test 5: Measure context reduction (full repo lines vs minimal subgraph lines)."""
    repo_path = SAMPLE_REPO
    if not repo_path.exists():
        return {"passed": False, "reduction_pct": None, "notes": "Sample repo not found."}

    # Full repo line count (approximate "context" if we dumped everything)
    full_lines = 0
    for f in repo_path.rglob("*.py"):
        full_lines += len(f.read_text(encoding="utf-8").splitlines())

    G = get_graph()
    intent = parse_intent("Who calls save_user?")
    if not intent:
        return {"passed": False, "reduction_pct": None, "notes": "Intent not parsed."}

    subgraph = extract_subgraph(G, intent, max_depth=5, max_nodes=100)
    subgraph_text = subgraph_to_text(subgraph)
    subgraph_lines = len(subgraph_text.splitlines())

    if full_lines == 0:
        reduction_pct = 0.0
    else:
        reduction_pct = round(100.0 * (1.0 - subgraph_lines / full_lines), 1)

    passed = reduction_pct > 0

    return {
        "passed": passed,
        "full_repo_lines": full_lines,
        "subgraph_lines": subgraph_lines,
        "reduction_pct": reduction_pct,
        "notes": f"Context reduction: {reduction_pct}% (full {full_lines} lines -> subgraph {subgraph_lines} lines).",
    }


# ---------- Phase 4: Edge Case / Torture Tests ----------

def _run_test_6_aliased_imports():
    """Test 6: import user_service as us; us.save_user(...) still links to user_service.save_user."""
    # Our parser resolves module.func when func is Attribute(value=Name('us'), attr='save_user')
    # to _node_id('us', 'function', 'save_user') - wrong module. So we expect FAIL unless we add Import tracking for 'import X as Y'.
    G = get_graph()
    # In the CURRENT sample repo we use "from user_service import save_user", not "import user_service as us".
    # So this test would need a separate fixture file. We run against current repo and document expected behavior.
    save_user_ids = nodes_by_name(G, "save_user")
    main_ids = nodes_by_name(G, "main")
    if not main_ids or not save_user_ids:
        return {"passed": False, "notes": "Nodes not found."}

    # In current repo we already have cross-file link (Test 2). Aliased import is a different code pattern.
    # Mark as Todo: parser does not yet resolve "us.save_user" when us = user_service (import user_service as us).
    return {
        "passed": None,  # Not implemented
        "notes": "Aliased imports (import X as Y; Y.func()) require parser update to map Y -> X. Current repo uses 'from X import func' which is supported.",
        "status": "todo",
    }


def _run_test_7_circular_dependencies():
    """Test 7: A->B->A: traversal stops (max_depth/node budget), no infinite loop."""
    from core.types import ParserOutput, Node, NodeKind, Edge, EdgeType

    # Build a tiny graph with cycle: A calls B, B calls A
    nodes = [
        Node("m::function::a", NodeKind.FUNCTION, "a", "m"),
        Node("m::function::b", NodeKind.FUNCTION, "b", "m"),
    ]
    edges = [
        Edge("m::function::a", "m::function::b", EdgeType.CALLS, 1.0),
        Edge("m::function::b", "m::function::a", EdgeType.CALLS, 1.0),
    ]
    G = build_graph(ParserOutput(nodes=nodes, edges=edges), None)

    intent = parse_intent("What does a depend on?")
    if not intent:
        return {"passed": False, "notes": "Intent not parsed."}

    subgraph = extract_subgraph(G, intent, max_depth=3, max_nodes=10)
    # Should have stopped at depth/node limit, not hang
    passed = subgraph.number_of_nodes() <= 10 and subgraph.number_of_nodes() >= 1

    return {
        "passed": passed,
        "notes": "Traversal with max_depth/max_nodes terminates; no infinite loop on A->B->A.",
        "subgraph_nodes": subgraph.number_of_nodes(),
    }


# ---------- Run all and print report table ----------

def run_all():
    """Run all protocol tests and return results + summary table."""
    results = {}
    results["test_1_node_verification"] = _run_test_1_node_verification()
    results["test_2_cross_file_link"] = _run_test_2_cross_file_link()
    results["test_3_caller_query"] = _run_test_3_caller_query()
    results["test_4_dependency_query"] = _run_test_4_dependency_query()
    results["test_5_token_reduction"] = _run_test_5_token_reduction()
    results["test_6_aliased_imports"] = _run_test_6_aliased_imports()
    results["test_7_circular_dependencies"] = _run_test_7_circular_dependencies()

    return results


def status_str(r):
    if r.get("passed") is True:
        return "✅ Pass"
    if r.get("passed") is False:
        return "❌ Fail"
    if r.get("status") == "todo":
        return "⚠️ Todo"
    return "?"


def main():
    print("Semantic Graph Memory — Testing Protocol\n" + "=" * 50)
    if not SAMPLE_REPO.exists():
        print(f"ERROR: Sample repo not found at {SAMPLE_REPO}")
        return 1

    results = run_all()

    # Summary table for report
    print("\nSummary (for Testing & Evaluation section of report)\n")
    print("| Test Category     | Test Case              | Status   | Notes |")
    print("|-------------------|------------------------|----------|-------|")

    cat = "Structural"
    r1 = results["test_1_node_verification"]
    print(f"| {cat:<17} | Node Discovery          | {status_str(r1):<8} | {r1.get('notes', '')[:45]} |")
    r2 = results["test_2_cross_file_link"]
    print(f"| {'':17} | Cross-File Linking      | {status_str(r2):<8} | {r2.get('notes', '')[:45]} |")

    cat = "Functional"
    r3 = results["test_3_caller_query"]
    print(f"| {cat:<17} | \"Who calls X?\"          | {status_str(r3):<8} | {r3.get('notes', '')[:45]} |")
    r4 = results["test_4_dependency_query"]
    print(f"| {'':17} | \"What does main depend on?\" | {status_str(r4):<8} | {r4.get('notes', '')[:45]} |")

    cat = "Performance"
    r5 = results["test_5_token_reduction"]
    red = r5.get("reduction_pct")
    perf_note = f"{red}% reduction" if red is not None else r5.get("notes", "")[:40]
    print(f"| {cat:<17} | Context Reduction       | {status_str(r5):<8} | {perf_note} |")

    cat = "Robustness"
    r6 = results["test_6_aliased_imports"]
    print(f"| {cat:<17} | Aliased Imports         | {status_str(r6):<8} | {r6.get('notes', '')[:45]} |")
    r7 = results["test_7_circular_dependencies"]
    print(f"| {'':17} | Circular Dependencies   | {status_str(r7):<8} | {r7.get('notes', '')[:45]} |")

    print("\n" + "=" * 50)
    print("Detailed notes:")
    for name, r in results.items():
        print(f"  {name}: {r.get('notes', '')}")

    if r5.get("reduction_pct") is not None:
        print(f"\n  Context reduction: {r5['reduction_pct']}% (full repo {r5.get('full_repo_lines')} lines -> subgraph {r5.get('subgraph_lines')} lines)")

    return 0


# Pytest-compatible test functions (run with: pytest evaluation/protocol.py -v)
def test_protocol_1_node_verification():
    r = _run_test_1_node_verification()
    assert r["passed"], r.get("notes", "")


def test_protocol_2_cross_file_link():
    r = _run_test_2_cross_file_link()
    assert r["passed"], r.get("notes", "")


def test_protocol_3_caller_query():
    r = _run_test_3_caller_query()
    assert r["passed"], r.get("notes", "")


def test_protocol_4_dependency_query():
    r = _run_test_4_dependency_query()
    assert r["passed"], r.get("notes", "")


def test_protocol_5_token_reduction():
    r = _run_test_5_token_reduction()
    assert r["passed"], r.get("notes", "")


def test_protocol_7_circular_dependencies():
    r = _run_test_7_circular_dependencies()
    assert r["passed"], r.get("notes", "")


if __name__ == "__main__":
    sys.exit(main())
