"""
Repository packer: scans directory, parses .gitignore, resolves cross-file call closures,
prunes code ASTs, and formats an AI-ready Markdown bundle.
"""

import os
from pathlib import Path
from fnmatch import fnmatch
from typing import Dict, List, Optional, Set
from astpack.analyzer import get_analyzer
from astpack.counter import estimate_tokens, compute_savings
from astpack.graph.resolver import DependencyGraph

DEFAULT_IGNORES = {
    ".git",
    ".github",
    ".vscode",
    ".idea",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".venv",
    "venv",
    "env",
    "node_modules",
    "dist",
    "build",
    ".next",
    ".nuxt",
    ".DS_Store",
    "*.pyc",
    "*.pyo",
    "*.pyd",
    "*.lock",
    "package-lock.json",
    "yarn.lock",
    "poetry.lock",
    "pnpm-lock.yaml",
    "uv.lock",
}

BINARY_EXTS = {
    ".png", ".jpg", ".jpeg", ".gif", ".webp", ".ico", ".svg",
    ".mp4", ".mp3", ".wav", ".ogg", ".zip", ".tar", ".gz",
    ".exe", ".dll", ".so", ".dylib", ".bin", ".woff", ".woff2",
    ".pdf", ".docx", ".xlsx",
}

EXT_TO_LANG = {
    "py": "python",
    "pyi": "python",
    "js": "javascript",
    "mjs": "javascript",
    "cjs": "javascript",
    "ts": "typescript",
    "tsx": "tsx",
    "jsx": "jsx",
    "md": "markdown",
    "json": "json",
    "yaml": "yaml",
    "yml": "yaml",
    "sh": "bash",
    "bash": "bash",
    "rs": "rust",
    "go": "go",
}


def load_gitignore_rules(root: Path) -> Set[str]:
    """Parse patterns from .gitignore if present in root."""
    rules = set()
    gitignore_path = root / ".gitignore"
    if gitignore_path.is_file():
        try:
            with open(gitignore_path, "r", encoding="utf-8", errors="replace") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        rules.add(line.rstrip("/"))
        except Exception:
            pass
    return rules


def should_ignore(path: Path, root: Path, custom_ignores: Optional[Set[str]] = None) -> bool:
    """Check if a path matches ignored patterns or .gitignore."""
    rel = path.relative_to(root)
    ignores = DEFAULT_IGNORES | (custom_ignores or set())

    for part in rel.parts:
        for pat in ignores:
            if part == pat or fnmatch(part, pat):
                return True

    rel_str = str(rel).replace("\\", "/")
    for pat in ignores:
        if fnmatch(rel_str, pat):
            return True

    if path.suffix.lower() in BINARY_EXTS:
        return True

    return False


def build_tree_structure(files: List[Path], root: Path) -> str:
    """Generates ASCII directory tree representation."""
    lines = [f"{root.name}/"]
    sorted_files = sorted(files, key=lambda p: str(p.relative_to(root)))
    for p in sorted_files:
        rel = p.relative_to(root)
        depth = len(rel.parts) - 1
        indent = "  " * depth
        lines.append(f"{indent}├── {rel.parts[-1]}")
    return "\n".join(lines)


def pack_repository(
    target_dir: str = ".",
    output_path: Optional[str] = None,
    focus_targets: Optional[List[str]] = None,
    prune_mode: str = "stubs",
    max_file_size_kb: int = 500,
    depth: int = 1,
) -> Dict:
    """
    Packs a repository or directory into an AI-ready Markdown bundle.
    Executes cross-file call graph resolution when focus_targets are provided.
    """
    root = Path(target_dir).resolve()
    if not root.exists():
        raise FileNotFoundError(f"Target path does not exist: {target_dir}")

    gitignore_rules = load_gitignore_rules(root)
    files_to_pack: List[Path] = []

    if root.is_file():
        files_to_pack.append(root)
        root = root.parent
    else:
        for p in root.rglob("*"):
            if p.is_file() and not should_ignore(p, root, gitignore_rules):
                if p.stat().st_size <= max_file_size_kb * 1024:
                    files_to_pack.append(p)

    # First Pass: Pre-read files and construct cross-file DependencyGraph
    global_graph = DependencyGraph()
    parsed_analyses = {}
    file_contents = {}

    for p in sorted(files_to_pack):
        try:
            with open(p, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
            file_contents[p] = content
            analyzer = get_analyzer(p.name)
            if analyzer:
                analysis = analyzer.parse(content, p.name)
                parsed_analyses[p] = (analyzer, analysis)
                global_graph.add_file(analysis)
        except Exception:
            continue

    # Resolve cross-file layers if focus specified
    primary_set = set(focus_targets or [])
    dep_set = set()
    if primary_set:
        layers = global_graph.resolve_layers(primary_set, max_depth=depth)
        primary_set = layers["primary"]
        dep_set = layers["dependencies"]

    total_orig_tokens = 0
    total_pruned_tokens = 0
    file_sections = []

    # Second Pass: Prune each file with cross-file awareness
    for p in sorted(files_to_pack):
        rel_path = str(p.relative_to(root)).replace("\\", "/")
        content = file_contents.get(p, "")
        orig_tok = estimate_tokens(content)
        total_orig_tokens += orig_tok

        if p in parsed_analyses:
            analyzer, analysis = parsed_analyses[p]
            pruned_content = analyzer.prune(
                analysis,
                focus_targets=primary_set,
                dependency_targets=dep_set,
                mode=prune_mode,
            )
        else:
            pruned_content = content

        pruned_tok = estimate_tokens(pruned_content)
        total_pruned_tokens += pruned_tok

        raw_ext = p.suffix.lstrip(".").lower()
        lang = EXT_TO_LANG.get(raw_ext, raw_ext or "text")
        file_sections.append(
            f"### `{rel_path}`\n\n```{lang}\n{pruned_content.strip()}\n```\n"
        )

    saved_tokens, reduction_pct = compute_savings(total_orig_tokens, total_pruned_tokens)
    tree_str = build_tree_structure(files_to_pack, root)

    bundle_header = f"""# Repository Context Pack (Generated by AstPack)

> **Semantic Compression Report**
> - **Files Processed**: {len(files_to_pack)}
> - **Original Tokens**: {total_orig_tokens:,}
> - **Pruned Tokens**: {total_pruned_tokens:,}
> - **Tokens Saved**: {saved_tokens:,} (**{reduction_pct}% reduction**)
> - **Pruning Mode**: `{prune_mode}`
> - **Focus Targets**: `{', '.join(primary_set) if primary_set else 'None'}`

## Project Structure
```text
{tree_str}
```

---

## File Contents
"""

    full_markdown = bundle_header + "\n" + "\n".join(file_sections)

    if output_path:
        out_p = Path(output_path).resolve()
        out_p.parent.mkdir(parents=True, exist_ok=True)
        with open(out_p, "w", encoding="utf-8") as f:
            f.write(full_markdown)

    return {
        "output_markdown": full_markdown,
        "files_count": len(files_to_pack),
        "original_tokens": total_orig_tokens,
        "pruned_tokens": total_pruned_tokens,
        "saved_tokens": saved_tokens,
        "reduction_pct": reduction_pct,
        "output_path": output_path,
        "primary_targets": list(primary_set),
        "dependency_targets": list(dep_set),
    }
