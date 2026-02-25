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
    
    For mutation queries, uses deeper traversal and includes class nodes
    even if the exact attribute node doesn't exist.
    """
    edge_types_set = {et.value for et in intent.edge_types}
    seed_ids = _resolve_seeds(G, intent.target_name)
    if not seed_ids:
        return nx.DiGraph()

    # For mutation queries, increase depth and include class-related nodes
    if intent.intent_type == "modification":
        # Also include successors of class nodes (methods that might modify attributes)
        additional_seeds = []
        for seed_id in seed_ids:
            node_kind = G.nodes[seed_id].get("kind", "")
            if node_kind == "class":
                # Include methods of this class that might modify attributes
                for succ in G.successors(seed_id):
                    if G.has_edge(seed_id, succ):
                        et = G.edges[seed_id, succ].get("edge_type", "")
                        if et in ("CALLS", "REFERENCES") and succ not in seed_ids:
                            additional_seeds.append(succ)
        seed_ids.extend(additional_seeds)

    subgraph_nodes: Set[str] = set(seed_ids)
    frontier = list(seed_ids)
    depth = 0
    # Increase max_depth for mutation queries to find deeper MODIFIED_BY chains
    effective_max_depth = max_depth + 2 if intent.intent_type == "modification" else max_depth
    
    while frontier and depth < effective_max_depth and len(subgraph_nodes) < max_nodes:
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
    """
    Resolve target name to graph node ids (by name or id).
    Handles qualified names like "Session.cookies" by trying:
    1. Exact match (full qualified name as node id)
    2. Simple name match (last component, e.g., "cookies")
    3. Class.attribute pattern: find class node, then look for attribute/variable
    """
    # Try exact match first
    if G.has_node(target_name):
        return [target_name]
    
    # Try simple name match
    matches = nodes_by_name(G, target_name)
    if matches:
        return matches
    
    # Handle qualified names like "Session.cookies" or "Response.status_code"
    if "." in target_name:
        parts = target_name.rsplit(".", 1)
        if len(parts) == 2:
            class_name, attr_name = parts
            # Try to find class node
            class_nodes = nodes_by_name(G, class_name)
            # Also try to find variable/attribute nodes with the attribute name
            attr_nodes = nodes_by_name(G, attr_name)
            # Return both - traversal will explore from all of them
            return class_nodes + attr_nodes
    
    return []
