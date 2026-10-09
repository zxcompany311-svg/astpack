"""
Analyzer registry and loader.
"""

from typing import List, Optional
from astpack.analyzer.base import BaseAnalyzer, FileAnalysis, SymbolNode, SymbolKind
from astpack.analyzer.python import PythonAnalyzer
from astpack.analyzer.javascript import JavaScriptAnalyzer

_ANALYZERS: List[BaseAnalyzer] = [
    PythonAnalyzer(),
    JavaScriptAnalyzer(),
]


def get_analyzer(filepath: str) -> Optional[BaseAnalyzer]:
    """Find an analyzer capable of processing the given file path."""
    for analyzer in _ANALYZERS:
        if analyzer.can_handle(filepath):
            return analyzer
    return None


__all__ = [
    "BaseAnalyzer",
    "FileAnalysis",
    "SymbolNode",
    "SymbolKind",
    "PythonAnalyzer",
    "JavaScriptAnalyzer",
    "get_analyzer",
]
