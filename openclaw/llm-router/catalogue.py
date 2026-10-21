"""Preview-only catalogue sync. Produces a scoped config patch; never writes client config/secrets."""
import argparse,json,pathlib,urllib.request

def plan(current,visible,approved,agent=None):
 providers={};diff=[]
 for tier,prefix in [('LOCAL','litellm-free'),('FREE','litellm-free'),('PAID','litellm-paid')]:
  if agent:prefix+='-'+agent
  aliases=approved[tier]['models'] if tier=='PAID' else approved[tier]
  for model in aliases:
   if model not in visible or 'embeddinggemma' in model or 'muse-glimmer' in model.lower():continue
   label='LOCAL' if tier=='LOCAL' else 'CLOUD FREE' if tier=='FREE' else 'CLOUD PAID OpenRouter'
   name=f'[{label}] {model}'
   existing=current.get('models',{}).get('providers',{}).get(prefix,{})
   old=next((m for m in existing.get('models',[]) if m['id']==model),None)
   # Existing authored definitions are never changed, including disabled entries.
   if old is not None:continue
   entry={'id':model,'name':name,'input':['text'],'contextWindow':8192,'maxTokens':2048}
   providers.setdefault(prefix,{'models':list(existing.get('models',[]))} if existing else {'baseUrl':'https://litellm.gangneux.org/v1','api':'openai-completions','models':[]})['models'].append(entry)
   diff.append({'action':'add','provider':prefix,'model':model,'label':label,'qualification':'NOT_TESTED','context_basis':'conservative admission limit, not validated maximum'})
 return {'models':{'providers':providers}},diff

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--config',required=True);p.add_argument('--policies',required=True);p.add_argument('--key-file',action='append',required=True);p.add_argument('--output',required=True);p.add_argument('--agent',choices=['pro','perso'],required=True);a=p.parse_args()
 visible=set()
 for f in a.key_file:
  req=urllib.request.Request('https://litellm.gangneux.org/v1/models',headers={'Authorization':'Bearer '+pathlib.Path(f).expanduser().read_text().strip()})
  with urllib.request.urlopen(req,timeout=20) as r:visible.update(m['id'] for m in json.load(r)['data'])
 current=json.loads(pathlib.Path(a.config).expanduser().read_text());policies=json.loads(pathlib.Path(a.policies).read_text())['policies']
 patch,diff=plan(current,visible,policies,a.agent)
 pathlib.Path(a.output).write_text(json.dumps(patch,indent=2)+'\n');print(json.dumps(diff,indent=2))
