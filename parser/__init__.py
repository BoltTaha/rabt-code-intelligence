"""
Static analysis layer: AST → nodes + static edges.
Single responsibility: parse source files and produce ParserOutput.
"""

from parser.ast_parser import parse_path

__all__ = ["parse_path"]
