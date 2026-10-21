import copy,importlib.util,pathlib,unittest
p=pathlib.Path(__file__).resolve().parents[1]/'catalogue.py';spec=importlib.util.spec_from_file_location('catalogue',p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class Sync(unittest.TestCase):
 def test_sync_preserves_auth_defaults_custom_and_disabled(self):
  custom={'id':'custom','name':'mine'};disabled={'id':'free/x','name':'disabled','disabled':True};provider={'models':[custom,disabled],'apiKey':'existing-secret'}
  current={'models':{'providers':{'litellm-free':provider}},'agents':{'entries':{'main':{'model':'untouched'}}}}
  before=copy.deepcopy(current);policy={'LOCAL':['local/x','local-ollama/embeddinggemma:latest'],'FREE':['free/x','free/new'],'PAID':{'models':['paid/x']}}
  patch,diff=m.plan(current,set(policy['LOCAL']+policy['FREE']+policy['PAID']['models']+['muse-glimmer','free/unapproved']),policy)
  self.assertEqual(current,before);self.assertNotIn('agents',patch)
  self.assertEqual([x['model'] for x in diff],['local/x','free/new','paid/x'])
  self.assertEqual(patch['models']['providers']['litellm-free']['models'][:2],[custom,disabled]);self.assertNotIn('apiKey',patch['models']['providers']['litellm-free'])
  merged=copy.deepcopy(current)
  for k,v in patch['models']['providers'].items():merged['models']['providers'].setdefault(k,{}).update(v)
  self.assertEqual(m.plan(merged,{'local/x','free/x','free/new','paid/x'},policy)[1],[])
if __name__=='__main__':unittest.main()
