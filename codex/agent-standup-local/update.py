"""Compare an upstream candidate and check patch applicability without promotion."""
import argparse
import difflib
import io
import json
from pathlib import Path
import subprocess
import tarfile
import urllib.request

here=Path(__file__).resolve().parent
repo=here.parents[1]
base=json.loads((here/'BASE.json').read_text())
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--source',type=Path,help='Unmodified upstream source to compare offline')
parser.add_argument('--ref',help='Explicit upstream commit/tag; download candidate only')
a=parser.parse_args()
if bool(a.source)==bool(a.ref):parser.error('Choose exactly one of --source or --ref')
work=repo/'artifacts/agent-standup-p3c/update-candidate'
work.mkdir(parents=True,exist_ok=True)
if a.ref:
 import re
 if not re.fullmatch(r'[a-zA-Z0-9_.-]{1,100}',a.ref):parser.error('Invalid upstream ref')
 req=urllib.request.Request('https://api.github.com/repos/Atoll92/agent-standup/commits/'+a.ref,headers={'User-Agent':'P3C-update-compare'})
 with urllib.request.urlopen(req,timeout=20) as f:sha=json.load(f)['sha']
 target=work/sha
 if not target.exists():
  with urllib.request.urlopen('https://codeload.github.com/Atoll92/agent-standup/tar.gz/'+sha,timeout=40) as f:blob=f.read()
  with tarfile.open(fileobj=io.BytesIO(blob),mode='r:gz') as t:t.extractall(work,filter='data')
 candidate=work/('agent-standup-'+sha)
else:candidate=a.source.resolve()
old=repo/'artifacts/agent-standup-p3c/source'/('agent-standup-'+base['commit'])
files=['codex.js','server.js','public/index.html','extension.js','package.json']
diffs=[];changed=[]
for name in files:
 x=(old/name).read_text();y=(candidate/name).read_text()
 if x!=y:
  changed.append(name);diffs.extend(difflib.unified_diff(x.splitlines(True),y.splitlines(True),fromfile='base/'+name,tofile='candidate/'+name))
(work/'upstream.diff').write_text(''.join(diffs))
r=subprocess.run(['python3',str(here/'build.py'),'--source',str(candidate),'--output',str(work/'build')],capture_output=True,text=True)
result={'candidate':str(candidate),'upstream_version':json.loads((candidate/'package.json').read_text()).get('version'),'changed_integration_files':changed,'patch_contexts_and_syntax':'PASS' if r.returncode==0 else 'BLOCKED','promoted':False,'report':str(work/'upstream.diff'),'requires_regression_and_visual_tests':True}
(work/'comparison.json').write_text(json.dumps(result,indent=2)+'\n')
if r.returncode:(work/'build-error.txt').write_text(r.stderr)
print(json.dumps(result,indent=2))
raise SystemExit(r.returncode)
