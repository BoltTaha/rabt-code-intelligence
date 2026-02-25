#!/usr/bin/env python3
"""
Visualize the dependency graph: load .graph.json and render with matplotlib.
Hot path (high execution weight) = red; cold path = blue.
Run from project root: python visualize_graph.py [--graph .graph.json] [--out graph.png]
"""

import argparse
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

def main() -> None:
    ap = argparse.ArgumentParser(description="Render dependency graph (red=hot, blue=cold)")
    ap.add_argument("--graph", "-g", default=".graph.json", help="Path to graph JSON")
    ap.add_argument("--out", "-o", default="graph.png", help="Output image path")
    ap.add_argument("--layout", choices=["spring", "shell", "kamada"], default="spring", help="Layout algorithm")
    ap.add_argument(
        "--focus-name",
        help="If set, visualize only an ego subgraph around nodes whose 'name' matches this value.",
    )
    ap.add_argument(
        "--radius",
        type=int,
        default=1,
        help="Radius (in hops) for ego subgraph when --focus-name is used (default: 1).",
    )
    ap.add_argument(
        "--max-labels",
        type=int,
        default=30,
        help="Maximum number of nodes to label (highest-heat nodes are labeled first).",
    )
    args = ap.parse_args()

    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import networkx as nx
    except ImportError as e:
        print("Install matplotlib and networkx: pip install matplotlib networkx", file=sys.stderr)
        sys.exit(1)

    from graph.storage import load_graph

    path = Path(args.graph)
    if not path.exists():
        print(f"Graph not found: {path}. Run the pipeline first to generate .graph.json.", file=sys.stderr)
        sys.exit(1)

    G = load_graph(path)
    if G.number_of_nodes() == 0:
        print("Graph is empty.", file=sys.stderr)
        sys.exit(0)

    # Optionally restrict to an ego subgraph around a focus node name
    if args.focus_name:
        # Find all nodes whose 'name' attribute matches focus-name
        focus_nodes = [
            n for n, d in G.nodes(data=True) if d.get("name") == args.focus_name
        ]
        if not focus_nodes:
            print(
                f"No nodes found with name={args.focus_name!r}; rendering full graph instead.",
                file=sys.stderr,
            )
        else:
            import networkx as nx

            # Take ego-graphs around each focus node and union them
            sub_nodes = set()
            for fn in focus_nodes:
                ego = nx.ego_graph(G, fn, radius=args.radius, undirected=False)
                sub_nodes.update(ego.nodes())
            G = G.subgraph(sub_nodes).copy()
            if G.number_of_nodes() == 0:
                print(
                    "Ego subgraph is empty after filtering; falling back to full graph.",
                    file=sys.stderr,
                )
                G = load_graph(path)

    # Compute "heat" per node: max of (sum of incident edge weights) so hot paths are red
    heat = {}
    for n in G.nodes():
        total = 0.0
        for _u, _v, d in G.edges(data=True):
            w = d.get("weight", 1.0)
            if _u == n or _v == n:
                total += float(w)
        heat[n] = total

    max_heat = max(heat.values()) if heat else 1.0
    min_heat = min(heat.values()) if heat else 0.0
    span = max_heat - min_heat if max_heat > min_heat else 1.0

    # Normalize to 0..1; 1 = red (hot), 0 = blue (cold)
    def norm(h: float) -> float:
        return (h - min_heat) / span if span else 0.0

    # Node colors: (r, g, b, a); red when hot, blue when cold
    node_colors = []
    for n in G.nodes():
        t = norm(heat[n])
        node_colors.append((t, 0.2, 1.0 - t, 1.0))  # red at t=1, blue at t=0

    # Layout
    if args.layout == "spring":
        pos = nx.spring_layout(G, k=1.5, iterations=50, seed=42)
    elif args.layout == "shell":
        pos = nx.shell_layout(G)
    else:
        pos = nx.kamada_kawai_layout(G)

    # Short labels: label only the hottest max_label nodes to reduce clutter
    # Use node "name" if available, else last part of id
    labels: dict = {}
    # Sort nodes by heat descending, take top-k
    top_nodes = sorted(heat, key=heat.get, reverse=True)[: max(args.max_labels, 0)]
    top_set = set(top_nodes)
    for n in top_set:
        data = G.nodes[n]
        name = data.get("name") if data else None
        if name:
            labels[n] = name
        else:
            labels[n] = n.split("::")[-1] if "::" in n else n

    fig, ax = plt.subplots(figsize=(12, 10))
    nx.draw_networkx_edges(G, pos, ax=ax, edge_color="gray", arrows=True, arrowsize=12, alpha=0.6)
    nx.draw_networkx_nodes(G, pos, node_color=node_colors, node_size=800, ax=ax)
    nx.draw_networkx_labels(G, pos, labels, font_size=7, ax=ax)

    ax.set_title("Dependency graph (red = hot path, blue = cold)")
    ax.axis("off")
    plt.tight_layout()
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"Saved: {out_path}")


if __name__ == "__main__":
    main()
