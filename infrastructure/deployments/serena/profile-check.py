import runpy,sys,contextlib,io,json,pathlib
out={}
for profile in ['pro','perso']:
 sys.argv=['validate.py',profile]
 with contextlib.redirect_stdout(io.StringIO()):ns=runpy.run_path('/srv/docker-local/serena/validate.py')
 tools=ns['rpc']('tools/list',{})['tools'];names=[t['name'] for t in tools]
 if profile=='perso':assert set(names)=={'get_current_time','convert_time'}
 else:assert 'serena_find_symbol' in names
 out[profile]={'tools':names,'time':ns['rpc']('tools/call',{'name':'get_current_time','arguments':{'timezone':'Europe/Paris'}})}
print(json.dumps(out,indent=2));pathlib.Path('/srv/docker-local/serena/profile-check.json').write_text(json.dumps(out,indent=2))
