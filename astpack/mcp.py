"""
Model Context Protocol (MCP) server for AstPack.
Allows Claude Desktop, Cursor, Cline, and other AI coding agents
to natively prune context and pack repositories via standard MCP stdio JSON-RPC.
"""

import sys
import json
from typing import Dict, Any
from astpack import __version__
from astpack.pruner import prune_code, prune_file
from astpack.packer import pack_repository

PROTOCOL_VERSION = "2024-11-05"

TOOLS = [
    {
        "name": "astpack_prune",
        "description": "Semantically prune code AST to collapse irrelevant implementations into type stubs/docstrings, saving up to 80% context tokens while preserving syntax and types.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "code": {
                    "type": "string",
                    "description": "Source code text to prune."
                },
                "filepath": {
                    "type": "string",
                    "description": "File name or path (e.g. 'service.py', 'handler.ts') to determine language analyzer."
                },
                "focus": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Optional list of target symbol names (functions/classes) to preserve in full implementation."
                },
                "mode": {
                    "type": "string",
                    "enum": ["focus", "stubs", "signatures"],
                    "description": "Pruning mode. Default is 'focus' if focus targets provided, else 'stubs'."
                }
            },
            "required": ["code", "filepath"]
        }
    },
    {
        "name": "astpack_pack",
        "description": "Pack a directory or repository into a semantically compressed Markdown context bundle optimized for LLM prompts.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "directory_path": {
                    "type": "string",
                    "description": "Path to the repository or directory to pack."
                },
                "focus": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Optional target symbols to preserve in full."
                },
                "mode": {
                    "type": "string",
                    "enum": ["focus", "stubs", "signatures"],
                    "description": "Pruning mode across the repository."
                }
            },
            "required": ["directory_path"]
        }
    },
    {
        "name": "astpack_stats",
        "description": "Analyze token footprint and potential compression savings of a codebase.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "directory_path": {
                    "type": "string",
                    "description": "Path to analyze."
                }
            },
            "required": ["directory_path"]
        }
    }
]


def handle_request(req: Dict[str, Any]) -> Dict[str, Any]:
    method = req.get("method")
    req_id = req.get("id")

    if method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "protocolVersion": PROTOCOL_VERSION,
                "capabilities": {
                    "tools": {}
                },
                "serverInfo": {
                    "name": "astpack-mcp",
                    "version": __version__
                }
            }
        }

    if method == "notifications/initialized":
        return None

    if method == "tools/list":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "tools": TOOLS
            }
        }

    if method == "tools/call":
        params = req.get("params", {})
        tool_name = params.get("name")
        args = params.get("arguments", {})

        if tool_name == "astpack_prune":
            code = args.get("code", "")
            filepath = args.get("filepath", "code.py")
            focus = args.get("focus")
            mode = args.get("mode") or ("focus" if focus else "stubs")
            pruned, stats = prune_code(code, filepath=filepath, focus=focus, mode=mode)
            content = (
                f"<!-- AstPack Pruned Context (Tokens: {stats['pruned_tokens']:,} / Saved: {stats['reduction_pct']}%) -->\n"
                f"{pruned}"
            )
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "content": [{"type": "text", "text": content}]
                }
            }

        if tool_name == "astpack_pack":
            target = args.get("directory_path", ".")
            focus = args.get("focus")
            mode = args.get("mode") or ("focus" if focus else "stubs")
            pack_res = pack_repository(target_dir=target, focus_targets=focus, prune_mode=mode)
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "content": [{"type": "text", "text": pack_res["output_markdown"]}]
                }
            }

        if tool_name == "astpack_stats":
            target = args.get("directory_path", ".")
            pack_res = pack_repository(target_dir=target, prune_mode="stubs")
            report = (
                f"Repository Token Footprint:\n"
                f"- Files: {pack_res['files_count']}\n"
                f"- Original Tokens: {pack_res['original_tokens']:,}\n"
                f"- Pruned Tokens: {pack_res['pruned_tokens']:,}\n"
                f"- Potential Savings: {pack_res['saved_tokens']:,} ({pack_res['reduction_pct']}%)\n"
            )
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "content": [{"type": "text", "text": report}]
                }
            }

        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "error": {"code": -32601, "message": f"Method or tool not found: {tool_name}"}
        }

    return {
        "jsonrpc": "2.0",
        "id": req_id,
        "error": {"code": -32601, "message": f"Method not found: {method}"}
    }


def run_mcp_server():
    """Run MCP server over standard input and output."""
    while True:
        line = sys.stdin.readline()
        if not line:
            break
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
            res = handle_request(req)
            if res is not None:
                sys.stdout.write(json.dumps(res) + "\n")
                sys.stdout.flush()
        except Exception as e:
            err_res = {
                "jsonrpc": "2.0",
                "id": None,
                "error": {"code": -32700, "message": f"Parse error: {str(e)}"}
            }
            sys.stdout.write(json.dumps(err_res) + "\n")
            sys.stdout.flush()


if __name__ == "__main__":
    run_mcp_server()
