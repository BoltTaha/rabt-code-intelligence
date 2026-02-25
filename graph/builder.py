"""
Build a NetworkX DiGraph from parser output (and optional runtime events).
Supports incremental update via merge_changes (remove nodes from changed files, add new parse output).
"""

import networkx as nx
from pathlib import Path
from typing import List, Optional

from core.types import EdgeType, ParserOutput, RuntimeEvent


def build_graph(
    parser_output: ParserOutput,
    runtime_events: Optional[List[RuntimeEvent]] = None,
) -> nx.DiGraph:
    """
    Build a directed graph from static parser output and optional runtime events.
    Returns a NetworkX DiGraph with node attributes and edge attributes (type, weight).
    """
    G = nx.DiGraph()

    for node in parser_output.nodes:
        G.add_node(
            node.id,
            kind=node.kind.value,
            name=node.name,
            module=node.module,
            line=node.line,
            **node.metadata,
        )

    def _resolve_target(target_id: str) -> Optional[str]:
        """If target_id is missing, try package re-export: e.g. parser::function::parse_path -> parser.ast_parser::function::parse_path."""
        if G.has_node(target_id):
            return target_id
        # target_id format: "module::kind::name"
        parts = target_id.split("::", 2)
        if len(parts) != 3:
            return None
        mod, kind, name = parts
        for nid in G.nodes():
            if G.nodes[nid].get("name") == name and G.nodes[nid].get("kind") == kind:
                nmod = G.nodes[nid].get("module", "")
                if nmod.startswith(mod + "."):
                    return nid
        return None

    for edge in parser_output.edges:
        target_id = _resolve_target(edge.target_id)
        if G.has_node(edge.source_id) and target_id:
            G.add_edge(
                edge.source_id,
                target_id,
                edge_type=edge.edge_type.value,
                weight=edge.weight,
                **edge.metadata,
            )

    # Helper to resolve runtime IDs (which might use __main__) to static graph IDs
    def _resolve_runtime_id(node_id: str | None) -> Optional[str]:
        """
        Map a runtime node_id to an existing node in G.

        - If the id exists as-is, return it.
        - If it starts with '__main__::', try to match by (kind, name) against
          nodes in the static graph and return the unique match.
        """
        if not node_id:
            return None
        if G.has_node(node_id):
            return node_id
        if node_id.startswith("__main__::"):
            parts = node_id.split("::", 2)
            if len(parts) == 3:
                _mod, kind, name = parts
                candidates = [
                    n
                    for n, attrs in G.nodes(data=True)
                    if attrs.get("name") == name and attrs.get("kind") == kind
                ]
                if len(candidates) == 1:
                    return candidates[0]
        return None

    if runtime_events:
        for ev in runtime_events:
            if ev.event_type == "call" and ev.source_id and ev.target_id:
                src = _resolve_runtime_id(ev.source_id)
                tgt = _resolve_runtime_id(ev.target_id)
                if src and tgt:
                    if G.has_edge(src, tgt):
                        G.edges[src, tgt]["weight"] = (
                            G.edges[src, tgt].get("weight", 1) + ev.count
                        )
                        # If this was a static CALLS edge, optionally upgrade to RUNTIME_CALL
                        if G.edges[src, tgt].get("edge_type") == EdgeType.CALLS.value:
                            G.edges[src, tgt]["edge_type"] = EdgeType.RUNTIME_CALL.value
                    else:
                        G.add_edge(
                            src,
                            tgt,
                            edge_type=EdgeType.RUNTIME_CALL.value,
                            weight=float(ev.count),
                        )
            elif ev.event_type == "mutation" and ev.source_id and ev.variable_id:
                src = _resolve_runtime_id(ev.source_id)
                var = _resolve_runtime_id(ev.variable_id)
                if src and var:
                    G.add_edge(
                        src,
                        var,
                        edge_type=EdgeType.MODIFIED_BY.value,
                        weight=float(ev.count),
                    )

    return G


def _file_to_module(repo_path: str, relative_file: str) -> str:
    """Convert a path relative to repo_path to module name (e.g. main.py -> examples.sample_repo.main)."""
    base = Path(repo_path)
    p = (base / relative_file).with_suffix("")
    return p.as_posix().replace("/", ".")


def merge_changes(
    G: nx.DiGraph,
    new_parser_output: ParserOutput,
    changed_files: List[str],
    repo_path: str,
) -> nx.DiGraph:
    """
    Remove nodes belonging to changed files from G, then add nodes/edges from new_parser_output.
    Nodes are matched by module (derived from file path). Makes the graph "living" without full re-parse.
    """
    if not changed_files:
        return G

    modules_to_remove = {_file_to_module(repo_path, f) for f in changed_files}
    nodes_to_remove = [
        n for n, attrs in G.nodes(data=True)
        if attrs.get("module") in modules_to_remove
    ]
    G.remove_nodes_from(nodes_to_remove)

    for node in new_parser_output.nodes:
        G.add_node(
            node.id,
            kind=node.kind.value,
            name=node.name,
            module=node.module,
            line=node.line,
            **node.metadata,
        )

    for edge in new_parser_output.edges:
        if G.has_node(edge.source_id) and G.has_node(edge.target_id):
            G.add_edge(
                edge.source_id,
                edge.target_id,
                edge_type=edge.edge_type.value,
                weight=edge.weight,
                **getattr(edge, "metadata", {}),
            )

    return G
