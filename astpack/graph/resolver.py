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

    def add_file(self, analysis: FileAnalysis):
        for sym in analysis.symbols:
            qname = sym.qualified_name()
            self.nodes[qname] = sym
            self.nodes[sym.name] = sym
            self.edges.setdefault(qname, set()).update(sym.dependencies)
            self.edges.setdefault(sym.name, set()).update(sym.dependencies)

            for child in sym.children:
                cqname = child.qualified_name()
                self.nodes[cqname] = child
                self.nodes[child.name] = child
                self.edges.setdefault(cqname, set()).update(child.dependencies)
                self.edges.setdefault(child.name, set()).update(child.dependencies)

    def resolve_closure(self, target_symbols: Set[str], max_depth: int = 1) -> Set[str]:
        """
        Calculates the dependency closure up to max_depth.
        Returns all symbols that should be preserved or stubbed as relevant context.
        """
        closure = set(target_symbols)
        current_frontier = set(target_symbols)

        for _ in range(max_depth):
            next_frontier = set()
            for sym in current_frontier:
                deps = self.edges.get(sym, set())
                for dep in deps:
                    if dep in self.nodes and dep not in closure:
                        closure.add(dep)
                        next_frontier.add(dep)
            current_frontier = next_frontier
            if not current_frontier:
                break

        return closure
