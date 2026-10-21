#!/usr/bin/env python3
"""Independent, stdlib-only MCP task router. No client configuration changes."""
import argparse
import email.utils
import fcntl
import hashlib
import http.client
import json
import math
import os
import re
from pathlib import Path
import socket
import stat
import sqlite3
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid

PROFILES = {
    'analysis': 'Precise technical analyst: separate facts and hypotheses; structured answer.',
    'coding': 'Careful coding agent: minimal correct changes, following supplied conventions.',
    'review': 'Rigorous reviewer: only high-confidence issues with locations and evidence.',
    'testing': 'Testing agent: smallest meaningful tests, exact commands and expected results.',
    'documentation': 'Documentation writer: concise, factual, faithful to supplied sources.',
}
LEVELS = {'off': 0, 'minimal': 0, 'low': 512, 'medium': 2048,
          'high': 8192, 'max': 16384, 'ultra': 8192}
TERMINAL = ('completed', 'failed', 'cancelled', 'unknown')
LOCAL = 'local-omlx/mlx-community--Qwen3.6-35B-A3B-4bit'
DISABLED = 'local-ollama/muse-glimmer:30b-mlx'

def contains_secrets(args):
    """Defence in depth; callers must label opaque/unrecognisable secrets too."""
    return args.get('contains_secrets', False) or bool(re.search(
        r'-----BEGIN (?:[A-Z0-9]+ )*PRIVATE KEY-----|'
        r'\b(?:password|passwd|mot de passe|token|api[_ -]?key|client[_ -]?secret)'
        r'[\s\"\x27]*[:=][\s\"\x27]*\S+|\bBearer\s+\S+|'
        r'\b(?:sk-[A-Za-z0-9_-]{16,}|gh[pousr]_[A-Za-z0-9_]{16,})',
        args['task'], re.IGNORECASE))

AUTO_ANSWER_MAX = 8192
AUTO_ANSWER_FLOORS = dict(analysis=3072, review=3072, diagnosis=3072,
    comparison=3072, synthesis=3072, architecture=3072, documentation=3072,
    coding=4096, testing=2048)

def output_budget(args, model_id):
    """Caller caps stay caps; absent caps get a bounded, task-sized local reserve.

    A supplied integer is not evidence of a human instruction. Legacy callers
    nevertheless retain their hard-cap contract unless they explicitly opt into
    auto mode, where that integer is an adjustable answer-reserve hint.
    """
    requested = args.get('max_output_tokens')
    mode = args.get('output_budget_mode', 'hard' if requested is not None else 'auto')
    if mode not in ('auto', 'hard') or (mode == 'hard' and requested is None):
        raise Fault('invalid_output_budget_mode')
    answer = requested if requested is not None else 2048
    source = 'caller' if requested is not None else 'default'
    if model_id == LOCAL and mode == 'auto':
        task_type = args.get('task_type', args['profile'])
        floor = AUTO_ANSWER_FLOORS[task_type]
        if len(args['task'].encode('utf-8')) >= 12000:
            floor = max(floor, 6144)
        answer = max(answer, floor, args.get('_auto_answer_tokens', 0))
        if answer > AUTO_ANSWER_MAX:
            raise Fault('auto_output_budget_too_large')
        source = 'recovery_policy' if '_auto_answer_tokens' in args else 'caller_hint' if requested is not None else 'task_policy'
    thinking = LEVELS[args.get('reasoning', 'medium').lower()] if model_id == LOCAL else 0
    # Observed oMLX accounting includes one thinking-boundary token (2049 for
    # budget 2048, 513 for 512). Reserve it outside the answer allowance.
    boundary = int(thinking > 0)
    return dict(mode=mode, source=source, requested_answer_tokens=requested,
                answer_tokens=answer, thinking_tokens=thinking,
                thinking_boundary_tokens=boundary,
                max_tokens_sent=answer + thinking + boundary)

def generation_limit(args, model_id):
    return output_budget(args, model_id)['max_tokens_sent']

class Fault(Exception):
    def __init__(self, code, status=None, retry_after=None, uncertain=False):
        super().__init__(code)
        self.code, self.status, self.retry_after, self.uncertain = code, status, retry_after, uncertain


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def request(url, key=None, payload=None, timeout=20):
    """Never log request content, credentials or provider error bodies. No redirects/retries."""
    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, *args):
            return None
    headers = {'Content-Type': 'application/json'}
    if key:
        headers['Authorization'] = 'Bearer ' + key
    req = urllib.request.Request(url, headers=headers,
        data=None if payload is None else json.dumps(payload).encode())
    try:
        with urllib.request.build_opener(NoRedirect).open(req, timeout=timeout) as res:
            data = json.load(res)
            if not isinstance(data, dict):
                raise Fault('invalid_response')
            cost = res.headers.get('x-litellm-response-cost')
            return data, cost
    except urllib.error.HTTPError as exc:
        raw = exc.headers.get('Retry-After')
        retry = None
        if raw:
            try:
                retry = time.time() + max(0, float(raw))
            except ValueError:
                try:
                    retry = email.utils.parsedate_to_datetime(raw).timestamp()
                except (TypeError, ValueError):
                    pass
        exc.close()
        raise Fault('http_' + str(exc.code), exc.code, retry) from None
    except (TimeoutError, socket.timeout):
        raise Fault('transport_timeout', uncertain=payload is not None) from None
    except urllib.error.URLError:
        # Cannot distinguish failure before/after request acceptance: never retry inference.
        raise Fault('transport_unavailable', uncertain=payload is not None) from None
    except (ValueError, OSError, http.client.HTTPException):
        raise Fault('invalid_or_interrupted_response', uncertain=payload is not None) from None


def stream_chat(url, key, payload, connect_timeout=20, inactivity_timeout=None, progress=None):
    """SSE: bounded connect, independently configurable idle timeout, no generation cap."""
    parsed = urllib.parse.urlparse(url)
    cls = http.client.HTTPSConnection if parsed.scheme == 'https' else http.client.HTTPConnection
    conn = cls(parsed.hostname, parsed.port, timeout=connect_timeout)
    sent = False
    try:
        conn.connect()
        conn.sock.settimeout(inactivity_timeout)
        payload = payload | {'stream':True,'stream_options':{'include_usage':True}}
        sent = True
        conn.request('POST',parsed.path,body=json.dumps(payload).encode(),
            headers={'Content-Type':'application/json','Authorization':'Bearer '+key})
        resp = conn.getresponse()
        if resp.status != 200:
            retry = resp.getheader('Retry-After')
            until = None
            if retry:
                try:
                    until = time.time()+max(0,float(retry))
                except ValueError:
                    try:
                        until = email.utils.parsedate_to_datetime(retry).timestamp()
                    except (TypeError,ValueError):
                        pass
            raise Fault('http_'+str(resp.status),resp.status,until)
        cost = resp.getheader('x-litellm-response-cost')
        routing_headers = {k:resp.getheader(k) for k in ('x-litellm-call-id','x-litellm-model-id','x-litellm-attempted-retries','x-litellm-attempted-fallbacks') if resp.getheader(k) is not None}
        if 'text/event-stream' not in (resp.getheader('Content-Type') or ''):
            data = json.load(resp)
            data['_routing_headers'] = routing_headers
            return data,cost
        text,model,usage,finish,done = [],None,{},None,False
        request_id = None
        last = 0
        while True:
            line = resp.readline()
            if not line:
                break
            if progress and time.monotonic()-last > .5:
                progress()
                last = time.monotonic()
            if not line.startswith(b'data:'):
                continue
            chunk = line[5:].strip()
            if chunk == b'[DONE]':
                done = True
                break
            obj = json.loads(chunk)
            if obj.get('error'):
                raise Fault('upstream_stream_error',uncertain=True)
            request_id = obj.get('id') or request_id
            model = obj.get('model') or model
            usage = obj.get('usage') or usage
            for choice in obj.get('choices',[]):
                if choice.get('index',0) != 0:
                    continue
                delta = choice.get('delta') or {}
                if delta.get('tool_calls'):
                    raise Fault('tool_result_requires_orchestrator')
                if delta.get('content'):
                    text.append(delta['content'])
                finish = choice.get('finish_reason') or finish
        if not done:
            raise Fault('stream_interrupted',uncertain=True)
        return dict(id=request_id,_routing_headers=routing_headers,model=model,usage=usage,choices=[dict(finish_reason=finish,message={'content':''.join(text)})]),cost
    except Fault:
        raise
    except (TimeoutError,socket.timeout):
        raise Fault('inactivity_timeout' if sent else 'connect_timeout',uncertain=sent) from None
    except (OSError,ValueError,TypeError,http.client.HTTPException):
        raise Fault('stream_transport_error',uncertain=sent) from None
    finally:
        conn.close()


def load_config(path):
    config = json.loads(Path(path).read_text())
    if config.get('identity') not in ('codex', 'openclaw-pro', 'openclaw-perso', 'isolated-test'):
        raise Fault('invalid_server_identity')
    for name in ('litellm_url', 'local_url'):
        url = config.get(name)
        if url:
            parsed = urllib.parse.urlparse(url)
            if parsed.username or parsed.password or parsed.query or parsed.fragment:
                raise Fault('unsafe_url')
            if parsed.scheme != 'https' and not (parsed.scheme == 'http' and parsed.hostname in ('127.0.0.1', 'localhost', '::1')):
                raise Fault('https_required')
    return config


class Engine:
    def __init__(self, config):
        self.c = config
        root = Path(config['state_dir']).expanduser()
        root.mkdir(parents=True, exist_ok=True, mode=0o700)
        os.chmod(root, 0o700)
        self.root = root
        marker = root / 'identity.json'
        try:
            with marker.open('x') as f:
                json.dump(config['identity'], f)
        except FileExistsError:
            if json.loads(marker.read_text()) != config['identity']:
                raise Fault('state_identity_mismatch')
        self.db = sqlite3.connect(root / 'tasks.sqlite', timeout=10)
        os.chmod(root / 'tasks.sqlite', 0o600)
        self.db.row_factory = sqlite3.Row
        self.db.executescript('''
        CREATE TABLE IF NOT EXISTS tasks (
          id TEXT PRIMARY KEY, identity TEXT NOT NULL, dedupe TEXT NOT NULL,
          state TEXT NOT NULL, created REAL NOT NULL, updated REAL NOT NULL,
          request TEXT NOT NULL, output TEXT, meta TEXT NOT NULL,
          UNIQUE(identity,dedupe));
        CREATE TABLE IF NOT EXISTS events (
          seq INTEGER PRIMARY KEY AUTOINCREMENT, task_id TEXT, identity TEXT,
          at REAL, state TEXT, meta TEXT);
        CREATE TABLE IF NOT EXISTS breakers (
          scope TEXT PRIMARY KEY, cause TEXT, since REAL, expires REAL,
          last_success REAL, last_failure REAL);
        CREATE TABLE IF NOT EXISTS cache (name TEXT PRIMARY KEY, at REAL, value TEXT);
        ''')
        self.db.commit()

    def event(self, task_id, state, meta):
        self.db.execute('INSERT INTO events(task_id,identity,at,state,meta) VALUES(?,?,?,?,?)',
            (task_id, self.c['identity'], time.time(), state, json.dumps(meta)))
        keep = max(1, int(self.c.get('history_limit', 1000)))
        self.db.execute('DELETE FROM events WHERE seq NOT IN (SELECT seq FROM events ORDER BY seq DESC LIMIT ?)', (keep,))

    def prune(self):
        # Keep active/uncertain work. Terminal payload retention is independently bounded.
        cutoff = time.time() - self.c.get('retention_seconds', 86400)
        self.db.execute("DELETE FROM tasks WHERE identity=? AND state IN ('completed','failed','cancelled') AND (updated<? OR id IN (SELECT id FROM tasks WHERE identity=? AND state IN ('completed','failed','cancelled') ORDER BY updated DESC LIMIT -1 OFFSET ?))",
            (self.c['identity'], cutoff, self.c['identity'], self.c.get('task_history_limit', 100)))
        self.db.commit()

    def get(self, tid):
        row = self.db.execute('SELECT * FROM tasks WHERE id=? AND identity=?', (tid, self.c['identity'])).fetchone()
        if not row:
            raise Fault('task_not_found')
        return row

    def update(self, tid, state, meta=None, output=None):
        row = self.get(tid)
        if row['state'] == 'cancel_requested' and state == 'running':
            state = 'cancel_requested'
        combined = json.loads(row['meta'])
        combined.update(meta or {})
        now = time.time()
        combined['duration_ms'] = int((now - row['created']) * 1000)
        self.db.execute('UPDATE tasks SET state=?,updated=?,meta=?,output=COALESCE(?,output) WHERE id=? AND identity=?',
            (state, now, json.dumps(combined), output, tid, self.c['identity']))
        self.event(tid, state, combined)
        self.db.commit()

    def submit(self, args):
        allowed = {'profile','task','model','allow_cloud','confidentiality','reasoning','required_capabilities',
                   'context_tokens','max_output_tokens','deadline','parent_session','idempotency_key','quality','paid_authorization',
                   'contains_secrets','complexity','task_type','output_budget_mode'}
        if set(args) - allowed:
            raise Fault('unsupported_argument')
        if args.get('profile') not in PROFILES or not isinstance(args.get('task'), str) or not args['task'].strip():
            raise Fault('invalid_task')
        if args.get('confidentiality', 'local') not in ('local', 'cloud-approved'):
            raise Fault('invalid_confidentiality')
        if 'contains_secrets' in args and type(args['contains_secrets']) is not bool:
            raise Fault('invalid_contains_secrets')
        if args.get('complexity', 'standard') not in ('trivial','standard','advanced','strategic'):
            raise Fault('invalid_complexity')
        if args.get('task_type', args['profile']) not in (*PROFILES, 'diagnosis','comparison','synthesis','architecture'):
            raise Fault('invalid_task_type')
        if args.get('model') and args['model'] not in self.c.get('models',{}):
            raise Fault('unknown_requested_model')
        if args.get('reasoning', 'medium').lower() not in LEVELS:
            raise Fault('invalid_reasoning')
        for field in ('context_tokens', 'max_output_tokens'):
            if field in args and (type(args[field]) is not int or args[field] <= 0):
                raise Fault('invalid_' + field)
        if args.get('output_budget_mode', 'auto') not in ('auto', 'hard') or (args.get('output_budget_mode') == 'hard' and 'max_output_tokens' not in args):
            raise Fault('invalid_output_budget_mode')
        for field in ('model','parent_session','idempotency_key','paid_authorization'):
            if field in args and (not isinstance(args[field], str) or len(args[field]) > 256):
                raise Fault('invalid_' + field)
        if set(args.get('required_capabilities',[])) & {'tools','vision'}:
            raise Fault('structured_tools_or_vision_input_not_supported')
        if 'deadline' in args and (type(args['deadline']) not in (float,int) or not math.isfinite(args['deadline'])):
            raise Fault('invalid_deadline')
        if 'allow_cloud' in args and type(args['allow_cloud']) is not bool:
            raise Fault('invalid_allow_cloud')
        if not isinstance(args.get('required_capabilities', []), list) or any(x not in ('tools','json','vision') for x in args.get('required_capabilities', [])):
            raise Fault('invalid_capabilities')
        quality = args.get('quality', {})
        if not isinstance(quality, dict) or set(quality) - {'kind','required','expected'}:
            raise Fault('invalid_quality')
        if quality.get('kind') not in (None,'json','python','exact'):
            raise Fault('unsupported_quality_check')
        if 'required' in quality and (not isinstance(quality['required'], list) or any(not isinstance(k,str) for k in quality['required'])):
            raise Fault('invalid_quality_required')
        policy = digest(self.c)
        key = digest([args, policy])
        if args.get('idempotency_key'):
            # Same supplied key with different request/policy is a conflict, never a new inference.
            key = digest(['explicit', args['idempotency_key']])
        previous = self.db.execute('SELECT id,request,meta FROM tasks WHERE identity=? AND dedupe=?', (self.c['identity'], key)).fetchone()
        if previous:
            if json.loads(previous['request']) != args or json.loads(previous['meta'])['policy'] != policy:
                raise Fault('idempotency_conflict')
            return self.status(previous['id'])
        self.prune()
        if self.db.execute("SELECT COUNT(*) FROM tasks WHERE state NOT IN ('completed','failed','cancelled')").fetchone()[0] >= self.c.get('max_pending', 100):
            raise Fault('queue_full')
        tid, now = str(uuid.uuid4()), time.time()
        meta = dict(profile=args['profile'], parent_session=args.get('parent_session'),
            task_type=args.get('task_type',args['profile']), complexity=args.get('complexity','standard'),
            secret_local_only=bool(contains_secrets(args)),
            requested_model=args.get('model'), actual_model=None, backend=None, usage=None,
            cost_usd=None, error=None, cooldown=None, paid_authorization=None,
            authorization_mode='DELEGATED', policy=policy, duration_ms=0)
        try:
            self.db.execute('INSERT INTO tasks VALUES(?,?,?,?,?,?,?,?,?)',
                (tid, self.c['identity'], key, 'queued', now, now, json.dumps(args), None, json.dumps(meta)))
            self.event(tid, 'queued', meta)
            self.db.commit()
        except sqlite3.IntegrityError:
            self.db.rollback()
            return self.submit(args)
        return self.status(tid)

    def status(self, tid):
        r = self.get(tid)
        return dict(task_id=tid, identity=r['identity'], state=r['state'], created=r['created'],
                    updated=r['updated'], **json.loads(r['meta']))

    def result(self, tid, offset=0, limit=4000):
        if type(offset) is not int or offset < 0 or type(limit) is not int or not 1 <= limit <= 16000:
            raise Fault('invalid_page')
        r = self.get(tid)
        text = r['output'] or ''
        return dict(task_id=tid, state=r['state'], text=text[offset:offset+limit],
                    next_offset=offset+limit if offset+limit < len(text) else None, total_chars=len(text))

    def cancel(self, tid):
        r = self.get(tid)
        if r['state'] == 'queued':
            with self.db:
                changed = self.db.execute("UPDATE tasks SET state='cancelled',updated=? WHERE id=? AND identity=? AND state='queued'", (time.time(),tid,self.c['identity'])).rowcount
                if changed:
                    self.event(tid, 'cancelled', json.loads(r['meta']))
            if changed:
                return self.status(tid)
        r = self.get(tid)
        if r['state'] == 'running':
            self.update(tid, 'cancel_requested')
        return self.status(tid)

    def activity(self, after=0, limit=100):
        if type(after) is not int or after < 0 or type(limit) is not int or not 1 <= limit <= 200:
            raise Fault('invalid_page')
        rows = self.db.execute('SELECT * FROM events WHERE identity=? AND seq>? ORDER BY seq LIMIT ?', (self.c['identity'],after,limit)).fetchall()
        minimum = self.db.execute('SELECT MIN(seq) FROM events WHERE identity=?', (self.c['identity'],)).fetchone()[0]
        return dict(events=[dict(r, meta=json.loads(r['meta'])) for r in rows],
            next_cursor=rows[-1]['seq'] if rows else after, history_truncated=bool(minimum and after < minimum-1),
            active=[self.status(r[0]) for r in self.db.execute("SELECT id FROM tasks WHERE identity=? AND state IN ('queued','running','cancel_requested','unknown')", (self.c['identity'],))])

    def key(self):
        # A configured private file takes precedence: never fall back to another identity.
        if self.c.get('key_file'):
            path = Path(self.c['key_file']).expanduser()
            try:
                fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
                with os.fdopen(fd) as source:
                    info = os.fstat(source.fileno())
                    if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid() or info.st_mode & 0o077:
                        raise Fault('litellm_credential_file_not_private')
                    value = source.read().strip()
            except OSError:
                raise Fault('litellm_credential_file_unavailable') from None
        else:
            value = os.environ.get(self.c.get('key_env', 'LLM_ROUTER_LITELLM_KEY'))
        if not value:
            raise Fault('litellm_credentials_missing')
        return value

    def blocked(self, scope):
        r = self.db.execute('SELECT * FROM breakers WHERE scope=?', (scope,)).fetchone()
        return dict(r) if r and (r['expires'] is None or r['expires'] > time.time()) else None

    def trip(self, scope, fault):
        self.db.execute('INSERT INTO breakers VALUES(?,?,?,?,?,?) ON CONFLICT(scope) DO UPDATE SET cause=excluded.cause,since=excluded.since,expires=excluded.expires,last_failure=excluded.last_failure',
            (scope, fault.code, time.time(), fault.retry_after, None, time.time()))
        self.db.commit()

    def catalogue(self, refresh=False):
        scope = 'credential:' + self.c['identity']
        if self.blocked(scope):
            raise Fault('credential_suspended')
        policy = digest(self.c)
        cache = self.db.execute("SELECT at,value FROM cache WHERE name=?", ('catalogue:' + policy,)).fetchone()
        if cache and not refresh and time.time()-cache['at'] < self.c.get('catalogue_ttl', 0):
            return json.loads(cache['value'])
        # No stale catalogue fallback: an outage cannot prove a model is still authorized.
        if not self.c.get('litellm_url'):
            if not self.c.get('isolated_local_only'):
                raise Fault('litellm_not_configured')
            return [self.c['models'][LOCAL] | {'id': LOCAL}]
        try:
            data, _ = request(self.c['litellm_url'].rstrip('/')+'/models', self.key())
        except Fault as exc:
            if exc.status in (401,403):
                self.trip(scope, exc)
            raise
        models = []
        if not isinstance(data.get('data'), list):
            raise Fault('invalid_catalogue')
        # Only client-visible ids, enriched by operator-qualified metadata. Unknowns denied.
        for entry in data['data']:
            mid = entry.get('id') if isinstance(entry,dict) else None
            info = self.c.get('models', {}).get(mid)
            if info and mid != DISABLED and info.get('enabled') and info.get('kind') in ('chat','pool'):
                models.append(info | {'id': mid})
        self.db.execute('INSERT OR REPLACE INTO cache VALUES(?,?,?)', ('catalogue:'+policy,time.time(),json.dumps(models)))
        self.db.commit()
        return models

    def select(self, args, exclude=()):
        if args.get('complexity') in ('trivial','strategic'):
            raise Fault('orchestrator_required')
        models = self.catalogue()
        candidates = []
        for m in models:
            if not m.get('enabled') or m['id'] == DISABLED or m.get('kind') not in ('chat','pool'):
                continue
            if args.get('model') and m['id'] != args['model']:
                continue
            if m['id'] in exclude:
                continue
            backend = m.get('backend')
            if backend not in ('local','free','paid'):
                continue
            if backend == 'paid' and not args.get('model'):
                continue  # Never propose a paid route automatically.
            if backend != 'local' and contains_secrets(args):
                continue
            if backend != 'local' and not (self.c.get('allow_cloud') and args.get('allow_cloud') and args.get('confidentiality') == 'cloud-approved'):
                continue
            if not set(args.get('required_capabilities',[])) <= set(m.get('verified_capabilities',[])):
                continue
            task_type = args.get('task_type', args['profile'])
            if args.get('complexity') == 'advanced' and task_type not in m.get('qualified_advanced_tasks',[]):
                continue
            # Conservative UTF-8 byte bound, plus messages and reserved completion; no chars/4 guess.
            required = max(args.get('context_tokens',0),len((PROFILES[args['profile']]+args['task']).encode())+256) + generation_limit(args, m['id'])
            if required > m.get('context',0):
                continue
            if m['kind'] == 'pool':
                members = m.get('members',[])
                by_id = {x['id']:x for x in models}
                if not members or any(x not in by_id for x in members):
                    continue
                if any(by_id[x].get('kind') != 'chat' or by_id[x].get('backend') != backend or required > by_id[x].get('context',0) or not set(args.get('required_capabilities',[])) <= set(by_id[x].get('verified_capabilities',[])) or (args.get('complexity') == 'advanced' and task_type not in by_id[x].get('qualified_advanced_tasks',[])) or x in exclude or self.blocked('model:'+x) or (by_id[x].get('provider') and self.blocked('provider:'+by_id[x]['provider'])) for x in members):
                    continue
            if self.blocked('model:'+m['id']) or (m.get('provider') and self.blocked('provider:'+m['provider'])):
                continue
            candidates.append(m)
        if not candidates:
            raise Fault('no_compatible_authorized_model')
        return sorted(candidates,key=lambda m: (('local','free','paid').index(m['backend']), m['kind']=='pool', m['id']))[0]

    def infer(self, args, model, progress=None):
        mid = model['id']
        if model['backend'] != 'local' and contains_secrets(args):
            raise Fault('secret_requires_local')
        if model['backend'] == 'paid':
            # The ordinary worker owns no paid credential and cannot mint or accept grants.
            raise Fault('paid_broker_not_connected')
        level = args.get('reasoning','medium').lower()
        payload = dict(model=mid, messages=[{'role':'system','content':PROFILES[args['profile']]}, {'role':'user','content':args['task']}], stream=False, max_tokens=generation_limit(args, mid))
        # Groq documents JSON object mode for all its chat models. Keep validation
        # strict: never strip fences to turn a failed response into a success.
        if args.get('quality',{}).get('kind') == 'json' and model.get('provider') == 'groq':
            payload['response_format'] = {'type':'json_object'}
            payload['messages'][0]['content'] += ' Return only a valid JSON object.'
        reasoning = dict(requested=level, sent=None, confirmed=None, adaptation=None)
        if mid == LOCAL:
            payload['chat_template_kwargs'] = {'enable_thinking': LEVELS[level] > 0}
            if LEVELS[level]:
                payload['thinking_budget'] = LEVELS[level]
            reasoning.update(sent={'chat_template_kwargs':payload['chat_template_kwargs'], 'thinking_budget':payload.get('thinking_budget')}, adaptation='ultra_to_high' if level == 'ultra' else None)
        elif level != 'off':
            reasoning['adaptation'] = 'unsupported_not_sent'
        if self.c.get('isolated_local_only'):
            if mid != LOCAL or model['backend'] != 'local':
                raise Fault('local_rescue_not_authorized')
            payload['model'] = mid.split('/',1)[1]
            url, key = self.c['local_url'], os.environ.get(self.c.get('local_key_env','LLM_ROUTER_LOCAL_KEY'))
            if not key:
                raise Fault('local_credentials_missing')
        else:
            url,key = self.c['litellm_url'],self.key()
        data, cost = stream_chat(url.rstrip('/')+'/chat/completions', key, payload,
            connect_timeout=self.c.get('connect_timeout',20),
            inactivity_timeout=self.c.get('inactivity_timeout'), progress=progress)
        try:
            choice = data['choices'][0]
            content = choice['message'].get('content')
            finish = choice.get('finish_reason')
            actual = data.get('model')
            if not isinstance(actual,str) or not actual:
                raise Fault('missing_actual_model')
            usage = data.get('usage') or {}
            details = usage.get('completion_tokens_details') or {}
            usage = {k:v for k,v in usage.items() if k in ('prompt_tokens','completion_tokens','total_tokens') and type(v) is int and v >= 0}
            if isinstance(details, dict) and type(details.get('reasoning_tokens')) is int and details['reasoning_tokens'] >= 0:
                usage['completion_tokens_details'] = {'reasoning_tokens':details['reasoning_tokens']}
            result_meta = dict(actual_model=actual if actual not in self.c.get('models',{}) else None,
                        response_model=actual, provider_model_confirmation='response_model' if actual not in self.c.get('models',{}) else 'alias_only_unconfirmed',
                        request_id=data.get('id'), routing_headers=data.get('_routing_headers',{}),
                        usage=usage, finish_reason=finish,
                        cost_usd=float(cost) if cost is not None and math.isfinite(float(cost)) else None,
                        reasoning=reasoning, quality='not_checked',
                        generation_limits=output_budget(args, mid),
                        output_format_sent=payload.get('response_format'))
            if finish != 'stop' or not isinstance(content,str) or not content.strip():
                fault = Fault('completion_truncated' if finish == 'length' else
                              'empty_completion' if finish == 'stop' else 'unexpected_finish_reason')
                fault.result_meta = result_meta
                if isinstance(content, str):
                    fault.rejected_output = content
                raise fault
            try:
                self.validate(content,args.get('quality',{}))
            except Fault as exc:
                exc.result_meta = result_meta | {'quality':'failed'}
                # Preserve rejected content privately for diagnosis, never in activity/events.
                exc.rejected_output = content
                raise
            result_meta['quality'] = 'passed' if args.get('quality') else 'not_checked'
            return content, result_meta
        except (KeyError,IndexError,TypeError,ValueError):
            raise Fault('invalid_completion_shape') from None

    @staticmethod
    def validate(content, rule):
        import ast
        try:
            if rule.get('kind') == 'json':
                obj = json.loads(content)
                if not isinstance(obj,dict) or not set(rule.get('required',[])) <= set(obj):
                    raise ValueError()
            elif rule.get('kind') == 'python':
                ast.parse(content)  # No execution of generated code.
            elif rule.get('kind') == 'exact' and content.strip() != str(rule['expected']).strip():
                raise ValueError()
        except (ValueError,SyntaxError,KeyError):
            raise Fault('objective_quality_failed') from None

    def run_one(self):
        with self.db:
            row = self.db.execute("SELECT * FROM tasks WHERE identity=? AND state='queued' ORDER BY created LIMIT 1", (self.c['identity'],)).fetchone()
            if not row:
                return False
            if not self.db.execute("UPDATE tasks SET state='running' WHERE id=? AND state='queued'", (row['id'],)).rowcount:
                return True
        tid = row['id']
        args = json.loads(row['request'])
        self.update(tid,'running',dict(started_at=time.time(),
            task_type=args.get('task_type',args['profile']),complexity=args.get('complexity','standard'),
            secret_local_only=bool(contains_secrets(args))))
        model = None
        try:
            if json.loads(row['meta'])['policy'] != digest(self.c):
                raise Fault('policy_changed_resubmit_required')
            if args.get('deadline') and time.time() >= args['deadline']:
                raise Fault('deadline_expired')
            model = self.select(args)
            reason = ('explicit_model' if args.get('model') else
                      'qualified_advanced_task' if args.get('complexity') == 'advanced' else 'compatible_local_first')
            self.update(tid,'running',dict(selected_model=model['id'],backend=model['backend'],route_reason=reason,router_attempts=1,upstream_attempts=None,cost_category=model['backend']))
            if model['backend'] == 'paid':
                self.update(tid,'failed',dict(error='paid_broker_not_connected', return_to_gpt=True, paid_authorization=dict(
                    state='approval_required',model=model['id'], task_id=tid,
                    reason='explicit_paid_candidate',cost_estimate_usd=None,budget_remaining_usd=None,
                    data_scope_hash=digest(args['task']), max_cost_usd=None)))
                return True
            if self.get(tid)['state'] == 'cancel_requested':
                self.update(tid,'cancelled',{'cancellation':'confirmed_before_inference'})
                return True
            attempts = []
            for attempt in range(2):
                if args.get('deadline') and time.time() >= args['deadline']:
                    raise Fault('deadline_expired')
                if self.get(tid)['state'] == 'cancel_requested':
                    self.update(tid,'cancelled',{'cancellation':'confirmed_before_inference'})
                    return True
                try:
                    text,meta = self.infer(args,model,progress=lambda: self.update(tid,self.get(tid)['state'],{'last_activity_at':time.time()}))
                    break
                except Fault as failure:
                    attempts.append(dict(model=model['id'],backend=model['backend'],error=failure.code,
                                         **getattr(failure,'result_meta',{})))
                    self.update(tid,'running',{'attempts':attempts})
                    recoverable = failure.status in (502,503,504) or failure.code in (
                        'completion_truncated','empty_completion','unexpected_finish_reason',
                        'objective_quality_failed','invalid_completion_shape')
                    if failure.code == 'completion_truncated':
                        failure.result_meta['recovery_blocked'] = ('attempt_limit' if attempt else
                            'explicit_model_no_retry' if args.get('model') else 'pending_admission')
                    if attempt or failure.uncertain or not recoverable or args.get('model'):
                        raise
                    try:
                        next_model = self.select(args, exclude=[model['id']])
                    except Fault as selection_failure:
                        if selection_failure.code != 'no_compatible_authorized_model':
                            raise
                        next_model = None
                    if next_model is None:
                        budget = output_budget(args, model['id'])
                        if model['id'] == LOCAL and failure.code == 'completion_truncated' and budget['mode'] == 'auto':
                            target = min(AUTO_ANSWER_MAX, 2 * budget['answer_tokens'])
                            if target <= budget['answer_tokens']:
                                failure.result_meta['recovery_blocked'] = 'automatic_answer_ceiling'
                                raise failure
                            retry_args = args | {'_auto_answer_tokens':target}
                            try:
                                next_model = self.select(retry_args)
                            except Fault as admission:
                                if admission.code != 'no_compatible_authorized_model':
                                    raise
                                failure.result_meta['recovery_blocked'] = 'context_or_route_unavailable'
                                raise failure
                            if next_model['id'] != model['id']:
                                raise failure
                            args = retry_args
                        elif model['backend'] != 'local' or failure.status not in (502,503,504):
                            if failure.code == 'completion_truncated' and budget['mode'] == 'hard':
                                failure.result_meta['recovery_blocked'] = 'caller_hard_cap'
                                failure.result_meta['next_action'] = 'resubmit_without_cap_or_explicitly_choose_auto'
                            raise failure
                        else:
                            next_model = model  # One targeted local transient retry; no third call.
                    if next_model['backend'] == 'paid':
                        raise failure
                    model = next_model
                    self.update(tid,'running',dict(selected_model=model['id'],backend=model['backend'],
                        route_reason='bounded_local_output_recovery' if '_auto_answer_tokens' in args else 'bounded_recovery',router_attempts=2,cost_category=model['backend']))
            current = self.get(tid)['state']
            if args.get('deadline') and time.time() > args['deadline']:
                meta['deadline_exceeded'] = True
            if current == 'cancel_requested':
                meta['cancellation'] = 'too_late_completion_received'
            self.db.execute('UPDATE breakers SET last_success=? WHERE scope=?', (time.time(),'model:'+model['id']))
            self.update(tid,'completed',meta, text)
        except Fault as exc:
            scope = 'credential:'+self.c['identity'] if exc.status in (401,403) else 'model:'+(model['id'] if model else 'catalogue')
            if exc.status in (401,403,404,429) or (exc.status and exc.status >= 500):
                self.trip(scope,exc)
            meta = dict(error=exc.code, cooldown=self.blocked(scope), return_to_gpt=True) | getattr(exc,'result_meta',{})
            if exc.status == 429:
                # Upstream quota scope is unknown: suspend this identity conservatively.
                self.trip('credential:'+self.c['identity'],exc)
            self.update(tid,'unknown' if exc.uncertain else 'failed',meta,getattr(exc,'rejected_output',None))
        except Exception:
            # An unclassified failure might occur after submission. Do not expose exception text.
            self.update(tid,'unknown',{'error':'internal_error','return_to_gpt':True})
        return True

    def worker(self, once=False):
        with open(self.root/'worker.lock','a') as lock:
            os.chmod(self.root/'worker.lock',0o600)
            try:
                fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
            except BlockingIOError:
                return
            for r in self.db.execute("SELECT id FROM tasks WHERE identity=? AND state IN ('running','cancel_requested')", (self.c['identity'],)).fetchall():
                self.update(r['id'],'unknown',{'error':'worker_interrupted_no_retry'})
            idle_since = time.monotonic()
            while True:
                worked = self.run_one()
                if worked:
                    idle_since = time.monotonic()
                if once:
                    return
                if not worked:
                    if time.monotonic()-idle_since >= self.c.get('worker_idle_exit',60):
                        return
                    time.sleep(.25)


SCHEMA = {'type':'object','properties':{
    'profile':{'type':'string','enum':list(PROFILES)},'task':{'type':'string'},
    'model':{'type':'string'},'allow_cloud':{'type':'boolean'},
    'confidentiality':{'enum':['local','cloud-approved']},
    'contains_secrets':{'type':'boolean','description':'True for any authentication secret in the transmitted task; forces local only.'},
    'complexity':{'enum':['trivial','standard','advanced','strategic']},
    'task_type':{'enum':[*PROFILES,'diagnosis','comparison','synthesis','architecture']},
    'reasoning':{'type':'string','enum':list(LEVELS)},
    'required_capabilities':{'type':'array','items':{'enum':['tools','json','vision']}},
    'context_tokens':{'type':'integer','minimum':1},
    'max_output_tokens':{'type':'integer','minimum':1,'description':'Optional hard answer-token cap from the caller (not proof of a human limit). Omit for automatic task sizing. In explicit auto mode only, this is an adjustable hint, not a ceiling.'},
    'output_budget_mode':{'enum':['auto','hard'],'description':'Omit both output-budget fields for task-sized local output and at most one eligible local size recovery. A supplied max_output_tokens defaults to hard and is never enlarged; auto explicitly allows enlargement. hard requires max_output_tokens. Cloud limits and reasoning budgets are unchanged.'},
    'deadline':{'type':'number'},'parent_session':{'type':'string'},'idempotency_key':{'type':'string'},
    'quality':{'type':'object'},'paid_authorization':{'type':'string'}},
    'required':['profile','task'],'additionalProperties':False}


def tools_list():
    out = [{'name':n,'description':d,'inputSchema':SCHEMA} for n,d in (
        ('submit','Persist a recoverable task; return immediately.'),
        ('delegate','Compatible five-profile delegation; prefer submit for long tasks.'))]
    for name,props,required in [
        ('status',{'task_id':{'type':'string'}},['task_id']),
        ('result',{'task_id':{'type':'string'},'offset':{'type':'integer'},'limit':{'type':'integer'}},['task_id']),
        ('cancel',{'task_id':{'type':'string'}},['task_id']),
        ('activity',{'after':{'type':'integer'},'limit':{'type':'integer'}},[]),
        ('catalogue',{'refresh':{'type':'boolean'}},[])]:
        out.append(dict(name=name,description=name,inputSchema=dict(type='object',properties=props,required=required,additionalProperties=False)))
    return out


def spawn_worker(path):
    subprocess.Popen([sys.executable,str(Path(__file__).resolve()),'--config',str(Path(path).resolve()),'--worker'],
        stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,
        start_new_session=True, close_fds=True)


def serve(engine,path):
    for line in sys.stdin:
        req = None
        try:
            req = json.loads(line)
            if not isinstance(req,dict):
                raise Fault('invalid_request')
            rid,method = req.get('id'),req.get('method')
            if rid is None:
                continue
            if method == 'initialize':
                result = dict(protocolVersion='2024-11-05',capabilities={'tools':{}},serverInfo={'name':'llm-router','version':'0.1.0'})
            elif method == 'ping':
                result = {}
            elif method == 'tools/list':
                result = {'tools':tools_list()}
            elif method == 'tools/call':
                p = req.get('params',{})
                name,args = p.get('name'),p.get('arguments',{})
                if name in ('submit','delegate'):
                    value = engine.submit(args)
                    spawn_worker(path)
                    if name == 'delegate':
                        # Caller disconnect does not kill the detached worker.
                        while value['state'] not in TERMINAL and value['state'] != 'cancel_requested':
                            time.sleep(.1)
                            value = engine.status(value['task_id'])
                        if value['state'] == 'completed':
                            value = dict(metadata=value, **engine.result(value['task_id'],0,16000))
                elif name in ('status','cancel'):
                    value = getattr(engine,name)(args['task_id'])
                elif name == 'result':
                    value = engine.result(args['task_id'],args.get('offset',0),args.get('limit',4000))
                elif name == 'activity':
                    value = engine.activity(args.get('after',0),args.get('limit',100))
                elif name == 'catalogue':
                    value = {'models':engine.catalogue(args.get('refresh',False))}
                else:
                    raise Fault('unknown_tool')
                result = dict(content=[dict(type='text',text=json.dumps(value))],isError=value.get('state') in ('failed','unknown'))
            else:
                print(json.dumps(dict(jsonrpc='2.0',id=rid,error=dict(code=-32601,message='method_not_found'))),flush=True)
                continue
            response = dict(jsonrpc='2.0',id=rid,result=result)
        except Exception as exc:
            code = exc.code if isinstance(exc,Fault) else 'invalid_request'
            response = dict(jsonrpc='2.0',id=req.get('id') if isinstance(req,dict) else None,
                result=dict(isError=True,content=[dict(type='text',text=json.dumps({'error':code}))]))
        try:
            print(json.dumps(response),flush=True)
        except BrokenPipeError:
            return


def main():
    os.umask(0o077)
    parser = argparse.ArgumentParser()
    parser.add_argument('--config',required=True)
    parser.add_argument('--worker',action='store_true')
    parser.add_argument('--once',action='store_true')
    parser.add_argument('--reset-scope',help='Operator-only explicit circuit reopening after diagnosis')
    opts = parser.parse_args()
    engine = Engine(load_config(opts.config))
    if opts.reset_scope:
        with engine.db:
            engine.db.execute('DELETE FROM breakers WHERE scope=?',(opts.reset_scope,))
            engine.event(None,'operator_reopened',{'scope':opts.reset_scope})
    elif opts.worker:
        engine.worker(opts.once)
    else:
        serve(engine,opts.config)

if __name__ == '__main__':
    main()
