"""Run on docker-02; Gateway credentials remain in memory and never enter output."""
import json,pathlib,urllib.request,urllib.error,sys,datetime
BASE=pathlib.Path('/srv/docker-local/compose/mcp-gateway')
def request(profile,payload,session=None):
 token=(BASE/'secrets'/f'{profile}.token').read_text().strip()
 h={'Content-Type':'application/json','Accept':'application/json, text/event-stream','Authorization':'Bearer '+token}
 if session:h['Mcp-Session-Id']=session
 req=urllib.request.Request('https://mcp-gateway.gangneux.org/'+profile+'/mcp',data=json.dumps(payload).encode(),headers=h)
 with urllib.request.urlopen(req,timeout=300) as r:
  b=r.read().decode();headers=dict(r.headers)
  if not b:return headers,None
  if b.startswith('event:') or b.startswith('data:'):b=next(l[5:].strip() for l in b.splitlines() if l.startswith('data:'))
  return headers,json.loads(b)
profile=sys.argv[1] if len(sys.argv)>1 else 'codex'
h,r=request(profile,{'jsonrpc':'2.0','id':1,'method':'initialize','params':{'protocolVersion':'2025-03-26','capabilities':{},'clientInfo':{'name':'serena-real-validation','version':'1'}}})
session=next((v for k,v in h.items() if k.lower()=='mcp-session-id'),None)
request(profile,{'jsonrpc':'2.0','method':'notifications/initialized'},session)
def rpc(method,params):
 _,r=request(profile,{'jsonrpc':'2.0','id':2,'method':method,'params':params},session)
 assert 'result' in r and not r['result'].get('isError'),r
 return r['result']
if len(sys.argv)>2:
 print(json.dumps(rpc('tools/call',{'name':sys.argv[2],'arguments':json.loads(sys.argv[3])}),indent=2))
else:
 tools=rpc('tools/list',{})['tools'];print(json.dumps({'profile':profile,'tools':tools},indent=2))
