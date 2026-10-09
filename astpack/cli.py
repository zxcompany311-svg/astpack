"""
AstPack Command Line Interface.
Provides high-speed AST context pruning and packing with rich visual feedback.
"""

import argparse
import sys
import os
from pathlib import Path
from astpack import __version__
from astpack.pruner import prune_file, prune_code
from astpack.packer import pack_repository

# Configure Windows terminal encoding safety
if sys.platform == "win32":
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


def _safe_check() -> str:
    try:
        "✓".encode(sys.stdout.encoding or "utf-8")
        return "✓"
    except Exception:
        return "[OK]"


# Optional rich support
try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    console = Console()
    HAS_RICH = True
except ImportError:
    console = None
    HAS_RICH = False


def print_banner():
    banner = rf"""
  ___       _   ___           _   
 / _ \     | | | _ \         | |  
/ /_\ \ ___| |_| |_) |__  ___| | __
|  _  |/ __| __|  __/ _ \/ __| |/ /
| | | |\__ \ |_| | | (_| | (__|   < 
\_| |_/|___/\__|_|  \__,_|\___|_|\_\  v{__version__}
AST-Aware Semantic Context Pruning for Coding Agents
"""
    if HAS_RICH:
        console.print(f"[bold cyan]{banner}[/bold cyan]")
    else:
        print(banner)


def cmd_prune(args):
    filepath = args.file
    focus_targets = args.focus.split(",") if args.focus else None
    mode = args.mode or "focus"
    depth = getattr(args, "depth", 1)

    if filepath == "-":
        content = sys.stdin.read()
        pruned, stats = prune_code(
            content,
            filepath="snippet.py",
            focus=focus_targets,
            mode=mode,
            depth=depth,
        )
    else:
        if not os.path.exists(filepath):
            print(f"Error: file not found: {filepath}", file=sys.stderr)
            sys.exit(1)
        pruned, stats = prune_file(
            filepath,
            focus=focus_targets,
            mode=mode,
            depth=depth,
        )

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(pruned)
        if HAS_RICH and not args.quiet:
            console.print(f"[green]{_safe_check()} Pruned content saved to:[/green] [bold]{args.output}[/bold]")
        elif not args.quiet:
            print(f"{_safe_check()} Pruned content saved to: {args.output}")
    else:
        print(pruned)

    if not args.quiet and sys.stdout.isatty() and args.output:
        _print_stats_table("Prune Summary", stats)


def cmd_pack(args):
    target = args.path or "."
    out_file = args.output or "astpack-context.md"
    focus_targets = args.focus.split(",") if args.focus else None
    mode = args.mode or ("focus" if args.focus else "stubs")
    depth = getattr(args, "depth", 1)

    if not args.quiet and HAS_RICH:
        console.print(f"[bold green]Packing repository:[/bold green] {target} (Mode: {mode})")

    res = pack_repository(
        target_dir=target,
        output_path=out_file,
        focus_targets=focus_targets,
        prune_mode=mode,
        depth=depth,
    )

    if not args.quiet:
        _print_stats_table("Pack Summary", res, is_pack=True)
        if HAS_RICH:
            console.print(f"\n[bold cyan]Context bundle written to:[/bold cyan] [underline]{out_file}[/underline]")
        else:
            print(f"\nContext bundle written to: {out_file}")


def cmd_stats(args):
    target = args.path or "."
    res = pack_repository(
        target_dir=target,
        output_path=None,
        prune_mode="stubs",
    )
    _print_stats_table("Repository Token Footprint", res, is_pack=True)


def cmd_mcp(args):
    from astpack.mcp import run_mcp_server
    run_mcp_server()


def cmd_serve(args):
    from astpack.web import start_playground
    start_playground(port=args.port, open_browser=not args.no_browser)


def _print_stats_table(title: str, stats: dict, is_pack: bool = False):
    if HAS_RICH:
        table = Table(title=title, title_style="bold magenta", border_style="dim")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="bold green", justify="right")

        if is_pack:
            table.add_row("Files Processed", str(stats.get("files_count", 0)))
        table.add_row("Original Tokens", f"{stats.get('original_tokens', 0):,}")
        table.add_row("Pruned Tokens", f"{stats.get('pruned_tokens', 0):,}")
        table.add_row("Saved Tokens", f"{stats.get('saved_tokens', 0):,}")
        table.add_row("Token Reduction", f"{stats.get('reduction_pct', 0.0)}%")
        console.print(table)
    else:
        print(f"\n--- {title} ---")
        if is_pack:
            print(f"Files Processed: {stats.get('files_count', 0)}")
        print(f"Original Tokens: {stats.get('original_tokens', 0):,}")
        print(f"Pruned Tokens:   {stats.get('pruned_tokens', 0):,}")
        print(f"Saved Tokens:    {stats.get('saved_tokens', 0):,}")
        print(f"Token Reduction: {stats.get('reduction_pct', 0.0)}%\n")


def main():
    parser = argparse.ArgumentParser(
        prog="astpack",
        description="AST-aware semantic context pruner & dependency packing engine for AI coding agents.",
    )
    parser.add_argument("-v", "--version", action="version", version=f"astpack {__version__}")

    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    # pack command
    p_pack = subparsers.add_parser("pack", help="Pack repository into pruned AI markdown bundle")
    p_pack.add_argument("path", nargs="?", default=".", help="Directory to pack (default: .)")
    p_pack.add_argument("-o", "--output", help="Output file path (default: astpack-context.md)")
    p_pack.add_argument("-f", "--focus", help="Comma-separated target symbols to preserve in full")
    p_pack.add_argument("-d", "--depth", type=int, default=1, help="Call graph closure traversal depth (default: 1)")
    p_pack.add_argument("-m", "--mode", choices=["focus", "stubs", "signatures"], default=None, help="Pruning mode")
    p_pack.add_argument("-q", "--quiet", action="store_true", help="Suppress progress output")

    # prune command
    p_prune = subparsers.add_parser("prune", help="Prune a single file or snippet")
    p_prune.add_argument("file", help="File to prune (use '-' for stdin)")
    p_prune.add_argument("-o", "--output", help="Output file path (default: stdout)")
    p_prune.add_argument("-f", "--focus", help="Comma-separated target symbols to preserve in full")
    p_prune.add_argument("-d", "--depth", type=int, default=1, help="Call graph closure traversal depth (default: 1)")
    p_prune.add_argument("-m", "--mode", choices=["focus", "stubs", "signatures"], default="focus", help="Pruning mode")
    p_prune.add_argument("-q", "--quiet", action="store_true", help="Suppress stats output")

    # stats command
    p_stats = subparsers.add_parser("stats", help="Analyze repository token footprint and potential savings")
    p_stats.add_argument("path", nargs="?", default=".", help="Directory to analyze (default: .)")

    # mcp command
    p_mcp = subparsers.add_parser("mcp", help="Run Model Context Protocol (MCP) server over stdio")

    # serve command
    p_serve = subparsers.add_parser("serve", help="Launch interactive Web Playground in browser")
    p_serve.add_argument("-p", "--port", type=int, default=7860, help="Port to serve on (default: 7860)")
    p_serve.add_argument("--no-browser", action="store_true", help="Do not automatically open browser")

    args = parser.parse_args()

    if not args.command:
        print_banner()
        parser.print_help()
        sys.exit(0)

    if args.command == "prune":
        cmd_prune(args)
    elif args.command == "pack":
        cmd_pack(args)
    elif args.command == "stats":
        cmd_stats(args)
    elif args.command == "mcp":
        cmd_mcp(args)
    elif args.command == "serve":
        cmd_serve(args)


if __name__ == "__main__":
    main()
