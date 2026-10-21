"""One bounded Codex submit, process-only per-tool approval, no global edits."""
import hashlib, json, pathlib, selectors, subprocess, time
ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = ROOT / 'artifacts/llm-router-p3a'
# Preserve the first, non-executing discovery attempt.
if (OUT/'isolated-session.json').exists():
    (OUT/'isolated-discovery-attempt.json').write_bytes((OUT/'isolated-session.json').read_bytes())
if (OUT/'recovered-task.json').exists():
    raise SystemExit('Recipe already executed; read preserved evidence, do not regenerate.')
CONFIG = pathlib.Path.home()/'.codex/config.toml'
before = hashlib.sha256(CONFIG.read_bytes()).hexdigest()
p = subprocess.Popen(['codex','app-server','--strict-config','-c','approval_policy="never"',
    '-c','mcp_servers.llm-router.tools.submit.approval_mode="approve"',
    '-c','mcp_servers.llm-router.enabled_tools=["submit"]','-c','mcp_servers.llm-router.required=true','-c','mcp_optional_startup_grace_ms=0'],
    stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=(OUT/'isolated-session.stderr').open('w'),text=True,bufsize=1)
transcript=[]
def send(i,m,params):
    p.stdin.write(json.dumps(dict(id=i,method=m,params=params))+'\n');p.stdin.flush()
def read():
    line=p.stdout.readline()
    if not line:raise RuntimeError('app-server EOF')
    r=json.loads(line);transcript.append(r);return r
def rpc(i,m,params):
    send(i,m,params)
    while True:
        r=read()
        if r.get('id')==i:
            if 'error' in r:raise RuntimeError(r['error'])
            return r['result']
try:
    rpc(1,'initialize',{'clientInfo':{'name':'p3a-bounded-validation','version':'1'},'capabilities':{'experimentalApi':True}})
    config=rpc(2,'config/read',{'includeLayers':False})['config']
    assert config['approval_policy']=='never'
    assert config['mcp_servers']['llm-router']['tools']=={'submit':{'approval_mode':'approve'}}
    thread=rpc(3,'thread/start',{'cwd':'/tmp','model':'gpt-6.1-sol','approvalPolicy':'never','ephemeral':True})['thread']
    tid=thread['id']; print('thread',tid,flush=True)
    servers=rpc(30,'mcpServerStatus/list',{'threadId':tid})
    match=[s for s in servers['data'] if s['name']=='llm-router']
    print('router discovery',json.dumps(match),flush=True)
    assert len(match)==1 and any('submit' in name for name in match[0]['tools']), 'submit absent from MCP catalogue'
    prompt=('Bounded P3-A validation. Call llm-router.submit exactly ONCE with '+json.dumps(dict(profile='testing',task='Reply with exactly OK.',reasoning='off',max_output_tokens=64,quality={'kind':'exact','expected':'OK'},allow_cloud=False,confidentiality='local',parent_session=tid,idempotency_key='p3a-local-'+tid))+'. You may use tool discovery/search to find llm-router.submit if deferred. Do not call any other business tool, read files, or run commands. Return only task_id and submitted state. Stop after submit; the operator recovers the result separately.')
    rpc(4,'turn/start',{'threadId':tid,'input':[{'type':'text','text':prompt}]})
    while True:
        r=read()
        if r.get('method')=='turn/completed':break
        if r.get('method')=='item/mcpToolCall/completed':print('MCP completed',flush=True)
    (OUT/'isolated-session.json').write_text(json.dumps(transcript,indent=2))
    print('completed; global config unchanged',before==hashlib.sha256(CONFIG.read_bytes()).hexdigest(),flush=True)
finally:
    p.terminate();p.wait(timeout=10)
    (OUT/'isolated-session.json').write_text(json.dumps(transcript,indent=2))
