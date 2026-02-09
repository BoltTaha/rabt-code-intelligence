"""
AST parser: walk Python AST and produce nodes + static edges.
Uses stdlib 'ast' for Python-only MVP; no external parser dependency.
"""

import ast
from pathlib import Path
from typing import List, Set

from core.types import (
    Edge,
    EdgeType,
    Node,
    NodeKind,
    ParserOutput,
)


def _node_id(module: str, kind: str, name: str) -> str:
    """Unique node id: module::kind::name."""
    return f"{module}::{kind}::{name}"


def parse_path(repo_path: str | None) -> ParserOutput:
    """
    Parse all Python files under repo_path and return a single ParserOutput.
    repo_path can be a directory or a single .py file. Returns empty output if None.
    """
    if repo_path is None:
        return ParserOutput(nodes=[], edges=[])
    path = Path(repo_path)
    if not path.exists():
        return ParserOutput(nodes=[], edges=[])

    if path.is_file():
        files = [path] if path.suffix == ".py" else []
    else:
        files = [
            f
            for f in path.rglob("*.py")
            if not any(part in (".venv", "venv", "__pycache__", ".git") for part in f.parts)
        ]

    all_nodes: List[Node] = []
    all_edges: List[Edge] = []
    seen_node_ids: Set[str] = set()

    for filepath in files:
        try:
            source = filepath.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        module_name = filepath.with_suffix("").as_posix().replace("/", ".")
        out = _parse_module(source, module_name, str(filepath))
        for n in out.nodes:
            if n.id not in seen_node_ids:
                seen_node_ids.add(n.id)
                all_nodes.append(n)
        all_edges.extend(out.edges)

    return ParserOutput(nodes=all_nodes, edges=all_edges)


def _parse_module(source: str, module_name: str, filepath: str) -> ParserOutput:
    """Parse a single module's source into nodes and edges."""
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return ParserOutput(nodes=[], edges=[])

    nodes: List[Node] = []
    edges: List[Edge] = []
    current_class: str | None = None
    # Map local name -> (target_module, target_name) for imported names
    imports_map: dict[str, tuple[str, str]] = {}

    # Module node
    mod_id = _node_id(module_name, "module", module_name)
    nodes.append(
        Node(
            id=mod_id,
            kind=NodeKind.MODULE,
            name=module_name,
            module=module_name,
            metadata={"file": filepath},
        )
    )

    def resolve_import_module(import_module: str) -> str:
        """Resolve relative import to full module path (best effort)."""
        if not import_module or "." in import_module:
            return import_module
        # Same package: e.g. main is examples.sample_repo.main -> sibling is examples.sample_repo.user_service
        prefix = module_name.rsplit(".", 1)[0] if "." in module_name else ""
        return f"{prefix}.{import_module}" if prefix else import_module

    def full_name(name: str) -> str:
        return f"{current_class}.{name}" if current_class else name

    class Visitor(ast.NodeVisitor):
        def visit_ClassDef(self, node: ast.ClassDef) -> None:
            nonlocal current_class
            name = node.name
            class_id = _node_id(module_name, "class", name)
            nodes.append(
                Node(
                    id=class_id,
                    kind=NodeKind.CLASS,
                    name=name,
                    module=module_name,
                    line=node.lineno,
                    metadata={"file": filepath},
                )
            )
            edges.append(
                Edge(mod_id, class_id, EdgeType.REFERENCES, 1.0)
            )
            # INHERITS
            for base in node.bases:
                if isinstance(base, ast.Name):
                    base_id = _node_id(module_name, "class", base.id)
                    edges.append(Edge(class_id, base_id, EdgeType.INHERITS, 1.0))
            prev = current_class
            current_class = name
            self.generic_visit(node)
            current_class = prev

        def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
            name = full_name(node.name)
            kind = NodeKind.FUNCTION
            func_id = _node_id(module_name, "function", name)
            nodes.append(
                Node(
                    id=func_id,
                    kind=kind,
                    name=node.name,
                    module=module_name,
                    line=node.lineno,
                    metadata={"class": current_class} if current_class else {},
                )
            )
            # Module or class references this function
            if current_class:
                class_id = _node_id(module_name, "class", current_class)
                edges.append(Edge(class_id, func_id, EdgeType.REFERENCES, 1.0))
            else:
                edges.append(Edge(mod_id, func_id, EdgeType.REFERENCES, 1.0))

            # Find calls and names used
            for child in ast.walk(node):
                if isinstance(child, ast.Call):
                    call_target = _resolve_call_target(
                        child.func, module_name, imports_map
                    )
                    if call_target:
                        edges.append(
                            Edge(func_id, call_target, EdgeType.CALLS, 1.0)
                        )
                if isinstance(child, ast.Name) and isinstance(
                    child.ctx, ast.Store
                ):
                    var_id = _node_id(module_name, "variable", full_name(child.id))
                    if not any(n.id == var_id for n in nodes):
                        nodes.append(
                            Node(
                                id=var_id,
                                kind=NodeKind.VARIABLE,
                                name=child.id,
                                module=module_name,
                                metadata={},
                            )
                        )
                    edges.append(
                        Edge(func_id, var_id, EdgeType.REFERENCES, 1.0)
                    )

            self.generic_visit(node)

        def visit_Import(self, node: ast.Import) -> None:
            for alias in node.names:
                target_mod = alias.asname or alias.name
                target_id = _node_id(target_mod, "module", target_mod)
                edges.append(Edge(mod_id, target_id, EdgeType.IMPORTS, 1.0))
            self.generic_visit(node)

        def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
            base = node.module or ""
            resolved_base = resolve_import_module(base) if base else ""
            for alias in node.names:
                name = alias.asname or alias.name
                imp_module = resolved_base or base or module_name
                target_id = _node_id(imp_module, "module", imp_module)
                edges.append(Edge(mod_id, target_id, EdgeType.IMPORTS, 1.0))
                if alias.name == "*":  # skip for call resolution; can't map * to a name
                    continue
                imports_map[name] = (resolved_base or base or module_name, alias.name)
            self.generic_visit(node)

    Visitor().visit(tree)
    return ParserOutput(nodes=nodes, edges=edges)


def _resolve_call_target(
    func: ast.expr, module_name: str, imports_map: dict | None = None
) -> str | None:
    """Resolve a call expression to a node id. Use imports_map for cross-module calls."""
    imports_map = imports_map or {}
    if isinstance(func, ast.Name):
        # Imported name: resolve to defining module
        if func.id in imports_map:
            target_module, target_name = imports_map[func.id]
            return _node_id(target_module, "function", target_name)
        return _node_id(module_name, "function", func.id)
    if isinstance(func, ast.Attribute):
        if isinstance(func.value, ast.Name):
            # module.func -> use module as defining module
            return _node_id(func.value.id, "function", func.attr)
        if isinstance(func.value, ast.Attribute):
            return _node_id(module_name, "function", func.attr)
    return None
