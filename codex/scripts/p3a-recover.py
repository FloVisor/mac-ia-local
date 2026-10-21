"""Read existing P3-A task over MCP, then one historical local MCP smoke call."""
import hashlib,json,pathlib,subprocess,tomllib
ROOT=pathlib.Path(__file__).resolve().parents[2]; OUT=ROOT/'artifacts/llm-router-p3a'
config=tomllib.loads((pathlib.Path.home()/'.codex/config.toml').read_text())
class MCP:
 def __init__(self,c):
  self.p=subprocess.Popen([c['command'],*c.get('args',[])],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,text=True);self.n=0
 def rpc(self,m,params=None):
  self.n+=1;self.p.stdin.write(json.dumps(dict(jsonrpc='2.0',id=self.n,method=m,params=params or {}))+'\n');self.p.stdin.flush();r=json.loads(self.p.stdout.readline());assert 'error' not in r,r;return r['result']
 def call(self,n,a):
  r=self.rpc('tools/call',{'name':n,'arguments':a});
  if r.get('isError') and n not in ('status','result'): raise RuntimeError(r)
  return r
 def close(self):self.p.stdin.close();self.p.wait(timeout=5);self.p.stdout.close()
rs=json.loads((OUT/'isolated-session.json').read_text());calls=[r['params']['item'] for r in rs if r.get('method')=='item/completed' and r['params']['item'].get('type')=='mcpToolCall' and r['params']['item'].get('tool')=='submit']
assert len(calls)==1
submitted=json.loads(calls[0]['result']['content'][0]['text']);tid=submitted['task_id']
c=MCP(config['mcp_servers']['llm-router'])
try:
 init=c.rpc('initialize');status=json.loads(c.call('status',{'task_id':tid})['content'][0]['text']);assert status['state'] in ('completed','failed'),status
 result=json.loads(c.call('result',{'task_id':tid})['content'][0]['text']);activity=json.loads(c.call('activity',{})['content'][0]['text'])
 assert status['parent_session']==submitted['parent_session']
 report=dict(submitted=submitted,status=status,result=result,activity=activity,submitting_client_closed=True)
 (OUT/'recovered-task.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
finally:c.close()
if (OUT/'legacy-smoke.json').exists():
 raise SystemExit('Historical smoke already recorded; no second inference.')
c=MCP(config['mcp_servers']['local_llm'])
try:
 init=c.rpc('initialize');tools=c.rpc('tools/list');result=c.call('delegate',{'profile':'testing','task':'Reply with exactly OK.'})
 report={'server':init['serverInfo'],'tools':[x['name'] for x in tools['tools']],'result':result}
 (OUT/'legacy-smoke.json').write_text(json.dumps(report,indent=2));print('historical',json.dumps(report))
finally:c.close()
