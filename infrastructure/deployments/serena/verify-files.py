import json,pathlib,subprocess
base=pathlib.Path('/srv/docker-local/serena');out={}
for key,group,repo in [('mac-symbol','primary','FloVisor/mac-ia-local'),('infra-symbol','primary','FloVisor/XITHI-Infrastructure-Ops')]:
 r=json.loads((base/(key+'.json')).read_text());w=json.loads(r['content'][0]['text']);symbols=json.loads(w['result']['content'][0]['text']);assert symbols
 for sym in symbols:
  p=base/'repositories'/group/repo/sym['relative_path'];assert p.is_file()
  text=p.read_text();assert 'def '+sym['name_path']+'(' in text
  # Serena's display body has escaped newlines; verify exact source range after unescaping.
  loc=sym['body_location'];source='\n'.join(text.splitlines()[loc['start_line']:loc['end_line']+1]);body=sym['body'];assert source==body or source==body.replace('\\n','\n').replace('\\\\','\\'),(key,source,body)
  assert w['revision']==subprocess.check_output(['git','-C',str(base/'repositories'/group/repo),'rev-parse','HEAD'],text=True).strip()
 out[key]={'path':str(p),'revision':w['revision'],'source_range_matches':True}
print(json.dumps(out,indent=2));(base/'source-verification.json').write_text(json.dumps(out,indent=2))
