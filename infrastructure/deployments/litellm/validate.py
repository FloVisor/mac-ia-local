"""Recette ciblée sur docker-02. Ne sort ni secrets, ni corps de réponse."""
import json
import pathlib
import subprocess

ROOT = pathlib.Path('/srv/docker-local/compose/litellm')
creds = json.loads((ROOT/'secrets/admin-credentials.json').read_text())
cid = subprocess.check_output(['docker','ps','-q','--filter',
    'label=com.docker.swarm.service.name=litellm_gateway'],text=True).strip()
code = r'''
import json,urllib.request,urllib.error,pathlib,jwt,re
base='http://127.0.0.1:4000'
results={}
def api(path,body=None,key=None):
    headers={'Content-Type':'application/json'}
    if key: headers['Authorization']='Bearer '+key
    req=urllib.request.Request(base+path,data=None if body is None else json.dumps(body).encode(),headers=headers)
    try:
        with urllib.request.urlopen(req,timeout=20) as r:
            raw=r.read()
            try: data=json.loads(raw)
            except (ValueError,UnicodeDecodeError): data=raw.decode(errors='replace')
            return r.status,data,r.headers
    except urllib.error.HTTPError as e:
        return e.code,None,e.headers
for path in ['/health/liveliness','/health/readiness','/ui/']:
    s,body,_=api(path);results[path]=s
    if path=='/ui/' and s==200:
        match=re.search(r'src="([^"]+\.js)"',body)
        if match:results['ui_js_asset']=api(match[1])[0]
for path in ['/openapi.json','/redoc','/docs']:
    results[path]=api(path)[0]
results['models_without_key']=api('/v1/models')[0]
results['models_wrong_key']=api('/v1/models',key='invalid-validation-key')[0]
results['chat_without_key']=api('/v1/chat/completions',{'model':'unavailable','messages':[{'role':'user','content':'LITELLM_SYNTHETIC_AUTH_PROBE_20261021'}]})[0]
s,login,headers=api('/v2/login',{'username':creds['username'],'password':creds['password']})
results['db_admin_login']=s
if s!=200:
    print(json.dumps(results));raise SystemExit(1)
token=jwt.decode(login['token'],options={'verify_signature':False});key=token['key']
results['admin_role']=token['user_role']
cookie=headers.get('Set-Cookie','')
results['cookie_secure']='Secure' in cookie
results['cookie_httponly']='HttpOnly' in cookie
master=pathlib.Path('/run/secrets/litellm_master_key').read_text().strip()
s,models,_=api('/model/info',key=key)
results['model_info_status']=s
results['configured_model_count']=len(models.get('data',[])) if isinstance(models,dict) else None
s,credentials,_=api('/credentials',key=key)
results['credential_list_status']=s
results['credential_names']=[x.get('credential_name') for x in credentials.get('credentials',[])] if isinstance(credentials,dict) else []
results['client_identities']={}
for name in ['codex','mcp-delegate','openclaw-pro','openclaw-perso','mcp-delegate-cloud-approved']:
    s,user,_=api('/user/info?user_id='+name,key=master)
    results['client_identities'][name]={'status':s,'role':user.get('user_info',{}).get('user_role') if isinstance(user,dict) else None}
results['bootstrap_login_disabled']=api('/v2/login',{'username':'bootstrap-admin','password':pathlib.Path('/run/secrets/litellm_bootstrap_password').read_text().strip()})[0]!=200
results['validation_session_logout']=api('/session/logout',{},key=key)[0]
print(json.dumps(results))
'''
r=subprocess.run(['docker','exec','-i',cid,'python','-'],input='creds='+repr(creds)+'\n'+code,
                 text=True,capture_output=True)
if r.returncode:
    print(r.stdout)
    raise SystemExit('Validation incomplète ; stderr non affiché pour préserver les secrets.')
data=json.loads(r.stdout)
logs=subprocess.check_output(['docker','service','logs','--raw','litellm_gateway'],stderr=subprocess.STDOUT,text=True)
sensitive=[]
for p in (ROOT/'secrets').iterdir():
    if p.is_file() and p.name!='pending-invitation.json':
        if p.suffix=='.json':
            a=json.loads(p.read_text());sensitive.extend(v for k,v in a.items() if k in ['password','key','token'])
        else:sensitive.append(p.read_text().strip())
data['secret_in_gateway_logs']=any(v and v in logs for v in sensitive)
backend_secret=pathlib.Path('/srv/docker-local/compose/freellmapi/secrets/litellm-api-key').read_text().strip()
data['freellmapi_key_in_gateway_logs']=bool(backend_secret and backend_secret in logs)
data['synthetic_auth_prompt_in_gateway_logs']='LITELLM_SYNTHETIC_AUTH_PROBE_20261021' in logs
for svc in ['litellm_gateway','litellm_postgres']:
    spec=json.loads(subprocess.check_output(['docker','service','inspect',svc],text=True))[0]
    data[svc]={'ports':spec.get('Endpoint',{}).get('Ports',[]),
        'resources':spec['Spec']['TaskTemplate'].get('Resources',{}),
        'constraints':spec['Spec']['TaskTemplate']['Placement']['Constraints'],
        'update_status':spec.get('UpdateStatus',{}).get('State')}
data['inference']='NOT_RUN: aucun fournisseur FreeLLMAPI ; oMLX écoute seulement sur loopback'
data['browser_ui']='NOT_RUN: aucun navigateur disponible via cua'
(ROOT/'validation.json').write_text(json.dumps(data,indent=2))
print(json.dumps(data,indent=2))
