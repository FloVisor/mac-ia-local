#!/usr/bin/env python3
"""Probe JSON-RPC stdio du MCP local-llm-mcp (garde de contexte).

Envoie initialize, tools/list, puis deux tools/call delegate :
  - tâche courte (acceptée, modèle réel)
  - tâche > 131072 tokens (rejetée par la garde, sans appel modèle)
"""
import json
import subprocess
import sys

BIN = "/Users/fngux2/.codex/bin/local-llm-mcp"


def run(requests):
    proc = subprocess.run(
        [BIN], input="\n".join(json.dumps(r) for r in requests) + "\n",
        capture_output=True, text=True, timeout=900,
    )
    return proc


def main():
    short = "Réponds uniquement par le mot OK."
    # ~150K tokens : répétition de mots courts, comptage réel côté serveur.
    huge = " ".join(["token"] * 150000)
    reqs = [
        {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}},
        {"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
        {"jsonrpc": "2.0", "id": 3, "method": "tools/call",
         "params": {"name": "delegate", "arguments": {"profile": "testing", "task": short}}},
        {"jsonrpc": "2.0", "id": 4, "method": "tools/call",
         "params": {"name": "delegate", "arguments": {"profile": "testing", "task": huge}}},
    ]
    proc = run(reqs)
    for line in proc.stdout.splitlines():
        obj = json.loads(line)
        if obj.get("id") == 4:
            text = obj["result"]["content"][0]["text"]
            obj["result"]["content"][0]["text"] = text[:300]
        print(json.dumps(obj, ensure_ascii=False))
    sys.stderr.write(proc.stderr)


if __name__ == "__main__":
    main()
