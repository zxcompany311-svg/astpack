"""
JavaScript and TypeScript Syntax Analyzer and Pruner.
Handles .js, .jsx, .ts, .tsx files, preserving type signatures and interfaces
while stubbing function implementations.
"""

import re
from typing import List, Optional, Set
from astpack.analyzer.base import (
    BaseAnalyzer,
    FileAnalysis,
    SymbolKind,
    SymbolNode,
)


class JavaScriptAnalyzer(BaseAnalyzer):
    """JS/TS syntax analyzer and pruner."""

    SUPPORTED_EXTS = {".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs"}

    def can_handle(self, filepath: str) -> bool:
        return any(filepath.endswith(ext) for ext in self.SUPPORTED_EXTS)

    def parse(self, code: str, filepath: str) -> FileAnalysis:
        analysis = FileAnalysis(
            filepath=filepath,
            language="typescript" if filepath.endswith((".ts", ".tsx")) else "javascript",
            raw_code=code,
        )

        # Extract imports
        import_pattern = re.compile(r'^\s*(?:import\s+.*?;\s*|const\s+.*?=\s*require\(.*?\);\s*)', re.MULTILINE)
        analysis.imports = [m.group(0).strip() for m in import_pattern.finditer(code)]

        # Extract functions / interfaces / classes
        # Matches: function name(...), const name = (...), class Name, interface Name, type Name
        decl_pattern = re.compile(
            r'^\s*(export\s+)?(default\s+)?(async\s+)?'
            r'(function\s+([a-zA-Z0-9_$]+)|'
            r'class\s+([a-zA-Z0-9_$]+)|'
            r'interface\s+([a-zA-Z0-9_$]+)|'
            r'type\s+([a-zA-Z0-9_$]+)\s*=|'
            r'const\s+([a-zA-Z0-9_$]+)\s*=\s*(?:async\s*)?\()',
            re.MULTILINE,
        )

        for match in decl_pattern.finditer(code):
            name = (
                match.group(5)  # function
                or match.group(6)  # class
                or match.group(7)  # interface
                or match.group(8)  # type
                or match.group(9)  # const func
            )
            if not name:
                continue

            full_match = match.group(0).strip()
            if "interface" in full_match:
                kind = SymbolKind.INTERFACE
            elif "class" in full_match:
                kind = SymbolKind.CLASS
            elif "type" in full_match:
                kind = SymbolKind.TYPE_ALIAS
            else:
                kind = SymbolKind.FUNCTION

            analysis.symbols.append(
                SymbolNode(
                    name=name,
                    kind=kind,
                    signature=full_match,
                    is_exported=bool(match.group(1)),
                )
            )

        return analysis

    def prune(
        self,
        analysis: FileAnalysis,
        focus_targets: Optional[Set[str]] = None,
        dependency_targets: Optional[Set[str]] = None,
        mode: str = "focus",
    ) -> str:
        """
        Prune function bodies into '{ /* ... implementation elided ... */ }'.
        Retains full implementation for focus_targets if in focus mode.
        """
        code = analysis.raw_code
        if not code:
            return ""

        targets = set(focus_targets or [])

        # Parse character by character to reliably balance curly braces
        result = []
        i = 0
        n = len(code)

        # Regex to locate function starts
        func_start_re = re.compile(
            r'(?:(?:export\s+)?(?:default\s+)?(?:async\s+)?function\s+([a-zA-Z0-9_$]+)[^{]*\{|'
            r'(?:export\s+)?(?:const|let)\s+([a-zA-Z0-9_$]+)\s*=\s*(?:async\s*)?\([^)]*\)[^{]*=>\s*\{|'
            r'([a-zA-Z0-9_$]+)\s*\([^)]*\)\s*(?::\s*[^\{]+)?\{)'
        )

        while i < n:
            match = func_start_re.search(code, i)
            if not match:
                result.append(code[i:])
                break

            start_idx = match.start()
            brace_open_idx = match.end() - 1
            func_name = match.group(1) or match.group(2) or match.group(3)

            # Append text before this function
            result.append(code[i:start_idx])

            # Find matching closing brace
            brace_count = 1
            curr = brace_open_idx + 1
            in_single_quote = False
            in_double_quote = False
            in_template = False
            in_line_comment = False
            in_block_comment = False

            while curr < n and brace_count > 0:
                char = code[curr]
                prev = code[curr - 1] if curr > 0 else ""

                if in_line_comment:
                    if char == "\n":
                        in_line_comment = False
                elif in_block_comment:
                    if char == "/" and prev == "*":
                        in_block_comment = False
                elif in_single_quote:
                    if char == "'" and prev != "\\":
                        in_single_quote = False
                elif in_double_quote:
                    if char == '"' and prev != "\\":
                        in_double_quote = False
                elif in_template:
                    if char == "`" and prev != "\\":
                        in_template = False
                else:
                    if char == "/" and curr + 1 < n and code[curr + 1] == "/":
                        in_line_comment = True
                    elif char == "/" and curr + 1 < n and code[curr + 1] == "*":
                        in_block_comment = True
                    elif char == "'":
                        in_single_quote = True
                    elif char == '"':
                        in_double_quote = True
                    elif char == "`":
                        in_template = True
                    elif char == "{":
                        brace_count += 1
                    elif char == "}":
                        brace_count -= 1

                curr += 1

            # Check if this function is focused
            is_focused = bool(func_name and func_name in targets)
            if mode == "focus" and is_focused:
                # Keep full body
                result.append(code[start_idx:curr])
            else:
                # Stub out body
                header = code[start_idx:brace_open_idx]
                result.append(f"{header}{{ /* ... implementation elided ... */ }}")

            i = curr

        return "".join(result)
