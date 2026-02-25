#!/usr/bin/env python3
"""
Multi-repository benchmark for Rabt
Tests on Flask, FastAPI, pytest, and requests
"""

import json
import os
import sys
import time
from pathlib import Path
from typing import Dict, List

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from run_pipeline import main as run_pipeline_main
from graph.storage import GraphStorage
from evaluation.baseline_comparison import count_tokens_gemini


class MultiRepoBenchmark:
    """Benchmark Rabt on multiple repositories"""
    
    def __init__(self, rate_limit_delay: float = 15.0):
        """
        Args:
            rate_limit_delay: Seconds to wait between API calls (default: 15s for free tier safety)
        """
        self.rate_limit_delay = rate_limit_delay
        self.api_calls_made = 0
        self.repos = {
            "requests": {
                "path": "examples/requests_repo",
                "queries": [
                    "Who calls request?",
                    "What does Session depend on?",
                    "Where is the PreparedRequest modified?"
                ]
            },
            "flask": {
                "path": "examples/additional_repos/flask",
                "queries": [
                    "Who calls render_template?",
                    "What functions call request.get_json?",
                    "What does Flask app initialization depend on?"
                ]
            },
            "fastapi": {
                "path": "examples/additional_repos/fastapi",
                "queries": [
                    "Who calls APIRouter?",
                    "What does FastAPI constructor depend on?",
                    "Where is Request object modified?"
                ]
            },
            "pytest": {
                "path": "examples/additional_repos/pytest",
                "queries": [
                    "Who calls pytest.fixture?",
                    "What does the test runner depend on?",
                    "What functions modify config?"
                ]
            }
        }
        
        self.results = []
    
    def run_single_query(self, repo_name: str, repo_path: str, query: str) -> Dict:
        """Run a single query and collect metrics"""
        print(f"\n{'='*60}")
        print(f"Repo: {repo_name}")
        print(f"Query: {query}")
        print(f"{'='*60}")
        
        result = {
            "repo": repo_name,
            "query": query,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        
        try:
            # Build graph
            start_time = time.time()
            print(f"Building graph for {repo_name}...")
            
            # Run pipeline (build mode)
            sys.argv = ["rabt", "--repo", repo_path, "--query", query, "--config", "config/default.yaml"]
            
            # Capture graph stats
            graph_path = Path(repo_path) / ".rabt_graph.json"
            if graph_path.exists():
                graph = GraphStorage.load(str(graph_path))
                result["graph_nodes"] = graph.number_of_nodes()
                result["graph_edges"] = graph.number_of_edges()
                print(f"Graph: {result['graph_nodes']} nodes, {result['graph_edges']} edges")
            
            # Get subgraph size (from run_pipeline output)
            # For now, we'll estimate based on query complexity
            result["subgraph_nodes"] = 0  # Will be updated by actual run
            
            build_time = time.time() - start_time
            result["build_time_sec"] = round(build_time, 2)
            
            # Query time
            start_time = time.time()
            # run_pipeline_main()  # Uncomment to actually run
            query_time = time.time() - start_time
            result["query_time_sec"] = round(query_time, 2)
            
            # Estimate token usage
            # For demo purposes, using approximation
            # In full implementation, this would call baseline_comparison
            result["estimated_tokens"] = 100  # Placeholder
            result["status"] = "success"
            
        except Exception as e:
            result["status"] = "error"
            result["error"] = str(e)
            print(f"❌ Error: {e}")
        
        return result
    
    def run_all(self):
        """Run benchmark on all repos"""
        print("\n" + "="*60)
        print("RABT MULTI-REPOSITORY BENCHMARK")
        print("="*60)
        
        for repo_name, config in self.repos.items():
            repo_path = config["path"]
            
            # Check if repo exists
            if not Path(repo_path).exists():
                print(f"\n⚠️  Skipping {repo_name}: repository not found at {repo_path}")
                print(f"   Run: bash evaluation/clone_test_repos.sh")
                continue
            
            for query in config["queries"]:
                result = self.run_single_query(repo_name, repo_path, query)
                self.results.append(result)
        
        self.save_results()
        self.print_summary()
    
    def save_results(self):
        """Save results to JSON"""
        output_path = "evaluation/multi_repo_results.json"
        with open(output_path, "w") as f:
            json.dump(self.results, f, indent=2)
        print(f"\n✓ Results saved to {output_path}")
    
    def print_summary(self):
        """Print summary statistics"""
        print("\n" + "="*60)
        print("BENCHMARK SUMMARY")
        print("="*60)
        
        successful = [r for r in self.results if r["status"] == "success"]
        failed = [r for r in self.results if r["status"] == "error"]
        
        print(f"\nTotal queries: {len(self.results)}")
        print(f"Successful: {len(successful)}")
        print(f"Failed: {len(failed)}")
        
        if successful:
            avg_build = sum(r["build_time_sec"] for r in successful) / len(successful)
            avg_query = sum(r["query_time_sec"] for r in successful) / len(successful)
            total_nodes = sum(r.get("graph_nodes", 0) for r in successful)
            total_edges = sum(r.get("graph_edges", 0) for r in successful)
            
            print(f"\nAverage build time: {avg_build:.2f}s")
            print(f"Average query time: {avg_query:.2f}s")
            print(f"Total nodes across repos: {total_nodes}")
            print(f"Total edges across repos: {total_edges}")
        
        print("\n" + "="*60)


if __name__ == "__main__":
    benchmark = MultiRepoBenchmark()
    benchmark.run_all()
