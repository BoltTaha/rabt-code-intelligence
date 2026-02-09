"""
Weighted BFS/DFS to extract minimal subgraph from seed nodes.
"""

from typing import List, Set

import networkx as nx

from agent.intent import QueryIntent
from graph.queries import nodes_by_name


def extract_subgraph(
    G: nx.DiGraph,
    intent: QueryIntent,
    max_depth: int = 5,
    max_nodes: int = 100,
) -> nx.DiGraph:
    """
    From the full graph G and a query intent, extract a minimal subgraph
    containing relevant nodes (seed + neighbors along intent edge types).
    """
    edge_types_set = {et.value for et in intent.edge_types}
    seed_ids = _resolve_seeds(G, intent.target_name)
    if not seed_ids:
        return nx.DiGraph()

    subgraph_nodes: Set[str] = set(seed_ids)
    frontier = list(seed_ids)
    depth = 0
    while frontier and depth < max_depth and len(subgraph_nodes) < max_nodes:
        next_frontier: List[str] = []
        for nid in frontier:
            if intent.reverse:
                # Predecessors (who calls / who modifies)
                for pred in G.predecessors(nid):
                    if G.has_edge(pred, nid):
                        et = G.edges[pred, nid].get("edge_type", "")
                        if et in edge_types_set and pred not in subgraph_nodes:
                            subgraph_nodes.add(pred)
                            next_frontier.append(pred)
            else:
                # Successors (forward impact / imports)
                for succ in G.successors(nid):
                    if G.has_edge(nid, succ):
                        et = G.edges[nid, succ].get("edge_type", "")
                        if et in edge_types_set and succ not in subgraph_nodes:
                            subgraph_nodes.add(succ)
                            next_frontier.append(succ)
        frontier = next_frontier
        depth += 1

    return G.subgraph(subgraph_nodes).copy()


def _resolve_seeds(G: nx.DiGraph, target_name: str) -> List[str]:
    """Resolve target name to graph node ids (by name or id)."""
    if G.has_node(target_name):
        return [target_name]
    return nodes_by_name(G, target_name)
