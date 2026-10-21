"""Reuse the shared read-only collector; never start an MCP or inference engine."""
from collector import Collector
import json
import os
import sys

home = os.environ.get('AGENT_STANDUP_CODEX') or os.environ.get('CODEX_HOME')
db = os.environ.get('P3C_ROUTER_DB')  # explicit fixture override; Codex identity remains fixed
collector = Collector(home=home, db=db)
for line in sys.stdin:
    if line.strip() == 'refresh':
        try:
            print(json.dumps(collector.snapshot()), flush=True)
        except Exception:
            print(json.dumps({'nodes': [], 'errors': ['collector_failed']}), flush=True)
