"""
High-level code and file pruning engine.
"""

import os
from typing import Dict, List, Optional, Set, Tuple
from astpack.analyzer import get_analyzer
from astpack.counter import estimate_tokens, compute_savings
from astpack.graph.resolver import DependencyGraph


def prune_code(
    code: str,
    filepath: str = "snippet.py",
    focus: Optional[List[str]] = None,
    mode: str = "focus",
) -> Tuple[str, Dict]:
    """
    Prunes code text according to focus symbols or general stubbing.
    Returns: (pruned_code, stats_dict)
    """
    analyzer = get_analyzer(filepath)
    if not analyzer:
        tokens = estimate_tokens(code)
        return code, {
            "original_tokens": tokens,
            "pruned_tokens": tokens,
            "saved_tokens": 0,
            "reduction_pct": 0.0,
            "language": "unsupported",
        }

    analysis = analyzer.parse(code, filepath)
    focus_targets = set(focus or [])

    pruned_code = analyzer.prune(analysis, focus_targets=focus_targets, mode=mode)

    orig_tok = estimate_tokens(code)
    prun_tok = estimate_tokens(pruned_code)
    saved_tok, pct = compute_savings(orig_tok, prun_tok)

    stats = {
        "original_tokens": orig_tok,
        "pruned_tokens": prun_tok,
        "saved_tokens": saved_tok,
        "reduction_pct": pct,
        "language": analysis.language,
        "symbols_found": len(analysis.symbols),
    }

    return pruned_code, stats


def prune_file(
    filepath: str,
    focus: Optional[List[str]] = None,
    mode: str = "focus",
) -> Tuple[str, Dict]:
    """
    Prunes a single file from disk.
    """
    if not os.path.isfile(filepath):
        raise FileNotFoundError(f"File not found: {filepath}")

    with open(filepath, "r", encoding="utf-8", errors="replace") as f:
        code = f.read()

    return prune_code(code, filepath=filepath, focus=focus, mode=mode)
