"""Isolated real-oMLX stdio qualification; no client/service changes, no paid call."""
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time
import router

repo = Path(__file__).resolve().parents[2]
paths = [repo/'mcp/local-llm-mcp/local-llm-mcp.py',Path.home()/'.codex/bin/local-llm-mcp']
before = [hashlib.sha256(p.read_bytes()).hexdigest() for p in paths]
# Same documented credential source as the existing MCP. Never write/print the key.
key = json.loads((Path.home()/'.omlx/settings.json').read_text())['auth']['api_key']
with tempfile.TemporaryDirectory(prefix='llm-router-smoke-') as temp:
    config = json.loads((Path(__file__).parent/'config.example.json').read_text())
    config.update(state_dir=temp+'/state',isolated_local_only=True,litellm_url=None,worker_idle_exit=1)
    cfg = Path(temp)/'config.json'
    cfg.write_text(json.dumps(config))
    environment = os.environ | {'LLM_ROUTER_LOCAL_KEY':key}
    proc = subprocess.Popen([sys.executable,str(Path(router.__file__)),'--config',str(cfg)],stdin=subprocess.PIPE,stdout=subprocess.PIPE,text=True,env=environment)
    def rpc(mid,method,params=None):
        proc.stdin.write(json.dumps(dict(jsonrpc='2.0',id=mid,method=method,params=params or {}))+'\n')
        proc.stdin.flush()
        return json.loads(proc.stdout.readline())
    initialized = rpc(1,'initialize')
    listing = rpc(2,'tools/list')
    reply = rpc(3,'tools/call',{'name':'submit','arguments':{'profile':'testing','task':'Reply with exactly OK.','reasoning':'off','quality':{'kind':'exact','expected':'OK'},'parent_session':'isolated-smoke','max_output_tokens':64}})
    value = json.loads(reply['result']['content'][0]['text'])
    tid = value['task_id']
    proc.stdin.close()
    proc.wait(timeout=5)
    proc.stdout.close()
    e = router.Engine(config)
    for _ in range(600):
        state = e.status(tid)
        if state['state'] in router.TERMINAL:
            break
        time.sleep(.1)
    assert state['state'] == 'completed',state
    assert e.result(tid)['text'].strip() == 'OK'
    assert e.submit({'profile':'testing','task':'Reply with exactly OK.','reasoning':'off','quality':{'kind':'exact','expected':'OK'},'parent_session':'isolated-smoke','max_output_tokens':64})['task_id'] == tid
    # Wait for this isolated worker's configured idle exit before cleaning its state.
    time.sleep(1.5)
    print(json.dumps(dict(server=initialized['result']['serverInfo'],tools=[t['name'] for t in listing['result']['tools']],status=state,result=e.result(tid),events=len(e.activity()['events']),legacy_unchanged=before == [hashlib.sha256(p.read_bytes()).hexdigest() for p in paths]),indent=2))
    e.db.close()
