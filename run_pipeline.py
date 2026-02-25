#!/usr/bin/env python3
"""
Single entry point: parse repo → build graph → answer query (optional LLM).
Orchestration only; no business logic.
"""

import argparse
import sys
from pathlib import Path

# Allow running from project root without installing
_ROOT = Path(__file__).resolve().parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

# Load .env from project root (local only; never commit .env)
try:
    from dotenv import load_dotenv
    load_dotenv(_ROOT / ".env")
except ImportError:
    pass

import yaml

from parser import parse_path
from core.types import ParserOutput
from graph import build_graph, load_graph, save_graph, merge_changes
from agent import parse_intent, extract_subgraph, subgraph_to_text
from runtime import collect_runtime_events
from llm import answer_with_llm
from utils.git_utils import get_changed_files


def load_config(config_path: str | None) -> dict:
    """Load YAML config; merge with defaults. Uses config/default.yaml if no path given."""
    defaults = {
        "traversal": {"max_depth": 5, "max_nodes": 100},
        "graph": {"persist_path": ".graph.json"},
    }
    path = Path(config_path) if config_path else _ROOT / "config" / "default.yaml"
    if path.exists():
        try:
            with open(path, encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
        except (OSError, yaml.YAMLError):
            data = {}
        for k, v in data.items():
            if v is None:
                continue  # keep default, don't overwrite with null
            if isinstance(v, dict) and k in defaults:
                defaults[k].update(v)
            else:
                defaults[k] = v
    return defaults


def run(
    repo_path: str,
    query: str | None = None,
    config_path: str | None = None,
    persist: bool = True,
    incremental: bool = False,
) -> dict:
    """
    Run the full pipeline: parse → graph → [query → subgraph] → optional LLM.
    Returns dict with keys: graph, subgraph, subgraph_text, answer, confidence (if query given).
    """
    config = load_config(config_path)
    persist_path = (config.get("graph") or {}).get("persist_path", ".graph.json")

    if not repo_path or not isinstance(repo_path, str):
        empty = build_graph(ParserOutput(nodes=[], edges=[]), None)
        result = {"graph": empty, "node_count": 0, "edge_count": 0}
        if query:
            result["error"] = "No repo path provided"
            result["subgraph_text"] = ""
            result["answer"] = ""
            result["confidence"] = "LOW"
        return result

    # Build or incrementally update graph
    persist_path_resolved = Path(persist_path)
    if incremental and persist_path_resolved.exists():
        print("Incremental mode: checking for changes...")
        G = load_graph(persist_path_resolved)
        changed = get_changed_files(repo_path)
        if not changed:
            print("No changes detected.")
        else:
            print("Detected changes in:", changed)
            partial_output = parse_path(repo_path, whitelist_files=changed)
            G = merge_changes(G, partial_output, changed, repo_path)
            if persist:
                save_graph(G, persist_path)
    else:
        parser_output = parse_path(repo_path)
        runtime_events = collect_runtime_events(repo_path, config)
        G = build_graph(parser_output, runtime_events or None)
        if persist:
            save_graph(G, persist_path)

    result = {"graph": G, "node_count": G.number_of_nodes(), "edge_count": G.number_of_edges()}

    if not query:
        return result

    # Query agent
    intent = parse_intent(query, config=config)
    if not intent:
        result["error"] = f"Unsupported query: {query!r}"
        result["subgraph_text"] = ""
        result["answer"] = ""
        result["confidence"] = "LOW"
        return result

    trav = config.get("traversal") or {}
    try:
        max_depth = int(trav.get("max_depth", 5))
        max_nodes = int(trav.get("max_nodes", 100))
    except (TypeError, ValueError):
        max_depth, max_nodes = 5, 100
    subgraph = extract_subgraph(
        G,
        intent,
        max_depth=max_depth,
        max_nodes=max_nodes,
    )
    subgraph_text = subgraph_to_text(subgraph)
    result["subgraph"] = subgraph
    result["subgraph_text"] = subgraph_text
    result["subgraph_node_count"] = subgraph.number_of_nodes()

    # Optional LLM
    answer, confidence, llm_usage = answer_with_llm(subgraph_text, query, config)
    result["answer"] = answer
    result["confidence"] = confidence
    result["llm_usage"] = llm_usage

    return result


def main() -> None:
    ap = argparse.ArgumentParser(description="Semantic Graph Memory pipeline")
    default_repo = str(_ROOT / "examples" / "sample_repo")
    ap.add_argument("--repo", default=default_repo, help="Path to repo or .py file")
    ap.add_argument("--query", "-q", help="Natural language query")
    ap.add_argument("--config", "-c", help="Config YAML path")
    ap.add_argument("--no-persist", action="store_true", help="Do not save graph to file")
    ap.add_argument("--incremental", "-i", action="store_true", help="Update graph only for changed files (git diff)")
    args = ap.parse_args()

    result = run(
        repo_path=args.repo,
        query=args.query,
        config_path=args.config,
        persist=not args.no_persist,
        incremental=args.incremental,
    )

    print(f"Graph: {result['node_count']} nodes, {result['edge_count']} edges")
    if args.query:
        if "error" in result:
            print("Error:", result["error"])
        else:
            print(f"Subgraph: {result.get('subgraph_node_count', 0)} nodes")
            print("Subgraph (text):")
            print(result["subgraph_text"])
            print("\nAnswer:", result["answer"])
            print("Confidence:", result["confidence"])


if __name__ == "__main__":
    main()
