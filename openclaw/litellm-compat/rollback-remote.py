"""Run on docker-02; restore audit metadata using native HTTP APIs only."""
import json
import pathlib
import subprocess

root = pathlib.Path('/srv/docker-local/compose')
models = json.loads((root / 'litellm/preimages/model-audit-20261021/models.json').read_text())
cid = subprocess.check_output(['docker', 'ps', '-q', '--filter',
    'label=com.docker.swarm.service.name=litellm_gateway'], text=True).strip()
code = 'models=' + repr(models) + '\n' + r'''
import json,pathlib,urllib.request
key=pathlib.Path('/run/secrets/litellm_master_key').read_text().strip()
def api(path,body=None):
 req=urllib.request.Request('http://127.0.0.1:4000'+path,
  data=None if body is None else json.dumps(body).encode(),
  headers={'Authorization':'Bearer '+key,'Content-Type':'application/json'},
  method='GET' if body is None else 'PATCH')
 with urllib.request.urlopen(req,timeout=20) as r:return json.load(r)
expected={'free/task-fast':262144,'free/task-coding':128000,
 'free/task-reasoning':131072,'free/task-long-context':256000}
current={m['model_name']:m for m in api('/model/info')['data']}
for old in models:
 name=old['model_name']; now=current[name]
 assert now['model_info']['max_tokens']==expected[name], 'Concurrent context change'
 assert now['litellm_params'].get('max_tokens')==2048, 'Concurrent output change'
 assert now['litellm_params']['model']==old['litellm_params']['model'], 'Concurrent route change'
for old in models:
 info={k:old['model_info'].get(k) for k in ['id','max_tokens','max_input_tokens','max_output_tokens']}
 api('/model/'+info['id']+'/update',{'model_info':info,
  'litellm_params':{'max_tokens':old['litellm_params'].get('max_tokens')}})
after={m['model_name']:m for m in api('/model/info')['data']}
for old in models:
 now=after[old['model_name']]
 for field in ['max_tokens','max_input_tokens','max_output_tokens']:
  assert now['model_info'].get(field)==old['model_info'].get(field), 'Rollback readback failed'
print('LiteLLM pools restored and verified')
'''
subprocess.run(['docker', 'exec', '-i', cid, 'python', '-'], input=code, text=True, check=True)
# Existing admin credentials stay on the host and in process memory.
credentials = json.loads((root / 'freellmapi/secrets/admin-credentials.json').read_text())
cid = subprocess.check_output(['docker', 'ps', '-q', '--filter',
    'label=com.docker.swarm.service.name=freellmapi_api'], text=True).strip()
code = 'const c=' + json.dumps(credentials) + ';' + r'''
const b='http://127.0.0.1:3001';
const login=await fetch(b+'/api/auth/login',{method:'POST',headers:{'Content-Type':'application/json'},
 body:JSON.stringify({email:c.email||c.username,password:c.password})});
if(!login.ok)throw Error('Login HTTP '+login.status);
const {token}=await login.json();const headers={Authorization:'Bearer '+token,'Content-Type':'application/json'};
const before=(await(await fetch(b+'/api/models',{headers})).json()).find(m=>m.id===281);
if(before.modelId!=='codestral-2508'||before.contextWindow!==128000)throw Error('Concurrent Codestral change');
const response=await fetch(b+'/api/models/281',{method:'PATCH',headers,body:JSON.stringify({contextWindow:256000})});
if(!response.ok)throw Error('PATCH HTTP '+response.status);
const after=(await(await fetch(b+'/api/models',{headers})).json()).find(m=>m.id===281);
if(after.contextWindow!==256000)throw Error('Readback failed');
console.log('Codestral metadata restored and verified');
'''
subprocess.run(['docker', 'exec', '-i', cid, 'node', '--input-type=module'],
    input=code, text=True, check=True)
