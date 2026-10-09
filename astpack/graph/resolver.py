"""
Symbol dependency graph and call closure resolver.
Computes the minimal transitive call graph needed for an LLM coding task.
"""

from typing import Dict, List, Set, Optional
from astpack.analyzer.base import FileAnalysis, SymbolNode


class DependencyGraph:
    """Directed graph representing symbol call and inheritance relationships."""

    def __init__(self):
        self.nodes: Dict[str, SymbolNode] = {}
        self.edges: Dict[str, Set[str]] = {}
        self.file_map: Dict[str, str] = {}  # symbol_name -> filepath

    def add_file(self, analysis: FileAnalysis):
        for sym in analysis.symbols:
            qname = sym.qualified_name()
            self.nodes[qname] = sym
            self.nodes[sym.name] = sym
            self.file_map[qname] = analysis.filepath
            self.file_map[sym.name] = analysis.filepath
            self.edges.setdefault(qname, set()).update(sym.dependencies)
            self.edges.setdefault(sym.name, set()).update(sym.dependencies)

            for child in sym.children:
                cqname = child.qualified_name()
                self.nodes[cqname] = child
                self.nodes[child.name] = child
                self.file_map[cqname] = analysis.filepath
                self.file_map[child.name] = analysis.filepath
                self.edges.setdefault(cqname, set()).update(child.dependencies)
                self.edges.setdefault(child.name, set()).update(child.dependencies)

    def resolve_closure(self, target_symbols: Set[str], max_depth: int = 1) -> Set[str]:
        """
        Calculates the complete transitive dependency closure up to max_depth.
        Returns all symbols (both targets and dependencies).
        """
        layers = self.resolve_layers(target_symbols, max_depth)
        return layers["primary"] | layers["dependencies"]

    def resolve_layers(self, target_symbols: Set[str], max_depth: int = 1) -> Dict[str, Set[str]]:
        """
        Calculates dependency closure divided into layers:
        - 'primary': the exact target symbols
        - 'dependencies': upstream/downstream called symbols within max_depth
        """
        primaries = set(target_symbols)
        dependencies = set()
        current_frontier = set(target_symbols)

        for _ in range(max(1, max_depth)):
            next_frontier = set()
            for sym in current_frontier:
                deps = self.edges.get(sym, set())
                for dep in deps:
                    if dep in self.nodes and dep not in primaries and dep not in dependencies:
                        dependencies.add(dep)
                        next_frontier.add(dep)
            current_frontier = next_frontier
            if not current_frontier:
                break

        return {
            "primary": primaries,
            "dependencies": dependencies,
        }
