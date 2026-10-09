"""
Zero-dependency local Web Playground server for AstPack.
Provides interactive side-by-side code pruning visualization and token savings analytics.
"""

import http.server
import json
import socketserver
import webbrowser
from typing import Optional
from astpack.pruner import prune_code

HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AstPack Playground | AST Context Pruning for AI Agents</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/styles/atom-one-dark.min.css">
    <script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/highlight.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/languages/python.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/languages/typescript.min.js"></script>
    <style>
        :root {
            --bg: #0d1117;
            --surface: #161b22;
            --border: #30363d;
            --accent: #58a6ff;
            --green: #3fb950;
            --text: #c9d1d9;
            --text-muted: #8b949e;
        }
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            background-color: var(--bg);
            color: var(--text);
            display: flex;
            flex-direction: column;
            height: 100vh;
            overflow: hidden;
        }
        header {
            padding: 12px 24px;
            background: var(--surface);
            border-bottom: 1px solid var(--border);
            display: flex;
            align-items: center;
            justify-content: space-between;
        }
        .brand {
            display: flex;
            align-items: center;
            gap: 12px;
            font-size: 1.25rem;
            font-weight: 700;
            color: #fff;
        }
        .brand span { color: var(--accent); }
        .controls {
            display: flex;
            gap: 12px;
            align-items: center;
        }
        .stats-bar {
            display: flex;
            gap: 16px;
            background: #21262d;
            padding: 6px 14px;
            border-radius: 6px;
            font-size: 0.85rem;
        }
        .stat-item b { color: var(--green); }
        input, select, button {
            background: #21262d;
            border: 1px solid var(--border);
            color: #fff;
            padding: 6px 12px;
            border-radius: 6px;
            font-size: 0.85rem;
        }
        button {
            background: #238636;
            cursor: pointer;
            font-weight: 600;
            border: none;
            transition: opacity 0.2s;
        }
        button:hover { opacity: 0.9; }
        .workspace {
            display: grid;
            grid-template-columns: 1fr 1fr;
            flex: 1;
            overflow: hidden;
        }
        .pane {
            display: flex;
            flex-direction: column;
            border-right: 1px solid var(--border);
            overflow: hidden;
        }
        .pane-header {
            padding: 8px 16px;
            background: #1b2129;
            font-size: 0.8rem;
            color: var(--text-muted);
            border-bottom: 1px solid var(--border);
            display: flex;
            justify-content: space-between;
        }
        textarea {
            flex: 1;
            background: #0d1117;
            color: #e6edf3;
            border: none;
            padding: 16px;
            font-family: ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, monospace;
            font-size: 13px;
            line-height: 1.5;
            resize: none;
            outline: none;
        }
        pre {
            flex: 1;
            margin: 0;
            background: #0d1117;
            overflow: auto;
            padding: 16px;
            font-size: 13px;
            line-height: 1.5;
        }
        code { font-family: ui-monospace, SFMono-Regular, Menlo, monospace; }
        .copy-btn {
            background: #30363d;
            padding: 2px 8px;
            font-size: 0.75rem;
        }
    </style>
</head>
<body>
    <header>
        <div class="brand">
            🌳 Ast<span>Pack</span> Playground
        </div>
        <div class="stats-bar">
            <div>Original: <b id="stat-orig">0</b> tokens</div>
            <div>Pruned: <b id="stat-pruned">0</b> tokens</div>
            <div>Saved: <b id="stat-saved">0</b> (<b id="stat-pct">0%</b>)</div>
        </div>
        <div class="controls">
            <input type="text" id="focus-input" placeholder="Focus symbol (e.g. process_order)" value="process_order">
            <select id="mode-select">
                <option value="focus">Focus Mode</option>
                <option value="stubs">All Stubs</option>
            </select>
            <button onclick="triggerPrune()">Prune AST</button>
        </div>
    </header>
    <div class="workspace">
        <div class="pane">
            <div class="pane-header">
                <span>INPUT (RAW CODE)</span>
                <span>Python / TypeScript</span>
            </div>
            <textarea id="code-input" spellcheck="false">class PaymentGateway:
    def __init__(self, api_key: str):
        self.api_key = api_key

    def charge(self, amount: float, card_token: str) -> bool:
        '''Connects to banking gateway and charges credit card.'''
        print(f"Connecting to banking gateway...")
        if amount <= 0:
            raise ValueError("Invalid amount")
        return True

    def refund(self, tx_id: str, amount: float) -> bool:
        '''Issue refund to customer.'''
        return True

def calculate_shipping(weight_kg: float) -> float:
    '''Calculate shipping cost.'''
    return weight_kg * 1.5 + 5.0

def process_order(items: list, card_token: str, gateway: PaymentGateway) -> dict:
    '''
    Main business transaction function:
    Validates cart, charges customer, and logs order.
    '''
    total = 120.0
    shipping = calculate_shipping(weight_kg=2.5)
    success = gateway.charge(amount=total + shipping, card_token=card_token)
    return {"status": "ok", "total": total + shipping}</textarea>
        </div>
        <div class="pane">
            <div class="pane-header">
                <span>OUTPUT (SEMANTICALLY PRUNED AST)</span>
                <button class="copy-btn" onclick="copyOutput()">Copy for Claude/Cursor</button>
            </div>
            <pre><code id="code-output" class="language-python"></code></pre>
        </div>
    </div>

    <script>
        async function triggerPrune() {
            const code = document.getElementById('code-input').value;
            const focus = document.getElementById('focus-input').value.trim();
            const mode = document.getElementById('mode-select').value;

            try {
                const res = await fetch('/api/prune', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        code: code,
                        filepath: 'example.py',
                        focus: focus ? [focus] : [],
                        mode: mode
                    })
                });
                const data = await res.json();
                const outElem = document.getElementById('code-output');
                outElem.textContent = data.pruned;
                hljs.highlightElement(outElem);

                document.getElementById('stat-orig').innerText = data.stats.original_tokens.toLocaleString();
                document.getElementById('stat-pruned').innerText = data.stats.pruned_tokens.toLocaleString();
                document.getElementById('stat-saved').innerText = data.stats.saved_tokens.toLocaleString();
                document.getElementById('stat-pct').innerText = data.stats.reduction_pct + '%';
            } catch (err) {
                console.error(err);
            }
        }

        function copyOutput() {
            const text = document.getElementById('code-output').textContent;
            navigator.clipboard.writeText(text);
            alert('Pruned code copied to clipboard!');
        }

        document.getElementById('code-input').addEventListener('input', () => {
            clearTimeout(window._pruneDebounce);
            window._pruneDebounce = setTimeout(triggerPrune, 400);
        });

        triggerPrune();
    </script>
</body>
</html>
"""


class PlaygroundHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/" or self.path == "/index.html":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(HTML_TEMPLATE.encode("utf-8"))
        else:
            self.send_error(404, "Not Found")

    def do_POST(self):
        if self.path == "/api/prune":
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length)
            try:
                data = json.loads(body.decode("utf-8"))
                code = data.get("code", "")
                filepath = data.get("filepath", "example.py")
                focus = data.get("focus") or []
                mode = data.get("mode", "focus")

                pruned, stats = prune_code(code, filepath=filepath, focus=focus, mode=mode)

                res = json.dumps({"pruned": pruned, "stats": stats}).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(res)
            except Exception as e:
                err_res = json.dumps({"error": str(e)}).encode("utf-8")
                self.send_response(500)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(err_res)
        else:
            self.send_error(404, "Endpoint not found")

    def log_message(self, format, *args):
        # Quiet logger
        pass


def start_playground(port: int = 7860, open_browser: bool = True):
    """Starts local Playground HTTP server."""
    server_address = ("", port)
    with socketserver.TCPServer(server_address, PlaygroundHandler) as httpd:
        url = f"http://localhost:{port}"
        print(f"\n🌳 AstPack Playground running at: {url}")
        print("Press Ctrl+C to stop.\n")
        if open_browser:
            webbrowser.open(url)
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down server...")


if __name__ == "__main__":
    start_playground()
