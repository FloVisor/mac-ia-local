"""Unauthenticated HEAD and public TLS checks. No redirects, cookies, or bodies saved."""
import concurrent.futures
import datetime
import json
import re
import socket
import ssl
import subprocess
from pathlib import Path

DEST=Path(__file__).resolve().parent.parent/'evidence'/'2026-10-21'
d=json.loads((DEST/'docker-02.json').read_text())
domains=set()
for cfg in d['docker']['traefik']:
    for router in cfg.get('configuration',{}).get('http',{}).get('routers',{}).values():
        if 'Path' not in router.get('rule','') and 'acme-bootstrap' not in router.get('rule',''):
            domains.update(re.findall(r'Host\(`([^`]+)`\)',router.get('rule','')))


def probe(item):
    domain, family=item
    ip='192.168.205.10' if family==4 else '2a01:e0a:8ce:68c5::10'
    target=ip if family==4 else '['+ip+']'
    p=subprocess.run(['curl','--noproxy','*','--silent','--show-error','--head','--max-time','8',
                      '--resolve',f'{domain}:443:{target}','-o','/dev/null','-w','%{json}',f'https://{domain}/'],capture_output=True,text=True,timeout=12)
    try:j=json.loads(p.stdout)
    except ValueError:j={}
    return {'domain':domain,'family':family,'target':ip,'method':'HEAD','path':'/',
            'exit':p.returncode,'http_code':j.get('http_code'),'ssl_verify_result':j.get('ssl_verify_result'),
            'remote_ip':j.get('remote_ip'),'duration_seconds':j.get('time_total'),'error':p.stderr.strip()}


if __name__=='__main__':
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        results=list(pool.map(probe,[(d,f) for d in sorted(domains) for f in [4,6]]))
    tls={}
    try:
        with socket.create_connection(('192.168.205.10',443),timeout=8) as sock:
            with ssl.create_default_context().wrap_socket(sock,server_hostname='home.gangneux.org') as conn:
                tls={'verified':True,'certificate':conn.getpeercert(),'protocol':conn.version(),'cipher':conn.cipher()}
    except Exception as e:
        tls={'verified':False,'error':str(e)}
    out={'captured_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source':'Mac, forced frontend IP, no redirects, normal certificate validation',
         'excluded':'acme-bootstrap synthetic backend and OAuth authorization/callback endpoints', 'probes':results,'tls':tls}
    (DEST/'frontends.json').write_text(json.dumps(out,indent=2,ensure_ascii=False)+'\n')
    print(json.dumps({'results':results,'tls':tls},ensure_ascii=False))
