"""À exécuter sur docker-02 : initialisation native, sans sortie de secrets."""
import json
import pathlib
import secrets
import subprocess

ROOT = pathlib.Path('/srv/docker-local/compose/litellm')
if (ROOT/'initialization.json').exists():
    raise SystemExit('STOP: initialisation déjà terminée, ne pas recréer les comptes.')
account = ROOT / 'secrets/admin-credentials.json'
if account.exists():
    credentials = json.loads(account.read_text())
else:
    credentials = {'username': 'florian@gangneux.org', 'user_id': 'florian-admin',
                   'password': secrets.token_urlsafe(40)+'!Aa1'}
    account.write_text(json.dumps(credentials))
    account.chmod(0o600)
cid = subprocess.check_output(['docker', 'ps', '-q', '--filter',
                              'label=com.docker.swarm.service.name=litellm_gateway'], text=True).strip()
code = r'''
import json, urllib.request, urllib.error, pathlib, jwt
master = pathlib.Path('/run/secrets/litellm_master_key').read_text().strip()
def api(path, body=None, key=master):
    headers={'Content-Type':'application/json'}
    if key: headers['Authorization']='Bearer '+key
    req=urllib.request.Request('http://127.0.0.1:4000'+path,
        data=None if body is None else json.dumps(body).encode(),headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            raw=r.read(); return r.status,json.loads(raw) if raw else {},r.headers
    except urllib.error.HTTPError as e:
        detail=json.loads(e.read())
        print(json.dumps({'failed_path':path.split('?')[0],'status':e.code,
            'error':detail.get('error',detail.get('detail'))}))
        raise SystemExit(1)
_,bootstrap,_=api('/v2/login',{'username':'bootstrap-admin','password':pathlib.Path('/run/secrets/litellm_bootstrap_password').read_text().strip()},key=None)
bootstrap_key=jwt.decode(bootstrap['token'],options={'verify_signature':False})['key']
_,existing,_=api('/user/info?user_id='+creds['user_id'])
if not existing.get('user_info'):
    api('/user/new',{'user_id':creds['user_id'],'user_email':creds['username'],
        'user_role':'proxy_admin','auto_create_key':False,'send_invite_email':False})
if saved_invite:
    invite=saved_invite
else:
    _,invite,_=api('/invitation/new',{'user_id':creds['user_id']},key=bootstrap_key)
_,onboard,_=api('/onboarding/get_token?invite_link='+invite['id'],key=None)
claimkey=jwt.decode(onboard['token'],options={'verify_signature':False})['key']
api('/onboarding/claim_token',{'invitation_link':invite['id'],'user_id':creds['user_id'],
    'password':creds['password']},key=claimkey)
_,login,headers=api('/v2/login',{'username':creds['username'],'password':creds['password']},key=None)
session=jwt.decode(login['token'],options={'verify_signature':False})
assert session['user_role']=='proxy_admin'
print(json.dumps({'admin_created':True,'db_login':True,'role':session['user_role'],
    'cookie_secure':'Secure' in headers.get('Set-Cookie',''),
    'cookie_httponly':'HttpOnly' in headers.get('Set-Cookie','')}))
for name in ['codex','mcp-delegate','openclaw-pro','openclaw-perso','mcp-delegate-cloud-approved']:
    api('/user/new',{'user_id':name,'user_alias':name,'user_role':'internal_user',
        'auto_create_key':False,'send_invite_email':False})
print(json.dumps({'client_identities_created':5,'inference_keys_issued':0}))
'''
invite_file=ROOT/'secrets/pending-invitation.json'
saved_invite=json.loads(invite_file.read_text()) if invite_file.exists() else None
result = subprocess.run(['docker','exec','-i',cid,'python','-'],
                        input='creds='+repr(credentials)+'\nsaved_invite='+repr(saved_invite)+'\n'+code, text=True, capture_output=True)
print(result.stdout)
if result.returncode:
    print('Échec initialisation ; identifiants conservés. Aucun nouvel essai automatique.')
    raise SystemExit(result.returncode)
(ROOT/'initialization.json').write_text(result.stdout)
invite_file.unlink(missing_ok=True)
