"""Read-only metadata projection. No service calls, credentials, prompts or results."""
from contextlib import closing
import datetime as dt
import json
import math
import os
from pathlib import Path
import re
import sqlite3
import sys
import time

UUID = re.compile(r'^[0-9a-f-]{36}$', re.I)
ATOM = re.compile(r'^[a-zA-Z0-9_.:/ -]{1,160}$')
STATES = {'queued', 'running', 'completed', 'failed', 'cancelled', 'unknown'}
MAX_FILES = 200
MAX_LINE = 2 * 1024 * 1024
TAIL = 512 * 1024
RETENTION = 14 * 86400


def atom(value):
    return value if isinstance(value, str) and ATOM.fullmatch(value) and not re.search(r'(bearer|sk-|api.?key|token=)', value, re.I) else None


def ident(value):
    return value if isinstance(value, str) and UUID.fullmatch(value) else None


def number(value):
    return value if type(value) in (float, int) and math.isfinite(value) and value >= 0 else None


def stamp(value):
    try:
        return dt.datetime.fromisoformat(value.replace('Z', '+00:00')).timestamp()
    except (ValueError, TypeError, AttributeError):
        return None


def usage(value):
    return {k: number(v) for k, v in (value or {}).items() if k in {'input_tokens', 'output_tokens', 'total_tokens', 'prompt_tokens', 'completion_tokens', 'cached_input_tokens'}} if isinstance(value, dict) else None


class Collector:
    def __init__(self, home=None, db=None):
        self.home = Path(home or os.environ.get('CODEX_HOME', str(Path.home()/'.codex')))
        # Only Codex identity. Never discover or merge OpenClaw stores.
        self.db = Path(db or Path.home()/'.local/state/llm-router/codex/tasks.sqlite')
        self.cache = {}
        self.files = []
        self.scanned = 0

    def session(self, path):
        st = path.stat()
        sig = (st.st_ino, st.st_size, st.st_mtime_ns)
        cached = self.cache.get(str(path))
        if cached and cached[0] == sig:
            return self.temporal(dict(cached[1]), st.st_mtime)
        node = {'id': None, 'kind': 'session', 'parent': None, 'state': 'unknown', 'model': None,
                'provider': None, 'actual_model': None, 'cost_usd': None, 'usage': None,
                'connection': 'unknown', 'activity': None, 'started': None, 'updated': st.st_mtime,
                'history_partial': st.st_size > MAX_LINE + TAIL, 'history': [], 'router_submissions': []}
        with path.open('rb') as f:
            first = f.readline(MAX_LINE)
            if not first.endswith(b'\n'):
                return None  # do not infer metadata from a truncated JSON record
            try:
                r = json.loads(first)
            except ValueError:
                return None
            if r.get('type') != 'session_meta':
                return None
            p = r.get('payload', {})
            node['id'] = ident(p.get('id'))
            if not node['id']:
                return None
            src = p.get('source')
            if isinstance(src, dict) and isinstance(src.get('subagent'), dict) and src['subagent'].get('other') == 'guardian':
                return None  # automatic command review is not a task subagent
            spawn = ((src.get('subagent') or {}).get('thread_spawn') or {}) if isinstance(src, dict) and isinstance(src.get('subagent'), dict) else {}
            node['parent'] = ident(p.get('parent_thread_id')) or ident(spawn.get('parent_thread_id'))
            node['kind'] = 'native_subagent' if node['parent'] or isinstance(src, dict) and src.get('subagent') else 'session'
            node['source'] = atom(src) if isinstance(src, str) else 'subagent'
            node['runtime'] = atom(p.get('cli_version'))
            node['provider'] = atom(p.get('model_provider'))
            node['started'] = stamp(r.get('timestamp'))
            # Technical runtime labels only; never prompt text.
            node['role'] = atom(spawn.get('agent_role'))
            node['nickname'] = atom(spawn.get('agent_nickname'))
            node['agent_path'] = atom(spawn.get('agent_path'))
            node['model'] = atom(p.get('model'))
            remaining = st.st_size - f.tell()
            if remaining <= MAX_LINE + TAIL:
                data = f.read(MAX_LINE + TAIL)
            else:
                data = f.read(MAX_LINE)
                data = data[:data.rfind(b'\n')+1]
                f.seek(max(f.tell(), st.st_size - TAIL))
                f.readline(MAX_LINE)  # cut partial record
                data += f.read(TAIL)
        for line in data.splitlines():
            try:
                r = json.loads(line)
            except ValueError:
                continue
            p = r.get('payload') or {}
            if not isinstance(p, dict):
                continue
            ts = stamp(r.get('timestamp'))
            if node['kind'] == 'native_subagent' and ts and node['started'] and ts < node['started']:
                continue  # inherited fork history is not activity of the new agent
            if r.get('type') == 'turn_context':
                node['model'] = atom(p.get('model')) or node['model']
            elif r.get('type') == 'event_msg':
                typ = p.get('type')
                if typ == 'mcp_tool_call_end':
                    inv = p.get('invocation') or {}
                    result = (p.get('result') or {}).get('Ok') or {}
                    if inv.get('server') == 'llm-router' and inv.get('tool') in {'submit', 'delegate'} and not result.get('isError'):
                        for item in result.get('content', []):
                            try:
                                value = json.loads(item.get('text', ''))
                            except (ValueError, TypeError):
                                continue
                            if isinstance(value, dict) and value.get('identity') == 'codex' and ident(value.get('task_id')):
                                node['router_submissions'].append(value['task_id'])
                state = {'task_started':'running', 'turn_started':'running', 'task_complete':'completed', 'turn_complete':'completed', 'turn_aborted':'cancelled'}.get(typ)
                if state:
                    node['state'] = state
                    if ts is not None:
                        node['history'].append({'at': ts, 'state': state})
                        node['history'] = node['history'][-64:]
                    node['activity'] = typ
                    if state == 'running':
                        node['turn_started'] = ts
                        node.pop('turn_finished', None)
                    else:
                        node['turn_finished'] = ts
                if typ == 'token_count':
                    info = p.get('info') or {}
                    node['usage'] = usage(info.get('total_token_usage'))
            elif r.get('type') == 'response_item' and p.get('type') in {'function_call', 'custom_tool_call'}:
                name = p.get('name', '')
                # Only tool name, never arguments or response text.
                if 'local_llm' in name or 'local-llm' in name:
                    node['legacy_mcp_observed'] = True
                node['activity'] = atom(name) or node['activity']
        self.cache[str(path)] = (sig, dict(node))
        return self.temporal(node, st.st_mtime)

    @staticmethod
    def temporal(node, modified):
        if node['state'] == 'running' and time.time() - modified > 300:
            node['state'] = 'unknown'
        begin, end = node.get('turn_started'), node.get('turn_finished')
        node['duration_ms'] = max(0, ((end if end and begin and end >= begin else time.time()) - begin)*1000) if begin else None
        return node

    def router(self):
        if not self.db.exists():
            return [], 'absent'
        nodes = []
        # Read-only SQLite diagnostic projection; no Engine initialization or writes.
        with closing(sqlite3.connect(self.db.resolve().as_uri()+'?mode=ro', uri=True, timeout=1)) as c:
            c.execute('PRAGMA query_only=ON')
            rows = c.execute("SELECT id,state,created,updated,meta FROM tasks WHERE identity='codex' ORDER BY updated DESC").fetchall()
            for tid, state, created, updated, raw in rows:
                m = json.loads(raw)
                n = dict(id='router:'+tid, task_id=ident(tid), kind='mcp_delegation', parent=ident(m.get('parent_session')),
                         parent_evidence='router.parent_session (déclaré)', state=state if state in STATES else 'unknown',
                         started=number(created), updated=number(updated), profile=atom(m.get('profile')),
                         model=atom(m.get('requested_model')), alias=atom(m.get('selected_model')),
                         actual_model=None, provider=None, backend=atom(m.get('backend')), usage=usage(m.get('usage')),
                         cost_usd=number(m.get('cost_usd')), duration_ms=number(m.get('duration_ms')),
                         request_id=atom(m.get('request_id')), error='Erreur routeur (détail masqué)' if m.get('error') else None,
                         result_available=state in {'completed','failed'}, connection='unknown')
                # Only show known structured error codes, never arbitrary provider messages.
                if m.get('error') in {'truncated_or_invalid_completion','objective_quality_failed','paid_broker_not_connected','no_compatible_authorized_model','worker_interrupted','cancel_requested'}:
                    n['error'] = m['error']
                n['provenance'] = atom(m.get('provider_model_confirmation')) or 'unknown'
                # Response-model alone is not provider confirmation; keep unknown.
                n['response_model'] = atom(m.get('response_model'))
                n['history'] = [dict(at=number(at), state=s if s in STATES else 'unknown') for at,s in c.execute("SELECT at,state FROM events WHERE identity='codex' AND task_id=? ORDER BY seq DESC LIMIT 20", (tid,))][::-1]
                nodes.append(n)
        return nodes, 'read_only'

    def snapshot(self):
        now = time.time()
        if now-self.scanned > 30:
            self.files = sorted((self.home/'sessions').glob('*/*/*/rollout-*.jsonl'), key=lambda p:p.stat().st_mtime, reverse=True)[:MAX_FILES]
            self.scanned = now
        nodes, errors = [], []
        for p in self.files:
            try:
                if p.stat().st_mtime >= now-RETENTION:
                    n = self.session(p)
                    if n:
                        nodes.append(n)
            except (OSError, ValueError, TypeError):
                errors.append('session_read_failed')
        alive = {str(p) for p in self.files}
        self.cache = {k:v for k,v in self.cache.items() if k in alive}
        try:
            delegated, router_state = self.router()
            nodes.extend(delegated)
        except (sqlite3.Error, ValueError, OSError):
            router_state = 'unavailable'
            errors.append('router_read_failed')
        # Only a successful structured submit/delegate result identifies the creator.
        # Mentions, status/result reads and timestamp proximity establish no parentage.
        creators = {}
        for session in nodes:
            for tid in session.pop('router_submissions', []):
                creators.setdefault(tid, set()).add(session['id'])
        for task in delegated if router_state == 'read_only' else []:
            candidates = creators.get(task['task_id'], set())
            if not task['parent'] and len(candidates) == 1:
                task['parent'] = next(iter(candidates))
                task['parent_evidence'] = 'Codex session_meta.id + mcp_tool_call_end submit/delegate task_id'
            if not task['parent']:
                task['unattached'] = True
                task['parent_evidence'] = 'Aucune session parente fiable observée'
        unique = {n['id']:n for n in nodes}
        for n in list(unique.values()):
            parent = n.get('parent')
            if parent and parent not in unique:
                unique[parent] = dict(id=parent, kind='session_reference', parent=None,
                    state='unknown', model=None, provider=None, actual_model=None,
                    connection='unknown', reference_only=True,
                    evidence='Identifiant parent présent ; trace de session absente de la fenêtre')
        return dict(nodes=list(unique.values()), at=now, errors=sorted(set(errors)), router=router_state,
                    limits=dict(files=MAX_FILES, days=14, scan_seconds=30, poll_seconds=5),
                    scope='codex-only', connection='unknown')


if __name__ == '__main__':
    c = Collector()
    if '--once' in sys.argv:
        print(json.dumps(c.snapshot()))
    else:
        for line in sys.stdin:
            if line.strip() == 'refresh':
                print(json.dumps(c.snapshot()), flush=True)
