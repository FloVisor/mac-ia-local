"""Recette réseau ciblée, à lancer sur docker-02. Aucun appel de modèle."""
import json
from pathlib import Path
import subprocess

root = Path('/srv/docker-local/compose/litellm')
cid = subprocess.check_output(['docker','ps','-q','--filter',
    'label=com.docker.swarm.service.name=freellmapi_api'],text=True).strip()
script = r'''
import https from 'node:https';
const tests=[];
async function request(domain,path,method='GET',wrongKey=false) {
 const body=method==='POST'?JSON.stringify({model:'unavailable',messages:[{role:'user',content:'SYNTHETIC_EXPOSURE_20261021'}],input:'SYNTHETIC_EXPOSURE_20261021'}):undefined;
 return await new Promise((resolve,reject)=>{
  const req=https.request({host:'172.29.2.2',port:443,servername:domain,path,method,
   headers:{Host:domain,'Content-Type':'application/json','X-Forwarded-For':'192.168.201.10',
    ...(body?{'Content-Length':Buffer.byteLength(body)}:{}),
    ...(wrongKey?{Authorization:'Bearer invalid-exposure-check'}:{})}},r=>{
     r.resume();r.on('end',()=>resolve(r.statusCode));
   });
  req.setTimeout(10000,()=>req.destroy(Error('timeout')));req.on('error',reject);
  req.end(body);
 });
}
for(const [method,path] of [['GET','/v1/models'],['POST','/v1/chat/completions'],['POST','/v1/responses']]){
 for(const wrongKey of [false,true]) tests.push({scope:'public_api',method,path,auth:wrongKey?'wrong':'absent',expected:401,status:await request('litellm.gangneux.org',path,method,wrongKey)});
}
for(const [method,path] of [
 ['GET','/ui/'],['POST','/v2/login'],['GET','/credentials'],['GET','/user/list'],
 ['POST','/user/new'],['POST','/key/generate'],['POST','/model/new'],['GET','/global/spend/logs'],
 ['GET','/health/readiness'],['GET','/metrics'],['GET','/openapi.json'],
 ['POST','/v1/models'],['GET','/v1/chat/completions'],['GET','/v1/responses'],
 ['HEAD','/v1/models'],['OPTIONS','/v1/chat/completions'],['POST','/v1/embeddings'],
 ['GET','/v1/models/'],['POST','/chat/completions'],['GET','/models'],
 ['POST','/v1/unknown'],['GET','/v1/models/../key/generate']]) {
 tests.push({scope:'private_fallback',method,path,expected:403,status:await request('litellm.gangneux.org',path,method)});
}
for(const path of ['/','/api/ping','/v1/models']) tests.push({scope:'freellmapi_private',method:'GET',path,expected:403,status:await request('freellmapi.gangneux.org',path)});
console.log(JSON.stringify({origin:'untrusted overlay; forged private X-Forwarded-For',tests,pass:tests.every(x=>x.status===x.expected),external_internet:'NOT_RUN'}));
'''
r=subprocess.run(['docker','exec',cid,'node','--input-type=module','-e',script],text=True,capture_output=True)
if r.returncode:
    raise SystemExit('Échec sonde réseau : '+r.stderr[-1500:])
result=json.loads(r.stdout)
(root/'exposure-validation.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
if not result['pass']:
    raise SystemExit('Échec de la matrice exposition ; analyser avant toute nouvelle action.')
