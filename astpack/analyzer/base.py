from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Set


class SymbolKind(str, Enum):
    FUNCTION = "function"
    ASYNC_FUNCTION = "async_function"
    CLASS = "class"
    METHOD = "method"
    IMPORT = "import"
    INTERFACE = "interface"
    TYPE_ALIAS = "type_alias"
    CONSTANT = "constant"


@dataclass
class SymbolNode:
    name: str
    kind: SymbolKind
    signature: str
    docstring: Optional[str] = None
    start_line: int = 1
    end_line: int = 1
    dependencies: Set[str] = field(default_factory=set)
    children: List["SymbolNode"] = field(default_factory=list)
    parent_name: Optional[str] = None
    is_exported: bool = True
    filepath: Optional[str] = None

    def qualified_name(self) -> str:
        if self.parent_name:
            return f"{self.parent_name}.{self.name}"
        return self.name


@dataclass
class FileAnalysis:
    filepath: str
    language: str
    imports: List[str] = field(default_factory=list)
    import_map: Dict[str, str] = field(default_factory=dict)
    symbols: List[SymbolNode] = field(default_factory=list)
    raw_code: str = ""
    module_docstring: Optional[str] = None

    def get_symbol(self, name: str) -> Optional[SymbolNode]:
        for sym in self.symbols:
            if sym.name == name or sym.qualified_name() == name:
                return sym
            for child in sym.children:
                if child.name == name or child.qualified_name() == name:
                    return child
        return None

    def all_symbol_names(self) -> Set[str]:
        names = set()
        for sym in self.symbols:
            names.add(sym.name)
            names.add(sym.qualified_name())
            for child in sym.children:
                names.add(child.name)
                names.add(child.qualified_name())
        return names


class BaseAnalyzer:
    """Base class for AST language analyzers."""

    def can_handle(self, filepath: str) -> bool:
        raise NotImplementedError

    def parse(self, code: str, filepath: str) -> FileAnalysis:
        raise NotImplementedError

    def prune(
        self,
        analysis: FileAnalysis,
        focus_targets: Optional[Set[str]] = None,
        dependency_targets: Optional[Set[str]] = None,
        mode: str = "focus",
    ) -> str:
        """
        Prunes code based on strategy:
        - 'focus': Keeps full implementation of focus_targets, stubs dependencies, strips unrelated.
        - 'stubs': Stubs all function/method bodies into docstrings + '...'.
        - 'signatures': Keeps only class & function headers and '...' (docstrings stripped).
        """
        raise NotImplementedError
