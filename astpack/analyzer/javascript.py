"""
JavaScript and TypeScript Syntax Analyzer and Pruner.
Handles .js, .jsx, .ts, .tsx files, preserving type signatures and interfaces
while stubbing function implementations and resolving call dependencies.
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
        decl_pattern = re.compile(
            r'^\s*(export\s+)?(default\s+)?(async\s+)?'
            r'(function\s+([a-zA-Z0-9_$]+)|'
            r'class\s+([a-zA-Z0-9_$]+)|'
            r'interface\s+([a-zA-Z0-9_$]+)|'
            r'type\s+([a-zA-Z0-9_$]+)\s*=|'
            r'(?:const|let)\s+([a-zA-Z0-9_$]+)\s*=\s*(?:async\s*)?\()',
            re.MULTILINE,
        )

        call_pattern = re.compile(r'\b([a-zA-Z0-9_$]+)\s*\(')

        for match in decl_pattern.finditer(code):
            name = (
                match.group(5)
                or match.group(6)
                or match.group(7)
                or match.group(8)
                or match.group(9)
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

            # Extract dependencies (called identifiers) within a reasonable window or body
            start_pos = match.start()
            sample_body = code[start_pos : start_pos + 1500]
            deps = {
                c.group(1)
                for c in call_pattern.finditer(sample_body)
                if c.group(1) != name and c.group(1) not in {"function", "require", "import", "if", "for", "while", "catch"}
            }

            analysis.symbols.append(
                SymbolNode(
                    name=name,
                    kind=kind,
                    signature=full_match,
                    is_exported=bool(match.group(1)),
                    dependencies=deps,
                    filepath=filepath,
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
        Prune function bodies into stubs:
        - 'signatures': Minimal empty braces '{}' without comments.
        - 'stubs': Standard '{ /* ... implementation elided ... */ }'.
        - 'focus': Keeps full implementation for primary targets, informative stubs
                   for dependencies, and minimal '{}' for unrelated code.
        """
        code = analysis.raw_code
        if not code:
            return ""

        primaries = set(focus_targets or [])
        deps = set(dependency_targets or [])

        result = []
        i = 0
        n = len(code)

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

            result.append(code[i:start_idx])

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

            is_primary = bool(func_name and func_name in primaries)
            is_dep = bool(func_name and func_name in deps)

            header = code[start_idx:brace_open_idx]

            if mode == "focus":
                if is_primary:
                    result.append(code[start_idx:curr])
                elif is_dep or not primaries:
                    result.append(f"{header}{{ /* ... dependency stub ... */ }}")
                else:
                    result.append(f"{header}{{}}")
            elif mode == "signatures":
                result.append(f"{header}{{}}")
            else:  # mode == "stubs"
                result.append(f"{header}{{ /* ... implementation elided ... */ }}")

            i = curr

        return "".join(result)
