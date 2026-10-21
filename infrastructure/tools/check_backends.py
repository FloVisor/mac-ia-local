"""Probe declared backends from the existing Traefik container. No test container created."""
import json
import re
import subprocess
from pathlib import Path

DEST=Path(__file__).resolve().parent.parent/'evidence'/'2026-10-21'
data=json.loads((DEST/'docker-02.json').read_text())
urls=set()
for cfg in data['docker']['traefik']:
    for name, service in cfg.get('configuration',{}).get('http',{}).get('services',{}).items():
        if name=='acme-bootstrap':continue
        lb=service.get('loadBalancer',{})
        for server in lb.get('servers',[]):
            url=server.get('url','').rstrip('/') + lb.get('healthCheck',{}).get('path','/')
            if url.startswith(('http://','https://')):urls.add(url)
remote='''import json,subprocess,re,concurrent.futures,datetime
URLS=__URLS__
def probe(url):
 p=subprocess.run(['docker','exec','Traefik','wget','-S','--spider','-T','4','-t','1',url],capture_output=True,text=True,timeout=10)
 text=p.stdout+'\\n'+p.stderr
 return {'url':url,'exit':p.returncode,'http_codes':re.findall(r'HTTP/[0-9.]+\\s+(\\d+)',text),'diagnostic':[s for s in ['bad address','Connection refused','timed out','certificate verification failed','TLS error','No route to host','Connection reset by peer'] if s.lower() in text.lower()]}
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool: results=list(pool.map(probe,URLS))
print(json.dumps({'captured_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source':'docker exec Traefik wget --spider, no bodies or headers exported','probes':results}))
'''.replace('__URLS__',repr(sorted(urls)))
p=subprocess.run(['ssh','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','-o','PreferredAuthentications=publickey','root@docker-02','python3 -'],input=remote,text=True,capture_output=True,timeout=120)
if p.returncode:raise SystemExit(p.stderr)
result=json.loads(p.stdout)
(DEST/'backends.json').write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n')
print(json.dumps(result,ensure_ascii=False))
