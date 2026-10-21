import runpy,sys,contextlib,io,json,pathlib,concurrent.futures
# Independent MCP sessions, each request explicitly identifies its immutable project.
def run(profile,repo):
 sys.argv=['validate.py',profile]
 # Import runpy uses globals only per result; serialize initialization, concurrent RPC below.
 with contextlib.redirect_stdout(io.StringIO()):ns=runpy.run_path('/srv/docker-local/serena/validate.py')
 return ns['rpc'],repo
first=run('codex','FloVisor/mac-ia-local');second=run('pro','FloVisor/XITHI-Infrastructure-Ops')
def invoke(item):
 rpc,repo=item;r=rpc('tools/call',{'name':'serena_repository_status','arguments':{'repository':repo}})
 w=json.loads(r['content'][0]['text']);assert w['repository']==repo;return w
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:out=list(pool.map(invoke,[first,second]))
# Re-read first session after the other project's call.
out.append(invoke(first));assert out[0]['revision']==out[2]['revision']
print(json.dumps(out,indent=2));pathlib.Path('/srv/docker-local/serena/isolation-test.json').write_text(json.dumps(out,indent=2))
