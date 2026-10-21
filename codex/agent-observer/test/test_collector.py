from contextlib import closing
import importlib.util
import json
from pathlib import Path
import sqlite3
import tempfile
import time
import unittest

spec=importlib.util.spec_from_file_location('collector',Path(__file__).parents[1]/'collector.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
P='11111111-1111-1111-1111-111111111111'
C='22222222-2222-2222-2222-222222222222'
T='33333333-3333-3333-3333-333333333333'

class Tests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
  self.dir=self.root/'sessions/2026/10/21';self.dir.mkdir(parents=True)
  self.db=self.root/'tasks.sqlite'
  with closing(sqlite3.connect(self.db)) as c, c:
   c.executescript('CREATE TABLE tasks(id,identity,state,created,updated,meta);CREATE TABLE events(seq,task_id,identity,at,state,meta);')
  self.c=m.Collector(self.root,self.db)
 def write(self,id=P,parent=None,state='task_started'):
  p=self.dir/('rollout-test-'+id+'.jsonl')
  data=[{'type':'session_meta','timestamp':'2026-10-21T12:00:00Z','payload':{'id':id,'parent_thread_id':parent,'source':'vscode','model_provider':'openai','secret':'sk-secret'}}, {'type':'turn_context','payload':{'model':'declared-model'}}, {'type':'event_msg','payload':{'type':state}}, {'type':'response_item','payload':{'type':'message','content':'CONFIDENTIAL'}}]
  p.write_text(''.join(json.dumps(x)+'\n' for x in data));return p
 def test_parent_and_native_and_no_prompts(self):
  self.write();self.write(C,P);s=self.c.snapshot();self.assertEqual(len(s['nodes']),2)
  child=next(n for n in s['nodes'] if n['id']==C);self.assertEqual(child['kind'],'native_subagent');self.assertEqual(child['parent'],P)
  self.assertNotIn('CONFIDENTIAL',json.dumps(s));self.assertNotIn('sk-secret',json.dumps(s));self.assertEqual(child['model'],'declared-model')
 def test_transition_and_restart_no_duplicates(self):
  p=self.write();self.assertEqual(self.c.snapshot()['nodes'][0]['state'],'running')
  with p.open('a') as f:f.write(json.dumps({'type':'event_msg','payload':{'type':'task_complete'}})+'\n')
  self.assertEqual(self.c.snapshot()['nodes'][0]['state'],'completed');self.assertEqual(len(m.Collector(self.root,self.db).snapshot()['nodes']),1)
 def test_router_isolation_provenance_errors_and_history(self):
  now=time.time();meta={'parent_session':P,'profile':'testing','selected_model':'free/pool','actual_model':'alias-lie','provider_model_confirmation':'response_model','error':'Bearer sk-secret','cost_usd':None,'usage':{'total_tokens':37,'secret':'bad'}}
  with closing(sqlite3.connect(self.db)) as c, c:
   for identity in ['codex','openclaw-perso']:c.execute('INSERT INTO tasks VALUES(?,?,?,?,?,?)',(T,identity,'failed',now,now,json.dumps(meta)))
   for i,state in enumerate(['queued','running','failed']):c.execute('INSERT INTO events VALUES(?,?,?,?,?,?)',(i,T,'codex',now,state,'{}'))
  before=self.db.read_bytes();s=self.c.snapshot();self.assertEqual(self.db.read_bytes(),before)
  self.assertEqual(len(s['nodes']),2);n=s['nodes'][0];self.assertTrue(s['nodes'][1]['reference_only']);self.assertEqual(n['parent'],P);self.assertIsNone(n['actual_model']);self.assertIsNone(n['provider']);self.assertIsNone(n['cost_usd']);self.assertEqual(len(n['history']),3);self.assertNotIn('sk-secret',json.dumps(s));self.assertTrue(n['result_available'])
 def test_stale_unknown(self):
  import os
  p=self.write();os.utime(p,(time.time()-600,time.time()-600));self.assertEqual(self.c.snapshot()['nodes'][0]['state'],'unknown')
 def test_partial_record_not_invented(self):
  p=self.write();p.write_bytes(b'{"type":"session_meta"');self.assertEqual(self.c.snapshot()['nodes'],[])
 def test_legacy_separate(self):
  p=self.write()
  with p.open('a') as f:f.write(json.dumps({'type':'response_item','payload':{'type':'function_call','name':'mcp__local_llm__delegate','arguments':'SECRET'}})+'\n')
  n=self.c.snapshot()['nodes'][0];self.assertTrue(n['legacy_mcp_observed']);self.assertNotIn('SECRET',json.dumps(n))

 def test_cancelled_event(self):
  self.write(state='turn_aborted')
  self.assertEqual(self.c.snapshot()['nodes'][0]['state'],'cancelled')
 def test_cached_state_becomes_unknown_without_file_change(self):
  from unittest.mock import patch
  self.write()
  self.assertEqual(self.c.snapshot()['nodes'][0]['state'],'running')
  later=time.time()+600
  with patch.object(m.time,'time',return_value=later):
   self.assertEqual(self.c.snapshot()['nodes'][0]['state'],'unknown')

if __name__=='__main__':unittest.main()

class CorrelationTests(Tests):
 def test_structured_submit_only_and_conflict(self):
  path=self.write()
  now=time.time()
  with closing(sqlite3.connect(self.db)) as c,c:
   c.execute('INSERT INTO tasks VALUES(?,?,?,?,?,?)',(T,'codex','failed',0,0,json.dumps({'parent_session':None,'error':'truncated_or_invalid_completion'})))
  def event(tool):
   return {'type':'event_msg','payload':{'type':'mcp_tool_call_end','invocation':{'server':'llm-router','tool':tool},'result':{'Ok':{'content':[{'type':'text','text':json.dumps({'task_id':T,'identity':'codex'})}]}}}}
  with path.open('a') as f:f.write(json.dumps(event('result'))+'\n')
  n=next(n for n in self.c.snapshot()['nodes'] if n.get('task_id')==T)
  self.assertIsNone(n['parent']);self.assertTrue(n['unattached'])
  with path.open('a') as f:f.write(json.dumps(event('submit'))+'\n')
  n=next(n for n in self.c.snapshot()['nodes'] if n.get('task_id')==T)
  self.assertEqual(n['parent'],P);self.assertEqual(n['error'],'truncated_or_invalid_completion')
  other=self.write(C)
  with other.open('a') as f:f.write(json.dumps(event('submit'))+'\n')
  self.c.scanned=0
  n=next(n for n in self.c.snapshot()['nodes'] if n.get('task_id')==T)
  self.assertIsNone(n['parent'])
