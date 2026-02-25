"""
Graph layer: build, persist, and query the dependency graph.
Single responsibility: hold DiGraph and answer structural queries.
"""

from graph.builder import build_graph, merge_changes
from graph.storage import load_graph, save_graph
from graph.queries import (
    get_node_by_id,
    nodes_by_name,
    what_calls_this,
    what_does_import,
    who_calls,
    where_modified,
)
from graph.change_detection import (
    get_changed_python_files,
    get_untracked_python_files,
    has_python_changes,
    is_git_repo,
)

__all__ = [
    "build_graph",
    "merge_changes",
    "load_graph",
    "save_graph",
    "who_calls",
    "what_calls_this",
    "what_does_import",
    "where_modified",
    "nodes_by_name",
    "get_node_by_id",
    "get_changed_python_files",
    "get_untracked_python_files",
    "has_python_changes",
    "is_git_repo",
]
