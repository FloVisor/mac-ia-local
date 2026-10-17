#!/opt/homebrew/bin/python3
"""MCP stdio server delegating to the local muse-glimmer:30b-mlx model.

Non-destructive: uses the standard Ollama /v1 wire (no auth), never the
Codex /api/codex/v1 wire. Single model, no fallback, reasoning effort high.
"""
import datetime
import json
import os
import sys
import urllib.error
import urllib.request

MODEL = "muse-glimmer:30b-mlx"
BASE_URL = os.environ.get("LOCAL_LLM_MCP_BASE_URL", "http://127.0.0.1:11434/v1")
REASONING_EFFORT = "high"
REQUEST_TIMEOUT = int(os.environ.get("LOCAL_LLM_MCP_TIMEOUT", "600"))

PROFILES = {
    "analysis": (
        "You are a precise technical analyst. Break down the task, "
        "state facts separately from hypotheses, and give a structured answer."
    ),
    "coding": (
        "You are a careful coding agent. Produce minimal, correct, "
        "surgical changes. Follow the repository conventions provided in the task."
    ),
    "review": (
        "You are a rigorous code reviewer. Report only high-confidence "
        "issues with file, lines, and evidence. No style nitpicks."
    ),
    "testing": (
        "You are a testing agent. Identify the smallest test set covering "
        "the change. State exact commands and expected results."
    ),
    "documentation": (
        "You are a documentation writer. Be concise, factual, and consistent "
        "with existing document structure and terminology."
    ),
}


def log(msg):
    sys.stderr.write(f"[local-llm-mcp] {msg}\n")
    sys.stderr.flush()


def call_model(profile, task):
    if profile not in PROFILES:
        return None, f"Unknown profile '{profile}'. Valid: {', '.join(sorted(PROFILES))}."
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": PROFILES[profile]},
            {"role": "user", "content": task},
        ],
        "reasoning_effort": REASONING_EFFORT,
        "stream": False,
    }
    req = urllib.request.Request(
        BASE_URL.rstrip("/") + "/chat/completions",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as resp:
            data = json.load(resp)
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")[:500]
        return None, f"Local model HTTP {e.code}: {body}"
    except urllib.error.URLError as e:
        return None, (
            f"Local model '{MODEL}' unreachable at {BASE_URL}: {e.reason}. "
            "No fallback is configured by design; fix the local provider "
            "(Ollama on 127.0.0.1:11434) and retry."
        )
    try:
        msg = data["choices"][0]["message"]
        content = msg.get("content") or ""
        reasoning = msg.get("reasoning") or ""
        out = content.strip()
        if not out:
            return None, "Local model returned empty content."
        meta = f"[profile={profile} model={MODEL} reasoning_effort={REASONING_EFFORT}]"
        return f"{meta}\n\n{out}", None
    except (KeyError, IndexError, TypeError) as e:
        return None, f"Unexpected local model response shape: {e}"


TOOLS = [
    {
        "name": "delegate",
        "description": (
            "Delegate a self-contained task to the local LLM "
            f"({MODEL}, reasoning effort high). No fallback: if the model "
            "is unavailable, a clear error is returned."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "profile": {
                    "type": "string",
                    "enum": sorted(PROFILES),
                    "description": "Agent profile selecting the system prompt.",
                },
                "task": {
                    "type": "string",
                    "description": "Complete, self-contained task description with all needed context.",
                },
            },
            "required": ["profile", "task"],
        },
    }
]


def send(obj):
    sys.stdout.write(json.dumps(obj) + "\n")
    sys.stdout.flush()


def handle(request):
    method = request.get("method")
    req_id = request.get("id")
    if method == "initialize":
        send({
            "jsonrpc": "2.0", "id": req_id, "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "local-llm-mcp", "version": "1.0.0"},
            },
        })
    elif method == "notifications/initialized":
        pass
    elif method == "tools/list":
        send({"jsonrpc": "2.0", "id": req_id, "result": {"tools": TOOLS}})
    elif method == "tools/call":
        params = request.get("params", {})
        name = params.get("name")
        args = params.get("arguments", {})
        if name != "delegate":
            send({"jsonrpc": "2.0", "id": req_id, "error": {
                "code": -32601, "message": f"Unknown tool '{name}'"}})
            return
        result, err = call_model(args.get("profile", ""), args.get("task", ""))
        if err:
            send({"jsonrpc": "2.0", "id": req_id, "result": {
                "content": [{"type": "text", "text": f"ERROR: {err}"}],
                "isError": True}})
        else:
            send({"jsonrpc": "2.0", "id": req_id, "result": {
                "content": [{"type": "text", "text": result}]}})
    elif method == "ping":
        send({"jsonrpc": "2.0", "id": req_id, "result": {}})
    elif req_id is not None:
        send({"jsonrpc": "2.0", "id": req_id, "error": {
            "code": -32601, "message": f"Method not found: {method}"}})


def main():
    log(f"starting: model={MODEL} base_url={BASE_URL} effort={REASONING_EFFORT}")
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            handle(json.loads(line))
        except json.JSONDecodeError as e:
            log(f"invalid JSON line: {e}")


if __name__ == "__main__":
    main()
