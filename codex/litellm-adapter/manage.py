#!/usr/bin/env python3
"""Discover/sync approved DIRECT models, scoped activation and guarded rollback."""
import argparse
import copy
import fcntl
import hashlib
import json
import os
from pathlib import Path
import plistlib
import secrets
import shutil
import subprocess
import tempfile
import time
import urllib.request

from adapter import api, private_file, OMLX
from reasoning_policy import reasoning_policy

ROOT = Path(__file__).resolve().parents[2]
HOME = Path.home()
STATE = HOME / '.local/state/codex-litellm-adapter'
CONF = HOME / '.config/codex-litellm-adapter'
CATALOG = HOME / '.codex/ollama-launch-models.json'
ROUTES = HOME / '.codex/ollama-launch-codex-routing.json'
BIN = '/Applications/ChatGPT.app/Contents/Resources/codex-cli/CodexCLI.app/Contents/MacOS/codex'
LABEL = 'org.gangneux.codex-litellm-adapter'
SYNC_LABEL = LABEL + '-sync'
PORT = 11439


def read(path):
    return json.loads(Path(path).read_text())


def atomic(path, data):
    path = Path(path)
    fd, tmp = tempfile.mkstemp(prefix='.' + path.name, dir=path.parent)
    try:
        with os.fdopen(fd, 'w') as output:
            json.dump(data, output, indent=2)
            output.write('\n')
            output.flush()
            os.fsync(output.fileno())
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def native_catalogue():
    # Official debug interface, isolated config. Bundled metadata follows the
    # installed Desktop version dynamically; no user auth/MCP copied or invoked.
    with tempfile.TemporaryDirectory(prefix='p3a-native-') as temp:
        raw = subprocess.check_output([BIN, 'debug', 'models', '--bundled'],
            env=os.environ | {'CODEX_HOME': temp}, timeout=30)
    return json.loads(raw)


def approved():
    p = read(ROOT / 'infrastructure/deployments/litellm/client-policies.json')['policies']
    return (set(p['LOCAL'] + p['FREE']) - {'local-ollama/embeddinggemma:latest'},
            set(p['PAID']['models']))


def display_name(slug):
    """Picker labels only; wire aliases and routing remain untouched."""
    names = {
        'local-omlx/mlx-community--Qwen3.6-35B-A3B-4bit': 'oMLX · Qwen3.6 35B',
        'local-ollama/qwen3:4b-instruct': 'Ollama · Qwen3 4B',
        'free-groq/gpt-oss-120b': 'Free · Groq GPT-OSS 120B',
        'free-groq/qwen3.8-27b': 'Free · Groq Qwen3.8 27B',
        'free-mistral/codestral-2508': 'Free · Mistral Codestral',
        'free-mistral/ministral-8b-2512': 'Free · Mistral Ministral 8B',
        'free-openrouter/dots-3-note-preview:free': 'Free · OpenRouter Dots 3 Note',
        'free-openrouter/north-mini-code:free': 'Free · OpenRouter North Mini Code',
        'free/task-fast': 'Free · Task Fast',
        'free/task-coding': 'Free · Task Coding',
        'free/task-reasoning': 'Free · Task Reasoning',
        'free/task-long-context': 'Free · Task Long Context',
        'paid-openrouter/deepseek-v4.1-flash-1017': 'Paid · DeepSeek V4.1 Flash',
        'paid-openrouter/glm-5.3': 'Paid · GLM-5.3',
        'paid/task-advanced': 'Paid · Task Advanced',
    }
    return names.get(slug, slug)


def sync(activate=False):
    local, paid = approved()
    discovered = set()
    for tier, filename in [('local-free', 'codex-direct-local-free.key'), ('paid', 'codex-direct-paid.key')]:
        data, _ = api('https://litellm.gangneux.org/v1', '/models',
                      private_file(HOME / '.config/llm-router' / filename))
        allowed = local if tier == 'local-free' else paid
        discovered |= {x['id'] for x in data['data']} & allowed
    if not (STATE/'owned.json').exists() and discovered != local | paid:
        raise RuntimeError('approved_catalogue_changed: review before publication')
    native = native_catalogue()
    current = read(CATALOG)
    original_gpt = [m for m in current['models'] if m['slug'].startswith(('gpt-', 'codex-'))]
    # Preserve every current GPT entry exactly. Discover refreshed metadata only
    # for new non-GPT entries; GPT changes require their own review.
    existing = {m['slug']: m for m in original_gpt}
    native_ids = {m['slug'] for m in native['models']}
    models = copy.deepcopy(original_gpt)
    template = next(m for m in current['models'] if m['slug'] in ('qwen36-omlx', OMLX))
    config = read(CONF / 'config.json')
    routes = read(ROUTES)
    owned_ids=local|paid|{'qwen36-omlx'}
    if (STATE/'owned.json').exists():
        previous=read(STATE/'owned.json')
        if (STATE/'rollback.json').exists():
            previous=read(STATE/'before.json')
        for current_data,old_data in [(current,previous['catalogue']),(routes,previous['routes'])]:
            if {m['slug']:m for m in current_data['models'] if m['slug'] in owned_ids} != {m['slug']:m for m in old_data['models'] if m['slug'] in owned_ids}:
                raise RuntimeError('owned_entries_changed_review_required')
    routes['models'] = [m for m in routes['models'] if m['slug'] not in owned_ids]
    ingress = private_file(CONF / 'ingress.key')
    config['models'] = {}
    for i, slug in enumerate(sorted(discovered)):
        is_local = slug.startswith('local-')
        is_paid = slug in paid
        tier = 'paid' if is_paid else 'local-free'
        category = 'LOCAL' if is_local else 'CLOUD PAID' if is_paid else 'CLOUD FREE'
        entry = copy.deepcopy(template)
        entry.update(slug=slug, display_name=display_name(slug),
                     description='LiteLLM DIRECT — ' + category,
                     priority=50+i, visibility='list', supports_search_tool=False,
                     web_search_tool_type='text', supports_reasoning_summaries=False,
                     supports_reasoning_summary_parameter=False,
                     include_apps_usage_instructions=False,
                     include_plugin_usage_instructions=False,
                     include_skills_usage_instructions=False)
        policy = reasoning_policy(slug)
        entry['supported_reasoning_levels'] = policy['levels']
        entry['default_reasoning_level'] = policy['default']
        if slug == OMLX:
            entry['auto_compact_token_limit'] = 100000
        if slug != OMLX:
            entry['supports_parallel_tool_calls'] = False
            entry['context_window'] = 8192
            entry['max_context_window'] = 8192
            entry['auto_compact_token_limit'] = 7000
            entry['description'] += ' ; ' + policy['note'] + ' ; admission 8192, maximum non qualifié'
        models.append(entry)
        routes['models'].append({'slug': slug, 'upstream': f'http://127.0.0.1:{PORT}/v1',
                                'upstream_model': slug, 'upstream_api_key': ingress})
        config['models'][slug] = {'tier': tier}
    # Legacy Qwen selection routes to the same adapter without changing GPT.
    legacy = copy.deepcopy(template)
    legacy['slug'] = 'qwen36-omlx'
    legacy['display_name'] = display_name(OMLX) + ' (ancien)'
    legacy['visibility'] = 'hide'
    legacy['supported_reasoning_levels'] = next(m for m in models if m['slug'] == OMLX)['supported_reasoning_levels']
    models.append(legacy)
    routes['models'].append({'slug': 'qwen36-omlx', 'upstream': f'http://127.0.0.1:{PORT}/v1',
                            'upstream_model': OMLX, 'upstream_api_key': ingress})
    # Retain fail-closed routes for revoked/removed aliases, so stale sessions
    # cannot fall through to the native GPT backend.
    for slug in sorted((local|paid)-discovered):
        routes['models'].append({'slug':slug,'upstream':f'http://127.0.0.1:{PORT}/v1',
                                'upstream_model':slug,'upstream_api_key':ingress})
    catalogue = {'models': models}
    if [m for m in catalogue['models'] if m['slug'].startswith(('gpt-', 'codex-'))] != original_gpt:
        raise RuntimeError('gpt_metadata_changed')
    revision = hashlib.sha256(json.dumps(sorted(discovered)).encode()).hexdigest()
    config['revision'] = revision
    atomic(CONF / 'config.json', config)
    if activate:
        with urllib.request.urlopen(f'http://127.0.0.1:{PORT}/health',timeout=5) as response:
            if json.load(response).get('status')!='ok':
                raise RuntimeError('adapter_not_healthy')
        # Route first, picker second: a new entry never reaches the GPT fallback.
        atomic(ROUTES, routes)
        atomic(CATALOG, catalogue)
        atomic(STATE / 'owned.json', {'models': sorted(owned_ids),
                                    'catalogue': catalogue, 'routes': routes})
        (STATE/'rollback.json').unlink(missing_ok=True)
    else:
        atomic(STATE / 'candidate-catalogue.json', catalogue)
        atomic(STATE / 'candidate-routes.json', routes)
    atomic(STATE / 'sync.json', {'time':time.time(),'models':sorted(discovered),
                               'revision': revision,'activated':activate,'gpt_entries_identical':True,
                               'native_bundled_count':len(native['models']),
                               'existing_gpt_not_bundled_preserved':sorted(set(existing)-native_ids)})
    atomic(STATE / 'reasoning-policy.json', {
        'evidence_date': '2026-10-21', 'ui_validation': 'PENDING_HUMAN',
        'activated': activate,
        'models': {slug: reasoning_policy(slug) for slug in sorted(discovered)}})


def prepare(identity_evidence):
    if (STATE / 'before.json').exists():
        before=read(STATE/'before.json')
        if before != {'catalogue':read(CATALOG),'routes':read(ROUTES)}:
            raise RuntimeError('preparation_snapshot_changed_review_required')
        # Resume an interrupted preparation, without replacing its snapshot.
        sync()
        write_plists()
        return
    proof = read(identity_evidence)
    assert proof['verified'] and proof['team']['max_budget'] == 40 and proof['team']['budget_duration'] == '1mo'
    assert not proof['team'].get('blocked')
    assert any(k['key_alias']=='codex-direct-paid' and k['user_id']=='codex-direct'
               and k['team_id']=='paid-openrouter-shared' for k in proof['keys'])
    atomic(STATE / 'before.json', {'catalogue':read(CATALOG),'routes':read(ROUTES)})
    (CONF / 'ingress.key').write_text(secrets.token_urlsafe(48))
    atomic(CONF / 'config.json', {'port':PORT,'litellm_url':'https://litellm.gangneux.org/v1',
        'ingress_key_file':str(CONF / 'ingress.key'), 'activity_log':str(STATE / 'activity.jsonl'),
        'paid_identity_verified':True,'models':{}, 'key_files':{
            tier:str(HOME / '.config/llm-router' / ('codex-direct-'+tier+'.key')) for tier in ['local-free','paid']}})
    sync()
    write_plists()


def write_plists():
    python = '/opt/homebrew/opt/python@3.14/bin/python3.14'
    for label,args,extra in [
        (LABEL,[python,str(Path(__file__).with_name('adapter.py')),'--config',str(CONF/'config.json')],{'RunAtLoad':True,'KeepAlive':True}),
        (SYNC_LABEL,[python,str(Path(__file__)),'sync'],{'StartInterval':300})]:
        plist={'Label':label,'ProgramArguments':args,'WorkingDirectory':str(ROOT),
               'StandardOutPath':str(STATE/(label+'.out.log')),
               'StandardErrorPath':str(STATE/(label+'.err.log')),**extra}
        (STATE/(label+'.plist')).write_bytes(plistlib.dumps(plist))


def rollback():
    before, owned = read(STATE/'before.json'), read(STATE/'owned.json')
    catalogue, routes = read(CATALOG), read(ROUTES)
    ids=set(owned['models'])
    def owned_entries(d):return [m for m in d['models'] if m['slug'] in ids]
    if owned_entries(catalogue)!=owned_entries(owned['catalogue']) or owned_entries(routes)!=owned_entries(owned['routes']):
        raise RuntimeError('owned_entries_changed: manual_reconciliation_required')
    stop_service(SYNC_LABEL)
    for current,original in [(catalogue,before['catalogue']),(routes,before['routes'])]:
        current['models']=[m for m in current['models'] if m['slug'] not in ids]+[m for m in original['models'] if m['slug'] in ids]
    atomic(CATALOG,catalogue)
    atomic(ROUTES,routes)
    stop_service(LABEL)
    atomic(STATE/'rollback.json',{'time':time.time(),'targeted':True})


def stop_service(label):
    target='gui/'+str(os.getuid())+'/'+label
    if subprocess.run(['launchctl','print',target],capture_output=True).returncode==0:
        subprocess.run(['launchctl','bootout',target],check=True)
    installed=HOME/'Library/LaunchAgents'/(label+'.plist')
    generated=STATE/(label+'.plist')
    if installed.exists():
        if installed.read_bytes()!=generated.read_bytes():
            raise RuntimeError('launchagent_changed_review_required')
        installed.unlink()


def start_service(label):
    installed=HOME/'Library/LaunchAgents'/(label+'.plist')
    generated=STATE/(label+'.plist')
    if installed.exists() and installed.read_bytes()!=generated.read_bytes():
        raise RuntimeError('launchagent_changed_review_required')
    if not installed.exists():shutil.copy2(generated,installed)
    target='gui/'+str(os.getuid())+'/'+label
    if subprocess.run(['launchctl','print',target],capture_output=True).returncode:
        subprocess.run(['launchctl','bootstrap','gui/'+str(os.getuid()),str(installed)],check=True)


def main():
    os.umask(0o077)
    for path in [STATE,CONF]:path.mkdir(parents=True,exist_ok=True,mode=0o700)
    parser=argparse.ArgumentParser()
    parser.add_argument('action',choices=['prepare','start','schedule','activate','sync','rollback'])
    parser.add_argument('--identity-evidence')
    args=parser.parse_args()
    with open(STATE/'manage.lock','a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX)
        if args.action=='prepare':prepare(args.identity_evidence)
        elif args.action=='start':start_service(LABEL)
        elif args.action=='schedule':start_service(SYNC_LABEL)
        elif args.action in ('activate','sync'):sync(activate=True)
        else:rollback()
    print(json.dumps({'action':args.action,'status':'ok'}))


if __name__=='__main__':main()
