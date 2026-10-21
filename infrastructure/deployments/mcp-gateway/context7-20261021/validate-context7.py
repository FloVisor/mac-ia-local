#!/usr/bin/env python3
"""Run on docker-02; tokens stay in memory, output contains no credentials."""
import json,pathlib,urllib.request,urllib.error,subprocess,datetime,ssl,concurrent.futures,time
BASE=pathlib.Path('/srv/docker-local/compose/mcp-gateway')
NAMES=['codex','pro','perso']
def docker(*args):return subprocess.check_output(['docker',*args],text=True,stderr=subprocess.STDOUT)
def parse(body):
 if not body:return None
 if body.startswith('event:') or body.startswith('data:'):
  return json.loads(next(l[5:].strip() for l in body.splitlines() if l.startswith('data:')))
 return json.loads(body)
def request(name,token,payload,session=None,method='POST'):
 headers={'Content-Type':'application/json','Accept':'application/json, text/event-stream','MCP-Protocol-Version':'2025-03-26'}
 if token:headers['Authorization']='Bearer '+token
 if session:headers['Mcp-Session-Id']=session
 req=urllib.request.Request('https://mcp-gateway.gangneux.org/'+name+'/mcp',data=json.dumps(payload).encode() if payload is not None else None,headers=headers,method=method)
 try:
  with urllib.request.urlopen(req,timeout=40) as r:return r.status,dict(r.headers),r.read().decode()
 except urllib.error.HTTPError as e:return e.code,dict(e.headers),e.read().decode()
def init():return {'jsonrpc':'2.0','id':1,'method':'initialize','params':{'protocolVersion':'2025-03-26','capabilities':{},'clientInfo':{'name':'gateway-deployment-validation','version':'1'}}}

import sys
names=sys.argv[1:] or NAMES
out={"profiles":{},"auth":{}}
tokens={n:(BASE/'secrets'/f'{n}.token').read_text().strip() for n in NAMES}
for name in names:
 status,h,b=request(name,tokens[name],init()); assert status==200,(name,status)
 session=next((v for k,v in h.items() if k.lower()=='mcp-session-id'),None)
 request(name,tokens[name],{'jsonrpc':'2.0','method':'notifications/initialized'},session)
 def rpc(method,params):
  status,_,body=request(name,tokens[name],{'jsonrpc':'2.0','id':2,'method':method,'params':params},session)
  data=parse(body); assert status==200 and 'result' in data,(status,data)
  assert not data['result'].get('isError'),data
  return data['result']
 tools=rpc('tools/list',{})['tools']
 record={'tools':tools}
 print(json.dumps({'profile':name,'tools':tools}),flush=True)
 if name!='perso':
  assert {'resolve-library-id','query-docs'}<=set(t['name'] for t in tools)
  record['resolve']=rpc('tools/call',{'name':'resolve-library-id','arguments':{'libraryName':'React','query':'React useState updater function previous state'}})
  record['docs']=rpc('tools/call',{'name':'query-docs','arguments':{'libraryId':'/websites/react_dev','query':'useState functional updater previous state concise example'}})
  assert 'react' in json.dumps(record['resolve']).lower()
  assert 'useState' in json.dumps(record['docs'])
 else: assert set(t['name'] for t in tools)=={'get_current_time','convert_time'}
 record['time']=rpc('tools/call',{'name':'get_current_time','arguments':{'timezone':'Europe/Paris'}})
 out['profiles'][name]=record
 request(name,tokens[name],None,session,method='DELETE')
 for source,token in [('anonymous',None),('invalid','deliberately-invalid-test-token')]+[(n,tokens[n]) for n in NAMES if n!=name]:
  status,_,_=request(name,token,init()); assert status==401,(name,source,status)
  out['auth'][name+':'+source]=status
print(json.dumps(out,indent=2))
