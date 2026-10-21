#!/usr/bin/env python3
"""Run on docker-02: explicit allowlist, no commits/push, clean ff-only update."""
import argparse,json,pathlib,subprocess,sys,fcntl
BASE=pathlib.Path('/srv/docker-local/serena')
lock=(BASE/'state'/'analysis.lock').open('a')
fcntl.flock(lock.fileno(),fcntl.LOCK_EX)
CAT=json.loads(pathlib.Path(__file__).with_name('repositories.json').read_text())
def run(*args):return subprocess.check_output(args,text=True).strip()
p=argparse.ArgumentParser();p.add_argument('repository');p.add_argument('--update',action='store_true');a=p.parse_args()
group=next((k for k,v in CAT.items() if a.repository in v),None)
if not group:sys.exit('Repository outside approved allowlist')
meta=json.loads(run('gh','api','repos/'+a.repository))
if not meta.get('permissions',{}).get('pull'):sys.exit('Read permission missing')
branch=meta['default_branch'];dest=BASE/'repositories'/group/a.repository
if not dest.exists():
 dest.parent.mkdir(parents=True,exist_ok=True)
 refs=run('git','ls-remote','--heads','https://github.com/'+a.repository+'.git')
 cmd=['git','-c','core.hooksPath=/dev/null','clone','--single-branch']
 if refs:cmd+=['--branch',branch]
 subprocess.run(cmd+['https://github.com/'+a.repository+'.git',str(dest)],check=True)
 run('git','-C',str(dest),'config','remote.origin.pushurl','disabled://read-only')
 run('git','-C',str(dest),'config','core.hooksPath','/dev/null')
elif a.update:
 if run('git','-C',str(dest),'status','--porcelain'):sys.exit('Local changes: update refused')
 if run('git','-C',str(dest),'branch','--show-current')!=branch:sys.exit('Default branch changed: manual review required')
 run('git','-C',str(dest),'fetch','origin',branch)
 if int(run('git','-C',str(dest),'rev-list','--count','refs/remotes/origin/'+branch+'..HEAD')):sys.exit('Local commits: update refused')
 # Refuse divergent or locally committed history; fast-forward only.
 run('git','-C',str(dest),'merge','--ff-only','refs/remotes/origin/'+branch)
head=subprocess.run(['git','-C',str(dest),'rev-parse','--verify','HEAD'],capture_output=True,text=True)
print(json.dumps({'repository':a.repository,'group':group,'branch':branch,'sha':head.stdout.strip() if head.returncode==0 else None,'dirty':bool(run('git','-C',str(dest),'status','--porcelain')),'path':str(dest)}))
