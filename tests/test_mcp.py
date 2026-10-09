import json
from astpack.mcp import handle_request


def test_mcp_initialize():
    req = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {}
    }
    res = handle_request(req)
    assert res["id"] == 1
    assert res["result"]["serverInfo"]["name"] == "astpack-mcp"
    assert "tools" in res["result"]["capabilities"]


def test_mcp_tools_list():
    req = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/list",
        "params": {}
    }
    res = handle_request(req)
    assert res["id"] == 2
    tools = res["result"]["tools"]
    tool_names = [t["name"] for t in tools]
    assert "astpack_prune" in tool_names
    assert "astpack_pack" in tool_names
    assert "astpack_stats" in tool_names


def test_mcp_tool_call_prune():
    code = """
def add(a: int, b: int) -> int:
    '''Add two numbers.'''
    res = a + b
    return res
"""
    req = {
        "jsonrpc": "2.0",
        "id": 3,
        "method": "tools/call",
        "params": {
            "name": "astpack_prune",
            "arguments": {
                "code": code,
                "filepath": "math_ops.py",
                "mode": "stubs"
            }
        }
    }
    res = handle_request(req)
    assert res["id"] == 3
    content = res["result"]["content"][0]["text"]
    assert "def add(a: int, b: int) -> int:" in content
    assert "..." in content
    assert "res = a + b" not in content
