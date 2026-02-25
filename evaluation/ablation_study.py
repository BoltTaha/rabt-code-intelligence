#!/usr/bin/env python3
"""
Ablation study: Compare static-only vs runtime-only vs hybrid graphs
This demonstrates the value of combining both approaches.
"""

import json
import sys
from pathlib import Path
from typing import Dict, List

sys.path.insert(0, str(Path(__file__).parent.parent))

from parser.ast_parser import parse_path
from graph.builder import build_graph
from agent.intent import parse_intent
from agent.traversal import extract_subgraph
from graph.storage import GraphStorage


class AblationStudy:
    """Compare three graph configurations"""
    
    def __init__(self, repo_path: str):
        self.repo_path = Path(repo_path)
        self.results = {
            "static_only": {},
            "runtime_only": {},
            "hybrid": {}
        }
    
    def build_static_graph(self):
        """Build graph with only static analysis"""
        print("\n📊 Building STATIC-ONLY graph...")
        
        parser_output = parse_path(str(self.repo_path))
        graph = build_graph(parser_output, merge_runtime=False)
        
        self.results["static_only"]["nodes"] = graph.number_of_nodes()
        self.results["static_only"]["edges"] = graph.number_of_edges()
        self.results["static_only"]["graph"] = graph
        
        print(f"✓ Static graph: {graph.number_of_nodes()} nodes, {graph.number_of_edges()} edges")
        return graph
    
    def build_runtime_only_graph(self):
        """Build graph with only runtime edges"""
        print("\n🏃 Building RUNTIME-ONLY graph...")
        
        # Parse to get basic nodes
        parser_output = parse_path(str(self.repo_path))
        builder = GraphBuilder()
        
        # Build with runtime events but filter out static edges
        graph = build_graph
        # Remove static edges (keep only RuntimeCall and MODIFIED_BY)
        runtime_graph = graph.copy()
        edges_to_remove = []
        for u, v, data in runtime_graph.edges(data=True):
            edge_type = data.get("edge_type", "")
            if edge_type not in ["RuntimeCall", "MODIFIED_BY"]:
                edges_to_remove.append((u, v))
        
        runtime_graph.remove_edges_from(edges_to_remove)
        
        self.results["runtime_only"]["nodes"] = runtime_graph.number_of_nodes()
        self.results["runtime_only"]["edges"] = runtime_graph.number_of_edges()
        self.results["runtime_only"]["graph"] = runtime_graph
        
        print(f"✓ Runtime graph: {runtime_graph.number_of_nodes()} nodes, {runtime_graph.number_of_edges()} edges")
        return runtime_graph
    
    def build_hybrid_graph(self):
        """Build full hybrid graph (current approach)"""
        print("\n🔀 Building HYBRID graph...")
        
        parser_output = parse_path(str(self.repo_path))
        builder = GraphBuilder()
        graph = build_graph
        self.results["hybrid"]["nodes"] = graph.number_of_nodes()
        self.results["hybrid"]["edges"] = graph.number_of_edges()
        self.results["hybrid"]["graph"] = graph
        
        print(f"✓ Hybrid graph: {graph.number_of_nodes()} nodes, {graph.number_of_edges()} edges")
        return graph
    
    def test_query(self, query: str, config: Dict):
        """Test same query on all three graph types"""
        print(f"\n{'='*60}")
        print(f"Testing query: {query}")
        print(f"{'='*60}")
        
        intent = parse_intent(query, config)
        
        for mode in ["static_only", "runtime_only", "hybrid"]:
            if "graph" not in self.results[mode]:
                continue
            
            graph = self.results[mode]["graph"]
            
            try:
                subgraph = extract_subgraph(
                    graph=graph,
                    intent=intent,
                    config=config
                )
                
                subgraph_size = subgraph.number_of_nodes()
                subgraph_edges = subgraph.number_of_edges()
                
                # Calculate coverage
                coverage = (subgraph_size / graph.number_of_nodes() * 100) if graph.number_of_nodes() > 0 else 0
                
                self.results[mode][f"query_{query}"] = {
                    "subgraph_nodes": subgraph_size,
                    "subgraph_edges": subgraph_edges,
                    "coverage_percent": round(coverage, 2)
                }
                
                print(f"{mode:15} → {subgraph_size} nodes, {subgraph_edges} edges ({coverage:.1f}% coverage)")
                
            except Exception as e:
                self.results[mode][f"query_{query}"] = {
                    "error": str(e)
                }
                print(f"{mode:15} → Error: {e}")
    
    def run(self, test_queries: List[str], config: Dict):
        """Run full ablation study"""
        print("\n" + "="*60)
        print("ABLATION STUDY: Static vs Runtime vs Hybrid")
        print("="*60)
        print(f"Repository: {self.repo_path}")
        
        # Build all three graphs
        self.build_static_graph()
        self.build_runtime_only_graph()
        self.build_hybrid_graph()
        
        # Test queries
        for query in test_queries:
            self.test_query(query, config)
        
        # Save results
        self.save_results()
        self.print_summary()
    
    def save_results(self):
        """Save results to JSON"""
        output_path = "evaluation/ablation_results.json"
        
        # Remove graph objects before saving
        save_data = {}
        for mode, data in self.results.items():
            save_data[mode] = {k: v for k, v in data.items() if k != "graph"}
        
        with open(output_path, "w") as f:
            json.dump(save_data, f, indent=2)
        
        print(f"\n✓ Results saved to {output_path}")
    
    def print_summary(self):
        """Print comparative summary"""
        print("\n" + "="*60)
        print("ABLATION STUDY SUMMARY")
        print("="*60)
        
        print("\nGraph Sizes:")
        print(f"{'Mode':<15} {'Nodes':<10} {'Edges':<10}")
        print("-" * 35)
        for mode in ["static_only", "runtime_only", "hybrid"]:
            nodes = self.results[mode].get("nodes", 0)
            edges = self.results[mode].get("edges", 0)
            print(f"{mode:<15} {nodes:<10} {edges:<10}")
        
        print("\n✅ Key Insights:")
        
        hybrid_edges = self.results["hybrid"].get("edges", 0)
        static_edges = self.results["static_only"].get("edges", 0)
        runtime_edges = self.results["runtime_only"].get("edges", 0)
        
        if hybrid_edges > static_edges:
            additional = hybrid_edges - static_edges
            print(f"• Hybrid adds {additional} runtime edges ({(additional/static_edges*100):.1f}% increase)")
        
        if runtime_edges > 0:
            print(f"• Runtime-only captures {runtime_edges} dynamic dependencies")
        
        print("\n" + "="*60)


def main():
    """Run ablation study on sample repo"""
    import yaml
    
    # Load config
    with open("config/default.yaml") as f:
        config = yaml.safe_load(f)
    
    # Test queries
    queries = [
        "Who calls save_user?",
        "Where is userData modified?",
        "What does main depend on?"
    ]
    
    study = AblationStudy("examples/sample_repo")
    study.run(queries, config)


if __name__ == "__main__":
    main()
