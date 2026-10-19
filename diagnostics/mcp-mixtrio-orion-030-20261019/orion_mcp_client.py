#!/usr/bin/env python3
"""Client MCP minimal pour recetter orion 0.3.0 (lecture seule)."""
import json, sqlite3, sys, os, urllib.request, urllib.error

DB = os.path.expanduser("~/.openclaw/state/openclaw.sqlite")
store_json = sqlite3.connect(DB).execute(
    "SELECT store_json FROM mcp_oauth_stores WHERE store_key LIKE 'orion%'").fetchone()[0]
store = json.loads(store_json)
TOKEN = store["tokens"]["access_token"]
BASE = store["discoveryState"]["authorizationServerUrl"]  # .../mcp-front
URL = BASE + "/mcp"
SESSION = {"id": None}

def post(payload):
    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
    }
    if SESSION["id"]:
        headers["Mcp-Session-Id"] = SESSION["id"]
    req = urllib.request.Request(URL, data=json.dumps(payload).encode(), headers=headers)
    try:
        r = urllib.request.urlopen(req, timeout=120)
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")
        return {"http_error": e.code, "body": body[:2000]}
    sid = r.headers.get("Mcp-Session-Id")
    if sid:
        SESSION["id"] = sid
    raw = r.read().decode(errors="replace")
    ct = r.headers.get("Content-Type", "")
    if "text/event-stream" in ct:
        # parse SSE data lines
        for line in raw.splitlines():
            if line.startswith("data:"):
                return json.loads(line[5:].strip())
        return {"sse_empty": raw[:500]}
    return json.loads(raw) if raw.strip() else {}

def rpc(method, params=None):
    payload = {"jsonrpc": "2.0", "id": 1, "method": method}
    if params is not None:
        payload["params"] = params
    return post(payload)

def call_tool(name, args):
    return rpc("tools/call", {"name": name, "arguments": args})

def text_content(res):
    if "http_error" in res:
        return f"HTTP {res['http_error']}: {res['body'][:400]}"
    if res.get("error"):
        return f"JSONRPC error {res['error'].get('code')}: {json.dumps(res['error'], ensure_ascii=False)[:600]}"
    content = res.get("result", {}).get("content", [])
    parts = [c.get("text", json.dumps(c, ensure_ascii=False)) for c in content]
    return "\n".join(parts)

if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "init":
        r = rpc("initialize", {
            "protocolVersion": "2025-06-18",
            "capabilities": {},
            "clientInfo": {"name": "recette-orion-030", "version": "0.3.0"},
        })
        print(json.dumps(r, ensure_ascii=False, indent=1)[:1500])
        rpc("notifications/initialized")  # notification, réponse vide attendue
    elif cmd == "tools":
        print(text_content(rpc("tools/list")).replace("\\n", "\n")[:4000])
        r = rpc("tools/list")
        tools = r.get("result", {}).get("tools", [])
        print("NOMBRE:", len(tools))
        print([t["name"] for t in tools])
    else:
        args = json.loads(sys.argv[3]) if len(sys.argv) > 3 else {}
        print(text_content(call_tool(sys.argv[2], args)))