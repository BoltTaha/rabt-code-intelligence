#!/usr/bin/env python3
"""
Update the persisted graph only if the repo has changed (git diff).
Use this after editing code or in a git hook so the graph stays fresh.
Run from project root: python update_graph_if_changed.py [--repo examples/sample_repo]
"""

import argparse
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

try:
    from dotenv import load_dotenv
    load_dotenv(_ROOT / ".env")
except ImportError:
    pass

import yaml
from parser import parse_path
from graph import build_graph, save_graph
from graph.change_detection import has_python_changes, is_git_repo
from runtime import collect_runtime_events


def load_config() -> dict:
    path = _ROOT / "config" / "default.yaml"
    defaults = {"graph": {"persist_path": ".graph.json"}}
    if path.exists():
        try:
            with open(path, encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
            for k, v in data.items():
                if v is None:
                    continue
                if isinstance(v, dict) and k in defaults:
                    defaults[k].update(v)
                else:
                    defaults[k] = v
        except (OSError, yaml.YAMLError):
            pass
    return defaults


def main() -> int:
    ap = argparse.ArgumentParser(description="Rebuild graph only if repo has changed")
    ap.add_argument("--repo", "-r", default=str(_ROOT / "examples" / "sample_repo"), help="Repo path")
    ap.add_argument("--force", "-f", action="store_true", help="Rebuild even if no git changes")
    args = ap.parse_args()

    repo_path = Path(args.repo).resolve()
    if not repo_path.exists():
        print(f"Repo not found: {repo_path}", file=sys.stderr)
        return 1

    config = load_config()
    persist_path = (config.get("graph") or {}).get("persist_path", ".graph.json")
    path_to_save = _ROOT / persist_path

    if not args.force and is_git_repo(repo_path) and not has_python_changes(repo_path):
        print("No Python files changed; graph not updated.")
        return 0

    parser_output = parse_path(str(repo_path))
    runtime_events = collect_runtime_events(str(repo_path), config)
    G = build_graph(parser_output, runtime_events or None)
    save_graph(G, path_to_save)
    print(f"Graph updated: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges -> {path_to_save}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
