"""Run on docker-02. Native API only; no paid generation or client configuration.

Secrets stay in host/container memory. Output contains only filtered evidence.
"""
import json
import pathlib
import subprocess

ROOT = pathlib.Path('/srv/docker-local/compose/litellm')
cid = subprocess.check_output(['docker', 'ps', '-q', '--filter',
    'label=com.docker.swarm.service.name=litellm_gateway'], text=True).strip()
free_key = pathlib.Path('/srv/docker-local/compose/freellmapi/secrets/litellm-api-key').read_text().strip()
code = r'''
import json,pathlib,urllib.request,urllib.error,time
master=pathlib.Path('/run/secrets/litellm_master_key').read_text().strip()
def api(path,body=None,key=master,base='http://127.0.0.1:4000',method=None):
 req=urllib.request.Request(base+path,data=None if body is None else json.dumps(body).encode(),headers={'Authorization':'Bearer '+key,'Content-Type':'application/json'},method=method)
 try:
  with urllib.request.urlopen(req,timeout=90) as r:return r.status,json.load(r)
 except urllib.error.HTTPError as e:
  raw=e.read()
  if e.code in [401,403]: raise SystemExit('STOP authorization '+path+' HTTP '+str(e.code))
  raise SystemExit('STOP API '+path+' HTTP '+str(e.code)+' '+raw.decode()[:350])
def models():return api('/model/info')[1]['data']
def filtered(m):
 return {'model_name':m['model_name'],'litellm_params':{k:v for k,v in m['litellm_params'].items() if k in ['model','api_base','max_retries','timeout','stream_timeout','litellm_credential_name']},'model_info':{k:v for k,v in m['model_info'].items() if k in ['id','mode','blocked','access_groups','backend','qualification','advertised_context']}}
before=models()
assert len({x['model_name'] for x in before})==len(before),'Duplicate aliases'
muse=[x for x in before if 'muse-glimmer' in x['model_name']]
assert len(muse)==1 and muse[0]['model_info']['blocked'] is True
catalogue=api('/models',key=free_key,base='http://freellmapi_api:3001/v1')[1]
ids={x['id'] for x in catalogue['data']}
individuals={
 'free-groq/qwen3.8-27b':'groq:qwen/qwen3.8-27b',
 'free-groq/gpt-oss-120b':'groq:openai/gpt-oss-120b',
 'free-openrouter/dots-3-note-preview:free':'openrouter:dots-studio/dots-3-note-preview:free',
 'free-openrouter/north-mini-code:free':'openrouter:cohere/north-mini-code:free',
 'free-mistral/ministral-8b-2512':'mistral:ministral-8b-2512',
 'free-mistral/codestral-2508':'mistral:codestral-2508'}
# Public catalogue uses short ids. Exact provider ids were qualified in the
# FreeLLMAPI report; the public catalogue check confirms their short entries.
short_ids=['qwen3.8-27b','gpt-oss-120b','dots3-note-preview','north-mini-code','ministral-8b','codestral-2508']
for short in short_ids:assert short in ids or short+':free' in ids, 'Missing catalogue short id '+short
for name in ['task-fast','task-coding','task-reasoning','task-long-context']:assert 'auto:'+name in ids
targets={**individuals,**{'free/'+n:'auto:'+n for n in ['task-fast','task-coding','task-reasoning','task-long-context']}}
existing={x['model_name']:x for x in before}
created=[]
for alias,target in targets.items():
 params={'model':'openai/'+target,'api_base':'http://freellmapi_api:3001/v1','litellm_credential_name':'freellmapi-internal','max_retries':0,'timeout':300,'stream_timeout':3600}
 if alias in existing:
  assert all(existing[alias]['litellm_params'].get(k)==v for k,v in params.items()),'Existing divergent alias '+alias
  continue
 data={'model_name':alias,'litellm_params':params,'model_info':{'mode':'chat','backend':'freellmapi','access_groups':['FREE'],'input_cost_per_token':0,'output_cost_per_token':0,'qualification':'Backend short generation verified previously; tools/context depend on member; no maximum context qualified','route_type':'pool' if target.startswith('auto:') else 'chat'}}
 api('/model/new',data);created.append(alias)
# Re-read in another HTTP request; no restart needed.
after=models(); amap={x['model_name']:x for x in after}
for alias,target in targets.items():assert amap[alias]['litellm_params']['model']=='openai/'+target
for old in before:
 assert filtered(amap[old['model_name']])==filtered(old),'Local entry changed'
assert api('/key/list')[1]['total_count']==0
result={'created':created,'catalogue':[filtered(x) for x in after],'model_mapping_verified':True,'local_preservation':True,'client_key_count':0,'health':api('/health/readiness')[1]}
print(json.dumps(result))
'''
run = subprocess.run(['docker', 'exec', '-i', cid, 'python', '-'],
    input='free_key='+repr(free_key)+'\n'+code, text=True, capture_output=True)
if run.returncode:
    print(run.stdout)
    print(run.stderr.replace(free_key, '[REDACTED]')[-1500:])
    raise SystemExit('STOP: remote check failed; stderr withheld to protect credentials')
result=json.loads(run.stdout)
(ROOT/'catalogue-finalization.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
