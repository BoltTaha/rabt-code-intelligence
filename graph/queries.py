"""
Graph queries: answer structural questions from the dependency graph.
"""

from typing import List, Optional

import networkx as nx


def get_node_by_id(G: nx.DiGraph, node_id: str) -> Optional[dict]:
    """Return node attributes as dict if node exists."""
    if not G.has_node(node_id):
        return None
    attrs = dict(G.nodes[node_id])
    attrs["id"] = node_id
    return attrs


def who_calls(G: nx.DiGraph, target_id: str) -> List[str]:
    """Return node ids that have a CALLS or RuntimeCall edge to target_id."""
    if not G.has_node(target_id):
        return []
    return [
        u
        for u in G.predecessors(target_id)
        if G.edges[u, target_id].get("edge_type") in ("CALLS", "RuntimeCall")
    ]


def what_calls_this(G: nx.DiGraph, target_id: str) -> List[str]:
    """Forward impact: who is called by target."""
    if not G.has_node(target_id):
        return []
    return list(G.successors(target_id))


def what_does_import(G: nx.DiGraph, module_id: str) -> List[str]:
    """Return node ids that module_id imports (IMPORTS edges)."""
    if not G.has_node(module_id):
        return []
    return [
        v
        for v in G.successors(module_id)
        if G.edges[module_id, v].get("edge_type") == "IMPORTS"
    ]


def where_modified(G: nx.DiGraph, variable_id: str) -> List[str]:
    """Return node ids that have MODIFIED_BY edge to variable_id."""
    if not G.has_node(variable_id):
        return []
    return [
        u
        for u in G.predecessors(variable_id)
        if G.edges[u, variable_id].get("edge_type") == "MODIFIED_BY"
    ]


def nodes_by_name(G: nx.DiGraph, name: str) -> List[str]:
    """Return node ids whose name equals name (any kind)."""
    return [
        nid
        for nid, attrs in G.nodes(data=True)
        if attrs.get("name") == name
    ]
