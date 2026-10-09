"""
AstPack: AST-aware semantic context pruner & dependency packing engine for AI coding agents.
"""

__version__ = "0.1.0"
__author__ = "AstPack Contributors"

from astpack.pruner import prune_file, prune_code
from astpack.packer import pack_repository
from astpack.counter import estimate_tokens

__all__ = [
    "__version__",
    "prune_file",
    "prune_code",
    "pack_repository",
    "estimate_tokens",
]
