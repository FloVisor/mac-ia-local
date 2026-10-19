#!/opt/homebrew/bin/python3
"""MCP stdio server delegating to the local Qwen3.6-35B-A3B model on oMLX.

Non-destructive: uses the standard OpenAI /v1 wire of the local oMLX server
(authenticated, localhost only), never the Codex /api/codex/v1 wire.
Single model, no fallback. Reasoning: native thinking of Qwen3.6
(reasoning_effort is ignored by this model's template; no silent downgrade).
"""
import datetime
import json
import os
import sys
import urllib.error
import urllib.request

MODEL = "mlx-community--Qwen3.6-35B-A3B-4bit"
BASE_URL = os.environ.get("LOCAL_LLM_MCP_BASE_URL", "http://127.0.0.1:8000/v1")
REQUEST_TIMEOUT = int(os.environ.get("LOCAL_LLM_MCP_TIMEOUT", "600"))
# Garde locale : plafond de contexte des tâches déléguées (tokens réels, via /tokenize).
# Aligné sur le cap oMLX du modèle (131072 = 128K) et le catalogue Codex qwen36-omlx.
# Le plafond dur reste le serveur : prompt système + tâche > 131072 → 400.
MAX_TASK_TOKENS = int(os.environ.get("LOCAL_LLM_MCP_MAX_TASK_TOKENS", "131072"))


def _api_key():
    """Read the oMLX API key from its settings (single source of truth)."""
    key = os.environ.get("LOCAL_LLM_MCP_API_KEY")
    if key:
        return key
    path = os.path.expanduser("~/.omlx/settings.json")
    try:
        with open(path) as f:
            return json.load(f)["auth"]["api_key"]
    except (OSError, KeyError, ValueError):
        return None


def _headers():
    headers = {"Content-Type": "application/json"}
    api_key = _api_key()
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    return headers


def count_task_tokens(task):
    """Exact token count of the task via the server tokenizer (/tokenize).

    Returns (count, None) on success, (None, error) on failure — fail closed.
    """
    req = urllib.request.Request(
        BASE_URL.rstrip("/").removesuffix("/v1") + "/tokenize",
        data=json.dumps({"model": MODEL, "prompt": task}).encode(),
        headers=_headers(),
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as resp:
            return json.load(resp)["count"], None
    except (urllib.error.URLError, KeyError, ValueError) as e:
        return None, f"Token counting unavailable ({e}); refusing task without a real count."


# Thinking natif par profil : ON (raisonnement profond) pour analyse/code/review,
# OFF (reponse directe, ~x3 plus rapide) pour documentation et tests.
PROFILE_THINKING = {
    "analysis": True,
    "coding": True,
    "review": True,
    "testing": False,
    "documentation": False,
}

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
    count, err = count_task_tokens(task)
    if err:
        return None, err
    if count > MAX_TASK_TOKENS:
        return None, (
            f"Task is {count} tokens > local MCP limit {MAX_TASK_TOKENS} "
            "(real count via oMLX /tokenize). Split the task or delegate it "
            "directly through the model provider."
        )
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": PROFILES[profile]},
            {"role": "user", "content": task},
        ],
        "stream": False,
    }
    if not PROFILE_THINKING.get(profile, True):
        payload["chat_template_kwargs"] = {"enable_thinking": False}
    headers = _headers()
    req = urllib.request.Request(
        BASE_URL.rstrip("/") + "/chat/completions",
        data=json.dumps(payload).encode(),
        headers=headers,
        method="POST",
    )
    started = datetime.datetime.now(datetime.timezone.utc)
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
            "(oMLX on 127.0.0.1:8000, LaunchAgent org.gangneux.omlx-serve) "
            "and retry."
        )
    try:
        msg = data["choices"][0]["message"]
        content = msg.get("content") or ""
        out = content.strip()
        if not out:
            return None, "Local model returned empty content."
        rid = data.get("id", "n/a")
        usage = data.get("usage") or {}
        dur_ms = int((datetime.datetime.now(datetime.timezone.utc) - started).total_seconds() * 1000)
        meta = (
            f"[profile={profile} model={MODEL} server=oMLX:8000 "
            f"request_id={rid} duration_ms={dur_ms} "
            f"completion_tokens={usage.get('completion_tokens', 'n/a')}]"
        )
        return f"{meta}\n\n{out}", None
    except (KeyError, IndexError, TypeError) as e:
        return None, f"Unexpected local model response shape: {e}"


TOOLS = [
    {
        "name": "delegate",
        "description": (
            "Delegate a self-contained task to the local LLM "
            f"({MODEL} on oMLX, native thinking). Task is rejected above "
            f"{MAX_TASK_TOKENS} tokens (real count via oMLX /tokenize). "
            "No fallback: if the model is unavailable, a clear error is returned."
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
                "serverInfo": {"name": "local-llm-mcp", "version": "1.1.0"},
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
    log(f"starting: model={MODEL} base_url={BASE_URL} server=oMLX")
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
