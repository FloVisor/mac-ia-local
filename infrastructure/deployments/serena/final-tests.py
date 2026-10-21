import runpy,sys,contextlib,io,json,pathlib
sys.argv=['validate.py','codex']
with contextlib.redirect_stdout(io.StringIO()):ns=runpy.run_path('/srv/docker-local/serena/validate.py')
rpc=ns['rpc'];out={}
cases=[('mac-symbol','serena_find_symbol',{'repository':'FloVisor/mac-ia-local','name_path_pattern':'main','relative_path':'mcp/local-llm-mcp/local-llm-mcp.py','include_body':True}),('infra-symbol','serena_find_symbol',{'repository':'FloVisor/XITHI-Infrastructure-Ops','name_path_pattern':'fingerprint','relative_path':'ansible/scripts/inventory/precompiled.py','include_body':True}),('mac-references','serena_find_references',{'repository':'FloVisor/mac-ia-local','name_path':'count_task_tokens','relative_path':'mcp/local-llm-mcp/local-llm-mcp.py'}),('secondary-read','serena_search_pattern',{'repository':'rldet9/m3-si-mixtrio-kit','substring_pattern':'function','relative_path':'tests/n8n-factice.js'}),('time','get_current_time',{'timezone':'Europe/Paris'}),('context7','resolve-library-id',{'libraryName':'Serena','query':'Serena read only semantic symbol search'})]
for key,name,args in cases:
 r=rpc('tools/call',{'name':name,'arguments':args});out[key]=r
 pathlib.Path('/srv/docker-local/serena/'+key+'.json').write_text(json.dumps(r,indent=2));print(key,json.dumps(r)[:1800],flush=True)
pathlib.Path('/srv/docker-local/serena/tests.json').write_text(json.dumps(out,indent=2))
