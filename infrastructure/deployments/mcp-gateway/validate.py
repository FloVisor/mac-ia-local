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
tokens={n:(BASE/'secrets'/f'{n}.token').read_text().strip() for n in NAMES}
assert len(set(tokens.values()))==3
out={'timestamp':datetime.datetime.now(datetime.timezone.utc).isoformat(),'auth':{},'profiles':{},'runtime':[]}
for name in NAMES:
 checks={}
 for source,token in [('anonymous',None),('invalid','deliberately-invalid-test-token')]+list(tokens.items()):
  status,headers,body=request(name,token,init()); checks[source]=status
  assert status==(200 if source==name else 401),(name,source,status,body[:150])
  if source==name:
   data=parse(body);assert 'result' in data,data
   session=next((v for k,v in headers.items() if k.lower()=='mcp-session-id'),None)
   request(name,token,None,session,method='DELETE')
 out['auth'][name]=checks
 status,headers,body=request(name,tokens[name],init());assert status==200
 session=next((v for k,v in headers.items() if k.lower()=='mcp-session-id'),None)
 status,_,_=request(name,tokens[name],{'jsonrpc':'2.0','method':'notifications/initialized'},session);assert status==202,status
 status,_,body=request(name,tokens[name],{'jsonrpc':'2.0','id':2,'method':'tools/list','params':{}},session)
 data=parse(body);tools=[t['name'] for t in data['result']['tools']]
 assert set(tools)=={'get_current_time','convert_time'},tools
 with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
  call=pool.submit(request,name,tokens[name],{'jsonrpc':'2.0','id':3,'method':'tools/call','params':{'name':'get_current_time','arguments':{'timezone':'Europe/Paris'}}},session)
  seen=set()
  while not call.done():
   ids=docker('ps','-q','--filter','label=docker-mcp-name=time').split()
   for cid in ids:
    if cid in seen:continue
    try:
     c=json.loads(docker('inspect','--format','{{json .HostConfig}}',cid))
     networks=json.loads(docker('inspect','--format','{{json .NetworkSettings.Networks}}',cid))
     image=docker('inspect','--format','{{.Config.Image}}',cid).strip()
    except subprocess.CalledProcessError:continue
    record={'id':cid,'profile_call':name,'node':'docker-02','image':image,'networks':list(networks),'memory':c['Memory'],'nano_cpus':c['NanoCpus'],'cpu_quota':c['CpuQuota'],'privileged':c['Privileged'],'no_new_privileges':c['SecurityOpt']}
    assert c['Memory']==0 and c['NanoCpus']==0 and c['CpuQuota']==0,record
    assert list(networks)==['TRAEFIK_BACKEND'] and not c['Privileged'],record
    out['runtime'].append(record);seen.add(cid)
   time.sleep(.15)
  status,_,body=call.result()
 data=parse(body);assert status==200 and 'result' in data and not data['result'].get('isError'),data
 out['profiles'][name]={'initialize':'PASS','tools':tools,'call':data['result']}
 request(name,tokens[name],None,session,method='DELETE')
assert out['runtime'], 'No live MCP container observed'
(BASE/'functional-validation.json').write_text(json.dumps(out,indent=2)+'\n')
for n in NAMES:
 s=json.loads(docker('service','inspect','mcp-gateway_'+n))[0]
 assert not s['Endpoint'].get('Ports')
 assert not s['Spec']['TaskTemplate'].get('Resources',{}).get('Limits')
 assert s['Spec']['TaskTemplate']['Placement']['Constraints']==['node.hostname == docker-02']
 logs=docker('service','logs','--raw','--tail','100','mcp-gateway_'+n)
 assert not any(t in logs for t in tokens.values()),'token found in logs'
 assert 'Calling tool get_current_time' in logs,'audit event absent'
out['logging']='PASS: call event present, tokens absent'
(BASE/'validation.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(out,indent=2))
