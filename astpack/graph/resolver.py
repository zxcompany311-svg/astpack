"""
Symbol dependency graph and call closure resolver.
Computes the minimal transitive call graph needed for an LLM coding task.
Supports Python import-aware cross-file call resolution.
"""

from typing import Dict, List, Set, Optional
from pathlib import Path
from astpack.analyzer.base import FileAnalysis, SymbolNode


class DependencyGraph:
    """Directed graph representing symbol call and inheritance relationships."""

    def __init__(self):
        self.nodes: Dict[str, SymbolNode] = {}
        self.edges: Dict[str, Set[str]] = {}
        self.file_map: Dict[str, str] = {}  # symbol_name -> filepath
        self.file_imports: Dict[str, Dict[str, str]] = {}  # filepath -> import_map

    def add_file(self, analysis: FileAnalysis):
        filepath = analysis.filepath
        self.file_imports[filepath] = analysis.import_map

        for sym in analysis.symbols:
            qname = sym.qualified_name()
            self.nodes[qname] = sym
            self.nodes[sym.name] = sym
            self.file_map[qname] = filepath
            self.file_map[sym.name] = filepath

            # Resolve symbol dependencies using import_map when available
            resolved_deps = set()
            for dep in sym.dependencies:
                # If dep was explicitly imported, resolve to target symbol
                if dep in analysis.import_map:
                    target_qual = analysis.import_map[dep]
                    resolved_deps.add(target_qual)
                    # Also keep short name of target
                    resolved_deps.add(target_qual.split(".")[-1])
                else:
                    resolved_deps.add(dep)

            self.edges.setdefault(qname, set()).update(resolved_deps)
            self.edges.setdefault(sym.name, set()).update(resolved_deps)

            for child in sym.children:
                cqname = child.qualified_name()
                self.nodes[cqname] = child
                self.nodes[child.name] = child
                self.file_map[cqname] = filepath
                self.file_map[child.name] = filepath

                child_resolved_deps = set()
                for dep in child.dependencies:
                    if dep in analysis.import_map:
                        target_qual = analysis.import_map[dep]
                        child_resolved_deps.add(target_qual)
                        child_resolved_deps.add(target_qual.split(".")[-1])
                    else:
                        child_resolved_deps.add(dep)

                self.edges.setdefault(cqname, set()).update(child_resolved_deps)
                self.edges.setdefault(child.name, set()).update(child_resolved_deps)

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

        # Depth 0 means target only, no dependencies
        if max_depth <= 0:
            return {"primary": primaries, "dependencies": dependencies}

        for _ in range(max_depth):
            next_frontier = set()
            for sym in current_frontier:
                deps = self.edges.get(sym, set())
                for dep in deps:
                    # Check if dep matches a known node (either directly or by short name)
                    matched_dep = dep if dep in self.nodes else None
                    if not matched_dep:
                        short = dep.split(".")[-1]
                        if short in self.nodes:
                            matched_dep = short

                    if matched_dep and matched_dep not in primaries and matched_dep not in dependencies:
                        dependencies.add(matched_dep)
                        next_frontier.add(matched_dep)
            current_frontier = next_frontier
            if not current_frontier:
                break

        return {
            "primary": primaries,
            "dependencies": dependencies,
        }
