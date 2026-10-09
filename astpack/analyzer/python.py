from __future__ import annotations
import ast
from typing import List, Optional, Set, Union
from astpack.analyzer.base import (
    BaseAnalyzer,
    FileAnalysis,
    SymbolKind,
    SymbolNode,
)


class DependencyVisitor(ast.NodeVisitor):
    """Collects names and attributes referenced in an AST node."""

    def __init__(self):
        self.dependencies: Set[str] = set()

    def visit_Name(self, node: ast.Name):
        self.dependencies.add(node.id)
        self.generic_visit(node)

    def visit_Attribute(self, node: ast.Attribute):
        self.dependencies.add(node.attr)
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call):
        if isinstance(node.func, ast.Name):
            self.dependencies.add(node.func.id)
        elif isinstance(node.func, ast.Attribute):
            self.dependencies.add(node.func.attr)
        self.generic_visit(node)


class PythonAnalyzer(BaseAnalyzer):
    """High-fidelity Python AST Analyzer."""

    def can_handle(self, filepath: str) -> bool:
        return filepath.endswith(".py") or filepath.endswith(".pyi")

    def parse(self, code: str, filepath: str) -> FileAnalysis:
        self.current_filepath = filepath
        try:
            tree = ast.parse(code, filename=filepath)
        except SyntaxError:
            return FileAnalysis(filepath=filepath, language="python", raw_code=code)

        module_doc = ast.get_docstring(tree)
        analysis = FileAnalysis(
            filepath=filepath,
            language="python",
            raw_code=code,
            module_docstring=module_doc,
        )

        for node in tree.body:
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                analysis.imports.append(ast.unparse(node))
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                sym = self._extract_function_symbol(node)
                analysis.symbols.append(sym)
            elif isinstance(node, ast.ClassDef):
                sym = self._extract_class_symbol(node)
                analysis.symbols.append(sym)
            elif isinstance(node, (ast.Assign, ast.AnnAssign)):
                sym = self._extract_constant_symbol(node)
                if sym:
                    analysis.symbols.append(sym)

        return analysis

    def _extract_function_symbol(
        self,
        node: ast.FunctionDef | ast.AsyncFunctionDef,
        parent_name: Optional[str] = None,
    ) -> SymbolNode:
        kind = (
            SymbolKind.ASYNC_FUNCTION
            if isinstance(node, ast.AsyncFunctionDef)
            else (SymbolKind.METHOD if parent_name else SymbolKind.FUNCTION)
        )
        doc = ast.get_docstring(node)

        func_cls = ast.AsyncFunctionDef if isinstance(node, ast.AsyncFunctionDef) else ast.FunctionDef
        kwargs = {
            "name": node.name,
            "args": node.args,
            "body": [ast.Pass()],
            "decorator_list": node.decorator_list,
            "returns": node.returns,
            "type_comment": getattr(node, "type_comment", None),
        }
        if hasattr(node, "type_params"):
            kwargs["type_params"] = node.type_params

        temp_node = func_cls(**kwargs)
        ast.copy_location(temp_node, node)
        ast.fix_missing_locations(temp_node)

        try:
            sig = ast.unparse(temp_node).split(":\n")[0] + ":"
        except Exception:
            sig = f"def {node.name}(...):"

        dep_visitor = DependencyVisitor()
        dep_visitor.visit(node)
        arg_names = {a.arg for a in node.args.args}
        deps = {d for d in dep_visitor.dependencies if d != node.name and d not in arg_names}

        return SymbolNode(
            name=node.name,
            kind=kind,
            signature=sig,
            docstring=doc,
            start_line=node.lineno,
            end_line=node.end_lineno or node.lineno,
            dependencies=deps,
            parent_name=parent_name,
            filepath=self.current_filepath,
        )

    def _extract_class_symbol(self, node: ast.ClassDef) -> SymbolNode:
        doc = ast.get_docstring(node)
        bases = [ast.unparse(b) for b in node.bases]
        sig = f"class {node.name}" + (f"({', '.join(bases)})" if bases else "") + ":"

        class_sym = SymbolNode(
            name=node.name,
            kind=SymbolKind.CLASS,
            signature=sig,
            docstring=doc,
            start_line=node.lineno,
            end_line=node.end_lineno or node.lineno,
        )

        for item in node.body:
            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                method_sym = self._extract_function_symbol(item, parent_name=node.name)
                class_sym.children.append(method_sym)
                class_sym.dependencies.update(method_sym.dependencies)

        return class_sym

    def _extract_constant_symbol(self, node: ast.Assign | ast.AnnAssign) -> Optional[SymbolNode]:
        try:
            sig = ast.unparse(node)
            name = ""
            if isinstance(node, ast.Assign) and node.targets:
                if isinstance(node.targets[0], ast.Name):
                    name = node.targets[0].id
            elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
                name = node.target.id
            if name and name.isupper():
                return SymbolNode(
                    name=name,
                    kind=SymbolKind.CONSTANT,
                    signature=sig,
                    start_line=node.lineno,
                    end_line=node.end_lineno or node.lineno,
                )
        except Exception:
            pass
        return None

    def prune(
        self,
        analysis: FileAnalysis,
        focus_targets: Optional[Set[str]] = None,
        dependency_targets: Optional[Set[str]] = None,
        mode: str = "focus",
    ) -> str:
        """
        Prunes the Python code into semantic stubs.
        - 'signatures': Strips implementations and docstrings for extreme token reduction.
        - 'stubs': Stubs implementations into '...' while preserving docstrings.
        - 'focus': Keeps full implementation of primary focus_targets, preserves stubs for
                   dependency_targets, and strips docstrings from unrelated code.
        """
        if not analysis.raw_code:
            return ""

        try:
            tree = ast.parse(analysis.raw_code, filename=analysis.filepath)
        except SyntaxError:
            return analysis.raw_code

        primary_targets = set(focus_targets or [])
        dep_targets = set(dependency_targets or [])

        class PruneTransformer(ast.NodeTransformer):
            def __init__(self, primaries: Set[str], deps: Set[str], prune_mode: str):
                self.primaries = primaries
                self.deps = deps
                self.mode = prune_mode
                self.current_class: Optional[str] = None

            def visit_ClassDef(self, node: ast.ClassDef):
                prev_class = self.current_class
                self.current_class = node.name

                new_body = []
                for item in node.body:
                    res = self.visit(item)
                    if res:
                        new_body.append(res)

                self.current_class = prev_class
                ellipsis_expr = ast.Expr(value=ast.Constant(value=Ellipsis))
                ast.copy_location(ellipsis_expr, node)
                node.body = new_body or [ellipsis_expr]
                ast.fix_missing_locations(node)
                return node

            def visit_FunctionDef(self, node: ast.FunctionDef):
                return self._transform_func(node)

            def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
                return self._transform_func(node)

            def _transform_func(self, node: ast.FunctionDef | ast.AsyncFunctionDef):
                qual_name = f"{self.current_class}.{node.name}" if self.current_class else node.name
                
                is_primary = (
                    qual_name in self.primaries
                    or node.name in self.primaries
                    or (self.current_class and self.current_class in self.primaries)
                )
                is_dependency = (
                    qual_name in self.deps
                    or node.name in self.deps
                )

                if self.mode == "focus" and is_primary:
                    # Keep full implementation for primary focus targets
                    return node

                # Determine whether to retain docstrings:
                # In 'signatures' mode: never keep docstrings
                # In 'stubs' mode: always keep docstrings
                # In 'focus' mode: keep docstrings only for dependencies; strip for unrelated code
                if self.mode == "signatures":
                    keep_doc = False
                elif self.mode == "stubs":
                    keep_doc = True
                elif self.mode == "focus":
                    keep_doc = is_dependency or not self.primaries
                else:
                    keep_doc = True

                new_body = []
                doc = ast.get_docstring(node, clean=False)
                if keep_doc and doc:
                    doc_expr = ast.Expr(value=ast.Constant(value=doc))
                    ast.copy_location(doc_expr, node)
                    new_body.append(doc_expr)

                ellipsis_expr = ast.Expr(value=ast.Constant(value=Ellipsis))
                ast.copy_location(ellipsis_expr, node)
                new_body.append(ellipsis_expr)

                node.body = new_body
                ast.fix_missing_locations(node)
                return node

        transformer = PruneTransformer(
            primaries=primary_targets,
            deps=dep_targets,
            prune_mode=mode,
        )
        pruned_tree = transformer.visit(tree)
        ast.fix_missing_locations(pruned_tree)

        try:
            return ast.unparse(pruned_tree)
        except Exception:
            return analysis.raw_code
